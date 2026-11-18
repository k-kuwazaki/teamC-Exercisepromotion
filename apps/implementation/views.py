from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

implementation = Blueprint(
    "implementation",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/implementation_static",
)


@implementation.route("/implementation/run", methods=["GET", "POST"])
def index():
    if session.get("user_id") is None:
        return redirect(url_for("login.login"))

    selected_exercises = session.get("selected_exercises", [])
    conditions = session.get("selected_plan_conditions", {})

    raw_goal = str(conditions.get("duration", "0分")).replace("分", "")
    goal_minutes = int(raw_goal) if raw_goal.isdigit() else 0

    if request.method == "POST":
        self_exercises = request.form.get("self_exercises", "").strip()
        manual_minutes_text = request.form.get("manual_minutes", "").strip()

        error = None
        actual_minutes = None
        duration_seconds = None

        if not selected_exercises and not self_exercises:
            error = "メニューを選ぶか、自主運動の内容を入力してください。"

        elif request.form.get("use_manual_time") == "1":
            if (
                not manual_minutes_text.isdigit()
                or not 1 <= int(manual_minutes_text) <= 300
            ):
                error = "運動時間を1〜300分で入力してください。"
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
            )

        session["implementation_result"] = {
            "actual_minutes": actual_minutes,
            "duration_seconds": duration_seconds,
            "self_exercises": self_exercises,
        }

        return redirect(url_for("registration.save_registration"))

    return render_template(
        "implementation/implementation.html",
        selected_exercises=selected_exercises,
        plan_conditions=conditions,
        goal_minutes=goal_minutes,
        self_exercises="",
        manual_minutes="",
    )