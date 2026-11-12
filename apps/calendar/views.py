import calendar
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, session
from apps.lookingback.models import LookingBack

calendar_bp = Blueprint("calendar", __name__, template_folder="templates", static_folder="static", url_prefix="/calendar")


class TodayCalendar(calendar.HTMLCalendar):
    def __init__(self, today):
        super().__init__(firstweekday=6)
        self.today = today

    def formatday(self, day, weekday):
        if day == 0:
            return '<td class="noday">&nbsp;</td>'
        classes = self.cssclasses[weekday]
        if self.today and day == self.today.day:
            classes += ' today'
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

    is_current_month = (year == today.year and month == today.month)
    cal_today = today if is_current_month else None
    cal = TodayCalendar(cal_today)
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


@calendar_bp.route("/day/<int:year>/<int:month>/<int:day>")
def day_detail(year, month, day):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login.login"))

    record = LookingBack.query.filter_by(user_id=user_id, date=date(year, month, day)).first()
    return render_template("calendar/day_detail.html", year=year, month=month, day=day, record=record)
