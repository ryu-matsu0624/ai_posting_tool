# article_generator.py

import threading
from models import db, Article, Keyword
from keywords import (
    generate_title_prompt,
    generate_content_prompt,
    insert_images_into_content,
    generate_image_prompt,
    search_pixabay_images
)

def generate_articles_for_site(site):
    """
    サイトに紐づくキーワードに基づいて記事を1つずつ順番に生成。
    """
    from app import app  # 循環インポート回避

    def _task():
        with app.app_context():
            keywords = Keyword.query.filter_by(site_id=site.id).all()
            for kw in keywords:
                article = Article.query.filter_by(site_id=site.id, keyword=kw.keyword).first()
                if not article or article.status != "pending":
                    continue

                try:
                    title = generate_title_prompt(kw.keyword)
                    content = generate_content_prompt(title)
                    content_with_images = insert_images_into_content(content, kw.keyword, title)
                    image_prompt = generate_image_prompt(content, kw.keyword, title)
                    image_results = search_pixabay_images(image_prompt)
                    featured_image_url = image_results[0] if image_results else None

                    article.title = title
                    article.content = content_with_images
                    article.image_prompt = featured_image_url
                    article.status = "scheduled"
                    db.session.commit()

                except Exception as e:
                    print(f"❌ 記事生成エラー: {kw.keyword} - {e}")

    threading.Thread(target=_task).start()
