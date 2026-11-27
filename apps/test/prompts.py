# 運動トレーナーの指示文、候補データの形式、AIへ渡す文章
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
                    "movement_steps": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "phase": {"type": "STRING"},
                                "instruction": {"type": "STRING"},
                            },
                            "required": ["phase", "instruction"],
                        },
                    },
                },
                "required": [
                    "name",
                    "minutes",
                    "sets",
                    "target_value",
                    "unit",
                    "description",
                    "caution",
                    "movement_steps",
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

各候補に、動きが分かる3段階の movement_steps を設定してください。
各段階には phase（段階名）と instruction（その段階の姿勢・動作の説明）を含めてください。
動きのある運動は「開始姿勢」「動作」「戻す」の流れにしてください。
姿勢を保つ運動は「準備」「姿勢を保つ」「終了」の流れにしてください。
各 instruction は、実際の運動方法と注意点に合う具体的で短い説明にしてください。

身長や体重だけから健康状態を診断しないでください。
痛みが出た場合は運動を中止するよう伝えてください。
各候補の説明と各段階の指示は簡潔にしてください。
"""