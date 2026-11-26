from datetime import date

from flask import Blueprint, render_template, redirect, url_for, session, request
from apps.app import db
from apps.user.models import User
from apps.body_input.forms import EditProfileForm

body_input = Blueprint(
    "body_input",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/body_input",
)


@body_input.route("/body-input", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        return redirect(url_for("login.login"))

    user = db.session.get(User, session["user_id"])
    if user is None:
        session.clear()
        return redirect(url_for("login.login"))

    form = EditProfileForm(obj=user)

    today = date.today()
    age = today.year - user.birthday.year - (
        (today.month, today.day) < (user.birthday.month, user.birthday.day)
    )

    if form.validate_on_submit():
        session["edit_data"] = {
            "height": form.height.data,
            "weight": form.weight.data,
            "age": age,
            "exercise_habit": form.exercise_habit.data,
            "goal": form.goal.data,
        }
        return redirect(url_for("body_input.confirm"))

    return render_template("body_input/body_input.html", form=form, age=age)


@body_input.route("/body-input/confirm", methods=["GET", "POST"])
def confirm():
    if "user_id" not in session or "edit_data" not in session:
        return redirect(url_for("body_input.index"))

    if request.method == "POST":
        user = db.session.get(User, session["user_id"])
        if user is None:
            session.clear()
            return redirect(url_for("login.login"))

        data = session.pop("edit_data")
        user.height = data["height"]
        user.weight = data["weight"]
        user.exercise_habit = data["exercise_habit"]
        user.goal = data["goal"]

        db.session.commit()
        return render_template("body_input/body_update.html")

    return render_template("body_input/body_confirm.html", data=session["edit_data"])
