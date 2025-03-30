import requests
from requests.auth import HTTPBasicAuth

def upload_image_to_wordpress(site_url, username, app_password, image_url):
    """
    フリー画像URLを WordPress にアップロードし、media ID を取得する関数

    Parameters:
        site_url (str): WordPressサイトのURL（例: https://example.com）
        username (str): WordPressのユーザー名
        app_password (str): アプリケーションパスワード
        image_url (str): 画像の直接URL（Pixabayなど）

    Returns:
        int or None: アップロード成功時は media ID、失敗時は None
    """
    media_endpoint = f"{site_url}/wp-json/wp/v2/media"
    headers = {
        "Content-Disposition": "attachment; filename=featured.jpg",
        "Content-Type": "image/jpeg"
    }

    try:
        image_response = requests.get(image_url, timeout=15)
        image_response.raise_for_status()
        image_data = image_response.content

        response = requests.post(
            media_endpoint,
            headers=headers,
            data=image_data,
            auth=HTTPBasicAuth(username, app_password),
            timeout=20  # 🔧 タイムアウト追加
        )

        if response.status_code in [200, 201]:
            media_id = response.json().get("id")
            print("✅ 画像アップロード成功: media_id =", media_id)
            return media_id
        else:
            print(f"❌ アップロード失敗: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print("❌ 画像送信エラー:", str(e))
        return None


def post_to_wordpress_rest(site_url, username, app_password, title, content, featured_image_url=None):
    """
    WordPress REST API を使って記事を投稿する関数

    Parameters:
        site_url (str): サイトのURL（例: https://example.com）
        username (str): WordPressのユーザー名
        app_password (str): アプリケーションパスワード
        title (str): 投稿タイトル
        content (str): 投稿本文（HTML可）
        featured_image_url (str or None): アイキャッチ画像URL（あれば）

    Returns:
        response (requests.Response): 投稿結果のレスポンス
    """
    endpoint = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts"

    post_data = {
        "title": title,
        "content": content,
        "status": "publish"
    }

    # ✅ アイキャッチ画像を WordPress にアップして ID を取得
    if featured_image_url:
        media_id = upload_image_to_wordpress(site_url, username, app_password, featured_image_url)
        if media_id:
            post_data["featured_media"] = media_id

    try:
        response = requests.post(
            endpoint,
            json=post_data,
            auth=HTTPBasicAuth(username, app_password),
            timeout=20  # 🔧 タイムアウト追加
        )

        print("✅ 投稿レスポンス:", response.status_code)
        print(response.text)
        return response

    except Exception as e:
        print("❌ 投稿エラー:", str(e))
        return None
