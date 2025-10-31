from alembic import op
import sqlalchemy as sa


revision = "202407010001"
down_revision = "202401010001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "contracts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("release_id", sa.Integer(), sa.ForeignKey("releases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pdf_path", sa.String(length=1024), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="drafted"),
        sa.Column("sent_via", sa.String(length=32), nullable=False, server_default="email"),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("accept_token", sa.String(length=64), nullable=False),
        sa.Column("accept_token_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mail_message_key", sa.String(length=128), nullable=True),
        sa.UniqueConstraint("accept_token"),
        sa.UniqueConstraint("mail_message_key"),
    )
    op.create_index("ix_contracts_release_id", "contracts", ["release_id"])

    op.create_table(
        "mail_outbox",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("to_email", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("html", sa.Text(), nullable=True),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("attachments", sa.JSON(), nullable=True),
        sa.Column("message_key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_mail_outbox_message_key", "mail_outbox", ["message_key"], unique=True)

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("release_id", sa.Integer(), sa.ForeignKey("releases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("contract_id", sa.Integer(), sa.ForeignKey("contracts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("robokassa_inv_id", sa.Integer(), nullable=False),
        sa.Column("out_sum", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("signature_algo", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("is_test", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index("ix_payments_release_id", "payments", ["release_id"])
    op.create_index("ix_payments_robokassa_inv_id", "payments", ["robokassa_inv_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_payments_robokassa_inv_id", table_name="payments")
    op.drop_index("ix_payments_release_id", table_name="payments")
    op.drop_table("payments")
    op.drop_index("ix_mail_outbox_message_key", table_name="mail_outbox")
    op.drop_table("mail_outbox")
    op.drop_index("ix_contracts_release_id", table_name="contracts")
    op.drop_table("contracts")
