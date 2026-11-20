from datetime import datetime

def registration_form_data(form):
    """Read registration fields from a Werkzeug form object."""
    return {
        "username": form.get("name", "").strip(),
        "email": form.get("email", "").strip(),
        "password": form.get("password", ""),
        "height": form.get("height", type=float),
        "weight": form.get("weight", type=float),
        "birthday": form.get("birthday", ""),
        "exercise_habit": form.get("exercise_habit", ""),
        "goal": form.get("goal", "").strip(),
    }
