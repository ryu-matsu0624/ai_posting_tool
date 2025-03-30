import os
import requests
from datetime import datetime
from flask import Flask
from models import db, Article, WordPressSite
from requests.auth import HTTPBasicAuth
from keywords import generate_image_plan
from wordpress_client import upload_image_to_wordpress

# ✅ Flaskアプリ初期化（DB接続用）
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "instance", "mydatabase.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# ✅ 記事本文に画像を挿入する関数
def insert_images_into_content(content, keyword, title):
    image_plan = generate_image_plan(content, keyword, title, max_images=3)
    for plan in image_plan:
        paragraph_index = plan.get("paragraph_index")
        image_url = plan.get("image_url")
        if not image_url:
            continue
        paragraphs = content.split("\n\n")
        if 0 <= paragraph_index < len(paragraphs):
            img_tag = f'<div style="text-align:center;"><img src="{image_url}" alt="{keyword}" style="max-width:100%; height:auto;"></div>'
            paragraphs[paragraph_index] += f"\n\n{img_tag}"
        content = "\n\n".join(paragraphs)
    return content

# ✅ メイン投稿処理（スケジュール確認 + 投稿）
def main():
    with app.app_context():
        now = datetime.now()
        articles = Article.query.filter(
            Article.scheduled_time <= now,
            Article.status == 'scheduled'
        ).all()

        for article in articles:
            site = WordPressSite.query.get(article.site_id)
            print(f"\n▶ 投稿対象: {article.title}（サイト: {site.site_name}）")

            # 本文に画像を挿入
            article.content = insert_images_into_content(
                article.content,
                keyword=article.keyword,
                title=article.title
            )

            # 投稿URL（https強制）
            site_url = site.url.strip().replace("http://", "https://").rstrip("/")
            post_url = f"{site_url}/wp-json/wp/v2/posts"

            # 投稿データ生成
            post_data = {
                "title": article.title,
                "content": article.content,
                "status": "publish"
            }

            # ✅ アイキャッチ画像が指定されていればアップロード
            if article.image_prompt:
                media_id = upload_image_to_wordpress(site_url, site.wp_username, site.wp_app_password, article.image_prompt)
                if media_id:
                    post_data["featured_media"] = media_id

            # 投稿送信
            try:
                auth = HTTPBasicAuth(site.wp_username, site.wp_app_password)
                response = requests.post(post_url, json=post_data, auth=auth)

                if response.status_code == 201:
                    article.status = 'posted'
                    db.session.commit()
                    print(f"✅ 投稿完了: {article.title}")
                else:
                    print(f"❌ 投稿失敗: {article.title}")
                    print("🔴 ステータス:", response.status_code)
                    print("🔴 レスポンス:", response.text)

            except Exception as e:
                print(f"❌ 投稿処理エラー: {article.title} - {e}")

# ✅ CLI実行用
if __name__ == "__main__":
    main()
