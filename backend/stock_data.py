import logging
from typing import Optional

import twstock

logger = logging.getLogger(__name__)

# twstock.codes: dict of code -> StockCodeInfo
# StockCodeInfo has: name, group, market ("上市"/"上櫃")
_STOCK_MAP: dict[str, dict] = {}


def _build_stock_map() -> None:
    for code, info in twstock.codes.items():
        suffix = ".TW" if getattr(info, "market", "") == "上市" else ".TWO"
        _STOCK_MAP[code] = {
            "ticker": f"{code}{suffix}",
            "code": code,
            "name": info.name,
        }


def ensure_loaded() -> None:
    if not _STOCK_MAP:
        try:
            _build_stock_map()
        except Exception as e:
            logger.error(f"Failed to build stock map: {e}")


def search_stocks(keyword: str, limit: int = 10) -> list[dict]:
    ensure_loaded()
    keyword = keyword.strip()
    results = []
    for code, info in _STOCK_MAP.items():
        if keyword in code or keyword in info["name"]:
            results.append(info)
        if len(results) >= limit:
            break
    return results


def get_ticker(code: str) -> Optional[str]:
    ensure_loaded()
    entry = _STOCK_MAP.get(code)
    return entry["ticker"] if entry else None


def get_name(code: str) -> Optional[str]:
    ensure_loaded()
    entry = _STOCK_MAP.get(code)
    return entry["name"] if entry else None
