"""add pg_trgm and trigram indexes for typo-tolerant search

Revision ID: 7c1e4f3a9b02
Revises: 2a5b9f7b6dc9
Create Date: 2026-08-16 12:10:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '7c1e4f3a9b02'
down_revision: Union[str, Sequence[str], None] = '2a5b9f7b6dc9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Trigram support for the free-text search.

    Two things at once: pg_trgm accelerates the existing `ILIKE '%…%'`
    substring match (a btree index cannot), and it provides the
    word_similarity operator behind the typo fallback in app/api/search.py.
    GIN over the concatenated brand+model string is what the fallback
    actually probes.
    """
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE INDEX ix_product_brand_trgm ON product USING gin (brand gin_trgm_ops)")
    op.execute("CREATE INDEX ix_product_model_name_trgm ON product USING gin (model_name gin_trgm_ops)")
    op.execute(
        "CREATE INDEX ix_product_brand_model_trgm ON product "
        "USING gin ((brand || ' ' || model_name) gin_trgm_ops)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_product_brand_model_trgm")
    op.execute("DROP INDEX IF EXISTS ix_product_model_name_trgm")
    op.execute("DROP INDEX IF EXISTS ix_product_brand_trgm")
    # The extension is left in place: other objects may depend on it, and
    # dropping it is not something a schema downgrade should decide.
