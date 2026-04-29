"""
Dedicated sentiment analysis API endpoints.

This module provides REST endpoints specifically for sentiment analysis
of stock news and financial content using the AI-based SentimentAnalysisService.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from backend.app.services.sentiment_service import SentimentAnalysisService

router = APIRouter(prefix="/api/v1/sentiment", tags=["sentiment"])

# Initialize the AI sentiment analysis service
sentiment_service = SentimentAnalysisService()

class SentimentRequest(BaseModel):
    """Request model for sentiment analysis"""
    text: str
    context: Optional[str] = None

class SentimentResponse(BaseModel):
    """Response model for sentiment analysis"""
    status: str
    sentiment: str  # 'positive', 'negative', 'neutral'
    score: float     # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    explanation: str
    evidence: List[str]
    processed_at: str

class BatchSentimentRequest(BaseModel):
    """Request model for batch sentiment analysis"""
    texts: List[str]
    aggregate: bool = True

class BatchSentimentResponse(BaseModel):
    """Response model for batch sentiment analysis"""
    status: str
    total_analyzed: int
    overall_sentiment: str
    average_score: float
    confidence: float
    sentiment_distribution: Dict[str, int]
    individual_results: List[Dict[str, Any]]
    processed_at: str

@router.post("/analyze")
async def analyze_text_sentiment(request: SentimentRequest) -> SentimentResponse:
    """
    Analyze sentiment of a single text using AI-based analysis.
    
    This endpoint provides comprehensive sentiment analysis for any text,
    with special optimization for financial and stock market content.
    
    Features:
    - Financial keyword recognition
    - Context-aware sentiment modifiers
    - Confidence scoring
    - Evidence extraction
    - Detailed explanations
    
    Args:
        request: SentimentRequest containing text and optional context
        
    Returns:
        SentimentResponse with detailed analysis results
    """
    try:
        # Perform AI sentiment analysis
        result = sentiment_service.analyze_sentiment(request.text)
        
        return SentimentResponse(
            status="success",
            sentiment=result.sentiment,
            score=result.score,
            confidence=result.confidence,
            explanation=result.explanation,
            evidence=result.evidence,
            processed_at=result.processed_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze sentiment: {str(e)}")

@router.post("/analyze/batch")
async def analyze_batch_sentiment(request: BatchSentimentRequest) -> BatchSentimentResponse:
    """
    Analyze sentiment for multiple texts and aggregate results.
    
    This endpoint processes multiple texts simultaneously and provides
    both individual and aggregated sentiment analysis results.
    
    Use Cases:
    - Analyzing multiple news articles about the same stock
    - Batch processing of financial reports
    - Market sentiment aggregation
    
    Args:
        request: BatchSentimentRequest containing texts and aggregation preference
        
    Returns:
        BatchSentimentResponse with comprehensive analysis results
    """
    try:
        if not request.texts:
            raise HTTPException(status_code=400, detail="No texts provided for analysis")
        
        # Perform batch sentiment analysis
        analysis_result = sentiment_service.analyze_multiple_texts(request.texts)
        
        return BatchSentimentResponse(
            status="success",
            total_analyzed=analysis_result["total_analyzed"],
            overall_sentiment=analysis_result["overall_sentiment"],
            average_score=analysis_result["average_score"],
            confidence=analysis_result["confidence"],
            sentiment_distribution=analysis_result["sentiment_distribution"],
            individual_results=analysis_result["individual_results"],
            processed_at=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze batch sentiment: {str(e)}")

@router.get("/keywords")
async def get_sentiment_keywords() -> Dict[str, Any]:
    """
    Get the sentiment keywords and their weights used in analysis.
    
    This endpoint provides transparency into the sentiment analysis
    by showing the keywords and their associated weights that influence
    the sentiment scoring algorithm.
    
    Returns:
        Dictionary containing positive and negative keywords with weights
    """
    try:
        return {
            "status": "success",
            "positive_keywords": sentiment_service.positive_keywords,
            "negative_keywords": sentiment_service.negative_keywords,
            "intensity_modifiers": sentiment_service.intensity_modifiers,
            "financial_entities": list(sentiment_service.financial_entities),
            "explanation": {
                "positive_keywords": "Words that indicate positive sentiment with their weights (0.6-1.0)",
                "negative_keywords": "Words that indicate negative sentiment with their weights (0.6-1.0)",
                "intensity_modifiers": "Words that amplify or diminish sentiment intensity",
                "financial_entities": "Financial terms that add context to the analysis"
            },
            "scoring_algorithm": {
                "method": "Hybrid approach combining keyword analysis with context awareness",
                "normalization": "Sigmoid-like normalization to keep scores in [-1, 1] range",
                "confidence_factors": [
                    "Number of sentiment keywords (40% weight)",
                    "Sentiment strength (40% weight)", 
                    "Financial relevance (20% weight)"
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sentiment keywords: {str(e)}")

@router.get("/health")
async def sentiment_service_health() -> Dict[str, Any]:
    """
    Health check for the sentiment analysis service.
    
    Returns:
        Health status and service information
    """
    try:
        # Test the sentiment service with a simple example
        test_result = sentiment_service.analyze_sentiment("The stock market is performing well today")
        
        return {
            "status": "healthy",
            "service": "sentiment-analysis-service",
            "version": "1.0.0",
            "test_analysis": {
                "test_text": "The stock market is performing well today",
                "sentiment": test_result.sentiment,
                "score": test_result.score,
                "confidence": test_result.confidence
            },
            "capabilities": [
                "Single text sentiment analysis",
                "Batch sentiment analysis",
                "Financial keyword recognition",
                "Context-aware sentiment modifiers",
                "Confidence scoring",
                "Evidence extraction"
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "sentiment-analysis-service",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
