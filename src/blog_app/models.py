# -*- coding: utf-8 -*-
"""Database models for the Blog application."""

from __future__ import annotations
from typing import Optional, List

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Integer, String, Text, ForeignKey, func, select
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.exc import IntegrityError
from slugify import slugify

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model storing authentication and profile data."""
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationship to posts; deletes cascade when user is deleted
    posts: Mapped[List["Post"]] = relationship(
        back_populates="author",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # ----- Required methods -----
    def set_password(self, password: str) -> None:
        """Hash and store password using Werkzeug."""
        self.password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password hash."""
        return check_password_hash(self.password, password)

    def save(self) -> None:
        """Persist user to DB."""
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_by_id(user_id: int) -> Optional["User"]:
        """Get user by ID."""
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_email(email: str) -> Optional["User"]:
        """Get user by email (case-insensitive)."""
        stmt = select(User).where(func.lower(User.email) == func.lower(email))
        return db.session.execute(stmt).scalar_one_or_none()


class Post(db.Model):
    """Blog post entity: belongs to a user and exposes a public slug URL."""
    __tablename__ = "post"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    author: Mapped[User] = relationship(back_populates="posts")

    # ----- Required methods -----
    def _generate_unique_slug(self) -> str:
        """Generate a unique slug from the title; add numeric suffix when duplicated."""
        base = slugify(self.title) or "post"
        candidate = base
        counter = 1
        # Optimistic check to ensure uniqueness before commit
        while db.session.scalar(select(func.count()).select_from(Post).where(Post.slug == candidate)):
            candidate = f"{base}-{counter}"
            counter += 1
        return candidate

    def public_url(self) -> str:
        """Return the public URL path for this post (used in templates)."""
        return f"/post/{self.slug}/"

    def save(self) -> None:
        """Persist post with automatic slug generation and collision handling."""
        if not getattr(self, "slug", None):
            self.slug = self._generate_unique_slug()

        db.session.add(self)
        try:
            db.session.commit()
        except IntegrityError:
            # Handle rare race condition collisions: regenerate slug with numeric suffix
            db.session.rollback()
            base = slugify(self.title) or "post"
            counter = 1
            while True:
                new_slug = f"{base}-{counter}"
                self.slug = new_slug
                db.session.add(self)
                try:
                    db.session.commit()
                    break
                except IntegrityError:
                    db.session.rollback()
                    counter += 1

    @staticmethod
    def get_by_slug(slug: str) -> Optional["Post"]:
        """Get a single post by slug."""
        stmt = select(Post).where(Post.slug == slug)
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_all() -> list["Post"]:
        """Return all posts ordered by ID desc (newest first)."""
        stmt = select(Post).order_by(Post.id.desc())
        return list(db.session.execute(stmt).scalars().all())