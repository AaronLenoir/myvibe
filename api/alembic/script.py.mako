"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa

${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision | comma,n)}
branch_labels = ${repr(branch_labels | comma,n)}
depends_on = ${repr(depends_on | comma,n)}


def upgrade():
${upgrades if upgrades else "    pass"}


def downgrade():
${downgrades if downgrades else "    pass"}
