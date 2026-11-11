from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for
from apps.app import db
from apps.lookingback.models import LookingBack

lookingback = Blueprint("lookingback", __name__, template_folder="templates", static_folder="static", url_prefix="/lookingback")


@lookingback.route("/", methods=["GET", "POST"])
def index():
    today = date.today()
    already_posted = LookingBack.query.filter_by(date=today).first() is not None

    if request.method == "POST":
        comment = request.form.get("comment", "").strip()
        if comment and not already_posted:
            db.session.add(LookingBack(date=today, comment=comment))
            db.session.commit()
        return redirect(url_for("lookingback.index"))

    records = LookingBack.query.order_by(LookingBack.date.desc()).all()
    return render_template(
        "lookingback/lookingback.html",
        records=records,
        today=today.strftime('%Y年%m月%d日'),
        already_posted=already_posted,
    )


@lookingback.route("/delete/<int:record_id>", methods=["POST"])
def delete(record_id):
    record = LookingBack.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()

    return redirect(url_for("lookingback.index"))

