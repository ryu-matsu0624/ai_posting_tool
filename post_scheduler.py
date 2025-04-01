# post_scheduler.py

from datetime import datetime
from app_init import app  # ✅ app_init.py から app を読み込む
from models import db, Article, WordPressSite, PostLog
from keywords import generate_image_plan
from wordpress_client import upload_image_to_wordpress
from requests.auth import HTTPBasicAuth
import requests

# 画像挿入ロジック
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

# 投稿処理
def main():
    with app.app_context():
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        articles = Article.query.filter(
            Article.scheduled_time <= now,
            Article.status == 'scheduled'
        ).order_by(Article.scheduled_time.asc()).all()

        for article in articles:
            site = WordPressSite.query.get(article.site_id)
            print(f"\n▶ 投稿対象: {article.title}（サイト: {site.site_name}）")

            posted_today = Article.query.filter(
                Article.site_id == site.id,
                Article.status == 'posted',
                Article.scheduled_time >= today_start
            ).count()

            if posted_today >= 3:
                print(f"⏭️ スキップ: {site.site_name} は本日すでに 3件 投稿済")
                continue

            article.content = insert_images_into_content(
                article.content,
                keyword=article.keyword,
                title=article.title
            )

            site_url = site.url.strip().replace("http://", "https://").rstrip("/")
            post_url = f"{site_url}/wp-json/wp/v2/posts"

            post_data = {
                "title": article.title,
                "content": article.content,
                "status": "publish"
            }

            # アイキャッチ画像
            if article.image_prompt:
                media_id = upload_image_to_wordpress(
                    site_url, site.wp_username, site.wp_app_password, article.image_prompt
                )
                if media_id:
                    post_data["featured_media"] = media_id

            try:
                auth = HTTPBasicAuth(site.wp_username, site.wp_app_password)
                response = requests.post(post_url, json=post_data, auth=auth)

                if response.status_code == 201:
                    article.status = 'posted'
                    db.session.add(PostLog(
                        article_id=article.id,
                        status="成功",
                        response_message=response.text
                    ))
                    db.session.commit()
                    print(f"✅ 投稿完了: {article.title}")

                else:
                    db.session.add(PostLog(
                        article_id=article.id,
                        status="失敗",
                        response_message=response.text
                    ))
                    db.session.commit()
                    print(f"❌ 投稿失敗: {article.title}")
                    print("🔴 ステータス:", response.status_code)
                    print("🔴 レスポンス:", response.text)

            except Exception as e:
                db.session.rollback()
                db.session.add(PostLog(
                    article_id=article.id,
                    status="失敗",
                    response_message=str(e)
                ))
                db.session.commit()
                print(f"❌ 投稿処理エラー: {article.title} - {e}")

# 実行
if __name__ == "__main__":
    main()
