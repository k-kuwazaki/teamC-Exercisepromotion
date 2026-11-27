#入力フォーム
from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length
from wtforms import SelectMultipleField
from wtforms.widgets import CheckboxInput, ListWidget
#目標とカテゴリーの選択
class TranslationForm(FlaskForm):
    source_text = TextAreaField(
        "目標入力",
        validators=[DataRequired("目標を入力してください。")]
    )

    submit = SubmitField("決定")
    
class DeleteForm(FlaskForm):
    submit = SubmitField("削除")


class CoachForm(FlaskForm):
    question = TextAreaField(
        "相談内容",
        validators=[
            DataRequired(message="質問を入力してください。"),
            Length(max=500, message="質問は500文字以内で入力してください。"),
        ],
    )
    submit = SubmitField("AIに相談する")


class PlanForm(FlaskForm):
    category = SelectField(
        "運動カテゴリー",
        choices=[
            ("", "選択してください"),
            ("筋力トレーニング", "筋力トレーニング"),
            ("ダイエット", "ダイエット"),
            ("柔軟性・ストレッチ", "柔軟性・ストレッチ"),
            ("体力づくり", "体力づくり"),
            ("運動不足の解消", "運動不足の解消"),
            ("AIにおまかせ", "AIにおまかせ"),
        ],
        validators=[DataRequired(message="運動カテゴリーを選択してください。")],
    )
    experience = SelectField(
        "現在の運動経験",
        choices=[("初心者", "初心者・運動習慣がない"), ("中級者", "ある程度運動している"), ("上級者", "定期的に運動している")],
        default="初心者",
    )
    duration = SelectField(
        "運動できる時間",
        choices=[("5分", "5分"), ("10分", "10分"), ("20分", "20分"), ("30分", "30分")],
        default="10分",
    )
    equipment = SelectField(
        "トレーニング器具",
        choices=[("なし", "なし（自重トレーニングなど）"), ("あり", "あり")],
        default="なし",
    )
    submit = SubmitField("AIにメニューを提案してもらう")
    selected_exercises = SelectMultipleField(
    "取り入れたい運動（複数選択できます）",
    choices=[],
    option_widget=CheckboxInput(),
    widget=ListWidget(prefix_label=False),
)
