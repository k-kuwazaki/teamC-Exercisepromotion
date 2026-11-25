import calendar
import jpholiday
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, session
from apps.lookingback.models import LookingBack
from apps.app import db
from sqlalchemy import func
from apps.situation.models import Situation
from apps.user.models import User

calendar_bp = Blueprint(
    "calendar",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/calendar",
)


class TodayCalendar(calendar.HTMLCalendar):
    def __init__(self, today, year, month, exercised_days=None):
        super().__init__(firstweekday=6)
        self.today = today
        self.year = year
        self.month = month
        self.exercised_days = exercised_days or set()

    def formatweekday(self, day):
        weekdays = ["月", "火", "水", "木", "金", "土", "日"]
        return f"<th>{weekdays[day]}</th>"

    def formatday(self, day, weekday):
        if day == 0:
            return '<td class="noday">&nbsp;</td>'

        classes = self.cssclasses[weekday]

        if self.today and day == self.today.day:
            classes += " today"

        selected_date = date(self.year, self.month, day)
        if jpholiday.is_holiday(selected_date):
            classes += " holiday"

        if day in self.exercised_days:
            classes += " exercised"

        return f'<td class="{classes} clickable" data-day="{day}">{day}</td>'


@calendar_bp.route("/")
def index():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login.login"))

    today = date.today()
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)

    if year is None or month is None:
        return redirect(url_for("calendar.index", year=today.year, month=today.month))
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)

    is_current_month = year == today.year and month == today.month
    cal_today = today if is_current_month else None
    exercised_days = {
        r.created_at.day
        for r in Situation.query.filter_by(user_id=user_id, kind="registration")
        .filter(
            func.strftime("%Y", Situation.created_at) == str(year),
            func.strftime("%m", Situation.created_at) == f"{month:02d}",
        )
        .all()
    }

    cal = TodayCalendar(cal_today, year, month, exercised_days)
    calendar_html = cal.formatmonth(year, month)

    return render_template(
        "calendar/calendar.html",
        year=year,
        month=month,
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
        calendar_html=calendar_html,
    )

# カロリー計算用変数
CATEGORY_METS = {
    "筋力トレーニング": 3.5,
    "ダイエット": 4.0,
    "柔軟性・ストレッチ": 2.5,
    "体力づくり": 5.0,
    "運動不足の解消": 3.0,
    "AIにおまかせ": 3.5,
}
DEFAULT_METS = 3.5


# 変更　履歴を追加できるように
@calendar_bp.route("/day/<int:year>/<int:month>/<int:day>")
def day_detail(year, month, day):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login.login"))

    selected_date = date(year, month, day)

    record = LookingBack.query.filter_by(
        user_id=user_id,
        date=selected_date,
    ).first()

    exercise_records = (
        Situation.query.filter_by(user_id=user_id, kind="registration")
        .filter(func.date(Situation.created_at) == selected_date.isoformat())
        .order_by(Situation.created_at.desc())
        .all()
    )

    user = db.session.get(User, user_id)
    weight = user.weight if user and user.weight else 60

    calories_map = {
        r.id: round(
            CATEGORY_METS.get(r.category, DEFAULT_METS)
            * weight
            * (int(r.duration) / 60)
        )
        for r in exercise_records
        if r.duration and r.duration.isdigit()
    }

    return render_template(
        "calendar/day_detail.html",
        year=year,
        month=month,
        day=day,
        record=record,
        exercise_records=exercise_records,
        calories_map=calories_map,
    )


@calendar_bp.route("/delete/confirm/<int:record_id>")
def delete_confirm(record_id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login.login"))
    record = LookingBack.query.filter_by(id=record_id, user_id=user_id).first_or_404()
    return render_template("calendar/delete_confirm.html", record=record)


@calendar_bp.route("/delete/<int:record_id>", methods=["POST"])
def delete(record_id):
    user_id = session.get("user_id")
    record = LookingBack.query.filter_by(id=record_id, user_id=user_id).first_or_404()
    year, month, day = record.date.year, record.date.month, record.date.day
    db.session.delete(record)
    db.session.commit()
    return redirect(url_for("calendar.day_detail", year=year, month=month, day=day))
