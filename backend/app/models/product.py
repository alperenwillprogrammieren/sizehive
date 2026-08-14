from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Product(Base):
    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand: Mapped[str] = mapped_column(String(120), index=True)
    model_name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(60), index=True)
    gender: Mapped[str] = mapped_column(String(20))

    # Facet attributes (fit, rise, wash, material, ...), keyed by attribute name.
    attributes: Mapped[dict] = mapped_column(JSONB, default=dict)
    # Same keys as `attributes`; each value is {"source": "feed"|"rule"|"llm", "confidence": float}.
    attribute_sources: Mapped[dict] = mapped_column(JSONB, default=dict)

    variants: Mapped[list["Variant"]] = relationship(back_populates="product")

    __table_args__ = (
        Index("ix_product_attributes_gin", "attributes", postgresql_using="gin"),
    )
