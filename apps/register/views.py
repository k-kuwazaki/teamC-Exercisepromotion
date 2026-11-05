from flask import Blueprint, render_template, request
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
