# app_init.py

import os
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, WordPressSite, Keyword, User, Article

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# データベースパス（SQLite）
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "instance", "mydatabase.db")
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# DB初期化
db.init_app(app)

# ログインマネージャー設定
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
