import requests
from requests.auth import HTTPBasicAuth

def upload_image_to_wordpress(site_url, username, app_password, image_url):
    """
    画像を WordPress にアップロードし、media ID を取得
    """
    media_endpoint = f"{site_url.rstrip('/')}/wp-json/wp/v2/media"
    headers = {
        "Content-Disposition": "attachment; filename=featured.jpg",
        "Content-Type": "image/jpeg",
        "User-Agent": "AutoPoster/1.0"
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
            timeout=20
        )

        if response.ok:
            media_id = response.json().get("id")
            print(f"✅ 画像アップロード成功: media_id = {media_id}")
            return media_id
        else:
            print(f"❌ 画像アップロード失敗: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print("❌ 画像送信中の例外エラー:", str(e))
        return None


def post_to_wordpress_rest(site_url, username, app_password, title, content, featured_image_url=None):
    """
    WordPress REST API を使って記事を投稿する関数
    """
    endpoint = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "AutoPoster/1.0"
    }

    post_data = {
        "title": title,
        "content": content,
        "status": "publish"
    }

    if featured_image_url:
        media_id = upload_image_to_wordpress(site_url, username, app_password, featured_image_url)
        if media_id:
            post_data["featured_media"] = media_id

    try:
        response = requests.post(
            endpoint,
            json=post_data,
            headers=headers,
            auth=HTTPBasicAuth(username, app_password),
            timeout=20
        )

        if response.ok:
            print(f"🚀 投稿成功: {response.status_code}")
        else:
            print(f"❌ 投稿失敗: {response.status_code}")
            print(f"📨 送信データ: {post_data}")
            print(f"📥 レスポンス: {response.text}")

        return response

    except Exception as e:
        print("❌ 投稿中に例外エラー:", str(e))
        print(f"📨 送信データ: {post_data}")
        return None
