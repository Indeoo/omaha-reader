from functools import wraps

from flask import Blueprint, render_template, request, session, redirect, url_for, flash


def _require_auth(require_password):
    """Decorator to enforce auth when password protection is enabled."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not require_password:
                return f(*args, **kwargs)
            if not session.get("authenticated"):
                return redirect(url_for("web.login"))
            return f(*args, **kwargs)

        return wrapped

    return decorator


def create_web_blueprint(require_password, password, game_data_receiver):
    blueprint = Blueprint("web", __name__)

    @blueprint.route("/login", methods=["GET", "POST"])
    def login():
        if not require_password:
            return redirect(url_for("web.index"))

        if request.method == "POST":
            if request.form.get("password") == password:
                session["authenticated"] = True
                return redirect(url_for("web.index"))
            flash("Invalid password")
            return render_template("login.html", error="Invalid password")

        return render_template("login.html")

    @blueprint.route("/")
    @_require_auth(require_password)
    def index():
        return render_template("index.html")

    @blueprint.route("/client/<client_id>")
    @_require_auth(require_password)
    def client_view(client_id):
        """Individual client view page."""
        connected_clients = game_data_receiver.get_connected_clients()
        if client_id not in connected_clients:
            return render_template("index.html", error=f"Client '{client_id}' not found"), 404

        return render_template("client.html", client_id=client_id)

    return blueprint
