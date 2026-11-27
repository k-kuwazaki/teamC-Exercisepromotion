from datetime import datetime

def registration_form_data(form):
    return {
        "username": form.get("username", ""),
        "height": float(form.get("height")) if form.get("height") else None,
        "weight": float(form.get("weight")) if form.get("weight") else None,
        "birthday": form.get("birthday", ""),
        "email": form.get("email", ""),
        "password": form.get("password", ""),
        "exercise_habit": form.get("exercise_habit", ""),
        "goal": form.get("goal", ""),
    }

def validate_password(password):
    """Validate registration password."""
    if not (
        len(password) >= 8 and
        any(c.isupper() for c in password) and
        any(c.islower() for c in password) and
        any(c.isdigit() for c in password) and 
        any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    ):
        return False

    return True