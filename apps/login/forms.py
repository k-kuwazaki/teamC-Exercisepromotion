def login_form_data(form):
    """Read login fields from a Werkzeug form object."""
    return {
        "email": form.get("email", "").strip(),
        "password": form.get("password", ""),
    }
