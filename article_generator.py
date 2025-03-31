import threading
import traceback
import random
from datetime import datetime, timedelta, time as dtime
from concurrent.futures import ThreadPoolExecutor

from models import db, Article, Keyword
from keywords import (
    generate_title_prompt,
    generate_content_prompt,
    generate_image_prompt,
    search_pixabay_images,
    insert_images_into_content
)

MAX_WORKERS = 3  # 並列で処理する記事数（Renderのリソースと相談）

def generate_scheduled_times(keyword_count):
    """
    指定されたキーワード数に応じて、1日3記事ずつのランダムな投稿時間を生成
    """
    scheduled_times = []
    for i in range(keyword_count):
        day_offset = i // 3  # 1日3記事まで
        post_day = datetime.now().date() + timedelta(days=day_offset)

        # 平日と休日で時間帯を分ける
        weekday = post_day.weekday()
        hour_range = (7, 15) if weekday >= 5 else (10, 20)

        base_hour = random.randint(*hour_range)
        base_minute = random.randint(0, 59)
        buffer = random.randint(-10, 10)
        final_minute = base_minute + buffer
        final_hour = base_hour + final_minute // 60
        final_minute %= 60
        final_hour = max(6, min(final_hour, 22))

        dt = datetime.combine(post_day, dtime.min).replace(hour=final_hour, minute=final_minute)
        scheduled_times.append(dt)
    return scheduled_times

def process_article(site_id, kw, scheduled_time):
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

        # アイキャッチ画像生成
        image_prompt = generate_image_prompt(content, kw.keyword, title)
        image_results = search_pixabay_images(image_prompt)
        featured_image_url = image_results[0] if image_results else None

        # 最終チェック
        if not all([title, content_with_images]):
            print(f"⚠️ [{kw.keyword}] title or content missing")
            article.status = "error"
            db.session.commit()
            return

        # データベース更新
        article.title = title
        article.content = content_with_images
        article.image_prompt = featured_image_url
        article.scheduled_time = scheduled_time
        article.status = "scheduled"
        db.session.commit()

        print(f"✅ [{kw.keyword}] 記事生成完了 & scheduled")

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
                if not keywords:
                    print(f"⚠️ [{site.id}] キーワードがありません")
                    return

                print(f"📝 [{site.site_name}] 記事生成を開始します（{len(keywords)}件）")

                scheduled_times = generate_scheduled_times(len(keywords))

                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    for i, kw in enumerate(keywords):
                        executor.submit(process_article, site.id, kw, scheduled_times[i])

        except Exception as e:
            print("❌ generate_articles_for_site 全体例外:", e)
            traceback.print_exc()

    threading.Thread(target=_task).start()
