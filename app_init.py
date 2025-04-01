import os
from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from models import db, User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# ✅ データベース設定（Render対応：/tmp 配下に配置）
if os.environ.get("RENDER"):
    db_path = "/tmp/mydatabase.db"
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, "instance", "mydatabase.db")

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=3650)

# ✅ DB初期化とマイグレーション
db.init_app(app)
migrate = Migrate(app, db)

# ✅ ログインマネージャー設定
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ✅ ユーザー取得関数
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ✅ ルート読み込み（app 定義後に）
from routes import *
