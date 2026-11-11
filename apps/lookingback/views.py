from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, session
from apps.app import db
from apps.lookingback.models import LookingBack

lookingback = Blueprint("lookingback", __name__, template_folder="templates", static_folder="static", url_prefix="/lookingback")


@lookingback.route("/", methods=["GET", "POST"])
def index():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login.login"))

    today = date.today()
    already_posted = LookingBack.query.filter_by(user_id=user_id, date=today).first() is not None

    if request.method == "POST":
        comment = request.form.get("comment", "").strip()
        if comment and not already_posted:
            db.session.add(LookingBack(user_id=user_id, date=today, comment=comment))
            db.session.commit()
        return redirect(url_for("lookingback.index"))

    records = LookingBack.query.filter_by(user_id=user_id).order_by(LookingBack.date.desc()).all()

    return render_template(
        "lookingback/lookingback.html",
        records=records,
        today=today.strftime('%Y年%m月%d日'),
        already_posted=already_posted,
    )


@lookingback.route("/delete/<int:record_id>", methods=["POST"])
def delete(record_id):
    user_id = session.get("user_id")
    record = LookingBack.query.filter_by(id=record_id, user_id=user_id).first_or_404()
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for("lookingback.index"))
