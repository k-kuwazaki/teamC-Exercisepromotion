from flask_wtf.form import FlaskForm
from wtforms import TextAreaField
from wtforms.fields.simple import SubmitField
from wtforms.validators import DataRequired


class TranslationForm(FlaskForm):
    source_text = TextAreaField(
        "目標入力",
        validators=[DataRequired("目標を入力してください。")]
    )

    submit = SubmitField("決定")
    
class DeleteForm(FlaskForm):
    submit = SubmitField("削除")