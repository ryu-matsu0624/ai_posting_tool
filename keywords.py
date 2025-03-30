# keywords.py

import os
import requests
from dotenv import load_dotenv
from openai import OpenAI
from urllib.parse import quote

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")

# -------------------------
# ChatGPTとのやり取り関数
# -------------------------

def ask_chatgpt(prompt, role="あなたはSEOに詳しいライターです。"):
    try:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": role},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ OpenAIエラー:", e)
        return ""

# -------------------------
# プロンプト生成
# -------------------------

def genre_to_keywords_prompt(genre):
    return f"""
サイトジャンルからSEO対策として適切なキーワードを10個生成してください。
条件：
- すべて3語以上のロングテールキーワード
- SEOで上位表示されやすいもの
- 形式：1行に1つのキーワード

ジャンル: {genre}
"""

def keyword_to_title_prompt(keyword):
    return f"""
以下の条件でクリックされやすい魅力的なタイトルを10個作成してください。

【条件】
- 必ず「{keyword}」を含める
- 32文字以内
- 数字やベネフィットを入れると良い
- 「:」「：」「""」「''」「-」は禁止

出力形式：
タイトル1
タイトル2
タイトル3
"""

def title_to_article_prompt(title):
    return f"""
以下のQ&A記事タイトルに対する回答記事を生成してください：

【タイトル】
{title}

【条件】
・構成：問題提起 → 共感 → 解決策
・2500～3500文字程度
・段落は2行空ける、1行は30文字前後
・語りかけるように「あなた」視点で書く
・敬語で、親しみやすいトーンで
・見出し（H2, H3）を適切に使う
"""

def article_to_image_prompt(keyword, title, content):
    return f"""
以下の記事に最も合うPixabay検索用画像キーワードを5語以内の英語で提案してください。

キーワード: {keyword}
タイトル: {title}
本文抜粋:
{content[:700]}

出力形式（例）: city night skyline
"""

# -------------------------
# Pixabay画像検索
# -------------------------

def search_pixabay_images(keyword, max_results=5):
    if not PIXABAY_API_KEY:
        print("❌ Pixabay APIキーが設定されていません")
        return []

    encoded_query = quote(keyword)
    url = "https://pixabay.com/api/"
    params = {
        "key": PIXABAY_API_KEY,
        "q": encoded_query,
        "image_type": "photo",
        "per_page": max_results,
        "safesearch": "true"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json()
        return [hit["webformatURL"] for hit in results.get("hits", [])]
    except Exception as e:
        print("❌ Pixabay検索エラー:", e)
        return []

# -------------------------
# 段落挿入プラン生成
# -------------------------

def generate_image_plan(content, keyword, title, max_images=3):
    prompt = article_to_image_prompt(keyword, title, content)
    search_query = ask_chatgpt(prompt)

    if not search_query:
        return []

    image_urls = search_pixabay_images(search_query)
    if not image_urls:
        return []

    paragraphs = content.split("\n\n")
    total_paragraphs = len(paragraphs)
    max_images = min(max_images, len(image_urls), total_paragraphs)

    plan = []
    for i in range(max_images):
        position = (i + 1) * total_paragraphs // (max_images + 1)
        plan.append({
            "paragraph_index": position,
            "image_url": image_urls[i]
        })
    return plan

# -------------------------
# 公開API関数群
# -------------------------

def generate_keywords_from_genre(genre):
    prompt = genre_to_keywords_prompt(genre)
    result = ask_chatgpt(prompt)
    keywords = [line.strip("-・0123456789. ").strip() for line in result.splitlines() if line.strip()]
    return keywords[:10]

def generate_title_prompt(keyword):
    prompt = keyword_to_title_prompt(keyword)
    result = ask_chatgpt(prompt)
    titles = [line.strip() for line in result.splitlines() if line.strip()]
    return titles[0] if titles else f"{keyword} に関する記事"

def generate_content_prompt(title):
    prompt = title_to_article_prompt(title)
    return ask_chatgpt(prompt)

def generate_image_prompt(content, keyword="", title=""):
    return ask_chatgpt(article_to_image_prompt(keyword, title, content))
