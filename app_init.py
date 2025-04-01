# app_init.py

import os
from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

from models import db, User

# Flaskアプリ初期化
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# データベース設定（SQLite）
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "instance", "mydatabase.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# セッションの保持期間（任意：10年間に設定）
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=3650)

# DBとマイグレーション初期化（注意：db.init_app(app)は1回のみ！）
db.init_app(app)
migrate = Migrate(app, db)

# ログインマネージャー設定
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# 🔽 ユーザーIDからユーザーを取得
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 🔽 最後に routes をインポート（appが定義された後）
from routes import *
