# -*- coding: utf-8 -*-
"""Flask-WTF forms for authentication and Post creation."""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, Length


class SignupForm(FlaskForm):
    """User registration form."""
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=128)])
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    """User login form."""
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Log in")


class PostForm(FlaskForm):
    """Post creation form for the main entity."""
    title = StringField("Title", validators=[DataRequired(), Length(min=3, max=200)])
    category = StringField("Category", validators=[DataRequired(), Length(min=3, max=80)])
    content = TextAreaField("Content", validators=[DataRequired(), Length(min=10)])
    submit = SubmitField("Publish")