import os
import requests
import time
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIConnectionError
from urllib.parse import quote

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")

# -------------------------
# ChatGPTとのやり取り関数
# -------------------------
def ask_chatgpt(prompt, role="あなたはSEOに詳しいライターです。", retries=3):
    for attempt in range(retries):
        try:
            print(f"\n📤 ChatGPTプロンプト:\n{prompt}\n")
            response = client.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {"role": "system", "content": role},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                timeout=30
            )
            result = response.choices[0].message.content.strip()
            print(f"\n📥 ChatGPTレスポンス:\n{result}\n")
            return result
        except (RateLimitError, APIConnectionError) as e:
            print(f"⚠️ ChatGPT通信エラー: {e} - {attempt + 1}回目のリトライ中...")
            time.sleep(2 * (attempt + 1))
        except Exception as e:
            print(f"❌ OpenAIエラー: {e}")
            break
    return None  # 明示的に失敗を返す

# -------------------------
# プロンプト生成
# -------------------------
def genre_to_keywords_prompt(genre):
    return f"""
あなたはSEO専門家です。
以下のジャンルからSEO対策に適したロングテールキーワードを10個出力してください。

【条件】
- 3語以上の日本語キーワード
- 月間検索ボリュームが中以上を想定
- 実際に検索されそうな表現で

ジャンル: {genre}
"""

def keyword_to_title_prompt(keyword):
    return f"""
以下の条件でクリックされやすい日本語タイトルを10個作成してください。

【条件】
- 必ず「{keyword}」を含める
- 32文字以内
- 数字、ベネフィットを含めると良い
- 記号（:,：,""''-）は禁止

"""

def title_to_article_prompt(title):
    return f"""
以下のQ&A形式の日本語記事を生成してください。

【タイトル】
{title}

【条件】
・構成：問題提起 → 共感 → 解決策
・本文：2500～3500文字
・文体：「あなた」視点で、親しみやすい語りかけ
・敬語で、初心者にも分かりやすく
・段落ごとに2行空ける、1行30文字程度
・H2/H3見出しを適切に使う
"""

def article_to_image_prompt(keyword, title, content):
    return f"""
以下の記事にマッチするPixabay画像を検索するための英語キーワードを提案してください。

【キーワード】
{keyword}

【タイトル】
{title}

【本文抜粋】
{content[:700]}

【出力形式】
city night skyline など、スペース区切りの5語以内英語キーワード
"""

# -------------------------
# Pixabay画像検索
# -------------------------
def search_pixabay_images(keyword, max_results=5):
    if not PIXABAY_API_KEY:
        print("❌ Pixabay APIキーが未設定です")
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
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        results = response.json()
        return [hit["webformatURL"] for hit in results.get("hits", [])]
    except Exception as e:
        print("❌ Pixabay検索エラー:", e)
        return []

# -------------------------
# 画像挿入位置の決定
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
# 記事中に画像挿入
# -------------------------
def insert_images_into_content(content, keyword, title, max_images=3):
    image_plan = generate_image_plan(content, keyword, title, max_images=max_images)
    for plan in image_plan:
        paragraph_index = plan.get("paragraph_index")
        image_url = plan.get("image_url")
        if not image_url:
            continue
        paragraphs = content.split("\n\n")
        if 0 <= paragraph_index < len(paragraphs):
            img_tag = f'<div style="text-align:center;"><img src="{image_url}" alt="{keyword}" style="max-width:100%; height:auto;"></div>'
            paragraphs[paragraph_index] += f"\n\n{img_tag}"
        content = "\n\n".join(paragraphs)
    return content

# -------------------------
# 公開関数
# -------------------------
def generate_keywords_from_genre(genre):
    prompt = genre_to_keywords_prompt(genre)
    result = ask_chatgpt(prompt)
    if not result:
        return []
    keywords = [line.strip("-・0123456789. ").strip() for line in result.splitlines() if line.strip()]
    return keywords[:10]

def generate_title_prompt(keyword):
    prompt = keyword_to_title_prompt(keyword)
    result = ask_chatgpt(prompt)
    if not result:
        print(f"⚠️ タイトル生成失敗（keyword: {keyword}）")
        return None
    titles = [line.strip() for line in result.splitlines() if line.strip()]
    return titles[0] if titles else None

def generate_content_prompt(title):
    prompt = title_to_article_prompt(title)
    result = ask_chatgpt(prompt)
    return result if result else None

def generate_image_prompt(content, keyword="", title=""):
    return ask_chatgpt(article_to_image_prompt(keyword, title, content))
