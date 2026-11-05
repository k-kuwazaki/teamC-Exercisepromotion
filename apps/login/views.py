from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
from apps.user.models import User
from apps.login.forms import login_form_data

login_bp = Blueprint(
    "login",
    __name__,
    template_folder="templates",
)


@login_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        form_data = login_form_data(request.form)
        user = User.query.filter_by(email=form_data["email"]).first()

        if user and check_password_hash(user.password_hash, form_data["password"]):
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("home.index"))

        return render_template(
            "login/login.html",
            error="メールアドレスまたはパスワードが違います。",
        )

    return render_template("login/login.html")
