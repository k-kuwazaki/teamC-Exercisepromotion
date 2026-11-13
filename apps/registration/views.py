from flask import Blueprint,current_app, redirect,render_template, request ,url_for,session
#各種リンク先は後々それ用のファイルに移動させる
registration = Blueprint("registration", __name__, template_folder="templates", static_folder="static")
from apps.app import db
from apps.situation.models import Situation
# トップページ
@registration.route("/")
def index():
    return render_template("home/index.html")

# 振り返り
@registration.route("/lookingback")
def lookingback():
    return redirect(url_for("lookingback.index"))
#飛んで保存
#変更　AIのメニューを選択とここで二回データベースへ登録していたのでこちらのみに変更
@registration.route("/registration", methods=["GET", "POST"])
def save_registration():
    selected_exercises = session.get("selected_exercises", [])
    conditions = session.get("selected_plan_conditions", {})

    if request.method == "GET":
        return render_template(
            "registration/registration.html",
            selected_exercises=selected_exercises,
            self_exercises="",
        )

    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("login.login"))
    self_exercises = request.form.get("self_exercises", "").strip()
    if not selected_exercises and not self_exercises:
        return render_template(
            "registration/registration.html",
            selected_exercises=selected_exercises,
            self_exercises=self_exercises,
            error="選択した運動か、自主的に行った運動を入力してください。",
        )

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
            duration=conditions.get("duration"),
            equipment=conditions.get("equipment"),
        )

        db.session.add(record)
        db.session.commit()

        session.pop("selected_exercises", None)
        session.pop("selected_plan_conditions", None)

        return redirect(url_for("registration.lookingback"))

    except Exception:
        db.session.rollback()
        current_app.logger.exception("運動実施内容の保存に失敗しました")

        return render_template(
            "registration/registration.html",
            selected_exercises=selected_exercises,
            self_exercises=self_exercises,
            error="登録内容を保存できませんでした。",
        )



