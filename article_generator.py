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
    from app import app

    def _task():
        with app.app_context():
            keywords = Keyword.query.filter_by(site_id=site.id).all()

            for kw in keywords:
                # ✴️ ここで事前に記事がなければスキップ
                article = Article.query.filter_by(site_id=site.id, keyword=kw.keyword).first()
                if not article or article.status != "pending":
                    print(f"⏭ スキップ: {kw.keyword}（記事が存在しないか、pendingでない）")
                    continue

                try:
                    print(f"🔍 タイトル生成中: {kw.keyword}")
                    title = generate_title_prompt(kw.keyword)
                    if not title:
                        print(f"⚠️ タイトル生成失敗: {kw.keyword}")
                        continue

                    print(f"📝 コンテンツ生成中: {title}")
                    content = generate_content_prompt(title)
                    if not content:
                        print(f"⚠️ コンテンツ生成失敗: {kw.keyword}")
                        continue

                    print(f"🖼️ 画像挿入中: {kw.keyword}")
                    content_with_images = insert_images_into_content(content, kw.keyword, title)

                    image_prompt = generate_image_prompt(content, kw.keyword, title)
                    image_results = search_pixabay_images(image_prompt)
                    featured_image_url = image_results[0] if image_results else None

                    # 🔐 もう一度チェック（念のため）
                    if not all([title, content_with_images]):
                        print(f"⚠️ 最終チェックでNULLが検出されました: {kw.keyword}")
                        continue

                    # ✅ 更新処理
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

    threading.Thread(target=_task).start()
