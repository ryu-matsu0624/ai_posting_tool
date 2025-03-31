import threading
import traceback
from concurrent.futures import ThreadPoolExecutor

from models import db, Article, Keyword
from keywords import (
    generate_title_prompt,
    generate_content_prompt,
    generate_image_prompt,
    search_pixabay_images,
    insert_images_into_content
)

MAX_WORKERS = 3  # 同時に何記事処理するか（Renderのリソースと相談）

def process_article(site_id, kw):
    try:
        print(f"🟡 [{kw.keyword}] 記事処理開始")

        article = Article.query.filter_by(site_id=site_id, keyword=kw.keyword).first()
        if not article or article.status != "pending":
            print(f"⏭ [{kw.keyword}] スキップ（記事なし or ステータス未対応）")
            return

        # タイトル生成
        title = generate_title_prompt(kw.keyword)
        if not title:
            print(f"⚠️ [{kw.keyword}] タイトル生成失敗")
            article.status = "error"
            db.session.commit()
            return

        # 本文生成
        content = generate_content_prompt(title)
        if not content:
            print(f"⚠️ [{kw.keyword}] 本文生成失敗")
            article.status = "error"
            db.session.commit()
            return

        # 本文に画像挿入
        content_with_images = insert_images_into_content(content, kw.keyword, title)

        # アイキャッチ画像
        image_prompt = generate_image_prompt(content, kw.keyword, title)
        image_results = search_pixabay_images(image_prompt)
        featured_image_url = image_results[0] if image_results else None

        # 最終チェック
        if not all([title, content_with_images]):
            print(f"⚠️ [{kw.keyword}] 最終チェック失敗（title/contentなし）")
            article.status = "error"
            db.session.commit()
            return

        # DB更新
        article.title = title
        article.content = content_with_images
        article.image_prompt = featured_image_url
        article.status = "scheduled"
        db.session.commit()

        print(f"✅ [{kw.keyword}] 記事生成完了")

    except Exception as e:
        db.session.rollback()
        print(f"❌ [{kw.keyword}] 例外エラー発生: {e}")
        traceback.print_exc()
        try:
            article.status = "error"
            db.session.commit()
        except:
            print(f"⚠️ [{kw.keyword}] DB更新も失敗")

def generate_articles_for_site(site):
    from app import app

    def _task():
        try:
            with app.app_context():
                keywords = Keyword.query.filter_by(site_id=site.id).all()

                # 並列処理で複数記事を同時生成
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    for kw in keywords:
                        executor.submit(process_article, site.id, kw)
        except Exception as e:
            print("❌ generate_articles_for_site() 全体で例外:", e)
            traceback.print_exc()

    # スレッドで非同期実行
    threading.Thread(target=_task).start()
