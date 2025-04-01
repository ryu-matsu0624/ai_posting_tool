from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ✅ ユーザー
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    sites = db.relationship("WordPressSite", backref="owner", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

# ✅ WordPressサイト
class WordPressSite(db.Model):
    __tablename__ = 'word_press_site'
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    wp_username = db.Column(db.String(100), nullable=False)
    wp_password = db.Column(db.String(100), nullable=False)
    wp_app_password = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    keywords = db.relationship("Keyword", backref="site", lazy=True, cascade="all, delete-orphan")
    articles = db.relationship("Article", backref="site", lazy=True, cascade="all, delete-orphan")
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
    title = db.Column(db.String, nullable=False, default="タイトル未設定")
    content = db.Column(db.Text, nullable=False, default="")
    image_prompt = db.Column(db.String, nullable=False, default="")
    scheduled_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default='pending')  # scheduled / posted / pending / error
    retry_count = db.Column(db.Integer, default=0)  # 🔁 投稿リトライ回数（新規追加）
    site_id = db.Column(db.Integer, db.ForeignKey("word_press_site.id"), nullable=False)

    # ✅ 投稿ログ（時系列順で取得可能）
    post_logs = db.relationship("PostLog", backref="article", lazy=True, cascade="all, delete-orphan", order_by="PostLog.timestamp")

    def update_status(self, new_status):
        if new_status in ['pending', 'scheduled', 'posted', 'error']:
            self.status = new_status
            db.session.commit()

# ✅ 投稿ログ
class PostLog(db.Model):
    __tablename__ = 'post_log'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey("article.id"), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # 成功 / 失敗
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    response_message = db.Column(db.Text)

retry_count = db.Column(db.Integer, default=0)