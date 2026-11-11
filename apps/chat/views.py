import os

from flask import (
    Blueprint,
    current_app,
    render_template,
    request,
    session,
)
from google import genai
from google.genai import types

from apps.app import db
from apps.chat.forms import CoachForm, PlanForm
from apps.situation.models import Situation


chat = Blueprint(
    "chat",
    __name__,
    template_folder="templates",
    static_folder="static",
)


SYSTEM_INSTRUCTION = (
    "あなたは日本語で回答する運動トレーナーです。"
    "利用者の質問に直接答えてください。"
    "自然で正確な日本語を使用してください。"
    "存在しない運動名や専門用語を作らないでください。"
    "分からないことを推測で事実のように説明しないでください。"
    "利用者の名前を勝手に作ったり、変更したりしないでください。"
    "運動方法は番号付きの手順で、分かりやすく説明してください。"
    "説明を途中で終わらせず、最後まで回答してください。"
    "痛みがある場合は運動を中止するよう伝えてください。"
    "医療上の診断はしないでください。"
)


@chat.app_context_processor
def inject_chat_forms():
    if request.path == "/chat":
        return {
            "coach_form": CoachForm(),
            "plan_form": PlanForm(),
        }
    return {}


def generate_answer(
    prompt,
    system_instruction=None,
    log_message="Gemini API request failed",
):
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return None, "Gemini APIキーが設定されていません。"

    config_options = {"max_output_tokens": 2048}

    if system_instruction:
        config_options["system_instruction"] = system_instruction

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config=types.GenerateContentConfig(**config_options),
        )

        if not response.text:
            return None, (
                "回答を生成できませんでした。"
                "質問を変えてお試しください。"
            )

        return response.text, None

    except Exception:
        current_app.logger.exception(log_message)
        return None, (
            "Gemini APIとの通信に失敗しました。"
            "APIキー、モデル名、利用制限を確認してください。"
        )


def save_situation(
    kind,
    answer,
    question=None,
    category=None,
    experience=None,
    duration=None,
    equipment=None,
):
    """ログイン中のユーザーに回答履歴を紐づけて保存する。"""
    user_id = session.get("user_id")

    if user_id is None:
        return "履歴を保存するにはログインしてください。"

    try:
        record = Situation(
            user_id=user_id,
            kind=kind,
            question=question,
            category=category,
            experience=experience,
            duration=duration,
            equipment=equipment,
            answer=answer,
        )

        db.session.add(record)
        db.session.commit()
        return None

    except Exception:
        db.session.rollback()
        current_app.logger.exception("履歴の保存に失敗しました")
        return "履歴を保存できませんでした。"


@chat.route("/chat", methods=["GET", "POST"])
def index():
    coach_form = CoachForm()
    plan_form = PlanForm()

    chat_answer = None
    plan_answer = None
    chat_error = None
    plan_error = None

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

                prompt = f"""
あなたは日本語で回答する運動トレーナーです。

利用者の条件に合った運動メニューを提案してください。

【運動カテゴリー】
{category}

【運動経験】
{experience}

【運動時間】
{duration}

【器具】
{equipment}

次の順番で説明してください。
1. 今回のメニューの目的
2. 具体的な運動メニュー
3. 各運動の回数・セット数・休憩時間
4. 正しいフォームと注意点
5. 継続するための短いアドバイス

条件：
- 実在する一般的な運動名を使う。
- 架空の運動名や専門用語を作らない。
- 指定された運動時間に収まるメニューにする。
- 初心者には無理のない負荷を提案する。
- 自然で正確な日本語で、最後まで回答する。
- 痛みが出た場合は運動を中止するよう伝える。
- 医療上の診断をしない。
- 目標達成を保証しない。
"""

                plan_answer, plan_error = generate_answer(
                    prompt,
                    log_message="運動メニューの生成に失敗しました",
                )

                if plan_answer:
                    plan_error = save_situation(
                        kind="plan",
                        answer=plan_answer,
                        category=category,
                        experience=experience,
                        duration=duration,
                        equipment=equipment,
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
    )