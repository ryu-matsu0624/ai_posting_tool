import threading
import traceback
from models import db, Article, Keyword
from keywords import (
    generate_title_prompt,
    generate_content_prompt,
    generate_image_prompt,
    search_pixabay_images,
    insert_images_into_content
)

def generate_articles_for_site(site):
    """
    サイトに紐づくキーワードに基づいて記事を1つずつ順番に生成。
    """
    from app import app  # 🔁 循環インポート防止のため関数内に記述

    def _task():
        with app.app_context():
            keywords = Keyword.query.filter_by(site_id=site.id).all()

            for kw in keywords:
                article = Article.query.filter_by(site_id=site.id, keyword=kw.keyword).first()
                if not article or article.status != "pending":
                    continue

                try:
                    print(f"🔍 '{kw.keyword}' のタイトルを生成中...")
                    title = generate_title_prompt(kw.keyword)
                    if not title:
                        print(f"⚠️ タイトル生成失敗: {kw.keyword}")
                        continue

                    print(f"📝 '{title}' の本文を生成中...")
                    content = generate_content_prompt(title)
                    if not content:
                        print(f"⚠️ コンテンツ生成失敗: {kw.keyword}")
                        continue

                    print(f"🖼️ 画像を本文に挿入中...")
                    content_with_images = insert_images_into_content(content, kw.keyword, title)

                    print(f"🔎 画像検索プロンプト作成中...")
                    image_prompt = generate_image_prompt(content, kw.keyword, title)
                    image_results = search_pixabay_images(image_prompt)
                    featured_image_url = image_results[0] if image_results else None

                    article.title = title
                    article.content = content_with_images
                    article.image_prompt = featured_image_url
                    article.status = "scheduled"

                    db.session.commit()
                    print(f"✅ 記事生成完了: {kw.keyword}")

                except Exception as e:
                    db.session.rollback()
                    print(f"❌ 記事生成エラー: {kw.keyword} - {e}")
                    traceback.print_exc()

    # 🔄 別スレッドでバックグラウンド実行
    threading.Thread(target=_task).start()
