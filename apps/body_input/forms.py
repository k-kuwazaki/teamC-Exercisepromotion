from flask_wtf import FlaskForm
from wtforms import FloatField, IntegerField, PasswordField, SelectField, SubmitField, TextAreaField
from wtforms.validators import Optional, EqualTo


class EditProfileForm(FlaskForm):
    height = FloatField("身長", validators=[Optional()])
    weight = FloatField("体重", validators=[Optional()])
    age = IntegerField("年齢", validators=[Optional()])
    exercise_habit = SelectField("運動習慣", choices=[
        ("", "選択してください"),
        ("rarely", "ほとんどしない"),
        ("sometimes", "週に1〜2回"),
        ("often", "週に3回以上"),
    ])
    goal = TextAreaField("目標", validators=[Optional()])
    password = PasswordField("新しいパスワード", validators=[Optional()])
    password_confirm = PasswordField("新しいパスワード（確認）", validators=[Optional(), EqualTo("password", message="パスワードが一致しません。")])
    submit = SubmitField("確認画面へ")
