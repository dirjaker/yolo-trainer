import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="yolo")
    classes: Mapped[list | None] = mapped_column(JSON, nullable=True)  # ["person", "car", ...]
    stats: Mapped[dict | None] = mapped_column(JSON, nullable=True)    # {"train": 1000, "val": 200, ...}
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="uploading", index=True
        # uploading, processing, ready, error
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Relationships
    user = relationship("User", back_populates="datasets")
    trainings = relationship("Training", back_populates="dataset", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Dataset {self.name}>"
