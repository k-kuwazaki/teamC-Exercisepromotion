from flask import Blueprint, redirect, render_template, session, url_for,current_app

from apps.situation.models import Situation


situation = Blueprint(
    "situation",
    __name__,
    template_folder="templates",
    static_folder="static",
)


@situation.route("/situation")
def index():
    user_id = session.get("user_id")
    print("session user_id:", user_id)

    if user_id is None:
        return redirect(url_for("login.login"))

    situations = (
        Situation.query
        .filter_by(user_id=user_id)
        .order_by(Situation.created_at.desc())
        .all()
    )
    print("取得した履歴件数:", len(situations))

    return render_template(
        "situation/index.html",
        situations=situations,
    )

# @situation.route("/")
# def index():
#     return render_template("home/index.html")

