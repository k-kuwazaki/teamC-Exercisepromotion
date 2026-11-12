#運動トレーナーの指示文、候補データの形式、AIへ渡す文章
SYSTEM_INSTRUCTION = (
    "あなたは日本語で回答する運動トレーナーです。"
    "利用者の質問に直接答えてください。"
    "自然で正確な日本語を使用してください。"
    "存在しない運動名や専門用語を作らないでください。"
    "分からないことを推測で事実のように説明しないでください。"
    "運動方法は番号付きの手順で、分かりやすく説明してください。"
    "痛みがある場合は運動を中止するよう伝えてください。"
    "医療上の診断はしないでください。"
)


EXERCISE_OPTIONS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "options": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "minutes": {"type": "INTEGER"},
                    "sets": {"type": "INTEGER"},
                    "target_value": {"type": "INTEGER"},
                    "unit": {
                        "type": "STRING",
                        "enum": ["回", "秒", "分", "kg"],
                    },
                    "description": {"type": "STRING"},
                    "caution": {"type": "STRING"},
                },
                "required": [
                    "name",
                    "minutes",
                    "sets",
                    "target_value",
                    "unit",
                    "description",
                    "caution",
                ],
            },
        },
    },
    "required": ["options"],
}


def build_exercise_options_prompt(
    profile_text,
    category,
    experience,
    duration,
    equipment,
):
    return f"""
あなたは日本語で回答する運動トレーナーです。
利用者に合う運動候補を3つ作成してください。

【利用者の登録情報】
{profile_text}

【今回選択した条件】
カテゴリー：{category}
運動経験：{experience}
運動できる時間：{duration}
器具：{equipment}

各候補は、実在する一般的な運動にしてください。
目安時間は指定された運動時間以内にしてください。
初心者には無理のない内容を提案してください。
標準目標値と単位も設定してください。
身長や体重だけから健康状態を診断しないでください。
痛みが出た場合は運動を中止するよう伝えてください。
各候補の説明は簡潔にしてください。
"""