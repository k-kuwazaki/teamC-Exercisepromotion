#画面表示、フォーム送信、候補の選択、ページ遷移
from flask import Blueprint, render_template, request, session
from apps.chat.ai_service import generate_answer, generate_exercise_options
from apps.chat.forms import CoachForm, PlanForm
from apps.chat.history_service import save_situation
from flask import redirect, url_for
from apps.chat.prompts import (
    SYSTEM_INSTRUCTION,
    build_exercise_options_prompt,
)
from apps.user.models import User

chat = Blueprint(
    "chat",
    __name__,
    template_folder="templates",
    static_folder="static",
)


@chat.app_context_processor
def inject_chat_forms():
    if request.path == "/chat":
        return {
            "coach_form": CoachForm(),
            "plan_form": PlanForm(),
        }
    return {}


def get_user_profile_text():
    user_id = session.get("user_id")

    if user_id is None:
        return None

    user = User.query.filter_by(id=user_id).first()

    if user is None:
        return None

    return f"""
年齢：{user.age if user.age is not None else "未登録"}
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


@chat.route("/chat", methods=["GET", "POST"])
def index():
    coach_form = CoachForm()
    plan_form = PlanForm()

    chat_answer = None
    plan_answer = None
    chat_error = None
    plan_error = None

    plan_options = session.get("plan_options", [])
    plan_conditions = session.get("plan_conditions", {})

    # 選択画面で、送信された候補IDをWTFormsが確認できるようにする
    plan_form.selected_exercises.choices = get_option_choices(plan_options)

    if request.method == "POST":
        action = request.form.get("action", "")

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
                        for errors in plan_form.errors.values()
                        for message in errors
                    ),
                    "入力内容を確認してください。",
                    )
        elif action == "select_exercises":
            plan_options = session.get("plan_options", [])
            plan_conditions = session.get("plan_conditions", {})
            plan_form.selected_exercises.choices = get_option_choices(
                plan_options
            )

            if not plan_options or not plan_conditions:
                plan_error = "候補がありません。先に運動候補を作成してください。"

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
                        option["minutes"] for option in selected_options
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
                            url_for("implementation.registration")
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
        "chat/chat.html",
        coach_form=coach_form,
        plan_form=plan_form,
        chat_answer=chat_answer,
        plan_answer=plan_answer,
        chat_error=chat_error,
        plan_error=plan_error,
        plan_options=plan_options,
        plan_conditions=plan_conditions,
    )