from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from apps.app import db
from apps.situation.models import Situation
from apps.user.models import User
import json

# 各種リンク先は後々それ用のファイルに移動させる
registration = Blueprint(
    "registration",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/registration"
)


# トップページ
@registration.route("/")
def index():
    return render_template("home/index.html")


# 振り返り
@registration.route("/lookingback")
def lookingback():
    return redirect(url_for("lookingback.index"))


# 運動内容を保存
@registration.route("/registration", methods=["GET", "POST"])
def save_registration():
    selected_exercises = session.get("selected_exercises", [])
    conditions = session.get("selected_plan_conditions", {})
    implementation_result = session.get("implementation_result", {})

    if request.method == "GET":
        return render_template(
            "registration/registration.html",
            selected_exercises=selected_exercises,
            self_exercises=implementation_result.get("self_exercises", ""),
            actual_minutes=implementation_result.get("actual_minutes", ""),
        )

    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("login.login"))

    # 登録画面で編集された値があればそれを使い、空欄なら実施画面の値を使う
    self_exercises = (
        request.form.get("self_exercises", "").strip()
        or implementation_result.get("self_exercises", "")
    )

    actual_minutes_text = (
        request.form.get("actual_minutes", "").strip()
        or str(implementation_result.get("actual_minutes", ""))
    )

    if not selected_exercises and not self_exercises:
        return render_template(
            "registration/registration.html",
            selected_exercises=selected_exercises,
            self_exercises=self_exercises,
            actual_minutes=actual_minutes_text,
            error="選択した運動か、自主的に行った運動を入力してください。",
        )

    if (
        not actual_minutes_text.isdigit()
        or not 1 <= int(actual_minutes_text) <= 30
    ):
        return render_template(
            "registration/registration.html",
            selected_exercises=selected_exercises,
            self_exercises=self_exercises,
            actual_minutes=actual_minutes_text,
            error="運動時間を1〜30分で入力してください。",
        )

    actual_minutes = int(actual_minutes_text)

    selected_text = "\n".join(
        (
            f'{index}. {exercise["name"]}：'
            f'{exercise["sets"]}セット、'
            f'標準目標 {exercise["target_value"]}{exercise["unit"]}'
        )
        for index, exercise in enumerate(selected_exercises, start=1)
    )
    

    try:
        record = Situation(
            user_id=user_id,
            kind="registration",
            answer=selected_text or "自主的に行った運動",
            self_exercises=self_exercises or None,
            category=conditions.get("category"),
            experience=conditions.get("experience"),
            duration=str(actual_minutes),
            equipment=conditions.get("equipment"),
            question=json.dumps(selected_exercises, ensure_ascii=False),
        )

        db.session.add(record)
        db.session.commit()

        session.pop("selected_exercises", None)
        session.pop("selected_plan_conditions", None)
        session.pop("implementation_result", None)

        return redirect(url_for("registration.lookingback"))

    except Exception:
        db.session.rollback()
        current_app.logger.exception("運動実施内容の保存に失敗しました")

        return render_template(
            "registration/registration.html",
            selected_exercises=selected_exercises,
            self_exercises=self_exercises,
            actual_minutes=actual_minutes_text,
            error="登録内容を保存できませんでした。",
        )
