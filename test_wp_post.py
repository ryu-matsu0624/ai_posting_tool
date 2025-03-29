import requests
from requests.auth import HTTPBasicAuth

def post_to_wordpress_rest(site_url, username, app_password, title, content):
    """
    WordPress REST API を使って記事を投稿する関数

    Parameters:
        site_url (str): サイトのURL（例: "https://example.com"）※httpではなくhttps!!
        username (str): WordPressのユーザー名
        app_password (str): WordPressで生成したアプリケーションパスワード
        title (str): 投稿する記事タイトル
        content (str): 投稿する記事本文

    Returns:
        response (requests.Response): 投稿のレスポンスオブジェクト
    """
    endpoint = f"{site_url}/wp-json/wp/v2/posts"

    post_data = {
        "title": title,
        "content": content,
        "status": "publish"
    }

    try:
        response = requests.post(
            endpoint,
            json=post_data,
            auth=HTTPBasicAuth(username, app_password)
        )
        print("✅ WordPress 投稿レスポンス:", response.status_code)
        print(response.text)
        return response

    except Exception as e:
        print("❌ 投稿エラー:", str(e))
        return None
