from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from apps.user.models import User
from apps.login.forms import login_form_data
from datetime import datetime
from apps.app import db
from flask import jsonify


login_bp = Blueprint(
    "login",
    __name__,
    template_folder="templates",
    static_folder="static", 
    url_prefix="/login"
)


@login_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        form_data = login_form_data(request.form)
        user = User.query.filter_by(email=form_data["email"]).first()

        if user and check_password_hash(user.password_hash, form_data["password"]):
            session.clear()
            session["user_id"] = user.id
            session["username"] = user.username
            session["display_mode"] = "simple"

            user.last_seen = datetime.now()
            db.session.commit()

            return redirect(url_for("home.index"))

        return render_template(
            "login/login.html",
            error="メールアドレスまたはパスワードが違います。",
        )

    return render_template("login/login.html")


@login_bp.route("/change-password", methods=["GET", "POST"])
def change_password():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("login.login"))

    error = None
    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        user = db.session.get(User, user_id)

        if user is None:
            session.clear()
            return redirect(url_for("login.login"))
        if not new_password:
            error = "新しいパスワードを入力してください。"
        elif new_password != confirm_password:
            error = "新しいパスワードが一致しません。"
        else:
            try:
                user.password_hash = generate_password_hash(new_password)
                db.session.commit()
                return render_template(
                    "login/change_password.html",
                    success=True,
                )
            except Exception:
                db.session.rollback()
                error = "パスワードを変更できませんでした。もう一度お試しください。"

    return render_template("login/change_password.html", error=error)


@login_bp.route("/logout", methods=["GET", "POST"])
def logout():
    if request.method == "POST":
        user_id = session.get("user_id")
        user = db.session.get(User, user_id) if user_id else None

        if user:
            user.last_seen = None
            db.session.commit()

        session.clear()
        return render_template("login/logout.html")

    return render_template("login/logout_check.html")

@login_bp.route("/heartbeat", methods=["POST"])
def heartbeat():
    user_id = session.get("user_id")

    if user_id is None:
        return jsonify({"status": "unauthorized"}), 401

    user = db.session.get(User, user_id)

    if user is None:
        session.clear()
        return jsonify({"status": "unauthorized"}), 401

    user.last_seen = datetime.now()
    db.session.commit()

    return jsonify({"status": "ok"})
