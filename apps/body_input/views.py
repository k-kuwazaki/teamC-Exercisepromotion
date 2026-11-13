from flask import Blueprint, render_template, redirect, url_for, session, request
from apps.app import db
from apps.user.models import User
from apps.body_input.forms import EditProfileForm

body_input = Blueprint("body_input", __name__, template_folder="templates", static_folder="static")


@body_input.route("/body-input", methods=["GET", "POST"])
def index():
    if "user_id" not in session:
        return redirect(url_for("login.login"))

    user = User.query.get(session["user_id"])
    form = EditProfileForm(obj=user)

    if form.validate_on_submit():
        session["edit_data"] = {
            "height": form.height.data,
            "weight": form.weight.data,
            "age": form.age.data,
            "exercise_habit": form.exercise_habit.data,
            "goal": form.goal.data,
            "change_password": bool(form.password.data),
            "password": form.password.data,
        }
        return redirect(url_for("body_input.confirm"))

    return render_template("body_input/body_input.html", form=form)


@body_input.route("/body-input/confirm", methods=["GET", "POST"])
def confirm():
    if "user_id" not in session or "edit_data" not in session:
        return redirect(url_for("body_input.index"))

    if request.method == "POST":
        user = User.query.get(session["user_id"])
        data = session.pop("edit_data")
        user.height = data["height"]
        user.weight = data["weight"]
        user.age = data["age"]
        user.exercise_habit = data["exercise_habit"]
        user.goal = data["goal"]
        if data["change_password"] and data["password"]:
            user.password = data["password"]
        db.session.commit()
        return render_template("body_input/body_update.html")

    return render_template("body_input/body_confirm.html", data=session["edit_data"])
