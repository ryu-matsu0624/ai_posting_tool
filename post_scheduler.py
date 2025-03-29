import os
import requests
from datetime import datetime
from flask import Flask
from models import db, Article, WordPressSite
from requests.auth import HTTPBasicAuth
from keywords import generate_image_plan, search_pixabay_images

# ✅ Flaskアプリ初期化（DB接続用）
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "instance", "mydatabase.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# ✅ 画像をHTMLで挿入する関数
def insert_images_into_content(content, keyword, title):
    image_plan = generate_image_plan(content, keyword, title, max_images=3)
    for plan in image_plan:
        paragraph_index = plan.get("paragraph_index")
        image_url = plan.get("image_url")
        if not image_url:
            continue

        # content を段落に分割
        paragraphs = content.split("\n\n")
        if 0 <= paragraph_index < len(paragraphs):
            # HTML の <img> タグを挿入
            img_tag = f'<div style="text-align:center;"><img src="{image_url}" alt="{keyword}" style="max-width:100%; height:auto;"></div>'
            paragraphs[paragraph_index] += f"\n\n{img_tag}"

        content = "\n\n".join(paragraphs)

    return content

# ✅ メイン投稿処理（スケジュールチェック + 自動投稿）
def main():
    with app.app_context():
        now = datetime.now()
        scheduled_articles = Article.query.filter(
            Article.scheduled_time <= now,
            Article.status == 'scheduled'
        ).all()

        for article in scheduled_articles:
            site = WordPressSite.query.get(article.site_id)

            # ✅ 記事内容に画像を挿入
            article.content = insert_images_into_content(
                article.content,
                keyword=article.keyword,
                title=article.title
            )

            # ✅ WordPress投稿処理（REST API）
            try:
                post_url = f"{site.url.rstrip('/')}/wp-json/wp/v2/posts"
                post_data = {
                    "title": article.title,
                    "content": article.content,
                    "status": "publish"
                }
                auth = HTTPBasicAuth(site.wp_username, site.wp_app_password)
                response = requests.post(post_url, json=post_data, auth=auth)

                if response.status_code == 201:
                    article.status = 'posted'
                    db.session.commit()
                    print(f"✅ 投稿完了: {article.title}")
                else:
                    print(f"❌ 投稿失敗: {article.title} - {response.status_code} - {response.text}")

            except Exception as e:
                print(f"❌ 投稿中にエラー発生: {article.title} - {e}")

# ✅ CLIから実行
if __name__ == "__main__":
    main()
