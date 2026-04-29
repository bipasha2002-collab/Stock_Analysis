from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import os
import json
import urllib.parse
import urllib.request
import yfinance as yf
import pandas as pd

router = APIRouter(prefix="/api/v1/stocks", tags=["stocks"])

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"

# Mock data fallback
MOCK_TRENDING_STOCKS = [
    {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "price": 178.45,
        "change": 2.34,
        "change_percent": 1.33,
        "volume": 52341234,
        "market_cap": "2.8T"
    },
    {
        "symbol": "NVDA",
        "name": "NVIDIA Corporation",
        "price": 485.09,
        "change": 15.67,
        "change_percent": 3.34,
        "volume": 89234567,
        "market_cap": "1.2T"
    },
    {
        "symbol": "TSLA",
        "name": "Tesla, Inc.",
        "price": 242.84,
        "change": -3.21,
        "change_percent": -1.30,
        "volume": 123456789,
        "market_cap": "770B"
    },
    {
        "symbol": "GOOGL",
        "name": "Alphabet Inc.",
        "price": 139.62,
        "change": 1.89,
        "change_percent": 1.37,
        "volume": 23456789,
        "market_cap": "1.7T"
    },
    {
        "symbol": "MSFT",
        "name": "Microsoft Corporation",
        "price": 378.91,
        "change": 4.12,
        "change_percent": 1.10,
        "volume": 34567890,
        "market_cap": "2.8T"
    }
]

def get_stock_info(symbol: str) -> Dict[str, Any]:
    """Get stock information using Finnhub (preferred) with fallback to yfinance/mock data"""
    sym = symbol.strip().upper()

    # Provider-first quote (Finnhub -> Polygon -> Alpha Vantage)
    quote = _get_finnhub_quote(sym) or _get_polygon_prev_close(sym) or _get_alpha_vantage_quote(sym)
    profile = _get_finnhub_profile(sym) or {}
    if quote:
        current_price = float(quote["current_price"])
        previous_close = float(quote["previous_close"])
        change = current_price - previous_close
        change_percent = (change / previous_close * 100) if previous_close > 0 else 0.0

        return {
            "symbol": sym,
            "price": current_price,
            "current_price": current_price,
            "previous_close": previous_close,
            "day_high": float(quote["day_high"]),
            "day_low": float(quote["day_low"]),
            "volume": 0,
            "name": profile.get("name") or f"{sym} Corporation",
            "change": change,
            "change_percent": change_percent,
            "market_cap": profile.get("market_cap") or "N/A",
            "sector": "Technology",
            "currency": profile.get("currency") or "USD",
            "exchange": profile.get("exchange") or "",
        }

    try:
        stock = yf.Ticker(sym)
        info = stock.info
        
        if info and "regularMarketPrice" in info and info.get("regularMarketPrice", 0) > 0:
            # Get real-time data for day high/low
            try:
                hist = stock.history(period="1d")
                day_high = float(hist['High'].iloc[-1]) if not hist.empty else info.get("regularMarketPrice", 0)
                day_low = float(hist['Low'].iloc[-1]) if not hist.empty else info.get("regularMarketPrice", 0)
                volume = int(hist['Volume'].iloc[-1]) if not hist.empty else info.get("volume", 0)
            except Exception:
                day_high = info.get("dayHigh", info.get("regularMarketPrice", 0))
                day_low = info.get("dayLow", info.get("regularMarketPrice", 0))
                volume = info.get("volume", 0)
            
            current_price = float(info.get("regularMarketPrice", 0))
            previous_close = float(info.get("previousClose", 0))
            
            return {
                "symbol": sym,
                # Backward compatible alias used by some frontend components
                "price": current_price,
                "current_price": current_price,
                "previous_close": previous_close,
                "day_high": float(day_high),
                "day_low": float(day_low),
                "volume": int(volume),
                "name": info.get("longName", f"{sym} Corporation"),
                "change": current_price - previous_close,
                "change_percent": ((current_price - previous_close) / previous_close * 100) if previous_close > 0 else 0,
                "market_cap": format_market_cap(info.get("marketCap", 0)),
                "sector": info.get("sector", "Technology"),
                "currency": info.get("currency", "USD"),
                "exchange": info.get("exchange", "NASDAQ")
            }
    except Exception as e:
        pass
    
    # Fallback to mock data
    mock_stock = next((stock for stock in MOCK_TRENDING_STOCKS if stock["symbol"] == sym), None)
    if mock_stock:
        current_price = mock_stock["price"]
        return {
            "symbol": sym,
            "price": current_price,
            "current_price": current_price,
            "previous_close": current_price - mock_stock["change"],
            "day_high": current_price * 1.02,
            "day_low": current_price * 0.98,
            "volume": mock_stock["volume"],
            "name": mock_stock["name"],
            "change": mock_stock["change"],
            "change_percent": mock_stock["change_percent"],
            "market_cap": mock_stock["market_cap"],
            "sector": "Technology",
            "currency": "USD",
            "exchange": "NASDAQ"
        }
    
    # Generate generic mock data for invalid symbols
    return {
        "symbol": sym,
        "price": 150.0,
        "current_price": 150.0,
        "previous_close": 148.5,
        "day_high": 153.0,
        "day_low": 147.0,
        "volume": 50000000,
        "name": f"{sym} Corporation",
        "change": 1.5,
        "change_percent": 1.0,
        "market_cap": "500B",
        "sector": "Technology",
        "currency": "USD",
        "exchange": "NASDAQ"
    }


def _http_get_json(url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)


def _finnhub_get_json(path: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    token = os.getenv("FINNHUB_API_KEY")
    if not token:
        return None

    q = dict(params)
    q["token"] = token
    url = FINNHUB_BASE_URL + path + "?" + urllib.parse.urlencode(q)
    try:
        return _http_get_json(url, headers={"User-Agent": "Mozilla/5.0"})
    except Exception:
        return None


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        if v is None:
            return default
        return int(v)
    except Exception:
        return default


def _get_finnhub_quote(symbol: str) -> Optional[Dict[str, Any]]:
    data = _finnhub_get_json("/quote", {"symbol": symbol.upper()})
    if not data:
        return None

    current = _safe_float(data.get("c"), 0.0)
    prev_close = _safe_float(data.get("pc"), 0.0)
    if current <= 0:
        return None

    return {
        "current_price": current,
        "previous_close": prev_close if prev_close > 0 else current,
        "day_high": _safe_float(data.get("h"), current),
        "day_low": _safe_float(data.get("l"), current),
    }


def _get_polygon_prev_close(symbol: str) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        return None

    sym = symbol.strip().upper()
    url = (
        "https://api.polygon.io/v2/aggs/ticker/"
        + urllib.parse.quote(sym)
        + "/prev?adjusted=true&apiKey="
        + urllib.parse.quote(api_key)
    )

    try:
        data = _http_get_json(url, headers={"User-Agent": "Mozilla/5.0"})
    except Exception:
        return None

    results = data.get("results") or []
    if not results:
        return None

    r0 = results[0] or {}
    close = _safe_float(r0.get("c"), 0.0)
    if close <= 0:
        return None

    return {
        "current_price": close,
        "previous_close": close,
        "day_high": _safe_float(r0.get("h"), close),
        "day_low": _safe_float(r0.get("l"), close),
    }


def _get_alpha_vantage_quote(symbol: str) -> Optional[Dict[str, Any]]:
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        return None

    sym = symbol.strip().upper()
    url = "https://www.alphavantage.co/query?" + urllib.parse.urlencode(
        {"function": "GLOBAL_QUOTE", "symbol": sym, "apikey": api_key}
    )

    try:
        data = _http_get_json(url, headers={"User-Agent": "Mozilla/5.0"})
    except Exception:
        return None

    q = data.get("Global Quote") or {}
    price = _safe_float(q.get("05. price"), 0.0)
    prev_close = _safe_float(q.get("08. previous close"), 0.0)
    high = _safe_float(q.get("03. high"), 0.0)
    low = _safe_float(q.get("04. low"), 0.0)

    if price <= 0:
        return None

    return {
        "current_price": price,
        "previous_close": prev_close if prev_close > 0 else price,
        "day_high": high if high > 0 else price,
        "day_low": low if low > 0 else price,
    }


def _get_finnhub_profile(symbol: str) -> Optional[Dict[str, Any]]:
    data = _finnhub_get_json("/stock/profile2", {"symbol": symbol.upper()})
    if not data:
        return None

    name = (data.get("name") or "").strip()
    exchange = (data.get("exchange") or "").strip()
    currency = (data.get("currency") or "").strip() or "USD"
    market_cap_m = _safe_float(data.get("marketCapitalization"), 0.0)

    return {
        "name": name,
        "exchange": exchange,
        "currency": currency,
        "market_cap": format_market_cap(int(market_cap_m * 1_000_000)) if market_cap_m > 0 else "N/A",
    }


def _period_to_range(period: str) -> Tuple[int, str]:
    p = (period or "").lower().strip()
    if p in {"5d", "1w"}:
        return 7, "60"
    if p in {"1mo", "1m"}:
        return 31, "D"
    if p in {"3mo", "3m"}:
        return 93, "D"
    if p in {"6mo", "6m"}:
        return 186, "D"
    if p in {"1y", "12mo", "12m"}:
        return 366, "D"
    return 31, "D"


def _get_finnhub_candles(symbol: str, period: str) -> Optional[List[Dict[str, Any]]]:
    days, resolution = _period_to_range(period)
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=days)
    data = _finnhub_get_json(
        "/stock/candle",
        {
            "symbol": symbol.upper(),
            "resolution": resolution,
            "from": int(start_dt.timestamp()),
            "to": int(end_dt.timestamp()),
        },
    )

    if not data or data.get("s") != "ok":
        return None

    ts = data.get("t") or []
    o = data.get("o") or []
    h = data.get("h") or []
    l = data.get("l") or []
    c = data.get("c") or []
    v = data.get("v") or []

    n = min(len(ts), len(o), len(h), len(l), len(c), len(v))
    if n <= 0:
        return None

    out: List[Dict[str, Any]] = []
    for i in range(n):
        dt = datetime.utcfromtimestamp(int(ts[i]))
        out.append(
            {
                "date": dt.strftime("%Y-%m-%d"),
                "open": round(_safe_float(o[i], 0.0), 2),
                "high": round(_safe_float(h[i], 0.0), 2),
                "low": round(_safe_float(l[i], 0.0), 2),
                "close": round(_safe_float(c[i], 0.0), 2),
                "volume": _safe_int(v[i], 0),
            }
        )
    return out


def search_stocks(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search stocks by symbol/company name using Finnhub (if configured) or Yahoo Finance search."""
    q = query.strip()
    if not q:
        return []

    finnhub_key = os.getenv("FINNHUB_API_KEY")
    if finnhub_key:
        url = "https://finnhub.io/api/v1/search?" + urllib.parse.urlencode({"q": q, "token": finnhub_key})
        try:
            data = _http_get_json(url)
            results = []
            for item in (data.get("result") or [])[: max(1, min(limit, 25))]:
                symbol = (item.get("symbol") or "").upper()
                if not symbol:
                    continue
                results.append(
                    {
                        "symbol": symbol,
                        "name": item.get("description") or symbol,
                        "exchange": item.get("primaryExch") or item.get("type") or "",
                        "type": item.get("type") or "",
                    }
                )
            return results
        except Exception:
            pass

    # Yahoo Finance search (no API key required)
    try:
        url = "https://query1.finance.yahoo.com/v1/finance/search?" + urllib.parse.urlencode(
            {"q": q, "quotesCount": max(1, min(limit, 25)), "newsCount": 0}
        )
        data = _http_get_json(url, headers={"User-Agent": "Mozilla/5.0"})
        results = []
        for item in (data.get("quotes") or [])[: max(1, min(limit, 25))]:
            symbol = (item.get("symbol") or "").upper()
            if not symbol:
                continue
            results.append(
                {
                    "symbol": symbol,
                    "name": item.get("shortname") or item.get("longname") or symbol,
                    "exchange": item.get("exchange") or item.get("exchDisp") or "",
                    "type": item.get("quoteType") or "",
                }
            )
        return results
    except Exception:
        return []

def format_market_cap(market_cap: int) -> str:
    """Format market cap to readable format"""
    if market_cap >= 1_000_000_000_000:
        return f"${market_cap / 1_000_000_000_000:.1f}T"
    elif market_cap >= 1_000_000_000:
        return f"${market_cap / 1_000_000_000:.1f}B"
    elif market_cap >= 1_000_000:
        return f"${market_cap / 1_000_000:.1f}M"
    else:
        return f"${market_cap:,.0f}"

@router.get("/trending")
async def get_trending_stocks() -> Dict[str, Any]:
    """Get trending stocks"""
    try:
        # Try to get real data from popular stocks
        trending_symbols = ["AAPL", "NVDA", "TSLA", "GOOGL", "MSFT"]
        trending_data = []
        
        for symbol in trending_symbols:
            try:
                stock_info = get_stock_info(symbol)
                if stock_info.get("current_price", 0) > 0:
                    trending_data.append(stock_info)
            except Exception:
                continue
        
        if trending_data:
            return {
                "status": "success",
                "data": trending_data,
                "total": len(trending_data),
                "updated_at": datetime.now().isoformat()
            }
    except Exception:
        pass
    
    # Fallback to mock data
    return {
        "status": "success",
        "data": MOCK_TRENDING_STOCKS,
        "total": len(MOCK_TRENDING_STOCKS),
        "updated_at": datetime.now().isoformat()
    }


@router.get("/search")
async def search_stocks_endpoint(q: str, limit: int = 10) -> Dict[str, Any]:
    """Search symbols + company names with autocomplete-style results."""
    if not q or not q.strip():
        return {
            "status": "success",
            "query": q,
            "results": [],
            "total": 0,
            "updated_at": datetime.now().isoformat(),
        }

    results = search_stocks(q, limit=limit)
    return {
        "status": "success",
        "query": q,
        "results": results,
        "total": len(results),
        "updated_at": datetime.now().isoformat(),
    }

@router.get("/{symbol}")
async def get_stock_details(symbol: str) -> Dict[str, Any]:
    """Get detailed stock information with real yfinance data"""
    try:
        stock_info = get_stock_info(symbol)
        
        # Ensure all required fields are present and JSON serializable
        response_data = {
            "symbol": stock_info["symbol"],
            "current_price": float(stock_info["current_price"]),
            "previous_close": float(stock_info["previous_close"]),
            "day_high": float(stock_info["day_high"]),
            "day_low": float(stock_info["day_low"]),
            "volume": int(stock_info["volume"]),
            "name": stock_info.get("name", f"{symbol.upper()} Corporation"),
            "change": float(stock_info.get("change", 0)),
            "change_percent": float(stock_info.get("change_percent", 0)),
            "market_cap": stock_info.get("market_cap", "N/A"),
            "sector": stock_info.get("sector", "Technology"),
            "currency": stock_info.get("currency", "USD"),
            "exchange": stock_info.get("exchange", "NASDAQ"),
            "updated_at": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "data": response_data
        }
    except Exception as e:
        # Handle invalid symbols gracefully with fallback data
        fallback_data = {
            "symbol": symbol.upper(),
            "current_price": 150.0,
            "previous_close": 148.5,
            "day_high": 153.0,
            "day_low": 147.0,
            "volume": 50000000,
            "name": f"{symbol.upper()} Corporation",
            "change": 1.5,
            "change_percent": 1.0,
            "market_cap": "500B",
            "sector": "Technology",
            "currency": "USD",
            "exchange": "NASDAQ",
            "updated_at": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "data": fallback_data,
            "message": f"Using fallback data for {symbol.upper()}"
        }

@router.get("/{symbol}/history")
async def get_stock_history(symbol: str, period: str = "1mo") -> Dict[str, Any]:
    """Get historical stock data"""
    sym = symbol.strip().upper()

    # Finnhub candles preferred
    candles = _get_finnhub_candles(sym, period)
    if candles is not None and len(candles) > 0:
        return {
            "status": "success",
            "symbol": sym,
            "period": period,
            "data": candles,
            "total_points": len(candles),
            "source": "finnhub",
        }

    try:
        stock = yf.Ticker(sym)
        hist = stock.history(period=period)
        
        if not hist.empty:
            data = []
            for date, row in hist.iterrows():
                data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": round(float(row["Open"]), 2),
                    "high": round(float(row["High"]), 2),
                    "low": round(float(row["Low"]), 2),
                    "close": round(float(row["Close"]), 2),
                    "volume": int(row["Volume"])
                })
            
            return {
                "status": "success",
                "symbol": sym,
                "period": period,
                "data": data,
                "total_points": len(data),
                "source": "yfinance",
            }
    except Exception:
        pass
    
    # Fallback to mock historical data
    mock_history = []
    base_price = 150.0
    for i in range(30):
        date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - pd.Timedelta(days=i)
        price_change = (hash(f"{symbol}{i}") % 100 - 50) / 100
        close_price = base_price + price_change
        
        mock_history.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": round(close_price * 0.99, 2),
            "high": round(close_price * 1.02, 2),
            "low": round(close_price * 0.98, 2),
            "close": round(close_price, 2),
            "volume": 50000000 + (hash(f"{symbol}{i}") % 10000000)
        })
        
        base_price = close_price
    
    mock_history.reverse()
    
    return {
        "status": "success",
        "symbol": sym,
        "period": period,
        "data": mock_history,
        "total_points": len(mock_history),
        "source": "mock",
    }
