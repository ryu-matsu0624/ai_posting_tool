from wordpress_client import post_to_wordpress_rest
import requests
from requests.auth import HTTPBasicAuth
from flask import Flask, render_template, redirect, url_for, flash
from forms import SignupForm, SiteRegisterForm, LoginForm
from models import db, WordPressSite, Keyword, User, Article
from keywords import generate_keywords_from_genre
from keywords import (
    generate_title_prompt,
    generate_content_prompt,
    generate_image_prompt,
    generate_keywords_from_genre
)
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from datetime import datetime, timedelta, time as dtime
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "instance", "mydatabase.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        user = User(email=form.email.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("ユーザー登録完了", "success")
        return redirect(url_for("dashboard"))
    return render_template("signup.html", form=form)

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            flash("ログイン成功", "success")
            return redirect(url_for("dashboard"))
        flash("メールアドレスまたはパスワードが違います", "danger")
    return render_template("login.html", form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))

# 🔁 改善：投稿時間生成ロジック
def generate_scheduled_times(keyword_count):
    scheduled_times = []
    for i in range(keyword_count):
        day_offset = i // 3
        post_day = datetime.now().date() + timedelta(days=day_offset)
        weekday = post_day.weekday()
        if weekday >= 5:  # 土日
            hour_range = (7, 15)
        else:  # 平日
            hour_range = (10, 20)
        base_hour = random.randint(*hour_range)
        base_minute = random.randint(0, 59)
        minute_buffer = random.randint(-10, 10)
        final_minute = base_minute + minute_buffer
        final_hour = base_hour + final_minute // 60
        final_minute = final_minute % 60
        final_hour = max(6, min(final_hour, 22))
        dt = datetime.combine(post_day, dtime.min).replace(
            hour=final_hour, minute=final_minute, second=0, microsecond=0
        )
        scheduled_times.append(dt)
    return scheduled_times

@app.route("/register_site", methods=["GET", "POST"])
@login_required
def register_site():
    form = SiteRegisterForm()
    if form.validate_on_submit():
        site = WordPressSite(
            site_name=form.site_name.data,
            url=form.url.data,
            genre=form.genre.data,
            wp_username=form.wp_username.data,
            wp_password=form.wp_password.data,
            wp_app_password=form.wp_app_password.data,
            owner=current_user
        )
        db.session.add(site)
        db.session.commit()
        print("✅ サイト登録成功、site.id:", site.id)
        keywords = generate_keywords_from_genre(site.genre)
        schedule_times = generate_scheduled_times(len(keywords))
        for idx, kw in enumerate(keywords):
            scheduled_time = schedule_times[idx]
            title = generate_title_prompt(kw)
            content = generate_content_prompt(title)
            image_prompt = generate_image_prompt(content, kw, title)
            db.session.add(Keyword(keyword=kw, site_id=site.id))
            article = Article(
                keyword=kw,
                title=title,
                content=content,
                image_prompt=image_prompt,
                scheduled_time=scheduled_time,
                status="scheduled",
                site_id=site.id
            )
            db.session.add(article)
        db.session.commit()
        flash("記事が正常に生成されました", "success")
        return redirect(url_for("post_complete", site_id=site.id))
    return render_template("register_site.html", form=form)

@app.route("/post_complete/<int:site_id>")
@login_required
def post_complete(site_id):
    site = WordPressSite.query.get(site_id)
    articles = Article.query.filter_by(site_id=site.id).all()
    return render_template("post_complete.html", site=site, articles=articles)

@app.route("/site_list")
@login_required
def site_list():
    sites = WordPressSite.query.filter_by(user_id=current_user.id).all()
    site_data = []
    for site in sites:
        keywords = Keyword.query.filter_by(site_id=site.id).all()
        keyword_data = []
        for kw in keywords:
            article = Article.query.filter_by(site_id=site.id, keyword=kw.keyword).first()
            keyword_data.append({
                "keyword": kw.keyword,
                "status": article.status if article else "not_generated"
            })
        articles = Article.query.filter_by(site_id=site.id).all()
        posted_count = sum(1 for a in articles if a.status == "posted")
        total_count = len(articles)
        site_data.append({
            "site": site,
            "keywords": keyword_data,
            "posted_count": posted_count,
            "total_count": total_count
        })
    return render_template("site_list.html", site_data=site_data)

@app.route("/generate_article/<int:site_id>/<keyword>")
@login_required
def generate_article(site_id, keyword):
    site = WordPressSite.query.get_or_404(site_id)
    article = Article.query.filter_by(site_id=site.id, keyword=keyword).first()
    if not article:
        flash("記事が見つかりません", "danger")
        return redirect(url_for("site_list"))
    title = generate_title_prompt(keyword)
    content = generate_content_prompt(title)
    image_prompt = generate_image_prompt(content, keyword, title)
    response = post_to_wordpress_rest(
        site_url=site.url,
        username=site.wp_username,
        app_password=site.wp_app_password,
        title=title,
        content=content
    )
    if response.status_code == 201:
        article.title = title
        article.content = content
        article.image_prompt = image_prompt
        article.status = 'posted'
        db.session.commit()
        flash("✅ WordPressに投稿完了", "success")
    else:
        flash(f"❌ 投稿失敗: {response.status_code} - {response.text}", "danger")
    return redirect(url_for("post_complete", site_id=site.id))

@app.route("/dashboard")
@login_required
def dashboard():
    sites = WordPressSite.query.filter_by(user_id=current_user.id).all()
    return render_template("dashboard.html", sites=sites)

@app.route("/post_logs")
@login_required
def post_logs():
    articles = Article.query.join(WordPressSite).filter(
        WordPressSite.user_id == current_user.id
    ).order_by(Article.scheduled_time.desc()).all()
    return render_template("post_logs.html", articles=articles)

@app.route("/calendar")
@login_required
def calendar():
    articles = Article.query.join(WordPressSite).filter(
        WordPressSite.user_id == current_user.id
    ).all()
    events = []
    for article in articles:
        events.append({
            "title": f"{article.site.site_name}: {article.title or '無題'}",
            "start": article.scheduled_time.strftime('%Y-%m-%dT%H:%M:%S'),
            "color": "green" if article.status == "posted" else "orange"
        })
    return render_template("calendar.html", events=events)

if __name__ == "__main__":
    app.run(debug=True)
