import os
import smtplib
import requests
from datetime import datetime
from flask import Flask
from models import db, Article, WordPressSite
from requests.auth import HTTPBasicAuth
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ✅ Flaskアプリ初期化（DB接続用）
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "instance", "mydatabase.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# ✅ メール通知関数
def send_completion_email(to_email, site_name, article_titles):
    sender_email = "your_gmail@gmail.com"
    sender_password = "アプリパスワード"  # セキュアに管理するのがベスト

    subject = f"✅ {site_name} の全記事投稿が完了しました！"
    body = f"{site_name} に対する以下の全記事投稿が完了しました：\n\n"
    for title in article_titles:
        body += f"・{title}\n"
    body += "\nお疲れさまでした！"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print("✅ メール通知を送信しました。")
    except Exception as e:
        print(f"❌ メール送信失敗: {e}")

# ✅ メイン投稿処理（REST API）
def main():
    with app.app_context():
        now = datetime.now()
        scheduled_articles = Article.query.filter(
            Article.scheduled_time <= now,
            Article.status == 'scheduled'
        ).all()

        site_article_map = {}

        for article in scheduled_articles:
            site = WordPressSite.query.get(article.site_id)

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

                    if site.id not in site_article_map:
                        site_article_map[site.id] = {
                            "site": site,
                            "titles": []
                        }
                    site_article_map[site.id]["titles"].append(article.title)
                else:
                    print(f"❌ 投稿失敗: {article.title} - {response.status_code} - {response.text}")

            except Exception as e:
                print(f"❌ 投稿失敗: {article.title} - {e}")

        # ✅ 投稿完了したサイトごとに「全記事完了チェック」と通知
        for site_id, data in site_article_map.items():
            site = data["site"]
            all_articles = Article.query.filter_by(site_id=site.id).all()
            if all(a.status == 'posted' for a in all_articles):
                user = site.user
                send_completion_email(user.email, site.site_name, data["titles"])

# ✅ 実行
if __name__ == "__main__":
    main()
