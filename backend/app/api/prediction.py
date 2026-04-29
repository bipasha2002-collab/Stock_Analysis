"""
Simple prediction API endpoints for stock recommendations.

This module provides basic prediction endpoints that complement the more sophisticated
trend prediction service. These endpoints are designed to be lightweight and fast, providing
quick recommendations without complex analysis.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from datetime import datetime
import random

router = APIRouter(prefix="/api/v1/prediction", tags=["prediction"])

# Simple mock prediction data
MOCK_PREDICTIONS = {
    'AAPL': {
        'recommendation': 'BUY',
        'confidence': 0.85,
        'reasoning': 'Strong fundamentals with consistent growth, positive technical indicators'
    },
    'GOOGL': {
        'recommendation': 'BUY',
        'confidence': 0.78,
        'reasoning': 'Strong market position, diversified revenue streams, positive outlook'
    },
    'MSFT': {
        'recommendation': 'BUY',
        'confidence': 0.82,
        'reasoning': 'Cloud computing growth, enterprise dominance, strong financial performance'
    },
    'TSLA': {
        'recommendation': 'HOLD',
        'confidence': 0.65,
        'reasoning': 'High volatility, production challenges, competitive pressure'
    },
    'NVDA': {
        'recommendation': 'BUY',
        'confidence': 0.88,
        'reasoning': 'AI chip dominance, strong growth in data center demand, positive technical outlook'
    },
    'AMZN': {
        'recommendation': 'BUY',
        'confidence': 0.80,
        'reasoning': 'E-commerce dominance, AWS growth, strong logistics network'
    },
    'META': {
        'recommendation': 'HOLD',
        'confidence': 0.60,
        'reasoning': 'Regulatory challenges, competition concerns, transition phase'
    },
    'NFLX': {
        'recommendation': 'SELL',
        'confidence': 0.70,
        'reasoning': 'Declining user engagement, competition concerns, platform uncertainty'
    }
}

def get_simple_prediction(symbol: str) -> Dict[str, Any]:
    """
    Generate a simple prediction based on symbol.
    
    Uses a hash-based approach for consistent results:
    - Hash symbol to get consistent prediction type
    - Generate confidence between 0.5-0.9
    - Provide reasoning based on common market knowledge
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Dictionary with prediction data
    """
    # Use symbol hash for consistent predictions
    symbol_upper = symbol.upper()
    hash_value = sum(ord(c) for c in symbol_upper)
    
    # Determine recommendation based on hash
    if symbol_upper in MOCK_PREDICTIONS:
        return MOCK_PREDICTIONS[symbol_upper]
    
    # Generate prediction for unknown symbols
    prediction_types = ['BUY', 'HOLD', 'SELL']
    recommendation = prediction_types[hash_value % 3]
    confidence = 0.5 + (hash_value % 40) / 100  # 0.5 to 0.9
    
    reasoning_map = {
        'BUY': 'Technical analysis suggests upward momentum, favorable market conditions',
        'HOLD': 'Mixed signals indicate consolidation phase, waiting for clearer direction',
        'SELL': 'Technical indicators suggest downward pressure, risk factors present'
    }
    
    return {
        'symbol': symbol_upper,
        'recommendation': recommendation,
        'confidence': round(confidence, 2),
        'reasoning': reasoning_map[recommendation],
        'generated_at': datetime.now().isoformat()
    }

@router.get("/{symbol}")
async def get_prediction(symbol: str) -> Dict[str, Any]:
    """
    Get simple stock prediction.
    
    Provides a quick recommendation based on symbol analysis.
    This is a lightweight endpoint designed for fast responses.
    
    Args:
        symbol: Stock symbol (e.g., AAPL, GOOGL, MSFT)
        
    Returns:
        Prediction data with recommendation, confidence, and reasoning
        
    Example Response:
    {
        "symbol": "AAPL",
        "recommendation": "BUY",
        "confidence": 0.85,
        "reasoning": "Strong fundamentals with consistent growth, positive technical indicators",
        "generated_at": "2024-01-17T10:26:00Z"
    }
    """
    try:
        if not symbol or len(symbol.strip()) < 1:
            raise HTTPException(status_code=400, detail="Symbol is required")
        
        symbol_clean = symbol.strip().upper()
        
        # Get prediction
        prediction = get_simple_prediction(symbol_clean)
        
        return {
            "status": "success",
            "data": prediction
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Return error response
        return {
            "status": "error",
            "message": f"Prediction failed for {symbol}: {str(e)}",
            "symbol": symbol_clean if 'symbol_clean' in locals() else symbol,
            "generated_at": datetime.now().isoformat()
        }

@router.get("/{symbol}/simple")
async def get_simple_prediction(symbol: str) -> Dict[str, Any]:
    """
    Get simple prediction (alternative endpoint).
    
    This is an alternative endpoint that returns the same data as the main prediction endpoint
    but with a different URL path for compatibility.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Same prediction data as main endpoint
    """
    return await get_prediction(symbol)

@router.get("/{symbol}/analysis")
async def get_prediction_analysis(symbol: str) -> Dict[str, Any]:
    """
    Get detailed prediction analysis.
    
    Provides more detailed information about the prediction including
    technical indicators and risk assessment.
    
    Args:
        symbol: Stock symbol
        
    Returns:
        Enhanced prediction data with additional analysis
    """
    try:
        if not symbol or len(symbol.strip()) < 1:
            raise HTTPException(status_code=400, detail="Symbol is required")
        
        symbol_clean = symbol.strip().upper()
        
        # Get base prediction
        prediction = get_simple_prediction(symbol_clean)
        
        # Add additional analysis
        analysis = {
            'risk_level': 'LOW' if prediction['confidence'] > 0.7 else 'MEDIUM' if prediction['confidence'] > 0.5 else 'HIGH',
            'volatility': random.uniform(1.0, 5.0),
            'trend_strength': prediction['confidence'],
            'market_sentiment': random.choice(['positive', 'neutral', 'negative']),
            'time_horizon': 'short-term (1-2 weeks)',
            'key_factors': [
                'Technical indicators',
                'Market conditions',
                'Company fundamentals'
            ],
            'disclaimer': 'This is a simplified prediction and should not be considered financial advice'
        }
        
        return {
            "status": "success",
            "data": {
                **prediction,
                "analysis": analysis
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Analysis failed for {symbol}: {str(e)}",
            "symbol": symbol_clean if 'symbol_clean' in locals() else symbol,
            "generated_at": datetime.now().isoformat()
        }

@router.get("/health")
async def prediction_health() -> Dict[str, Any]:
    """
    Health check for prediction service.
    
    Returns:
        Service health status and basic metrics
    """
    try:
        # Test with a known symbol
        test_prediction = get_simple_prediction('AAPL')
        
        return {
            "status": "healthy",
            "service": "prediction-service",
            "version": "1.0.0",
            "test_prediction": {
                "symbol": test_prediction["symbol"],
                "recommendation": test_prediction["recommendation"],
                "confidence": test_prediction["confidence"]
            },
            "available_symbols": list(MOCK_PREDICTIONS.keys()),
            "capabilities": [
                "Simple stock predictions",
                "Confidence scoring",
                "Basic reasoning",
                "Risk assessment"
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "prediction-service",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/symbols")
async def get_available_symbols() -> Dict[str, Any]:
    """
    Get list of available symbols for prediction.
    
    Returns:
        List of symbols that have pre-defined predictions
    """
    return {
        "status": "success",
        "symbols": list(MOCK_PREDICTIONS.keys()),
        "total": len(MOCK_PREDICTIONS),
        "updated_at": datetime.now().isoformat()
    }
