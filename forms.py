# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class SignupForm(FlaskForm):
    email = StringField("メールアドレス", validators=[DataRequired(), Email()])
    password = PasswordField("パスワード", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("登録")
from wtforms.validators import DataRequired, URL
class LoginForm(FlaskForm):
    email = StringField("メールアドレス", validators=[DataRequired(), Email()])
    password = PasswordField("パスワード", validators=[DataRequired()])
    submit = SubmitField("ログイン")


class SiteRegisterForm(FlaskForm):
    site_name = StringField("サイト名", validators=[DataRequired()])
    url = StringField("URL", validators=[DataRequired(), URL()])
    genre = StringField("ジャンル", validators=[DataRequired()])
    wp_username = StringField("WordPressユーザー名", validators=[DataRequired()])
    wp_password = StringField("WordPressパスワード", validators=[DataRequired()])
    submit = SubmitField("サイトを登録")
class LoginForm(FlaskForm):
    email = StringField("メールアドレス", validators=[DataRequired(), Email()])
    password = PasswordField("パスワード", validators=[DataRequired()])
    submit = SubmitField("ログイン")

# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired

class SiteRegisterForm(FlaskForm):
    site_name = StringField("サイト名", validators=[DataRequired()])
    url = StringField("URL", validators=[DataRequired()])
    genre = StringField("ジャンル", validators=[DataRequired()])
    wp_username = StringField("WordPressユーザー名", validators=[DataRequired()])
    wp_password = PasswordField("WordPressログインパスワード")  # ← 古いXML-RPC用
    wp_app_password = PasswordField("WordPressアプリパスワード", validators=[DataRequired()])
