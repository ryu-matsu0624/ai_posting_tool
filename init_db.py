from app import app
from models import db

# Flaskのアプリケーションコンテキスト内で実行
with app.app_context():
    db.create_all()
    print("✅ データベース作成完了！（mydatabase.db）")
