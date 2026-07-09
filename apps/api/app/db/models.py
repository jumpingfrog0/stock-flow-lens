from sqlalchemy import Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Stock(Base):
    __tablename__ = "stocks"

    code: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    market: Mapped[str] = mapped_column(String, nullable=False)
    secid: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)


class MoneyFlowDaily(Base):
    __tablename__ = "money_flow_daily"
    __table_args__ = (
        UniqueConstraint("stock_code", "trade_date", "source", name="uq_money_flow_daily"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    stock_code: Mapped[str] = mapped_column(String, nullable=False, index=True)
    trade_date: Mapped[str] = mapped_column(String, nullable=False, index=True)
    main_net_inflow: Mapped[float] = mapped_column(Float, nullable=False)
    super_large_inflow: Mapped[float | None] = mapped_column(Float)
    large_inflow: Mapped[float | None] = mapped_column(Float)
    medium_inflow: Mapped[float | None] = mapped_column(Float)
    small_inflow: Mapped[float | None] = mapped_column(Float)
    close_price: Mapped[float | None] = mapped_column(Float)
    change_pct: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String, nullable=False, default="eastmoney")
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
