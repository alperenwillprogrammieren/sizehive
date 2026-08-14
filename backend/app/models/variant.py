from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Variant(Base):
    __tablename__ = "variant"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), index=True)
    shop_id: Mapped[int] = mapped_column(ForeignKey("shop.id"), index=True)
    shop_sku: Mapped[str] = mapped_column(String(120))
    ean: Mapped[str | None] = mapped_column(String(20), nullable=True)
    size_raw: Mapped[str] = mapped_column(String(60))
    size_w: Mapped[int | None] = mapped_column(nullable=True)
    size_l: Mapped[int | None] = mapped_column(nullable=True)
    color: Mapped[str] = mapped_column(String(60))
    url: Mapped[str] = mapped_column(String(1000))

    product: Mapped["Product"] = relationship(back_populates="variants")
    shop: Mapped["Shop"] = relationship(back_populates="variants")
    price_snapshots: Mapped[list["PriceSnapshot"]] = relationship(
        back_populates="variant", order_by="PriceSnapshot.captured_at"
    )

    __table_args__ = (
        # Identity of a variant within a shop's catalog — the anchor for idempotent import (M2).
        UniqueConstraint("shop_id", "shop_sku", name="uq_variant_shop_sku"),
    )
