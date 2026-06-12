"""Hyperparameter search database models."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class HyperparameterSearch(Base):
    """Hyperparameter search job model."""
    __tablename__ = "hyperparameter_searches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    method: Mapped[str] = mapped_column(String(20), nullable=False, default="bayesian")
    search_space: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    search_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    base_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    n_trials: Mapped[int] = mapped_column(Integer, default=0)
    completed_trials: Mapped[int] = mapped_column(Integer, default=0)
    best_metric: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    best_trial_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="hyperparameter_searches")
    trials = relationship("HyperparameterTrial", back_populates="search", lazy="selectin")

    def __repr__(self) -> str:
        return f"<HyperparameterSearch {self.name} [{self.status}]>"


class HyperparameterTrial(Base):
    """Individual trial within a hyperparameter search."""
    __tablename__ = "hyperparameter_trials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    search_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hyperparameter_searches.id"), nullable=False, index=True
    )
    trial_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )
    params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    metric_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    search = relationship("HyperparameterSearch", back_populates="trials")

    def __repr__(self) -> str:
        return f"<HyperparameterTrial #{self.trial_number} [{self.status}]>"
