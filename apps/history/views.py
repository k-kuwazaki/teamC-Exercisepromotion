
from flask import  Blueprint,redirect,render_template,session,url_for
from apps.situation.models import Situation
#各種リンク先は後々それ用のファイルに移動させる

from flask import Blueprint, render_template, redirect, url_for


history = Blueprint("history", __name__, template_folder="templates", static_folder="static")


@history.route("/")
def index():
    return render_template("home/index.html")

@history.route("/calendar")
def calendar():
    return redirect(url_for("calendar.index"))

@history.route("/situation")
def situation():
    user_id = session.get("user_id")

    if user_id is None:
        return redirect(url_for("login.login"))

    situations = (
        Situation.query
        .filter_by(user_id=user_id)
        .order_by(Situation.created_at.desc())
        .all()
    )

    return render_template(
        "situation/situation.html",
        situations=situations,
    )

    return render_template("situation/situation.html")

