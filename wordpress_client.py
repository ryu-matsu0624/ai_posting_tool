# wordpress_client.py
import requests
from requests.auth import HTTPBasicAuth

def post_to_wordpress_rest(site_url, username, app_password, title, content):
    post_url = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts"
    
    data = {
        "title": title,
        "content": content,
        "status": "publish"
    }

    auth = HTTPBasicAuth(username, app_password)
    response = requests.post(post_url, json=data, auth=auth)

    return response
