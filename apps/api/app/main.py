import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.query_history import router as query_history_router
from app.api.routes.stocks import router as stocks_router
from app.api.routes.watchlists import router as watchlists_router
from app.core.config import settings
from app.db.init_db import init_db
from app.modules.money_flow.auto_refresh import auto_refresh_service
from app.modules.money_flow.board_routes import board_flow_router, boards_router
from app.modules.money_flow.routes import router as money_flow_router
from app.modules.stock_move_attribution.routes import router as stock_move_attribution_router


logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    auto_refresh_service.start()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await auto_refresh_service.stop()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(money_flow_router)
app.include_router(stocks_router)
app.include_router(query_history_router)
app.include_router(watchlists_router)
app.include_router(boards_router)
app.include_router(board_flow_router)
app.include_router(stock_move_attribution_router)
