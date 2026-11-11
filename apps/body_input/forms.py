from flask_wtf import FlaskForm
from wtforms import FloatField, IntegerField, SelectField, SubmitField, TextAreaField
from wtforms.validators import Optional


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
    submit = SubmitField("更新")
