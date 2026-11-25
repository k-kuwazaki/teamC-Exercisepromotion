import json
from datetime import date, timedelta

from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import func

from apps.situation.models import Situation


implementation = Blueprint(
    "implementation",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/implementation_static",
)


@implementation.route("/implementation/run", methods=["GET", "POST"])
def index():
    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("login.login"))

    # 前日の最新の実施記録を取得
    yesterday = date.today() - timedelta(days=1)
    yesterday_record = (
        Situation.query
        .filter_by(user_id=user_id, kind="registration")
        .filter(func.date(Situation.created_at) == yesterday.isoformat())
        .order_by(Situation.created_at.desc())
        .first()
    )

    # 「前日と同じメニューを使う」ボタンから来た場合、記録をセッションへ読み込む
    if (
        request.method == "GET"
        and request.args.get("repeat") == "yesterday"
        and yesterday_record
    ):
        try:
            previous_exercises = json.loads(yesterday_record.question or "[]")
            if not isinstance(previous_exercises, list):
                previous_exercises = []
        except (TypeError, json.JSONDecodeError):
            previous_exercises = []

        session["selected_exercises"] = previous_exercises
        session["selected_plan_conditions"] = {
            "category": yesterday_record.category,
            "experience": yesterday_record.experience,
            "duration": yesterday_record.duration,
            "equipment": yesterday_record.equipment,
        }
        session["repeat_self_exercises"] = (
            yesterday_record.self_exercises or ""
        )

        return redirect(url_for("implementation.index", source="repeat"))

    selected_exercises = session.get("selected_exercises", [])
    conditions = session.get("selected_plan_conditions", {})

    source = (
        request.form.get("source", "")
        if request.method == "POST"
        else request.args.get("source", "")
    )

    if source == "home":
        default_tab = "self-menu"
    elif source == "chat":
        default_tab = "ai-menu"
    else:
        default_tab = "ai-menu" if selected_exercises else "self-menu"

    if request.method == "POST":
        submitted_tab = request.form.get("active_tab", "")
        if submitted_tab in ("ai-menu", "self-menu"):
            default_tab = submitted_tab

    raw_goal = str(conditions.get("duration", "0分")).replace("分", "")
    goal_minutes = int(raw_goal) if raw_goal.isdigit() else 0
    can_repeat_yesterday = bool(
        yesterday_record
        and (yesterday_record.question or yesterday_record.self_exercises)
    )

    if request.method == "POST":
        self_exercises = request.form.get("self_exercises", "").strip()
        manual_minutes_text = request.form.get("manual_minutes", "").strip()

        # タイマー開始時の目標時間チェック。範囲外なら再読み込みしてエラーを表示する。
        if request.form.get("validate_goal") == "1":
            goal_minutes_text = request.form.get("goal_minutes", "").strip()
            if (
                not goal_minutes_text.isdigit()
                or not 1 <= int(goal_minutes_text) <= 30
            ):
                error = "目標時間を1〜30分で入力してください。"
            else:
                error = None

            return render_template(
                "implementation/implementation.html",
                selected_exercises=selected_exercises,
                plan_conditions=conditions,
                goal_minutes=goal_minutes,
                goal_minutes_input=goal_minutes_text,
                self_exercises=self_exercises,
                manual_minutes=manual_minutes_text,
                error=error,
                default_tab=default_tab,
                source=source,
                can_repeat_yesterday=can_repeat_yesterday,
            )

        error = None
        actual_minutes = None
        duration_seconds = None

        if not selected_exercises and not self_exercises:
            error = "メニューを選ぶか、自主運動の内容を入力してください。"

        elif request.form.get("use_manual_time") == "1":
            if (
                not manual_minutes_text.isdigit()
                or not 1 <= int(manual_minutes_text) <= 30
            ):
                error = "運動時間を1〜30分で入力してください。"
            else:
                actual_minutes = int(manual_minutes_text)
                duration_seconds = actual_minutes * 60

        else:
            duration_seconds = request.form.get(
                "duration_seconds",
                type=int,
            )

            if duration_seconds is None or duration_seconds < 60:
                error = (
                    "運動時間が1分未満です。"
                    "1分以上運動してから終了するか、"
                    "タイマーを使わず運動時間を入力してください。"
                )
            else:
                actual_minutes = duration_seconds // 60

        if error:
            return render_template(
                "implementation/implementation.html",
                selected_exercises=selected_exercises,
                plan_conditions=conditions,
                goal_minutes=goal_minutes,
                self_exercises=self_exercises,
                manual_minutes=manual_minutes_text,
                error=error,
                default_tab=default_tab,
                source=source,
                can_repeat_yesterday=can_repeat_yesterday,
            )

        session["implementation_result"] = {
            "actual_minutes": actual_minutes,
            "duration_seconds": duration_seconds,
            "self_exercises": self_exercises,
        }

        return redirect(url_for("registration.save_registration"))

    self_exercises = session.pop("repeat_self_exercises", "")

    return render_template(
        "implementation/implementation.html",
        selected_exercises=selected_exercises,
        plan_conditions=conditions,
        goal_minutes=goal_minutes,
        self_exercises=self_exercises,
        manual_minutes="",
        default_tab=default_tab,
        source=source,
        can_repeat_yesterday=can_repeat_yesterday,
    )
