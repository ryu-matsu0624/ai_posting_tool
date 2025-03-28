from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

# ✅ ユーザー（ログインユーザー）
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    sites = db.relationship("WordPressSite", backref="owner", lazy=True)

# ✅ WordPressサイト
class WordPressSite(db.Model):
    __tablename__ = 'word_press_site'
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    wp_username = db.Column(db.String(100), nullable=False)
    wp_password = db.Column(db.String(100), nullable=False)
    wp_app_password = db.Column(db.String(100), nullable=False)  # ✅ これを忘れずに！
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    keywords = db.relationship("Keyword", backref="site", lazy=True)
    articles = db.relationship("Article", backref="site", lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ✅ キーワード
class Keyword(db.Model):
    __tablename__ = 'keyword'
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), nullable=False)
    site_id = db.Column(db.Integer, db.ForeignKey("word_press_site.id"), nullable=False)

# ✅ 記事
class Article(db.Model):
    __tablename__ = 'article'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_prompt = db.Column(db.Text)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default='scheduled')  # scheduled / posted
    site_id = db.Column(db.Integer, db.ForeignKey("word_press_site.id"), nullable=False)

# ✅ 投稿ログ
class PostLog(db.Model):
    __tablename__ = 'post_log'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey("article.id"), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # 成功 or 失敗
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    response_message = db.Column(db.Text)  # レスポンス内容を保存
