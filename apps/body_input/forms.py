from flask_wtf import FlaskForm
from wtforms import FloatField, IntegerField, SelectField, SubmitField, TextAreaField
from wtforms.validators import Optional, NumberRange, DataRequired


class EditProfileForm(FlaskForm):
    height = FloatField(
        "身長",
        validators=[
            DataRequired(message="身長を入力してください。"),
            NumberRange(min=100.0, max=250.0, message="身長は100.0～250.0cmの範囲で入力してください。"),
        ],
    )
    weight = FloatField(
        "体重",
        validators=[
            DataRequired(message="体重を入力してください。"),
            NumberRange(min=20.0, max=300.0, message="体重は20.0～300.0kgの範囲で入力してください。"),
        ],
    )
    age = IntegerField("年齢", validators=[Optional()])
    exercise_habit = SelectField(
        "運動習慣",
        choices=[
            ("", "選択してください"),
            ("rarely", "ほとんどしない"),
            ("sometimes", "週に1〜2回"),
            ("often", "週に3回以上"),
        ],
    )
    goal = TextAreaField("目標", validators=[Optional()])
    submit = SubmitField("確認画面へ")