from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from apps.app import db
from apps.situation.models import Situation
from apps.user.models import User

def calculate_mets(category, experience, planned_duration, exercise_count):
    """運動条件からMETsを算出する"""

    mets_table = {
        "筋力トレーニング": {
            "初心者": [3.0, 3.0, 3.0, 3.0],
            "中級者": [3.5, 3.5, 3.5, 3.5],
            "上級者": [3.5, 3.5, 4.0, 4.0],
        },
        "ダイエット": {
            "初心者": [2.5, 3.0, 3.0, 3.5],
            "中級者": [3.5, 3.5, 3.5, 4.0],
            "上級者": [3.5, 5.0, 5.0, 5.0],
        },
        "柔軟性・ストレッチ": {
            "初心者": [2.0, 2.0, 2.0, 2.0],
            "中級者": [2.5, 2.5, 2.5, 2.5],
            "上級者": [2.5, 3.0, 3.0, 3.0],
        },
        "体力づくり": {
            "初心者": [2.5, 3.0, 3.0, 3.0],
            "中級者": [3.5, 4.0, 4.0, 4.5],
            "上級者": [4.5, 4.5, 4.5, 4.5],
        },
        "運動不足の解消": {
            "初心者": [2.5, 2.5, 3.0, 3.0],
            "中級者": [3.0, 3.5, 4.0, 4.0],
            "上級者": [5.0, 4.5, 4.5, 4.5],
        },
    }

    # 経験レベルの表記を統一
    experience_map = {
        "beginner": "初心者",
        "intermediate": "中級者",
        "advanced": "上級者",
        "初心者": "初心者",
        "中級者": "中級者",
        "上級者": "上級者",
    }

    experience = experience_map.get(experience)

    # 予定時間を数値に変換
    try:
        planned_duration = int(
            str(planned_duration).replace("分", "").strip()
        )
    except (ValueError, TypeError):
        return None

    duration_index = {
        5: 0,
        10: 1,
        20: 2,
        30: 3,
    }.get(planned_duration)

    if (
        category not in mets_table
        or experience not in mets_table[category]
        or duration_index is None
    ):
        return None

    if exercise_count not in (1, 2, 3):
        return None

    base_mets = mets_table[category][experience][duration_index]

    # 種目数による調整
    adjustment = {
        1: -0.5,
        2: 0.0,
        3: 0.5,
    }

    return round(base_mets + adjustment[exercise_count], 1)

# 各種リンク先は後々それ用のファイルに移動させる
registration = Blueprint(
    "registration",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/registration"
)


# トップページ
@registration.route("/")
def index():
    return render_template("home/index.html")


# 振り返り
@registration.route("/lookingback")
def lookingback():
    return redirect(url_for("lookingback.index"))


# 運動内容を保存
@registration.route("/registration", methods=["GET", "POST"])
def save_registration():
    selected_exercises = session.get("selected_exercises", [])
    conditions = session.get("selected_plan_conditions", {})
    implementation_result = session.get("implementation_result", {})

    if request.method == "GET":
        return render_template(
            "registration/registration.html",
            selected_exercises=selected_exercises,
            self_exercises=implementation_result.get("self_exercises", ""),
            actual_minutes=implementation_result.get("actual_minutes", ""),
        )

    user_id = session.get("user_id")
    if user_id is None:
        return redirect(url_for("login.login"))

    # 登録画面で編集された値があればそれを使い、空欄なら実施画面の値を使う
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
            "registration/registration.html",
            selected_exercises=selected_exercises,
            self_exercises=self_exercises,
            actual_minutes=actual_minutes_text,
            error="選択した運動か、自主的に行った運動を入力してください。",
        )

    if (
        not actual_minutes_text.isdigit()
        or not 1 <= int(actual_minutes_text) <= 300
    ):
        return render_template(
            "registration/registration.html",
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
        for index, exercise in enumerate(selected_exercises, start=1)
    )
    
    # ユーザー情報を取得
    user = db.session.get(User, user_id)

    # METsを計算
    if self_exercises:
        # 自主運動の場合は固定METs 5.0を使用
        mets = 5.0
    else:
        # AI提案メニューの場合は既存の条件別METsを使用
        mets = calculate_mets(
            category=conditions.get("category"),
            experience=conditions.get("experience"),
            planned_duration=conditions.get("duration"),
            exercise_count=len(selected_exercises),
        )

    # 運動時の体重を取得
    weight = user.weight if user else None

    # 消費カロリーを計算
    calories = None

    if mets is not None and weight is not None and weight > 0:
        calories = round(
            mets * weight * (actual_minutes / 60) * 1.05,
            1,
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
            
            # 消費カロリー関連
            mets=mets,
            weight_at_exercise=weight,
            calories=calories,
        )

        db.session.add(record)
        db.session.commit()

        session.pop("selected_exercises", None)
        session.pop("selected_plan_conditions", None)
        session.pop("implementation_result", None)

        return redirect(url_for("registration.lookingback"))

    except Exception:
        db.session.rollback()
        current_app.logger.exception("運動実施内容の保存に失敗しました")

        return render_template(
            "registration/registration.html",
            selected_exercises=selected_exercises,
            self_exercises=self_exercises,
            actual_minutes=actual_minutes_text,
            error="登録内容を保存できませんでした。",
        )