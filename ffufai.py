#!/usr/bin/env python3

import argparse
import os
import subprocess
import requests
import json
import re
from openai import OpenAI
import anthropic
from urllib.parse import urlparse
import tempfile
import os
from bs4 import BeautifulSoup

def get_api_key(cli_api_key=None, cli_api_base_url=None, cli_api_type=None):
    # Priority: CLI args > environment variables
    if cli_api_key:
        if cli_api_type == 'openai':
            return ('openai', cli_api_key, None)
        elif cli_api_type == 'anthropic':
            return ('anthropic', cli_api_key, None)
        elif cli_api_type == 'zai':
            if not cli_api_base_url:
                raise ValueError("--api-base-url is required when --api-type is 'zai'.")
            return ('zai', cli_api_key, cli_api_base_url)
        else:
            # Auto-detect based on whether base_url is provided
            if cli_api_base_url:
                return ('zai', cli_api_key, cli_api_base_url)
            else:
                return ('anthropic', cli_api_key, None)

    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    # z.ai uses ANTHROPIC_AUTH_TOKEN + ANTHROPIC_BASE_URL
    zai_key = os.getenv('ANTHROPIC_AUTH_TOKEN')
    zai_base_url = os.getenv('ANTHROPIC_BASE_URL')

    if zai_key and zai_base_url:
        return ('zai', zai_key, zai_base_url)
    elif anthropic_key:
        return ('anthropic', anthropic_key, None)
    elif openai_key:
        return ('openai', openai_key, None)
    else:
        raise ValueError("No API key found. Use --api-key or set ANTHROPIC_AUTH_TOKEN+ANTHROPIC_BASE_URL (z.ai), ANTHROPIC_API_KEY, or OPENAI_API_KEY.")


def get_response(url):
    try:
        response = requests.get(url, allow_redirects=True)

        soup = BeautifulSoup(response.content, 'html.parser')

        for tag in soup.select('style, link[rel="stylesheet"]'):
            tag.decompose()

        for tag in soup.find_all(True):
            if hasattr(tag, 'attrs') and tag.attrs is not None:
                tag.attrs.pop('style', None)

            if tag.name == 'svg':
                tag.decompose()
            if tag.name == 'img':
                tag.decompose()

        content = soup.prettify()

        return {
            "url": response.url,
            "headers": dict(response.headers),
            "cookies": dict(response.cookies),
            "content": content[:2500]
        }

    except requests.RequestException as e:
        print(f"Error fetching content: {e}")
        return {"error": "Error fetching content."}

def get_headers(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        return dict(response.headers)
    except requests.TooManyRedirects:
        try:
            response = requests.get(url, allow_redirects=False, timeout=10)
            return dict(response.headers)
        except requests.RequestException as e:
            print(f"Error fetching headers: {e}")
            return {"Header": "Error fetching headers."}
    except requests.RequestException as e:
        print(f"Error fetching headers: {e}")
        return {"Header": "Error fetching headers."}

def create_anthropic_client(api_key, base_url=None):
    if base_url:
        return anthropic.Anthropic(api_key=api_key, base_url=base_url)
    return anthropic.Anthropic(api_key=api_key)

def parse_json_response(text):
    """Parse JSON from AI response, stripping markdown code blocks if present."""
    text = text.strip()
    # Strip markdown code block wrapping like ```json ... ```
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        text = match.group(1)
    return json.loads(text.strip())

def get_ai_extensions(url, headers, api_type, api_key, api_base_url, max_extensions):
    prompt = f"""
    Given the following URL and HTTP headers, suggest the most likely file extensions for fuzzing this endpoint.
    Respond with a JSON object containing a list of extensions. The response will be parsed with json.loads(),
    so it must be valid JSON. No preamble or yapping. Use the format: {{"extensions": [".ext1", ".ext2", ...]}}.
    Do not suggest more than {max_extensions}, but only suggest extensions that make sense. For example, if the path is
    /js/ then don't suggest .css as the extension. Also, if limited, prefer the extensions which are more interesting.
    The URL path is great to look at for ideas. For example, if it says presentations, then it's likely there
    are powerpoints or pdfs in there. If the path is /js/ then it's good to use js as an extension.

    Examples:
    1. URL: https://example.com/presentations/FUZZ
       Headers: {{"Content-Type": "application/pdf", "Content-Length": "1234567"}}
       JSON Response: {{"extensions": [".pdf", ".ppt", ".pptx"]}}

    2. URL: https://example.com/FUZZ
       Headers: {{"Server": "Microsoft-IIS/10.0", "X-Powered-By": "ASP.NET"}}
       JSON Response: {{"extensions": [".aspx", ".asp", ".exe", ".dll"]}}

    URL: {url}
    Headers: {headers}

    JSON Response:
    """

    if api_type == 'openai':
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that suggests file extensions for fuzzing based on URL and headers."},
                {"role": "user", "content": prompt}
            ]
        )
        return parse_json_response(response.choices[0].message.content)
    elif api_type in ('anthropic', 'zai'):
        client = create_anthropic_client(api_key, api_base_url)
        model = os.getenv('ZAI_MODEL', 'claude-sonnet-4')
        message = client.messages.create(
            model=model,
            max_tokens=1000,
            temperature=0,
            system="You are a helpful assistant that suggests file extensions for fuzzing based on URL and headers.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )


        return parse_json_response(message.content[0].text)

def get_contextual_wordlist(url, headers, api_type, api_key, api_base_url, max_size, cookies=None, content=None):
    prompt = f"""
    Given the following URL and HTTP headers, suggest the most likely contextual wordlist for content discovery on this endpoint.
    Be as extensive as possible, provide the maximum number of directories and files that make sense for the endpoint.
    Try to create a list of size {max_size}.
    Respond with a JSON object containing a list of directories and files. The response will be parsed with json.loads(),
    so it must be valid JSON. No preamble or yapping. Use the format: { {"wordlist": ["dir1", "dir2", "file1", "file2"]} }.
    Only make suggestions that make sense. For example, if domain is for a book shop
    then don't suggest footbal as a directory. Also, if limited, prefer the files and directories which are more interesting.
    The URL path is great to look at for ideas, and so is the brand behind the URL.
    Focus on contents relevant to the identified industry and technology stack. Include technology-specific files.
    For example, if it says presentations, then it's likely there are powerpoints or pdfs in there. If the path is /js/ then it's good to fuzz for JS files.

    Example 1: WordPress Blog
    URL: https://blog.techstartup.io/wp-content/uploads/2024/FUZZ
    Headers: {{
      "Server": "nginx/1.22.1",
      "X-Powered-By": "PHP/8.1.2",
      "Link": "<https://blog.techstartup.io/wp-json/>; rel=\"https://api.w.org/\"",
      "Content-Type": "image/jpeg"
    }}

    Response:
    {{
      "wordlist": ["wp-content", "wp-includes", "wp-admin", "uploads", "themes", "plugins", "2024", "2023", "backup", "cache", "wp-config.php", "xmlrpc.php", "wp-login.php", "readme.html", ".htaccess", "wp-config.php.bak", "debug.log"],
    }}

    Example 2: E-commerce Platform
    URL: https://shop.globalretail.com/checkout/payment/FUZZ
    Headers:
    {{
      "Server": "Microsoft-IIS/10.0",
      "X-Powered-By": "ASP.NET",
      "X-AspNet-Version": "4.0.30319",
      "X-Frame-Options": "SAMEORIGIN",
      "Strict-Transport-Security": "max-age=31536000"
    }}

    Response:
    {{
      "wordlist": ["checkout", "payment", "api", "admin", "account", "orders", "products", "cart", "invoice", "App_Data", "bin", "Content", "web.config", "Global.asax", "payment.aspx", "checkout.aspx", "web.config.bak", "App_Data.mdf", "connectionstrings.config"],
    }}

    URL: {url}
    Headers: {headers}
    Cookies: {cookies}
    Content: {content}

    JSON Response:
    """

    if api_type == 'openai':
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that suggests wordlists for fuzzing based on URL and headers."},
                {"role": "user", "content": prompt}
            ]
        )
        return parse_json_response(response.choices[0].message.content)

    elif api_type in ('anthropic', 'zai'):
        client = create_anthropic_client(api_key, api_base_url)
        model = os.getenv('ZAI_MODEL', 'claude-sonnet-4')
        message = client.messages.create(
            model=model,
            max_tokens=10000,
            temperature=0,
            system="You are a helpful assistant that suggests wordlists for fuzzing based on URL and headers.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return parse_json_response(message.content[0].text)

def main():
    parser = argparse.ArgumentParser(description='ffufai - AI-powered ffuf wrapper')
    parser.add_argument('--ffuf-path', default='ffuf', help='Path to ffuf executable')
    parser.add_argument('--max-extensions', type=int, default=4, help='Maximum number of extensions to suggest')
    parser.add_argument('--wordlists', action='store_true', help='Generate contextual wordlists')
    parser.add_argument('--max-wordlist-size', type=int, help="The maximum size of the generated wordlist")
    parser.add_argument('--include-response', action='store_true', help='Makes a GET request and uses the Response as context for better wordlist generation (Uses More tokens)')
    parser.add_argument('--api-key', help='API key (Anthropic, OpenAI, or z.ai)')
    parser.add_argument('--api-base-url', help='API base URL (required for z.ai)')
    parser.add_argument('--api-type', choices=['openai', 'anthropic', 'zai'], help='API type (auto-detected if omitted)')
    args, unknown = parser.parse_known_args()

    # Find the -u argument in the unknown args
    try:
        url_index = unknown.index('-u') + 1
        url = unknown[url_index]
    except (ValueError, IndexError):
        print("Error: -u URL argument is required.")
        return

    parsed_url = urlparse(url)
    path_parts = parsed_url.path.split('/')
    base_url = url.replace('FUZZ', '')

    if 'FUZZ' not in path_parts[-1]:
        print("Warning: FUZZ keyword is not at the end of the URL path. Extension fuzzing may not work as expected.")

    headers = get_headers(base_url)

    api_type, api_key, api_base_url = get_api_key(
        cli_api_key=args.api_key,
        cli_api_base_url=args.api_base_url,
        cli_api_type=args.api_type
    )


    if args.wordlists:
        try:
            if args.max_wordlist_size:
                size = args.max_wordlist_size
            else:
                size = 200

            if args.include_response:
                response = get_response(base_url)
                headers = response['headers']
                cookies = response['cookies']
                content = response['content']
                wordlists_data = get_contextual_wordlist(url, headers, api_type, api_key, api_base_url, size, cookies=cookies, content=content)

            else:
                wordlists_data = get_contextual_wordlist(url, headers, api_type, api_key, api_base_url, size)

            print(wordlists_data)
            wordlist = '\n'.join(wordlists_data['wordlist'])

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing AI response. The Wordlist size may have been too big for your max_tokens. Try again. Error: {e}")
            return

        if wordlist:
            file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
            file.write(wordlist)
            file.close()
            ffuf_command = [args.ffuf_path] + unknown + ['-w', file.name]
            subprocess.run(ffuf_command)


    else:
        try:
            extensions_data = get_ai_extensions(url, headers, api_type, api_key, api_base_url, args.max_extensions)
            print(extensions_data)
            extensions = ','.join(extensions_data['extensions'][:args.max_extensions])

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing AI response. Try again. Error: {e}")
            return

        ffuf_command = [args.ffuf_path] + unknown + ['-e', extensions]

        subprocess.run(ffuf_command)


if __name__ == '__main__':
    main()
