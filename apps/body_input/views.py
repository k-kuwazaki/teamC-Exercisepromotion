from flask import Blueprint, render_template, redirect, url_for, session
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
        user.height = form.height.data
        user.weight = form.weight.data
        user.age = form.age.data
        user.exercise_habit = form.exercise_habit.data
        user.goal = form.goal.data
        db.session.commit()
        return render_template("body_input/body_input.html", form=form, success="更新しました。")

    return render_template("body_input/body_input.html", form=form)
