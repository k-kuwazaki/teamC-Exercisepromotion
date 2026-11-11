from datetime import datetime
from apps.app import db

class Situation(db.Model):
    __tablename__ = "situation"
    id = db.Column(db.Integer, primary_key=True)
    # この履歴を作成したユーザー
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    # "chat" または "plan"
    kind = db.Column(db.String(20), nullable=False)
    # チャット用。メニュー履歴では空
    question = db.Column(db.Text, nullable=True)
    # メニュー提案用。チャット履歴では空
    category = db.Column(db.String(50), nullable=True)
    experience = db.Column(db.String(20), nullable=True)
    duration = db.Column(db.String(10), nullable=True)
    equipment = db.Column(db.String(10), nullable=True)
    answer = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
    )