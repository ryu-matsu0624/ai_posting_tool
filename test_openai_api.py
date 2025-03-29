import os
from openai import OpenAI
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# 環境変数からAPIキーを取得
api_key = os.getenv("OPENAI_API_KEY")

# クライアント初期化
client = OpenAI(api_key=api_key)

# テスト用のプロンプト
try:
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "こんにちは！これはテストです。"}
        ]
    )

    # 結果表示
    print("✅ 通信成功：")
    print(res.choices[0].message.content)

except Exception as e:
    print("❌ エラーが発生しました：")
    print(e)
