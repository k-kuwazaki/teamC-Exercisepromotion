
import json
from datetime import date, timedelta

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import func

from apps.app import db
from apps.chat.ai_service import generate_answer, generate_exercise_options
from apps.chat.forms import CoachForm, PlanForm
from apps.chat.history_service import save_situation
from apps.chat.prompts import (
    SYSTEM_INSTRUCTION,
    build_exercise_options_prompt,
)
from apps.situation.models import Situation
from apps.user.models import User


test = Blueprint(
    "test",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/test"
)


# ========================================
# 共通関数
# ========================================

def calculate_age(birthday):
    if birthday is None:
        return None

    today = date.today()
    age = today.year - birthday.year

    if (today.month, today.day) < (birthday.month, birthday.day):
        age -= 1

    return age


def get_user_profile_text():
    user_id = session.get("user_id")

    if user_id is None:
        return None

    user = User.query.filter_by(id=user_id).first()

    if user is None:
        return None

    age = calculate_age(user.birthday)

    return f"""
年齢：{age if age is not None else "未登録"}
身長：{user.height if user.height is not None else "未登録"} cm
体重：{user.weight if user.weight is not None else "未登録"} kg
運動習慣：{user.exercise_habit or "未登録"}
目標：{user.goal or "未登録"}
"""


def get_option_choices(options):
    return [
        (
            option["id"],
            f'{option["name"]}（約{option["minutes"]}分）',
        )
        for option in options
    ]


def format_selected_exercises(options, conditions):
    lines = [
        f'カテゴリー：{conditions["category"]}',
        f'運動経験：{conditions["experience"]}',
        f'運動できる時間：{conditions["duration"]}',
        "",
        "選択した運動内容",
    ]

    for number, option in enumerate(options, start=1):
        lines.extend([
            "",
            f'{number}. {option["name"]}',
            f'目安時間：{option["minutes"]}分',
            f'セット数：{option["sets"]}セット',
            f'標準目標：{option["target_value"]}{option["unit"]}',
            f'内容：{option["description"]}',
            f'注意点：{option["caution"]}',
        ])

    return "\n".join(lines)


# ========================================
# 運動候補・AIチャット画面
# ========================================

@test.route("/", methods=["GET", "POST"])
def index():

    coach_form = CoachForm()
    plan_form = PlanForm()

    chat_answer = None
    plan_answer = None
    chat_error = None
    plan_error = None

    plan_options = session.get("plan_options", [])
    plan_conditions = session.get("plan_conditions", {})

    plan_form.selected_exercises.choices = get_option_choices(
        plan_options
    )

    if request.method == "POST":

        action = request.form.get("action", "")

        # AIへの質問
        if action == "coach":

            if coach_form.validate_on_submit():

                question = coach_form.question.data.strip()

                chat_answer, chat_error = generate_answer(
                    question,
                    system_instruction=SYSTEM_INSTRUCTION,
                )

                if chat_answer:
                    chat_error = save_situation(
                        kind="chat",
                        question=question,
                        answer=chat_answer,
                    )

            else:
                chat_error = next(
                    (
                        message
                        for errors in coach_form.errors.values()
                        for message in errors
                    ),
                    "質問を確認してください。",
                )

        # 運動候補の生成
        elif action == "plan":

            if plan_form.validate_on_submit():

                category = plan_form.category.data
                experience = plan_form.experience.data
                duration = plan_form.duration.data
                equipment = plan_form.equipment.data

                profile_text = get_user_profile_text()

                if profile_text is None:

                    plan_error = (
                        "ログインしてから運動メニューを作成してください。"
                    )

                else:

                    prompt = build_exercise_options_prompt(
                        profile_text=profile_text,
                        category=category,
                        experience=experience,
                        duration=duration,
                        equipment=equipment,
                    )

                    options, plan_error = generate_exercise_options(prompt)

                    if options:

                        plan_options = options

                        plan_conditions = {
                            "category": category,
                            "experience": experience,
                            "duration": duration,
                            "equipment": equipment,
                        }

                        session["plan_options"] = plan_options
                        session["plan_conditions"] = plan_conditions

                        plan_form.selected_exercises.choices = (
                            get_option_choices(plan_options)
                        )

            else:
                plan_error = next(
                    (
                        message
                        for field in (
                            "category",
                            "experience",
                            "duration",
                            "equipment",
                        )
                        for message in plan_form.errors.get(field, [])
                    ),
                    "入力内容を確認してください。",
                )

        # 運動候補の選択
        elif action == "select_exercises":

            plan_options = session.get("plan_options", [])
            plan_conditions = session.get("plan_conditions", {})

            plan_form.selected_exercises.choices = get_option_choices(
                plan_options
            )

            if not plan_options or not plan_conditions:

                plan_error = (
                    "候補がありません。先に運動候補を作成してください。"
                )

            elif plan_form.validate_on_submit():

                selected_ids = plan_form.selected_exercises.data or []

                if not selected_ids:

                    plan_error = "運動を1つ以上選択してください。"

                else:

                    selected_options = [
                        option
                        for option in plan_options
                        if option["id"] in selected_ids
                    ]

                    total_minutes = sum(
                        option["minutes"]
                        for option in selected_options
                    )

                    allowed_minutes = int(
                        plan_conditions["duration"].replace("分", "")
                    )

                    if total_minutes > allowed_minutes:

                        plan_error = (
                            f"選択した運動は合計約{total_minutes}分です。"
                            f"{allowed_minutes}分以内になるよう選び直してください。"
                        )

                    else:

                        session["selected_exercises"] = selected_options
                        session["selected_plan_conditions"] = plan_conditions

                        session.pop("plan_options", None)
                        session.pop("plan_conditions", None)

                        return redirect(
                            url_for("test.implementation", source="test")
                        )

            else:
                plan_error = next(
                    (
                        message
                        for errors in plan_form.errors.values()
                        for message in errors
                    ),
                    "選択内容を確認してください。",
                )

        else:
            chat_error = "送信内容を確認してください。"

    return render_template(
        "test/test_index.html",
        coach_form=coach_form,
        plan_form=plan_form,
        chat_answer=chat_answer,
        plan_answer=plan_answer,
        chat_error=chat_error,
        plan_error=plan_error,
        plan_options=plan_options,
        plan_conditions=plan_conditions,
    )


# ========================================
# 運動実施画面
# ========================================

@test.route("/implementation/run", methods=["GET", "POST"])
def implementation():

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

    # 前日と同じメニューを使う場合
    if (
        request.method == "GET"
        and request.args.get("repeat") == "yesterday"
        and yesterday_record
    ):

        try:
            previous_exercises = json.loads(
                yesterday_record.question or "[]"
            )

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

        return redirect(
            url_for("test.implementation", source="test")
        )

    selected_exercises = session.get("selected_exercises", [])
    conditions = session.get("selected_plan_conditions", {})

    source = (
        request.form.get("source", "")
        if request.method == "POST"
        else request.args.get("source", "")
    )

    # 初期表示タブ
    if source in ("chat", "test"):
        default_tab = "ai-menu"
    elif source == "home":
        default_tab = "self-menu"
    else:
        default_tab = (
            "ai-menu" if selected_exercises else "self-menu"
        )

    if request.method == "POST":

        submitted_tab = request.form.get("active_tab", "")

        if submitted_tab in ("ai-menu", "self-menu"):
            default_tab = submitted_tab

    raw_goal = str(
        conditions.get("duration", "0分")
    ).replace("分", "")

    goal_minutes = (
        int(raw_goal) if raw_goal.isdigit() else 0
    )

    can_repeat_yesterday = bool(
        yesterday_record
        and (
            yesterday_record.question
            or yesterday_record.self_exercises
        )
    )

    if request.method == "POST":

        self_exercises = request.form.get(
            "self_exercises", ""
        ).strip()

        manual_minutes_text = request.form.get(
            "manual_minutes", ""
        ).strip()

        # タイマー開始時の目標時間チェック
        if request.form.get("validate_goal") == "1":

            goal_minutes_text = request.form.get(
                "goal_minutes", ""
            ).strip()

            if (
                not goal_minutes_text.isdigit()
                or not 1 <= int(goal_minutes_text) <= 30
            ):
                error = "目標時間を1〜30分で入力してください。"
            else:
                error = None

            return render_template(
                "test/test_implementation.html",
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

            error = (
                "メニューを選ぶか、自主運動の内容を入力してください。"
            )

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
                "test/test_implementation.html",
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

        # 実施結果を保存
        session["implementation_result"] = {
            "actual_minutes": actual_minutes,
            "duration_seconds": duration_seconds,
            "self_exercises": self_exercises,
        }

        return redirect(
            url_for("test.save_registration")
        )

    self_exercises = session.pop(
        "repeat_self_exercises", ""
    )

    return render_template(
        "test/test_implementation.html",
        selected_exercises=selected_exercises,
        plan_conditions=conditions,
        goal_minutes=goal_minutes,
        self_exercises=self_exercises,
        manual_minutes="",
        default_tab=default_tab,
        source=source,
        can_repeat_yesterday=can_repeat_yesterday,
    )


# ========================================
# 運動実施内容の登録
# ========================================

@test.route("/registration", methods=["GET", "POST"])
def save_registration():

    selected_exercises = session.get("selected_exercises", [])
    conditions = session.get("selected_plan_conditions", {})
    implementation_result = session.get("implementation_result", {})

    # 登録画面の表示
    if request.method == "GET":

        return render_template(
            "test/test_registration.html",
            selected_exercises=selected_exercises,
            self_exercises=implementation_result.get(
                "self_exercises", ""
            ),
            actual_minutes=implementation_result.get(
                "actual_minutes", ""
            ),
        )

    user_id = session.get("user_id")

    if user_id is None:
        return redirect(url_for("login.login"))

    # 運動内容
    self_exercises = (
        request.form.get("self_exercises", "").strip()
        or implementation_result.get("self_exercises", "")
    )

    actual_minutes_text = (
        request.form.get("actual_minutes", "").strip()
        or str(implementation_result.get("actual_minutes", ""))
    )

    if not selected_exercises and not self_exercises:

        return render_template(
            "test/test_registration.html",
            selected_exercises=selected_exercises,
            self_exercises=self_exercises,
            actual_minutes=actual_minutes_text,
            error="選択した運動か、自主的に行った運動を入力してください。",
        )

    if (
        not actual_minutes_text.isdigit()
        or not 1 <= int(actual_minutes_text) <= 30
    ):

        return render_template(
            "test/test_registration.html",
            selected_exercises=selected_exercises,
            self_exercises=self_exercises,
            actual_minutes=actual_minutes_text,
            error="運動時間を1〜30分で入力してください。",
        )

    actual_minutes = int(actual_minutes_text)

    selected_text = "\n".join(
        (
            f'{index}. {exercise["name"]}：'
            f'{exercise["sets"]}セット、'
            f'標準目標 {exercise["target_value"]}{exercise["unit"]}'
        )
        for index, exercise in enumerate(
            selected_exercises, start=1
        )
    )

    try:

        record = Situation(
            user_id=user_id,
            kind="registration",
            answer=selected_text or "自主的に行った運動",
            self_exercises=self_exercises or None,
            category=conditions.get("category"),
            experience=conditions.get("experience"),
            duration=str(actual_minutes),
            equipment=conditions.get("equipment"),
            question=json.dumps(
                selected_exercises,
                ensure_ascii=False
            ),
        )

        db.session.add(record)
        db.session.commit()

        session.pop("selected_exercises", None)
        session.pop("selected_plan_conditions", None)
        session.pop("implementation_result", None)

        # 登録完了確認画面へ
        return redirect(url_for("test.registration_complete"))

    except Exception:

        db.session.rollback()

        current_app.logger.exception(
            "テスト用運動実施内容の保存に失敗しました"
        )

        return render_template(
            "test/test_registration.html",
            selected_exercises=selected_exercises,
            self_exercises=self_exercises,
            actual_minutes=actual_minutes_text,
            error="登録内容を保存できませんでした。",
        )

@test.route("/registration/complete", methods=["GET"])
def registration_complete():
    return render_template("test/test_registration_complete.html")