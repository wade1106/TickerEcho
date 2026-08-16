import concurrent.futures
import json
import logging
import math
import os
import threading
import time
from typing import Callable, TypeVar

import yfinance as yf
from fastapi import APIRouter, Depends, HTTPException, Query

from auth import get_current_user
from stock_data import search_stocks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stocks", tags=["stocks"])

# ── 持久化快取 ────────────────────────────────────────────────
_CACHE_FILE = "/app/data/yf_cache.json"
_cache_lock = threading.Lock()
PRICE_TTL = 60
INFO_TTL = 3600


def _load_disk_cache() -> dict:
    try:
        with open(_CACHE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"price": {}, "info": {}}


def _save_disk_cache(cache: dict) -> None:
    try:
        os.makedirs(os.path.dirname(_CACHE_FILE), exist_ok=True)
        with open(_CACHE_FILE, "w") as f:
            json.dump(cache, f)
    except Exception as e:
        logger.warning(f"Failed to save cache: {e}")


_disk_cache = _load_disk_cache()


def _get_cache(category: str, ticker: str, ttl: int):
    with _cache_lock:
        entry = _disk_cache.get(category, {}).get(ticker)
    if entry and time.time() - entry["ts"] < ttl:
        return entry["data"]
    return None


def _set_cache(category: str, ticker: str, data: dict) -> None:
    with _cache_lock:
        _disk_cache.setdefault(category, {})[ticker] = {"ts": time.time(), "data": data}
        _save_disk_cache(_disk_cache)


# ── Thread pool timeout ───────────────────────────────────────
T = TypeVar("T")
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)


def _run(fn: Callable[[], T], timeout: float = 12) -> T:
    future = _executor.submit(fn)
    try:
        return future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        raise HTTPException(status_code=502, detail="Upstream request timed out")


# ── 台股 tick size / bucket ───────────────────────────────────
def _tick_size(price: float) -> float:
    if price < 10:
        return 0.01
    elif price < 50:
        return 0.05
    elif price < 100:
        return 0.10
    elif price < 500:
        return 0.50
    elif price < 1000:
        return 1.00
    else:
        return 5.00


def _calc_bucket_size(min_price: float, max_price: float, target: int = 40) -> float:
    tick = _tick_size((min_price + max_price) / 2)
    ticks_per_bucket = max(1, math.ceil((max_price - min_price) / target / tick))
    return ticks_per_bucket * tick


VALID_PERIODS = {"5d", "1mo", "3mo", "6mo", "1y"}


def _normalize_ticker(ticker: str) -> str:
    """Auto-append .TW for pure numeric Taiwan stock codes (e.g. 2330 -> 2330.TW)."""
    return ticker + ".TW" if ticker.isdigit() else ticker


# ── Routes ────────────────────────────────────────────────────
@router.get("/search")
def search(
    q: str = Query(..., min_length=2),
    _: str = Depends(get_current_user),
):
    results = search_stocks(q, limit=10)
    return results


@router.get("/{ticker}/price")
def get_price(ticker: str, _: str = Depends(get_current_user)):
    ticker = _normalize_ticker(ticker)
    cached = _get_cache("price", ticker, PRICE_TTL)
    if cached:
        return cached
    stale = _disk_cache.get("price", {}).get(ticker, {}).get("data")
    try:
        def _fetch():
            fi = yf.Ticker(ticker).fast_info
            return fi.last_price, fi.previous_close
        price, prev_close = _run(_fetch)
        if price is None or prev_close is None:
            raise HTTPException(status_code=502, detail="Stock data temporarily unavailable")
        change_percent = ((price - prev_close) / prev_close * 100) if prev_close else 0
        data = {
            "ticker": ticker,
            "price": round(price, 2),
            "change_percent": round(change_percent, 2),
        }
        _set_cache("price", ticker, data)
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch price for {ticker}: {e}")
        if stale:
            logger.warning(f"Returning stale price cache for {ticker}")
            return stale
        raise HTTPException(status_code=502, detail="Failed to fetch stock price")


def _translate_summary(text: str) -> str:
    if not text:
        return text
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source="en", target="zh-TW").translate(text, timeout=5)
    except Exception as e:
        logger.warning(f"Translation failed, returning original: {e}")
        return text


@router.get("/{ticker}/info")
def get_info(ticker: str, _: str = Depends(get_current_user)):
    ticker = _normalize_ticker(ticker)
    cached = _get_cache("info", ticker, INFO_TTL)
    if cached:
        return cached
    stale = _disk_cache.get("info", {}).get(ticker, {}).get("data")
    try:
        info = _run(lambda: yf.Ticker(ticker).info)
        if not info:
            raise HTTPException(status_code=502, detail="Stock data temporarily unavailable")
        summary_en = info.get("longBusinessSummary", "")
        data = {
            "ticker": ticker,
            "name": info.get("longName") or info.get("shortName", ""),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "country": info.get("country", ""),
            "website": info.get("website", ""),
            "employees": info.get("fullTimeEmployees"),
            "market_cap": info.get("marketCap"),
            "currency": info.get("currency", ""),
            "summary": _run(lambda: _translate_summary(summary_en), timeout=6),
        }
        _set_cache("info", ticker, data)
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch info for {ticker}: {e}")
        if stale:
            logger.warning(f"Returning stale info cache for {ticker}")
            return stale
        raise HTTPException(status_code=502, detail="Failed to fetch stock info")


@router.get("/{ticker}/chart")
def get_chart(
    ticker: str,
    period: str = Query(default="3mo"),
    _: str = Depends(get_current_user),
):
    ticker = _normalize_ticker(ticker)
    if period not in VALID_PERIODS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid period. Must be one of: {', '.join(sorted(VALID_PERIODS))}",
        )
    try:
        df = _run(lambda: yf.Ticker(ticker).history(period=period))
        if df.empty:
            return []
        records = []
        for ts, row in df.iterrows():
            records.append({
                "time": ts.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })
        return records
    except Exception as e:
        logger.error(f"Failed to fetch chart for {ticker}: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch chart data")


@router.get("/{ticker}/volume-profile")
def get_volume_profile(
    ticker: str,
    period: str = Query(default="3mo"),
    _: str = Depends(get_current_user),
):
    ticker = _normalize_ticker(ticker)
    if period not in VALID_PERIODS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid period. Must be one of: {', '.join(sorted(VALID_PERIODS))}",
        )
    try:
        def _fetch_profile():
            tk = yf.Ticker(ticker)
            df = tk.history(period=period)
            price = tk.fast_info.last_price if not df.empty else None
            return df, price
        df, current_price = _run(_fetch_profile)
        if df.empty:
            return []
        min_price = float(df["Low"].min())
        max_price = float(df["High"].max())
        bucket_size = _calc_bucket_size(min_price, max_price)
        num_buckets = math.ceil((max_price - min_price) / bucket_size)

        volumes = [0.0] * num_buckets
        for _, row in df.iterrows():
            typical = (float(row["High"]) + float(row["Low"]) + float(row["Close"])) / 3
            idx = int((typical - min_price) / bucket_size)
            idx = min(idx, num_buckets - 1)
            volumes[idx] += float(row["Volume"])

        result = []
        for i in range(num_buckets - 1, -1, -1):
            low = round(min_price + i * bucket_size, 2)
            high = round(min_price + (i + 1) * bucket_size, 2)
            if low <= current_price < high:
                bar_type = "價"
            elif high <= current_price:
                bar_type = "支撐"
            else:
                bar_type = "壓力"
            result.append({
                "label": f"{low:.2f}~{high:.2f}",
                "price_low": low,
                "price_high": high,
                "volume": int(volumes[i]),
                "type": bar_type,
            })

        return result
    except Exception as e:
        logger.error(f"Failed to fetch volume profile for {ticker}: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch volume profile")
