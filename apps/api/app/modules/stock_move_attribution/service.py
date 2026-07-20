from sqlalchemy.orm import Session

from app.modules.stock_move_attribution.engine import StockMoveAttributionEngine
from app.modules.stock_move_attribution.evidence import StockMoveEvidenceProvider
from app.modules.stock_move_attribution.schemas import StockMoveAttributionResponse
from app.services.stock_service import StockService


class StockMoveAttributionService:
    def __init__(
        self,
        db: Session,
        evidence_provider: StockMoveEvidenceProvider,
        engine: StockMoveAttributionEngine | None = None,
    ):
        self.stocks = StockService(db)
        self.evidence_provider = evidence_provider
        self.engine = engine or StockMoveAttributionEngine()

    async def analyze(self, symbol: str) -> StockMoveAttributionResponse:
        code = self.stocks.resolve_symbol(symbol)
        evidence = await self.evidence_provider.fetch_context(code)
        return self.engine.analyze(evidence)
