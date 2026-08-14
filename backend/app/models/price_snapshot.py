from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PriceSnapshot(Base):
    __tablename__ = "price_snapshot"

    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("variant.id"), index=True)
    price_cents: Mapped[int] = mapped_column()
    list_price_cents: Mapped[int] = mapped_column()
    in_stock: Mapped[bool] = mapped_column()
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    variant: Mapped["Variant"] = relationship(back_populates="price_snapshots")
