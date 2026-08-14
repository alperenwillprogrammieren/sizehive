from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Shop(Base):
    __tablename__ = "shop"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    affiliate_network: Mapped[str] = mapped_column(String(60))

    variants: Mapped[list["Variant"]] = relationship(back_populates="shop")
