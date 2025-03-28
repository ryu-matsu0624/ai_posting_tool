from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

# --- ✅ プロンプト群 ---
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
あなたはSEOに詳しいライターです。
ネットマーケティングにも詳しい専門家です

入力された「Q＆A記事のタイトル」に対しての
回答記事を以下の###条件###に沿って書いてください。

###条件###
・文章の構成としては、問題提起、共感、問題解決策を入れて書いてください。
・Q＆A記事のタイトルについて悩んでいる人が知りたい事を書いてください。
・見出しを付けてわかりやすく書いてください
・記事の文字数は必ず2500文字〜3500文字程度でまとめてください
・1行の長さは30文字前後にして接続詞などで改行してください。
・「文章の島」は1行から3行以内にして、文章の島同士は2行空けてください
・親友に向けて話すように書いてください（ただし敬語を使ってください）
・読み手のことは「皆さん」ではなく必ず「あなた」と書いてください。

タイトル: {title}
"""

def article_to_image_prompt(keyword, title, content):
    return f"""
生成された記事のキーワード、記事タイトル、記事文章の内容を把握した上で、この記事に適する記事アイキャッチ画像を生成してください。

キーワード: {keyword}
タイトル: {title}
本文（抜粋）:
{content[:1000]}
"""

# --- ✅ 外部呼び出しAPI ---
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
