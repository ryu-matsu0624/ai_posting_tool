from flask import Flask
from app import app
from models import db

with app.app_context():
    db.create_all()
    print("✅ データベース作成完了！")

# init_db.py
from models import db
from app import app

with app.app_context():
    db.create_all()
    print("✅ DB 初期化完了")
from app import app
from models import db

with app.app_context():
    db.create_all()
    print("✅ データベース初期化完了（mydatabase.db）")
