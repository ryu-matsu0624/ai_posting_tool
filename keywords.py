# keywords.py

import os
from dotenv import load_dotenv
from openai import OpenAI
import requests

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")

# -------------------------
# ChatGPTとのやり取り関数
# -------------------------

def ask_chatgpt(prompt, role="あなたはSEOに詳しいライターです。"):
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": role},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# -------------------------
# プロンプト生成
# -------------------------

def genre_to_keywords_prompt(genre):
    return f"""
サイトジャンルからSEO対策として適切なキーワードを１０個生成してください。
キーワードは３語以上のロングテールキーワードとし、検索機能を利用してそのジャンルに関するサイト記事の情報を把握したうえで、最もSEOとして上位表示するキーワードを選択した上で、上記の指示にそってキーワードを生成してください。

ジャンル: {genre}
"""

def keyword_to_title_prompt(keyword):
    return f"""
あなたはSEOに詳しいプロのライターです。

以下の条件に従い、32文字以内の魅力的な記事タイトルを10個、改行区切りで作成してください。

【条件】
- 必ず「{keyword}」を含める
- クリックしたくなるような言葉を使う
- 数字やベネフィットを入れると効果的
- 禁止記号：：「」、""、''、-

【出力形式】
タイトル1
タイトル2
タイトル3
...
"""

def title_to_article_prompt(title):
    return f"""
あなたはSEOに詳しいライターで、ネットマーケティングの専門家です。

入力された「Q＆A記事のタイトル」に対しての回答記事を以下の###条件###に沿って書いてください。

###条件###
・文章の構成としては、問題提起、共感、問題解決策を入れてください。
・見出しを付けてわかりやすく書いてください。
・記事の文字数は2500〜3500文字程度にしてください。
・1行は30文字前後、段落の間は2行空けること。
・語り口調は「あなた」に向けて敬語で。
・親友に話すように、わかりやすく。

タイトル: {title}
"""

def article_to_image_prompt(keyword, title, content):
    return f"""
次の記事内容にふさわしいアイキャッチ画像のテーマを考えてください。

キーワード: {keyword}
タイトル: {title}
本文抜粋:
{content[:800]}

その内容に最も合う画像の検索キーワード（英語で）を1語〜5語で出力してください。
"""

# -------------------------
# Pixabay画像検索
# -------------------------

def search_pixabay_images(keyword, max_results=5):
    if not PIXABAY_API_KEY:
        print("❌ Pixabay APIキーが設定されていません")
        return []

    url = "https://pixabay.com/api/"
    params = {
        "key": PIXABAY_API_KEY,
        "q": keyword,
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
    # 画像キーワードを生成してPixabayで検索
    image_search_prompt = article_to_image_prompt(keyword, title, content)
    query = ask_chatgpt(image_search_prompt)
    image_urls = search_pixabay_images(query)

    # パラグラフに分解して挿入位置を割り当て
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
