from app.utils.errors import InvalidBoardError, InvalidSymbolError


def infer_market(symbol: str) -> str:
    if not symbol.isdigit() or len(symbol) != 6:
        raise InvalidSymbolError(symbol)
    if symbol.startswith(("600", "601", "603", "605", "688")):
        return "sh"
    if symbol.startswith(("000", "001", "002", "003", "300", "301")):
        return "sz"
    raise InvalidSymbolError(symbol)


def infer_secid(symbol: str) -> tuple[str, str]:
    market = infer_market(symbol)
    market_id = "1" if market == "sh" else "0"
    return f"{market_id}.{symbol}", market


def infer_board_secid(board: str) -> tuple[str, str]:
    normalized = board.strip().upper()
    code = normalized[3:] if normalized.startswith("90.") else normalized
    if code.startswith("BK") and len(code) == 6 and code[2:].isdigit():
        return f"90.{code}", code
    raise InvalidBoardError(board)
