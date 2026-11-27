#履歴のDB保存
from flask import current_app, session
from apps.app import db
from apps.situation.models import Situation


def save_situation(
    kind,
    answer,
    question=None,
    category=None,
    experience=None,
    duration=None,
    equipment=None,
):
    user_id = session.get("user_id")

    if user_id is None:
        return "履歴を保存するにはログインしてください。"

    try:
        record = Situation(
            user_id=user_id,
            kind=kind,
            question=question,
            category=category,
            experience=experience,
            duration=duration,
            equipment=equipment,
            answer=answer,
        )

        db.session.add(record)
        db.session.commit()
        return None

    except Exception:
        db.session.rollback()
        current_app.logger.exception("履歴の保存に失敗しました")
        return "履歴を保存できませんでした。"