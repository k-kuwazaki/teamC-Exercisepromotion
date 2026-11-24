
from flask import Blueprint, render_template, request, session, redirect, url_for
from apps.app import db
from apps.user.models import User
from apps.register.forms import registration_form_data
from datetime import date, datetime
from sqlalchemy.exc import IntegrityError

register_bp = Blueprint(
    "register",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/register"
)


@register_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        form_data = registration_form_data(request.form)

        # 生年月日の未入力チェック
        birthday_str = form_data.get("birthday")

        height = form_data.get("height")
        weight = form_data.get("weight")

        errors = []
        if height is None or not (100.0 <= height <= 250.0):
            errors.append("身長は100.0〜250.0cmの範囲で入力してください。")
        if weight is None or not (20.0 <= weight <= 300.0):
            errors.append("体重は20.0〜300.0kgの範囲で入力してください。")
        if errors:
            return render_template(
                "register/register.html",
                error=" ".join(errors)
            )

        if not birthday_str:
            return render_template(
                "register/register.html",
                error="生年月日を入力してください。"
            )

        # 生年月日の形式チェック
        try:
            birthday = datetime.strptime(
                birthday_str, "%Y-%m-%d"
            ).date()

            # 未来の日付を禁止
            if birthday > date.today():
                return render_template(
                    "register/register.html",
                    error="生年月日に未来の日付は入力できません。"
                )

        except (ValueError, TypeError):
            return render_template(
                "register/register.html",
                error="正しい生年月日を入力してください。"
            )

        try:
            user = User(
                username=form_data["username"],
                email=form_data["email"],
                height=form_data["height"],
                weight=form_data["weight"],
                birthday=birthday,
                exercise_habit=form_data["exercise_habit"],
                goal=form_data["goal"],
            )

            user.password = form_data["password"]

            db.session.add(user)
            db.session.commit()

            today = date.today()
            age = today.year - birthday.year - (
                (today.month, today.day) < (birthday.month, birthday.day)
            )
            return render_template(
                "register/confirmation.html",
                user=user,
                age=age
            )

        except IntegrityError:
            db.session.rollback()
            return render_template(
                "register/register.html",
                error="このメールアドレスは既に登録されています。"
            )

        except Exception:
            db.session.rollback()
            return render_template(
                "register/register.html",
                error="登録中に予期せぬエラーが発生しました。もう一度お試しください。"
            )

    return render_template("register/register.html")


# 削除用のルート
@register_bp.route("/delete_account", methods=["GET", "POST"])
def delete_account():
    if "user_id" not in session:
        return redirect(url_for("login.login"))

    if request.method == "POST":
        user = User.query.get(session["user_id"])

        if user:
            try:
                db.session.delete(user)
                db.session.commit()
            except Exception:
                db.session.rollback()
                return render_template(
                    "register/delete_check.html",
                    error="アカウントの削除中にエラーが発生しました。もう一度お試しください。"
                )

        session.clear()

        return render_template("register/deleted.html")

    return render_template("register/delete_check.html")
