from fastapi_cache.decorator import cache
import json
import re, os
import requests, ssl
from app.config.env import environment
from app.config import app_config
from cachetools import TTLCache
import time

app_configs = app_config.AppConfig.get_all_configs()

# Cache to store the token for 300 seconds (5 minutes)
token_cache = TTLCache(maxsize=1, ttl=3600)

def api_access_token():
    url = "https://login-itg.external.hp.com/as/token.oauth2"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": "HPIUIDITG=0LDlPLBnLGAYz4Lmwrgfck",
    }

    data = {
        "grant_type": "client_credentials",
        "client_id": "fCVyTLUc1C4yJwnfDSFdc0YMqlzxCrr7",
        "client_secret": "gzjWw1GBah37dxueZM7CtytExqaNLNP4KNCXzQTDA5sDBx4gfKpNPMFY1jo7cE2v",
    }

    response = requests.post(url, headers=headers, data=data)

    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Failed to get token: {response.status_code}")
        print(response.text)
        return None

def get_api_access_token():
    if 'token' not in token_cache:
        print("Fetching new token...")
        token_cache['token'] = api_access_token()
    else:
        print("Using cached token.")
    return token_cache['token']



@cache(expire=3600)
async def get_kaas_access_token1():
    """
    Fetches an access token from the API using the provided configuration.
    Returns:
        str: The access token on success, throws on failure HTTPError 401 Unauthorized.
    """
    auth_url = app_configs["kaas_auth_url"]
    auth_params = {
        "grant_type": "client_credentials",
        "client_id": app_configs["kaas_auth_client_id"],
        "client_secret": environment.AUTH_KAAS_CLIENT_SECRET,
    }
    print("auth_params:", auth_params)
    response = requests.post(auth_url, data=auth_params)
    response.raise_for_status()
    auth_data = response.json()
    access_token = auth_data.get("access_token")
    return access_token

@cache(expire=3600)
def get_kaas_access_token():
    auth_url = 'https://css.api.hp.com/oauth/accesstoken'
    auth_params = {
        'grant_type': 'client_credentials',
        'client_id': 'oVKELXf84JwfA1YKnAAAMt15mPs8T1BW',
        'client_secret': 'P2mEXdvp9UxBIkyNl4VlmH4bEL4ekuEl'
    }
    try:
        response = requests.post(auth_url, data=auth_params)
        response.raise_for_status()
        auth_data = response.json()
        access_token = response.json()["access_token"]
        if access_token:
            return access_token
        else:
            print("Error: Access token not found in response.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error in authentication request: {e}")
        return None
    
def getKaasLink(url, token=get_kaas_access_token()):

    payload = ""
    headers = {'Content-Type': 'application/json',
               "Authorization": f"Bearer {token}"}
    response=""

    if "extras_kaas" in url:
        response_temp = requests.get(url, headers=headers,verify=ssl.CERT_NONE)
        if response_temp.status_code==200:
            response=json.loads(response_temp.text)["render_link"]
        else:
            print(f"Error calling KaaS API")
            response = url
    else:
        response=url
    return response

def extract_markdown_links(markdown_text):
    """
    Extracts all hyperlinks from Markdown content.

    Args:
    - markdown_text (str): The Markdown content as a string.

    Returns:
    - List of tuples: [(link_text, url), ...]
    """

    pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'  # Regex to match [text](URL)
    links = re.findall(pattern, markdown_text)
    return links


def update_markdown_links(content, token):
    """
    Updates Markdown links by replacing multiple old URLs with new URLs containing dynamic tokens.

    """
    # Read the Markdown file
    url_mappings={}
    for text, url in extract_markdown_links(content):
        url_mappings[url] = getKaasLink(url,token)

    for old_url, new_url in url_mappings.items():
        # Generate a new token for each URL replacement


        # Regex pattern to match Markdown links: [text](old_url)
        pattern = rf'(\[.*?\])\({re.escape(old_url)}\)'

        # Replace old URL with new URL (containing the token)
        content = re.sub(pattern, rf'\1({new_url})', content)

        print(f"Updated {old_url} → {new_url}")

    # Write back the updated content
    return content

def get_text_embedding(input_text):
    try:
        #time.sleep(0.5)  # Slight delay to avoid rate limits

        token = get_api_access_token()
        url = (
            "https://davinci-dev-openai-api.corp.hpicloud.net/"
            "knowledgechatbot/openai/deployments/text-embedding-ada-002/"
            "embeddings?api-version=2023-05-15"
        )

        payload = json.dumps(
            {"input": input_text, "model": "text-embedding-ada-002"}
        )

        headers = {
            "api-key": "68201d536a9c4a8c94758292020a33d3",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        response = requests.post(url, headers=headers, data=payload, verify=False)
        response.raise_for_status()  # raises error for HTTP status codes like 4xx or 5xx

        data = response.json()
        return data["data"][0]["embedding"]

    except Exception as e:
        print(f"❌ Error during embedding generation: {e}")
        return None



def trust_only_custom_ca(custom_ca_path): 
    os.environ['REQUESTS_CA_BUNDLE'] = custom_ca_path 
    os.environ['SSL_CERT_FILE'] = custom_ca_path 



async def bulkrenderlink(documentIDs: list[str], language):
    access_token = await get_kaas_access_token1()
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + access_token,
    }

    data = {
        "languageCode": language,
        "requests": [
            {
                "languageCode": language,
                "ids": documentIDs,
            },
        ],
    }

    response = requests.post(
        app_configs["bulk_render_url"], headers=headers, json=data
    )
    response.raise_for_status()
    response_data = response.json()
    render_links = {
        i["id"]: i["renderLink"]
        for i in response_data[0]["renderLinks"]
        if "renderLink" in i
    }
    return render_links
