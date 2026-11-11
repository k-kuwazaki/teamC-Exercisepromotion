from flask import Blueprint, render_template, request, session, redirect, url_for
from apps.app import db
from apps.user.models import User
from apps.register.forms import registration_form_data

register_bp = Blueprint(
    "register",
    __name__,
    template_folder="templates",
)


@register_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        form_data = registration_form_data(request.form)
        user = User(
            username=form_data["username"],
            email=form_data["email"],
            height=form_data["height"],
            weight=form_data["weight"],
            age=form_data["age"],
            exercise_habit=form_data["exercise_habit"],
            goal=form_data["goal"],
        )
        user.password = form_data["password"]

        db.session.add(user)
        db.session.commit()

        return render_template("register/confirmation.html", user=user)

    return render_template("register/register.html")

# 削除用のルート
@register_bp.route("/delete_account", methods=["GET", "POST"])
def delete_account():
    if "user_id" not in session:
        return redirect(url_for("login.login"))

    if request.method == "POST":
        user = User.query.get(session["user_id"])
        if user:
            db.session.delete(user)
            db.session.commit()
        session.clear()
        return render_template("register/deleted.html")

    return render_template("register/delete_check.html")
