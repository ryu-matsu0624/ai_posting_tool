from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, current_user
from app import app  # Flaskアプリケーションインスタンスをインポート
from models import db, User, WordPressSite, Keyword, Article
from forms import SignupForm, LoginForm, SiteRegisterForm, EditArticleForm  # フォームをインポート
from keywords import generate_keywords_from_genre, generate_title_prompt, generate_content_prompt, insert_images_into_content, generate_image_prompt  # 必要な関数をインポート
from article_generator import generate_articles_for_site, generate_scheduled_times  # 記事生成関数をインポート
from wordpress_client import post_to_wordpress_rest  # WordPress投稿処理をインポート
from werkzeug.security import check_password_hash
from flask_login import LoginManager
from keywords import search_pixabay_images

# ログインマネージャーの初期化
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ユーザー登録ページ
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        # ユーザーを作成してDBに追加
        user = User(email=form.email.data, password=form.password.data)
        user.set_password(form.password.data)  # パスワードをハッシュ化
        db.session.add(user)
        db.session.commit()
        flash('ユーザー登録完了', 'success')
        return redirect(url_for('login'))  # 登録後にログインページにリダイレクト
    return render_template('signup.html', form=form)


# ログインページ
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # ユーザーが存在し、パスワードが一致するかチェック
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):  # ハッシュ化されたパスワードの照合
            login_user(user, remember=True)  # remember=True によってセッションが永久に保持される
            flash('ログイン成功', 'success')
            return redirect(url_for('dashboard'))  # ログイン後にダッシュボードにリダイレクト
        flash('メールアドレスまたはパスワードが違います', 'danger')
    return render_template('login.html', form=form)


# ログアウトページ
@app.route('/logout')
@login_required  # ログインしていないとアクセスできない
def logout():
    logout_user()  # ログアウト
    return redirect(url_for('login'))  # ログインページにリダイレクト


# ダッシュボードページ（ログイン後に表示されるページ）
@app.route('/dashboard')
@login_required  # ログインが必要
def dashboard():
    sites = WordPressSite.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', sites=sites)


# サイトを登録するページ
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

        keywords = generate_keywords_from_genre(site.genre)
        schedule_times = generate_scheduled_times(len(keywords))

        for idx, kw in enumerate(keywords):
            db.session.add(Keyword(keyword=kw, site_id=site.id))
            db.session.add(Article(
                keyword=kw,
                title="タイトル生成中…",  # 初期状態でタイトルを仮設定
                content="",
                image_prompt="",
                scheduled_time=schedule_times[idx],
                status="pending",
                site_id=site.id
            ))

        db.session.commit()

        # バックグラウンドで記事生成を開始
        generate_articles_for_site(site)

        return redirect(url_for("post_logs"))  # 記事生成後に投稿ログページに遷移
    return render_template("register_site.html", form=form)


# 投稿完了ページ
@app.route("/post_complete/<int:site_id>")
@login_required
def post_complete(site_id):
    site = WordPressSite.query.get(site_id)
    articles = Article.query.filter_by(site_id=site.id).all()
    return render_template("post_complete.html", site=site, articles=articles)


# サイト一覧ページ
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


# 記事生成処理
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
    content_with_images = insert_images_into_content(content, keyword, title)
    image_prompt = generate_image_prompt(content, keyword, title)
    image_results = search_pixabay_images(image_prompt)
    featured_image_url = image_results[0] if image_results else None

    response = post_to_wordpress_rest(
        site_url=site.url,
        username=site.wp_username,
        app_password=site.wp_app_password,
        title=title,
        content=content_with_images,
        featured_image_url=featured_image_url
    )

    if response and response.status_code == 201:
        article.title = title
        article.content = content_with_images
        article.image_prompt = featured_image_url
        article.status = 'posted'
        db.session.commit()
        flash("✅ WordPressに投稿完了", "success")
    else:
        flash("❌ 投稿失敗", "danger")

    return redirect(url_for("post_complete", site_id=site.id))


# 投稿ログ
@app.route("/post_logs")
@login_required
def post_logs():
    articles = Article.query.join(WordPressSite).filter(
        WordPressSite.user_id == current_user.id
    ).order_by(Article.scheduled_time.asc()).all()

    status_emojis = {
        "pending": "⏳",
        "scheduled": "✅",
        "posted": "🚀"
    }

    return render_template("post_logs.html", articles=articles, status_emojis=status_emojis)


# カレンダー表示
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


# 記事編集ページ
@app.route("/edit_article/<int:article_id>", methods=["GET", "POST"])
@login_required
def edit_article(article_id):
    article = Article.query.get_or_404(article_id)
    form = EditArticleForm(obj=article)
    if form.validate_on_submit():
        article.title = form.title.data
        article.content = form.content.data
        db.session.commit()
        flash("✅ 編集を保存しました", "success")
        return redirect(url_for("preview_article", article_id=article.id))
    return render_template("article_edit.html", form=form)

