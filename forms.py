from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, URL


# 🔐 ユーザー登録フォーム
class SignupForm(FlaskForm):
    email = StringField("メールアドレス", validators=[DataRequired()])
    password = PasswordField("パスワード", validators=[DataRequired()])
    submit = SubmitField("登録")


# 🔐 ログインフォーム
class LoginForm(FlaskForm):
    email = StringField("メールアドレス", validators=[DataRequired()])
    password = PasswordField("パスワード", validators=[DataRequired()])
    submit = SubmitField("ログイン")


# 🌐 サイト登録フォーム
class SiteRegisterForm(FlaskForm):
    site_name = StringField("サイト名", validators=[DataRequired()])
    url = StringField("サイトURL（https://～）", validators=[DataRequired(), URL()])
    genre = StringField("ジャンル", validators=[DataRequired()])
    wp_username = StringField("WordPressユーザー名", validators=[DataRequired()])
    wp_password = PasswordField("WordPressログインパスワード", validators=[DataRequired()])
    wp_app_password = PasswordField("アプリケーションパスワード", validators=[DataRequired()])
    submit = SubmitField("登録")


# 📝 記事編集フォーム（← 今回追加）
class EditArticleForm(FlaskForm):
    title = StringField("記事タイトル", validators=[DataRequired(), Length(max=100)])
    content = TextAreaField("記事本文", validators=[DataRequired()])
    submit = SubmitField("保存")
