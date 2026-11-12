#Gemini API呼び出しと候補データの読み取り
import json
import os

from flask import current_app
from google import genai
from google.genai import types

from apps.chat.prompts import EXERCISE_OPTIONS_SCHEMA


def generate_answer(
    prompt,
    system_instruction=None,
    log_message="Gemini API request failed",
    response_schema=None,
):
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return None, "Gemini APIキーが設定されていません。"

    config_options = {"max_output_tokens": 1024}

    if system_instruction:
        config_options["system_instruction"] = system_instruction

    if response_schema:
        config_options["response_mime_type"] = "application/json"
        config_options["response_schema"] = response_schema

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(**config_options),
        )

        if not response.text:
            return None, "回答を生成できませんでした。"

        return response.text, None

    except Exception:
        current_app.logger.exception(log_message)
        return None, (
            "Gemini APIとの通信に失敗しました。"
            "APIキー、モデル名、利用制限を確認してください。"
        )


def generate_exercise_options(prompt):
    response_text, error = generate_answer(
        prompt,
        log_message="運動候補の生成に失敗しました",
        response_schema=EXERCISE_OPTIONS_SCHEMA,
    )

    if error:
        return None, error

    try:
        result = json.loads(response_text)
        options = result["options"]

        if len(options) != 3:
            raise ValueError("候補が3件ではありません")

        allowed_units = {"回", "秒", "分", "kg"}

        for index, option in enumerate(options, start=1):
            option["id"] = str(index)

            if (
                not isinstance(option["minutes"], int)
                or option["minutes"] < 1
                or not isinstance(option["sets"], int)
                or option["sets"] < 1
                or not isinstance(option["target_value"], int)
                or option["target_value"] < 1
                or option["unit"] not in allowed_units
            ):
                raise ValueError("候補の値が正しくありません")

        return options, None

    except (ValueError, TypeError, KeyError):
        current_app.logger.exception("運動候補のJSON解析に失敗しました")
        return None, "運動候補を読み取れませんでした。もう一度お試しください。"