from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import logging
import os
import json
import urllib.parse
import urllib.request
import requests
from backend.app.services.sentiment_service import SentimentAnalysisService

router = APIRouter(prefix="/api/v1/news", tags=["news"])

FINNHUB_BASE_URL = "https://finnhub.io/api/v1"
NEWSAPI_BASE_URL = "https://newsapi.org/v2"
ALPHAVANTAGE_BASE_URL = "https://www.alphavantage.co"
GNEWS_BASE_URL = "https://gnews.io/api/v4"

logger = logging.getLogger(__name__)

def _get_demo_news(symbol: Optional[str]):
    now = datetime.now(timezone.utc)
    label = "Sample News (Demo Mode)"
    base = symbol or "Market"

    return [
        {
            "title": f"{base}: Investor sentiment briefing",
            "summary": f"This is demo news shown because real-time data is temporarily unavailable for {base}.",
            "source": label,
            "published_at": now.isoformat(),
        },
        {
            "title": f"{base}: Analysts share market commentary",
            "summary": "Analyst commentary provides additional context. Demo content for review.",
            "source": label,
            "published_at": (now - timedelta(hours=2)).isoformat(),
        },
        {
            "title": f"{base}: AI models signal neutral outlook",
            "summary": "Machine learning models indicate a neutral outlook. Demo placeholder.",
            "source": label,
            "published_at": (now - timedelta(hours=5)).isoformat(),
        },
    ]

def _http_get_json(url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw)

def _parse_rfc3339_utc(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def _finnhub_get_json(path: str, params: Dict[str, Any]) -> Optional[Any]:
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

def _parse_alphavantage_time_published(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    try:
        # AlphaVantage format: YYYYMMDDTHHMMSS (no timezone)
        dt = datetime.strptime(s, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        try:
            # Sometimes: YYYYMMDDTHHMM
            dt = datetime.strptime(s, "%Y%m%dT%H%M").replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

def _gnews_get_articles(query: str, limit: int) -> Optional[List[Dict[str, Any]]]:
    url = GNEWS_BASE_URL + "/search"
    params: Dict[str, Any] = {
        "q": query,
        "lang": "en",
        "max": max(1, min(int(limit), 100)),
        "token": os.getenv("GNEWS_API_KEY"),
    }

    if not params["token"]:
        logger.warning("GNEWS_API_KEY not set")
        return None

    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        if resp.status_code != 200 or not data.get("articles"):
            logger.warning(f"GNews returned no data: {data}")
            return None

        return data["articles"]
    except Exception as e:
        logger.error(f"GNews fetch failed: {e}")
        return None

def _newsapi_get_json(path: str, params: Dict[str, Any]) -> Optional[Any]:
    api_key = os.getenv("NEWSAPI_API_KEY") or os.getenv("NEWSAPI_KEY")
    if not api_key:
        return None

    q = dict(params)
    q["apiKey"] = api_key
    url = NEWSAPI_BASE_URL + path + "?" + urllib.parse.urlencode(q)
    try:
        return _http_get_json(url, headers={"User-Agent": "Mozilla/5.0"})
    except Exception:
        logger.exception("NewsAPI request failed")
        return None

def _format_finnhub_news_items(items: List[Dict[str, Any]], symbol: str, limit: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    sym = symbol.strip().upper()
    for item in (items or [])[: max(0, limit)]:
        title = (item.get("headline") or "").strip()
        summary = (item.get("summary") or "").strip()
        source = (item.get("source") or "").strip() or "Finnhub"
        url = (item.get("url") or "").strip()
        ts = item.get("datetime")
        if ts is None:
            continue
        try:
            published_at = datetime.fromtimestamp(int(ts), tz=timezone.utc)
        except Exception:
            continue

        if not title:
            continue

        out.append(
            {
                "id": hash(f"{sym}_{title}_{published_at}") % 1000000,
                "title": title,
                "summary": summary,
                "content": summary,
                "source": source,
                "author": source,
                "url": url,
                "published_at": published_at,
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "relevance_score": 0.6,
                "tags": [sym.lower(), "news"],
            }
        )
    return out

def _format_gnews_articles(articles: List[Dict[str, Any]], symbol: str, limit: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    sym = symbol.strip().upper()
    for a in (articles or [])[: max(0, limit)]:
        title = (a.get("title") or "").strip()
        if not title:
            continue
        summary = (a.get("description") or "").strip()
        url = (a.get("url") or "").strip()
        source_obj = a.get("source") if isinstance(a.get("source"), dict) else {}
        source = (source_obj.get("name") or "").strip() or "GNews"
        published_at = _parse_rfc3339_utc(a.get("publishedAt"))
        if not published_at:
            continue
        out.append(
            {
                "id": hash(f"{sym}_{title}_{published_at}") % 1000000,
                "title": title,
                "summary": summary,
                "content": summary,
                "source": source,
                "author": source,
                "url": url,
                "published_at": published_at,
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "relevance_score": 0.6,
                "tags": [sym.lower(), "news"],
            }
        )
    return out

def _format_alphavantage_feed(feed: List[Dict[str, Any]], symbol: str, limit: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    sym = symbol.strip().upper()
    for item in (feed or [])[: max(0, limit)]:
        title = (item.get("title") or "").strip()
        summary = (item.get("summary") or "").strip()
        url = (item.get("url") or "").strip()
        source = (item.get("source") or "").strip() or "Alpha Vantage"
        published_at = _parse_alphavantage_time_published(item.get("time_published"))
        if not title or not published_at:
            continue
        out.append(
            {
                "id": hash(f"{sym}_{title}_{published_at}") % 1000000,
                "title": title,
                "summary": summary,
                "content": summary,
                "source": source,
                "author": source,
                "url": url,
                "published_at": published_at,
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "relevance_score": 0.6,
                "tags": [sym.lower(), "news"],
            }
        )
    return out

def _format_newsapi_articles(articles: List[Dict[str, Any]], symbol: str, limit: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    sym = symbol.strip().upper()
    for a in (articles or [])[: max(0, limit)]:
        title = (a.get("title") or "").strip()
        summary = (a.get("description") or a.get("content") or "").strip()
        source_obj = a.get("source") if isinstance(a.get("source"), dict) else {}
        source = (source_obj.get("name") or "").strip() or "NewsAPI"
        url = (a.get("url") or "").strip()
        published_at = _parse_rfc3339_utc(a.get("publishedAt"))
        if not title or not published_at:
            continue
        out.append(
            {
                "id": hash(f"{sym}_{title}_{published_at}") % 1000000,
                "title": title,
                "summary": summary,
                "content": summary,
                "source": source,
                "author": source,
                "url": url,
                "published_at": published_at,
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "relevance_score": 0.6,
                "tags": [sym.lower(), "news"],
            }
        )
    return out

def _get_company_name(symbol: str) -> Optional[str]:
    sym = symbol.strip().upper()
    profile = _finnhub_get_json("/stock/profile2", {"symbol": sym})
    if not isinstance(profile, dict):
        return None
    name = (profile.get("name") or "").strip()
    return name or None

def _filter_market_news(items: List[Dict[str, Any]], symbol: str, company_name: Optional[str]) -> List[Dict[str, Any]]:
    sym = symbol.strip().upper()
    sym_l = sym.lower()
    name_l = (company_name or "").strip().lower()
    filtered: List[Dict[str, Any]] = []
    for item in items or []:
        headline = (item.get("headline") or "").strip()
        summary = (item.get("summary") or "").strip()
        haystack = f"{headline} {summary}".lower()
        if sym_l and sym_l in haystack:
            filtered.append(item)
            continue
        if name_l and name_l in haystack:
            filtered.append(item)
            continue
    return filtered

def fetch_stock_news(symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Compatibility wrapper that returns articles only (provider metadata handled in endpoints)."""
    articles, _, _ = fetch_stock_news_with_provider(symbol, limit)
    return articles

def fetch_stock_news_with_provider(symbol: str, limit: int = 10) -> tuple[List[Dict[str, Any]], str, bool]:
    sym = symbol.strip().upper()

    # 1) Finnhub company news
    end_dt = datetime.utcnow()
    start_dt = end_dt - timedelta(days=7)
    finnhub_items = _finnhub_get_json(
        "/company-news",
        {
            "symbol": sym,
            "from": start_dt.strftime("%Y-%m-%d"),
            "to": end_dt.strftime("%Y-%m-%d"),
        },
    )
    if isinstance(finnhub_items, list) and len(finnhub_items) > 0:
        logger.info("News provider used: Finnhub")
        return _format_finnhub_news_items(finnhub_items, sym, limit), "Finnhub", False

    # 2) Finnhub market news filtered
    market_items = _finnhub_get_json("/news", {"category": "general"})
    if isinstance(market_items, list) and len(market_items) > 0:
        company_name = _get_company_name(sym)
        filtered_market = _filter_market_news(market_items, sym, company_name)
        if filtered_market:
            logger.info("News provider used: Finnhub")
            return _format_finnhub_news_items(filtered_market, sym, limit), "Finnhub", False

    # 3) NewsAPI
    newsapi_result = _newsapi_get_json(
        "/everything",
        {
            "q": sym,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": max(1, min(int(limit), 100)),
        },
    )
    if isinstance(newsapi_result, dict) and isinstance(newsapi_result.get("articles"), list):
        articles = _format_newsapi_articles(newsapi_result.get("articles") or [], sym, limit)
        if articles:
            logger.info("News provider used: NewsAPI")
            return articles, "NewsAPI", False

    # 4) GNews
    gnews_articles = _gnews_get_articles(sym, limit)
    if isinstance(gnews_articles, list) and gnews_articles:
        articles = _format_gnews_articles(gnews_articles, sym, limit)
        if articles:
            logger.info("News provider used: GNews")
            return articles, "GNews", False

    # 5) Demo
    return _get_demo_news(sym), "Demo", True

def analyze_sentiment(text: str) -> tuple[str, float]:
    """
    Simple sentiment analysis based on keywords.
    
    DEPRECATED: Use SentimentAnalysisService for more accurate analysis.
    This function is kept for backward compatibility.
    """
    positive_words = ["up", "rise", "gain", "strong", "beat", "growth", "bull", "buy", "positive", "rally", "exceeds"]
    negative_words = ["down", "fall", "loss", "weak", "miss", "decline", "bear", "sell", "negative", "volatility", "concerns"]
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        return "positive", 0.7
    elif negative_count > positive_count:
        return "negative", -0.5
    else:
        return "neutral", 0.0

# Initialize the AI sentiment analysis service
sentiment_service = SentimentAnalysisService()

@router.get("/{symbol}")
async def get_stock_news(symbol: str, limit: int = 10) -> Dict[str, Any]:
    """Get news for a specific stock"""
    sym = symbol.strip().upper()
    try:
        news_items, provider, demo_mode = fetch_stock_news_with_provider(sym, limit)
    except Exception:
        news_items, provider, demo_mode = _get_demo_news(sym), "Demo", True

    # Analyze sentiment for each news item using AI sentiment analysis
    for item in news_items:
        full_text = f"{item.get('title', '')}. {item.get('summary', '')}"

        try:
            sentiment_result = sentiment_service.analyze_sentiment(full_text)
            item["sentiment"] = sentiment_result.sentiment
            item["sentiment_score"] = sentiment_result.score
            item["sentiment_confidence"] = sentiment_result.confidence
            item["sentiment_explanation"] = sentiment_result.explanation
            item["sentiment_evidence"] = sentiment_result.evidence
        except Exception:
            sentiment, score = analyze_sentiment(full_text)
            item["sentiment"] = sentiment
            item["sentiment_score"] = score
            item["sentiment_confidence"] = 0.5
            item["sentiment_explanation"] = f"Simple keyword analysis: {sentiment}"
            item["sentiment_evidence"] = []

    if news_items:
        avg_sentiment = sum(float(item.get("sentiment_score", 0.0)) for item in news_items) / len(news_items)
        overall_sentiment = "positive" if avg_sentiment > 0.1 else ("negative" if avg_sentiment < -0.1 else "neutral")
    else:
        avg_sentiment = 0.0
        overall_sentiment = "neutral"

    return {
        "status": "success",
        "demo_mode": demo_mode,
        "provider": provider,
        "symbol": sym,
        "articles": news_items,
        "summary": {
            "total_articles": len(news_items),
            "overall_sentiment": overall_sentiment,
            "average_sentiment_score": round(avg_sentiment, 3),
            "sentiment_distribution": {
                "positive": sum(1 for item in news_items if item.get("sentiment") == "positive"),
                "negative": sum(1 for item in news_items if item.get("sentiment") == "negative"),
                "neutral": sum(1 for item in news_items if item.get("sentiment") == "neutral"),
            },
        },
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

@router.get("/market/latest")
async def get_latest_market_news(limit: int = 20) -> Dict[str, Any]:
    """Get latest market news"""
    articles: List[Dict[str, Any]] = []
    provider = ""
    demo_mode = False

    # 1) Finnhub market news
    finnhub_items = _finnhub_get_json("/news", {"category": "general"})
    if isinstance(finnhub_items, list) and len(finnhub_items) > 0:
        articles = _format_finnhub_news_items(finnhub_items, "MARKET", limit)
        if articles:
            provider = "Finnhub"
            logger.info("News provider used: Finnhub")

    # 2) NewsAPI
    if not articles:
        newsapi_items = _newsapi_get_json(
            "/top-headlines",
            {
                "category": "business",
                "country": "us",
                "language": "en",
                "pageSize": max(1, min(int(limit), 100)),
            },
        )
        if (
            isinstance(newsapi_items, dict)
            and newsapi_items.get("status") == "ok"
            and isinstance(newsapi_items.get("articles"), list)
        ):
            articles = _format_newsapi_articles(newsapi_items.get("articles") or [], "MARKET", limit)
            if articles:
                provider = "NewsAPI"
                logger.info("News provider used: NewsAPI")

    # 3) GNews
    if not articles:
        gnews_articles = _gnews_get_articles("stock market", limit)
        if isinstance(gnews_articles, list) and gnews_articles:
            articles = _format_gnews_articles(gnews_articles, "MARKET", limit)
            if articles:
                provider = "GNews"
                logger.info("News provider used: GNews")

    # 4) Demo
    if not articles:
        articles = _get_demo_news(None)
        provider = "Demo"
        demo_mode = True
        logger.info("News provider used: Demo")

    return {
        "status": "success",
        "demo_mode": demo_mode,
        "provider": provider,
        "articles": articles,
        "total": len(articles),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "source": provider.lower() if provider else "",
    }

@router.get("/{symbol}/sentiment")
async def get_stock_sentiment(symbol: str) -> Dict[str, Any]:
    """
    Get comprehensive sentiment analysis for a specific stock.
    
    Uses AI-based sentiment analysis on multiple news articles to provide:
    - Overall sentiment classification (Positive/Neutral/Negative)
    - Sentiment score (-1.0 to 1.0)
    - Confidence score (0.0 to 1.0)
    - Detailed explanation of the analysis
    - Evidence from news articles
    """
    try:
        # Get news articles for sentiment analysis
        news_items = fetch_stock_news(symbol, 20)
        
        if not news_items:
            return {
                "status": "success",
                "symbol": symbol.upper(),
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "analysis": "Insufficient news data for sentiment analysis",
                "explanation": "No news articles found for this stock",
                "evidence": [],
                "articles_analyzed": 0,
                "updated_at": datetime.now().isoformat()
            }
        
        # Extract text content from news articles
        news_texts = []
        for item in news_items:
            full_text = f"{item['title']}. {item['summary']}"
            news_texts.append(full_text)
        
        # Use AI sentiment analysis service for comprehensive analysis
        try:
            analysis_result = sentiment_service.analyze_multiple_texts(news_texts)
            
            return {
                "status": "success",
                "symbol": symbol.upper(),
                "sentiment": analysis_result["overall_sentiment"],
                "sentiment_score": analysis_result["average_score"],
                "confidence": analysis_result["confidence"],
                "analysis": f"Based on {analysis_result['total_analyzed']} news articles",
                "explanation": f"Found {analysis_result['sentiment_distribution']['positive']} positive, {analysis_result['sentiment_distribution']['negative']} negative, and {analysis_result['sentiment_distribution']['neutral']} neutral indicators",
                "evidence": [result["explanation"] for result in analysis_result["individual_results"][:5]],
                "articles_analyzed": analysis_result["total_analyzed"],
                "sentiment_distribution": analysis_result["sentiment_distribution"],
                "individual_results": analysis_result["individual_results"],
                "updated_at": datetime.now().isoformat()
            }
        except Exception as e:
            # Fallback to simple sentiment analysis if AI service fails
            sentiment_scores = []
            for item in news_items:
                full_text = f"{item['title']}. {item['summary']}"
                sentiment, score = analyze_sentiment(full_text)
                sentiment_scores.append(score)
            
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
            sentiment = "positive" if avg_sentiment > 0.1 else ("negative" if avg_sentiment < -0.1 else "neutral")
            confidence = min(abs(avg_sentiment) * 2, 1.0)
            
            return {
                "status": "success",
                "symbol": symbol.upper(),
                "sentiment": sentiment,
                "sentiment_score": round(avg_sentiment, 3),
                "confidence": round(confidence, 3),
                "analysis": f"Simple keyword analysis of {len(news_items)} news articles",
                "explanation": f"Average sentiment score: {avg_sentiment:.3f} based on keyword analysis",
                "evidence": [f"Article {i+1}: {analyze_sentiment(news_items[i]['title'] + '. ' + news_items[i]['summary'])[0]}" for i in range(min(5, len(news_items)))],
                "articles_analyzed": len(news_items),
                "updated_at": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "status": "success",
            "symbol": symbol.upper(),
            "sentiment": "neutral",
            "sentiment_score": 0.0,
            "confidence": 0.0,
            "analysis": "Sentiment temporarily unavailable",
            "explanation": "Sentiment analysis service is unavailable or rate-limited",
            "evidence": [],
            "articles_analyzed": 0,
            "updated_at": datetime.now().isoformat(),
        }
