import os
from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

from models import db, User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# ✅ Renderでも安全なSQLiteパスの作成
basedir = os.path.abspath(os.path.dirname(__file__))
db_dir = os.path.join(basedir, "instance")
os.makedirs(db_dir, exist_ok=True)  # ← フォルダが無ければ作成（Render対応）

db_path = os.path.join(db_dir, "mydatabase.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# セッションの保持期間（任意）
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=3650)

# DB初期化
db.init_app(app)
migrate = Migrate(app, db)

# ログイン設定
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 最後にルーティングを読み込む
from routes import *
