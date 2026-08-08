import logging
from typing import Literal

import yfinance as yf
from fastapi import APIRouter, Depends, HTTPException, Query

from auth import get_current_user
from stock_data import search_stocks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/stocks", tags=["stocks"])

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
    try:
        info = yf.Ticker(ticker).fast_info
        price = info.last_price
        prev_close = info.previous_close
        change_percent = ((price - prev_close) / prev_close * 100) if prev_close else 0
        return {
            "ticker": ticker,
            "price": round(price, 2),
            "change_percent": round(change_percent, 2),
        }
    except Exception as e:
        logger.error(f"Failed to fetch price for {ticker}: {e}")
        raise HTTPException(status_code=502, detail="Failed to fetch stock price")


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
        df = yf.Ticker(ticker).history(period=period)
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
        tk = yf.Ticker(ticker)
        df = tk.history(period=period)
        if df.empty:
            return []

        current_price = tk.fast_info.last_price
        min_price = float(df["Low"].min())
        max_price = float(df["High"].max())
        num_buckets = 40
        bucket_size = (max_price - min_price) / num_buckets

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
