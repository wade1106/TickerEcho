import concurrent.futures
import logging
import math
import time
from typing import Callable, TypeVar

import yfinance as yf
from fastapi import APIRouter, Depends, HTTPException, Query

T = TypeVar("T")
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)


def _run(fn: Callable[[], T], timeout: float = 12) -> T:
    """在 thread pool 執行 fn，超過 timeout 秒直接拋 502。"""
    future = _executor.submit(fn)
    try:
        return future.result(timeout=timeout)
    except concurrent.futures.TimeoutError:
        raise HTTPException(status_code=502, detail="Upstream request timed out")

from auth import get_current_user
from stock_data import search_stocks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stocks", tags=["stocks"])

# 簡易 TTL 快取，減少對 Yahoo Finance 的請求頻率
_price_cache: dict[str, tuple[float, dict]] = {}   # ticker -> (ts, data)
_info_cache: dict[str, tuple[float, dict]] = {}    # ticker -> (ts, data)
PRICE_TTL = 60        # 秒
INFO_TTL  = 3600      # 秒


def _tick_size(price: float) -> float:
    """台股最小跳動單位（依股價分級）"""
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
    """以 tick size 為單位計算 bucket 寬度，目標約 target 格"""
    tick = _tick_size((min_price + max_price) / 2)
    ticks_per_bucket = max(1, math.ceil((max_price - min_price) / target / tick))
    return ticks_per_bucket * tick

VALID_PERIODS = {"5d", "1mo", "3mo", "6mo", "1y"}


@router.get("/search")
def search(
    q: str = Query(..., min_length=2),
    _: str = Depends(get_current_user),
):
    results = search_stocks(q, limit=10)
    return results


@router.get("/{ticker}/price")
def get_price(ticker: str, _: str = Depends(get_current_user)):
    cached = _price_cache.get(ticker)
    if cached and time.time() - cached[0] < PRICE_TTL:
        return cached[1]
    try:
        def _fetch():
            fi = yf.Ticker(ticker, session=_yf_session).fast_info
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
        _price_cache[ticker] = (time.time(), data)
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch price for {ticker}: {e}")
        if cached:
            logger.warning(f"Returning stale price cache for {ticker}")
            return cached[1]
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


import requests_cache

class _CachedSession(requests_cache.CachedSession):
    def request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", 10)
        return super().request(method, url, **kwargs)

_yf_session = _CachedSession(
    cache_name="/app/data/yf_cache",
    backend="sqlite",
    urls_expire_after={
        "*crumb*": requests_cache.DO_NOT_CACHE,  # crumb 不快取（每次需要新的）
        "*/v10/finance/quoteSummary/*": 3600,    # info: 1 小時
        "*/v8/finance/chart/*": 120,             # chart/price: 2 分鐘
        "*": 300,                                # 其他: 5 分鐘
    },
    allowable_codes=[200],
)


@router.get("/{ticker}/info")
def get_info(ticker: str, _: str = Depends(get_current_user)):
    cached = _info_cache.get(ticker)
    if cached and time.time() - cached[0] < INFO_TTL:
        return cached[1]
    try:
        info = _run(lambda: yf.Ticker(ticker, session=_yf_session).info)
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
        _info_cache[ticker] = (time.time(), data)
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch info for {ticker}: {e}")
        if cached:
            logger.warning(f"Returning stale info cache for {ticker}")
            return cached[1]
        raise HTTPException(status_code=502, detail="Failed to fetch stock info")


@router.get("/{ticker}/chart")
def get_chart(
    ticker: str,
    period: str = Query(default="3mo"),
    _: str = Depends(get_current_user),
):
    if period not in VALID_PERIODS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid period. Must be one of: {', '.join(sorted(VALID_PERIODS))}",
        )
    try:
        df = _run(lambda: yf.Ticker(ticker, session=_yf_session).history(period=period))
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
    if period not in VALID_PERIODS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid period. Must be one of: {', '.join(sorted(VALID_PERIODS))}",
        )
    try:
        def _fetch_profile():
            tk = yf.Ticker(ticker, session=_yf_session)
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
