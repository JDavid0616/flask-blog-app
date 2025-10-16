# -*- coding: utf-8 -*-
"""
Main Flask application with routes, authentication, and views.
Fulfills requirements: Flask-Login, Flask-WTF, SQLAlchemy, PostgreSQL, slugs, CSRF, etc.
"""

from __future__ import annotations
import os
from urllib.parse import urlparse, urljoin

from flask import (
    Flask, render_template, redirect, url_for, flash, request, abort
)
from flask_login import (
    LoginManager, login_user, login_required, logout_user, current_user
)
from sqlalchemy.exc import IntegrityError

from .models import db, User, Post
from .forms import SignupForm, LoginForm, PostForm


def create_app() -> Flask:
    """Application factory."""
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # --- Security / Config ---
    # SECRET_KEY must be set from environment for production; for dev we fallback.
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

    # Database: PostgreSQL connection string is required.
    # Format: postgresql+psycopg://user:password@host:port/database
    db_uri = os.environ.get("DATABASE_URL", "").strip()
    if not db_uri:
        # Helpful message for devs if not configured
        app.logger.warning("DATABASE_URL is not set. Example: postgresql+psycopg://user:pass@localhost:5432/blog_app")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # --- Extensions init ---
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        """Flask-Login loader required to keep users logged in."""
        try:
            return User.get_by_id(int(user_id))
        except (TypeError, ValueError):
            return None

    # --- Utilities ---
    def is_safe_url(target: str) -> bool:
        """
        Validate the 'next' parameter to prevent open redirect.
        Only allow relative URLs or same-host paths.
        """
        if not target:
            return False
        ref_url = urlparse(request.host_url)
        test_url = urlparse(urljoin(request.host_url, target))
        return (test_url.scheme in ("http", "https")) and (ref_url.netloc == test_url.netloc)

    # --- Routes ---

    @app.route("/", methods=["GET"])
    def index():
        """Public home page listing all posts."""
        posts = Post.get_all()
        return render_template("index.html", posts=posts)

    @app.route("/post/<string:slug>/", methods=["GET"])
    def post_detail(slug: str):
        """Public detail view by slug; return 404 if not found."""
        post = Post.get_by_slug(slug)
        if not post:
            abort(404)
        return render_template("post_view.html", post=post)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Login route with safe next redirection and remember_me support."""
        if current_user.is_authenticated:
            return redirect(url_for("index"))

        form = LoginForm()
        if form.validate_on_submit():
            user = User.get_by_email(form.email.data)
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)

                next_url = request.args.get("next")
                if next_url and is_safe_url(next_url):
                    return redirect(next_url)
                return redirect(url_for("index"))

            flash("Invalid credentials. Please check your email and password.", "danger")

        return render_template("login_form.html", form=form)

    @app.route("/signup/", methods=["GET", "POST"])
    def signup():
        """Register new users; auto-login on success; check duplicate emails."""
        if current_user.is_authenticated:
            return redirect(url_for("index"))

        form = SignupForm()
        if form.validate_on_submit():
            if User.get_by_email(form.email.data):
                flash("Email already registered. Please use another one or log in.", "warning")
                return render_template("admin/signup_form.html", form=form)

            user = User(name=form.name.data, email=form.email.data)
            user.set_password(form.password.data)
            try:
                user.save()
            except IntegrityError:
                # Extremely rare: race on email uniqueness
                db.session.rollback()
                flash("Email already registered. Please try a different one.", "danger")
                return render_template("admin/signup_form.html", form=form)

            login_user(user)
            return redirect(url_for("index"))

        return render_template("admin/signup_form.html", form=form)

    @app.route("/logout", methods=["GET"])
    @login_required
    def logout():
        """Logout current user and redirect to home."""
        logout_user()
        return redirect(url_for("index"))

    @app.route("/admin/post/", methods=["GET", "POST"])
    @login_required
    def create_post():
        """Protected route to create a new Post owned by current_user."""
        form = PostForm()
        if form.validate_on_submit():
            post = Post(
                user_id=current_user.id,
                title=form.title.data,
                category=form.category.data,
                content=form.content.data
            )
            post.save()
            flash("Post created successfully!", "success")
            return redirect(post.public_url())

        return render_template("admin/post_form.html", form=form)

    # --- Error handlers ---

    @app.errorhandler(404)
    def not_found(error):
        return render_template("base_template.html", content="<h1>404 Not Found</h1>"), 404

    # --- Create tables on first request (development convenience) ---
    @app.before_request
    def ensure_db_initialized():
        # Create tables if they do not exist. In real production you would run migrations.
        if db.engine.url and db.engine.url.get_backend_name().startswith("postgresql"):
            with app.app_context():
                db.create_all()

    return app


# Allow `python -m blog_app.run` or `flask --app blog_app.run run`
app = create_app()

if __name__ == "__main__":
    # Local debug run:
    app.run(debug=True, host="127.0.0.1", port=5000)