"""
Trend prediction API endpoints.

This module provides REST endpoints for trend-based stock recommendations
using technical analysis. The predictions are explainable and follow standard
technical analysis principles suitable for interviews/viva explanations.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from backend.app.services.trend_prediction_service import TrendPredictionService, Recommendation

router = APIRouter(prefix="/api/v1/trends", tags=["trends"])

# Initialize the trend prediction service
trend_service = TrendPredictionService()

class TrendRequest(BaseModel):
    """Request model for trend prediction"""
    symbol: str
    days: Optional[int] = 30  # Number of days of historical data to use

class TrendResponse(BaseModel):
    """Response model for trend prediction"""
    status: str
    symbol: str
    recommendation: str  # BUY, HOLD, SELL
    confidence: float    # 0.0 to 1.0
    reasoning: str
    signals: List[Dict[str, Any]]
    technical_summary: Dict[str, Any]
    risk_level: str
    prediction_date: str

class BatchTrendRequest(BaseModel):
    """Request model for batch trend predictions"""
    symbols: List[str]
    days: Optional[int] = 30

class BatchTrendResponse(BaseModel):
    """Response model for batch trend predictions"""
    status: str
    predictions: List[Dict[str, Any]]
    summary: Dict[str, Any]
    processed_at: str

def get_historical_data_for_symbol(symbol: str, days: int = 30) -> List[Dict[str, Any]]:
    """
    Get historical data for a symbol using yfinance or mock data.
    
    This is a helper function to fetch historical data for trend analysis.
    In a production environment, this would connect to a proper data source.
    """
    try:
        import yfinance as yf
        import pandas as pd
        from datetime import datetime, timedelta
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Fetch data from yfinance
        stock = yf.Ticker(symbol.upper())
        hist = stock.history(start=start_date, end=end_date)
        
        if hist.empty:
            return generate_mock_historical_data(symbol, days)
        
        # Convert to list of dictionaries
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
        
        return data
    except Exception:
        # Fallback to mock data if yfinance fails
        return generate_mock_historical_data(symbol, days)

def generate_mock_historical_data(symbol: str, days: int) -> List[Dict[str, Any]]:
    """
    Generate mock historical data for testing purposes.
    
    This creates realistic-looking price data with trends and volatility.
    """
    import random
    from datetime import datetime, timedelta
    
    # Base price with some randomness based on symbol
    base_price = 100 + (hash(symbol) % 200)
    data = []
    current_date = datetime.now() - timedelta(days=days)
    
    # Add trend component
    trend_slope = (hash(f"{symbol}_trend") % 100 - 50) / 10000  # -0.005 to 0.005
    
    for i in range(days):
        date = current_date + timedelta(days=i)
        
        # Add random walk component
        random_change = (hash(f"{symbol}_{i}") % 200 - 100) / 10000  # -0.01 to 0.01
        
        # Calculate price
        price = base_price * (1 + trend_slope * i + random_change)
        
        # Generate OHLC data
        high = price * (1 + abs(random_change) * 0.02)
        low = price * (1 - abs(random_change) * 0.02)
        open_price = low + (high - low) * random.random()
        
        # Volume with some randomness
        volume = int(1000000 + (hash(f"{symbol}_{i}_volume") % 5000000))
        
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": round(open_price, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(price, 2),
            "volume": volume
        })
        
        base_price = price
    
    return data

@router.post("/predict")
async def predict_trend(request: TrendRequest) -> TrendResponse:
    """
    Generate trend-based prediction for a single stock.
    
    This endpoint analyzes historical price data using technical analysis
    to generate Buy/Hold/Sell recommendations without predicting exact prices.
    
    Technical Indicators Used:
    - Moving Average Crossovers (Golden/Death Cross)
    - Relative Strength Index (RSI)
    - MACD (Moving Average Convergence Divergence)
    - Trend Analysis (Linear Regression)
    - Volatility Assessment
    
    The algorithm follows standard technical analysis principles and is
    designed to be explainable for interviews/viva examinations.
    
    Args:
        request: TrendRequest containing symbol and optional days parameter
        
    Returns:
        TrendResponse with recommendation and detailed analysis
    """
    try:
        # Get historical data
        days = request.days if request.days else 30
        historical_data = get_historical_data_for_symbol(request.symbol, days)
        
        if not historical_data:
            raise HTTPException(
                status_code=404, 
                detail=f"No historical data found for symbol {request.symbol}"
            )
        
        # Generate trend prediction
        prediction = trend_service.predict_trend(request.symbol, historical_data)
        
        return TrendResponse(
            status="success",
            symbol=prediction.symbol,
            recommendation=prediction.recommendation.value,
            confidence=prediction.confidence,
            reasoning=prediction.reasoning,
            signals=[
                {
                    "type": signal.signal_type,
                    "strength": signal.strength,
                    "direction": signal.direction,
                    "indicator": signal.indicator,
                    "explanation": signal.explanation,
                    "value": signal.value
                }
                for signal in prediction.signals
            ],
            technical_summary=prediction.technical_summary,
            risk_level=prediction.risk_level,
            prediction_date=prediction.prediction_date.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to predict trend for {request.symbol}: {str(e)}")

@router.post("/predict/batch")
async def predict_batch_trends(request: BatchTrendRequest) -> BatchTrendResponse:
    """
    Generate trend-based predictions for multiple stocks.
    
    This endpoint processes multiple stocks simultaneously and provides
    both individual and aggregated prediction results.
    
    Use Cases:
    - Portfolio analysis
    - Market overview
    - Batch recommendation generation
    - Risk assessment across multiple stocks
    
    Args:
        request: BatchTrendRequest containing symbols and optional days parameter
        
    Returns:
        BatchTrendResponse with comprehensive analysis results
    """
    try:
        if not request.symbols:
            raise HTTPException(status_code=400, detail="No symbols provided for batch prediction")
        
        predictions = []
        recommendation_counts = {"BUY": 0, "HOLD": 0, "SELL": 0}
        confidence_scores = []
        
        # Process each symbol
        for symbol in request.symbols:
            try:
                days = request.days if request.days else 30
                historical_data = get_historical_data_for_symbol(symbol, days)
                
                if historical_data:
                    prediction = trend_service.predict_trend(symbol, historical_data)
                    predictions.append({
                        "symbol": symbol,
                        "recommendation": prediction.recommendation.value,
                        "confidence": prediction.confidence,
                        "reasoning": prediction.reasoning,
                        "risk_level": prediction.risk_level,
                        "signal_count": len(prediction.signals),
                        "trend_strength": prediction.technical_summary["trend_strength"]
                    })
                    
                    recommendation_counts[prediction.recommendation.value] += 1
                    confidence_scores.append(prediction.confidence)
                else:
                    predictions.append({
                        "symbol": symbol,
                        "recommendation": "HOLD",
                        "confidence": 0.0,
                        "reasoning": f"No historical data available for {symbol}",
                        "risk_level": "UNKNOWN",
                        "signal_count": 0,
                        "trend_strength": 0.0
                    })
                    recommendation_counts["HOLD"] += 1
                    
            except Exception as e:
                predictions.append({
                    "symbol": symbol,
                    "recommendation": "HOLD",
                    "confidence": 0.0,
                    "reasoning": f"Error analyzing {symbol}: {str(e)}",
                    "risk_level": "UNKNOWN",
                    "signal_count": 0,
                    "trend_strength": 0.0
                })
                recommendation_counts["HOLD"] += 1
        
        # Calculate summary statistics
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        most_common_recommendation = max(recommendation_counts, key=recommendation_counts.get)
        
        return BatchTrendResponse(
            status="success",
            predictions=predictions,
            summary={
                "total_analyzed": len(request.symbols),
                "recommendation_distribution": recommendation_counts,
                "average_confidence": avg_confidence,
                "most_common_recommendation": most_common_recommendation,
                "processed_at": datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process batch trend prediction: {str(e)}")

@router.get("/indicators")
async def get_available_indicators() -> Dict[str, Any]:
    """
    Get information about the technical indicators used in trend analysis.
    
    This endpoint provides transparency into the prediction methodology by explaining
    the technical indicators and their interpretation.
    
    Returns:
        Dictionary containing indicator information
    """
    try:
        return {
            "status": "success",
            "indicators": {
                "moving_averages": {
                    "name": "Moving Averages (MA)",
                    "description": "Smooth price data to identify trends",
                    "types": ["SMA (Simple Moving Average)", "EMA (Exponential Moving Average)"],
                    "signals": [
                        "Golden Cross: 50-day SMA crossing above 200-day SMA (Bullish)",
                        "Death Cross: 50-day SMA crossing below 200-day SMA (Bearish)"
                    ],
                    "explanation": "Moving averages help identify trend direction and potential reversals"
                },
                "rsi": {
                    "name": "Relative Strength Index (RSI)",
                    "description": "Momentum oscillator measuring overbought/oversold conditions",
                    "range": "0 to 100",
                    "levels": {
                        "overbought": f"{trend_service.rsi_overbought} (Potential Sell Signal)",
                        "oversold": f"{trend_service.rsi_oversold} (Potential Buy Signal)",
                        "neutral": "50 (Momentum Reference)"
                    },
                    "explanation": "RSI helps identify when a stock is overbought or oversold and potential reversals"
                },
                "macd": {
                    "name": "Moving Average Convergence Divergence (MACD)",
                    "description": "Trend-following momentum indicator",
                    "components": [
                        "MACD Line: EMA(fast) - EMA(slow)",
                        "Signal Line: EMA of MACD line",
                        "Histogram: MACD line - Signal line"
                    ],
                    "signals": [
                        "MACD above Signal: Bullish momentum",
                        "MACD below Signal: Bearish momentum",
                        "Positive Histogram: Bullish momentum",
                        "Negative Histogram: Bearish momentum"
                    ],
                    "explanation": "MACD helps identify trend changes and momentum shifts"
                },
                "trend_analysis": {
                    "name": "Trend Analysis",
                    "description": "Linear regression to determine trend direction and strength",
                    "metrics": [
                        "Trend Direction: Uptrend/Downtrend/Neutral",
                        "Trend Strength: 0.0 to 1.0",
                        "R-squared: Trend reliability (0.0 to 1.0)"
                    ],
                    "explanation": "Trend analysis helps determine the overall market direction and strength"
                }
            },
            "prediction_logic": {
                "buy_conditions": [
                    "Multiple bullish signals (2+)",
                    "Strong uptrend with high R-squared",
                    "Low volatility (< 3%)",
                    "High confidence (> 0.6)"
                ],
                "sell_conditions": [
                    "Multiple bearish signals (2+)",
                    "Downtrend with high volatility",
                    "Negative momentum indicators",
                    "High confidence (> 0.6)"
                ],
                "hold_conditions": [
                    "Mixed or conflicting signals",
                    "Neutral trend or high volatility",
                    "Low confidence (< 0.4)",
                    "Insufficient data"
                ]
            },
            "confidence_calculation": {
                "factors": [
                    "Signal consensus (40% weight)",
                    "Signal strength (30% weight)",
                    "Trend strength (20% weight)",
                    "Trend reliability (10% weight)"
                ],
                "range": "0.0 to 1.0",
                "interpretation": "Higher confidence indicates stronger consensus and evidence"
            },
            "risk_assessment": {
                "factors": [
                    "Volatility: Higher volatility = higher risk",
                    "Trend Strength: Weak trends = higher risk"
                ],
                "levels": {
                    "LOW": "< 2.5% volatility AND strong trend",
                    "MEDIUM": "2.5-5.0% volatility OR weak trend",
                    "HIGH": "> 5.0% volatility"
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get indicator information: {str(e)}")

@router.get("/health")
async def trend_service_health() -> Dict[str, Any]:
    """
    Health check for the trend prediction service.
    
    Returns:
        Health status and service information
    """
    try:
        # Test the trend service with sample data
        sample_data = generate_mock_historical_data("AAPL", 30)
        test_result = trend_service.predict_trend("AAPL", sample_data)
        
        return {
            "status": "healthy",
            "service": "trend-prediction-service",
            "version": "1.0.0",
            "test_analysis": {
                "symbol": test_result.symbol,
                "recommendation": test_result.recommendation.value,
                "confidence": test_result.confidence,
                "risk_level": test_result.risk_level,
                "signals_analyzed": len(test_result.signals)
            },
            "capabilities": [
                "Moving Average Crossover Analysis",
                "RSI Overbought/Oversold Detection",
                "MACD Momentum Analysis",
                "Trend Strength Assessment",
                "Volatility-Based Risk Assessment",
                "Multi-Signal Consensus Building"
            ],
            "methodology": "Technical Analysis",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "trend-prediction-service",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
