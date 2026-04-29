"""
AI-based sentiment analysis service for stock news.

This service analyzes news articles and text content to determine sentiment
using multiple techniques:
1. Keyword-based analysis with weighted scoring
2. Financial sentiment lexicon
3. Context-aware sentiment modifiers
4. Confidence scoring based on evidence strength

The sentiment analysis is specifically tuned for financial news and stock market content.
"""

import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SentimentResult:
    """Data class for sentiment analysis results"""
    sentiment: str  # 'positive', 'negative', 'neutral'
    score: float   # -1.0 to 1.0
    confidence: float  # 0.0 to 1.0
    explanation: str
    evidence: List[str]  # Key phrases that influenced the sentiment
    processed_at: datetime

class SentimentAnalysisService:
    """
    AI-based sentiment analysis service specialized for financial news.
    
    Uses a hybrid approach combining:
    - Financial keyword dictionaries
    - Context-aware sentiment modifiers
    - Confidence scoring based on evidence strength
    """
    
    def __init__(self):
        """Initialize sentiment analysis with financial lexicons"""
        
        # Financial positive keywords with weights
        self.positive_keywords = {
            # Strong positive indicators (weight: 1.0)
            'bullish': 1.0, 'rally': 1.0, 'surge': 1.0, 'soar': 1.0, 'jump': 1.0,
            'spike': 1.0, 'boom': 1.0, 'breakthrough': 1.0, 'milestone': 1.0,
            'record': 1.0, 'all-time high': 1.0, 'unprecedented': 1.0,
            
            # Growth indicators (weight: 0.8)
            'growth': 0.8, 'expansion': 0.8, 'increase': 0.8, 'rise': 0.8,
            'gain': 0.8, 'profit': 0.8, 'earnings': 0.8, 'revenue': 0.8,
            'beat': 0.8, 'exceed': 0.8, 'outperform': 0.8, 'strong': 0.8,
            'robust': 0.8, 'solid': 0.8, 'healthy': 0.8, 'optimistic': 0.8,
            
            # Moderate positive (weight: 0.6)
            'up': 0.6, 'higher': 0.6, 'improved': 0.6, 'positive': 0.6,
            'favorable': 0.6, 'encouraging': 0.6, 'promising': 0.6,
            'stable': 0.6, 'steady': 0.6, 'resilient': 0.6, 'recovery': 0.6,
            
            # Investment positive (weight: 0.7)
            'buy': 0.7, 'investment': 0.7, 'opportunity': 0.7, 'undervalued': 0.7,
            'attractive': 0.7, 'potential': 0.7, 'upside': 0.7, 'dividend': 0.7,
        }
        
        # Financial negative keywords with weights
        self.negative_keywords = {
            # Strong negative indicators (weight: 1.0)
            'bearish': 1.0, 'crash': 1.0, 'plunge': 1.0, 'slump': 1.0, 'collapse': 1.0,
            'panic': 1.0, 'crisis': 1.0, 'disaster': 1.0, 'catastrophe': 1.0,
            'scandal': 1.0, 'fraud': 1.0, 'investigation': 1.0, 'lawsuit': 1.0,
            'bankruptcy': 1.0, 'default': 1.0, 'delisted': 1.0, 'suspended': 1.0,
            
            # Decline indicators (weight: 0.8)
            'decline': 0.8, 'drop': 0.8, 'fall': 0.8, 'decrease': 0.8, 'loss': 0.8,
            'miss': 0.8, 'below': 0.8, 'underperform': 0.8, 'weak': 0.8,
            'poor': 0.8, 'disappointing': 0.8, 'concern': 0.8, 'worry': 0.8,
            
            # Moderate negative (weight: 0.6)
            'down': 0.6, 'lower': 0.6, 'reduced': 0.6, 'negative': 0.6,
            'unfavorable': 0.6, 'trouble': 0.6, 'risk': 0.6, 'volatility': 0.6,
            'uncertainty': 0.6, 'challenges': 0.6, 'headwinds': 0.6, 'pressure': 0.6,
            
            # Investment negative (weight: 0.7)
            'sell': 0.7, 'overvalued': 0.7, 'bubble': 0.7, 'correction': 0.7,
            'downgrade': 0.7, 'cut': 0.7, 'selloff': 0.7, 'fear': 0.7,
        }
        
        # Context modifiers that affect sentiment intensity
        self.intensity_modifiers = {
            # Amplifiers
            'very': 1.5, 'extremely': 2.0, 'significantly': 1.8, 'dramatically': 2.0,
            'sharply': 1.7, 'steeply': 1.6, 'massive': 1.9, 'huge': 1.8,
            'major': 1.5, 'substantial': 1.4, 'considerable': 1.3,
            
            # Diminishers
            'slightly': 0.7, 'marginally': 0.6, 'modestly': 0.7, 'mildly': 0.6,
            'somewhat': 0.8, 'relatively': 0.9, 'comparatively': 0.9,
            
            # Negation (reverses sentiment)
            'not': -1.0, 'no': -1.0, 'never': -1.0, 'neither': -1.0,
            'despite': -0.5, 'although': -0.3, 'however': -0.3,
        }
        
        # Financial entities that add context
        self.financial_entities = {
            'earnings', 'revenue', 'profit', 'loss', 'dividend', 'stock', 'share',
            'market', 'index', 'commodity', 'currency', 'bond', 'treasury', 'fed',
            'inflation', 'interest', 'rate', 'gdp', 'economy', 'recession', 'growth'
        }
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for analysis.
        
        Steps:
        1. Convert to lowercase
        2. Remove special characters but keep important financial symbols
        3. Tokenize words
        4. Remove common stop words
        """
        # Convert to lowercase
        text = text.lower()
        
        # Keep important financial symbols and punctuation
        text = re.sub(r'[^a-z0-9\s$%.,-]', ' ', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _find_sentiment_keywords(self, text: str) -> List[Tuple[str, float, str]]:
        """
        Find sentiment keywords in text with their weights and positions.
        
        Returns list of (keyword, weight, position) tuples
        """
        keywords_found = []
        words = text.split()
        
        for i, word in enumerate(words):
            # Check for multi-word phrases first
            for phrase_length in range(3, 0, -1):
                if i + phrase_length <= len(words):
                    phrase = ' '.join(words[i:i+phrase_length])
                    
                    # Check positive phrases
                    for positive_phrase, weight in self.positive_keywords.items():
                        if positive_phrase in phrase:
                            keywords_found.append((positive_phrase, weight, phrase))
                            break
                    
                    # Check negative phrases
                    for negative_phrase, weight in self.negative_keywords.items():
                        if negative_phrase in phrase:
                            keywords_found.append((negative_phrase, -weight, phrase))
                            break
            
            # Check single words if no phrases found
            if not any(phrase[2] == ' '.join(words[i:i+len(phrase[2].split())]) for phrase in keywords_found if i <= words.index(phrase[2].split()[0]) if phrase[2].split()[0] in words):
                # Check positive words
                for positive_word, weight in self.positive_keywords.items():
                    if positive_word == word:
                        keywords_found.append((positive_word, weight, word))
                        break
                
                # Check negative words
                for negative_word, weight in self.negative_keywords.items():
                    if negative_word == word:
                        keywords_found.append((negative_word, -weight, word))
                        break
        
        return keywords_found
    
    def _apply_intensity_modifiers(self, keywords: List[Tuple[str, float, str]], text: str) -> List[Tuple[str, float, str]]:
        """
        Apply intensity modifiers to sentiment keywords.
        
        Looks for words that amplify or diminish sentiment intensity.
        """
        modified_keywords = []
        words = text.split()
        
        for keyword, weight, context in keywords:
            modified_weight = weight
            
            # Look for modifiers within 3 words of the keyword
            keyword_words = context.split()
            keyword_start_idx = None
            
            # Find the starting position of the keyword in the text
            for i in range(len(words) - len(keyword_words) + 1):
                if words[i:i+len(keyword_words)] == keyword_words:
                    keyword_start_idx = i
                    break
            
            if keyword_start_idx is not None:
                # Check for modifiers in the vicinity
                for modifier, modifier_factor in self.intensity_modifiers.items():
                    for j in range(max(0, keyword_start_idx - 3), 
                                 min(len(words), keyword_start_idx + len(keyword_words) + 3)):
                        if words[j] == modifier:
                            modified_weight *= modifier_factor
                            break
            
            modified_keywords.append((keyword, modified_weight, context))
        
        return modified_keywords
    
    def _calculate_base_sentiment(self, keywords: List[Tuple[str, float, str]]) -> float:
        """
        Calculate base sentiment score from keywords.
        
        Algorithm:
        1. Sum all keyword weights
        2. Normalize by number of keywords to prevent bias from text length
        3. Apply sigmoid function to keep score in [-1, 1] range
        """
        if not keywords:
            return 0.0
        
        # Sum all weights
        total_weight = sum(weight for _, weight, _ in keywords)
        
        # Normalize by number of keywords (average weight)
        avg_weight = total_weight / len(keywords)
        
        # Apply sigmoid-like normalization to keep in [-1, 1] range
        # Using tanh for smooth normalization
        normalized_score = max(-1.0, min(1.0, avg_weight))
        
        return normalized_score
    
    def _calculate_confidence(self, sentiment_score: float, keywords: List[Tuple[str, float, str]]) -> float:
        """
        Calculate confidence score based on evidence strength.
        
        Confidence factors:
        1. Number of sentiment keywords found
        2. Absolute value of sentiment score (stronger signals = higher confidence)
        3. Presence of financial entities (indicates relevant content)
        4. Text length (longer texts with consistent sentiment = higher confidence)
        """
        if not keywords:
            return 0.0
        
        # Base confidence from number of keywords
        keyword_confidence = min(1.0, len(keywords) / 5.0)  # More keywords = higher confidence
        
        # Score strength confidence (stronger sentiment = higher confidence)
        score_confidence = abs(sentiment_score)
        
        # Financial entity presence confidence
        financial_keywords = sum(1 for _, _, context in keywords 
                               if any(entity in context for entity in self.financial_entities))
        financial_confidence = min(1.0, financial_keywords / max(1, len(keywords)))
        
        # Combine confidences with weights
        combined_confidence = (
            0.4 * keyword_confidence +    # 40% weight on keyword count
            0.4 * score_confidence +       # 40% weight on sentiment strength
            0.2 * financial_confidence    # 20% weight on financial relevance
        )
        
        return round(combined_confidence, 3)
    
    def _generate_explanation(self, sentiment_score: float, keywords: List[Tuple[str, float, str]]) -> str:
        """
        Generate human-readable explanation for the sentiment analysis.
        
        Explanation includes:
        1. Overall sentiment classification
        2. Key evidence found
        3. Confidence reasoning
        """
        if not keywords:
            return "No sentiment indicators found in the text."
        
        # Determine sentiment
        if sentiment_score > 0.1:
            sentiment_label = "positive"
        elif sentiment_score < -0.1:
            sentiment_label = "negative"
        else:
            sentiment_label = "neutral"
        
        # Get top contributing keywords
        sorted_keywords = sorted(keywords, key=lambda x: abs(x[1]), reverse=True)[:5]
        
        # Count positive and negative keywords
        positive_count = sum(1 for _, weight, _ in keywords if weight > 0)
        negative_count = sum(1 for _, weight, _ in keywords if weight < 0)
        
        # Generate explanation
        explanation_parts = []
        
        explanation_parts.append(f"Sentiment classified as {sentiment_label}")
        
        if positive_count > 0 and negative_count > 0:
            explanation_parts.append(f"Found {positive_count} positive and {negative_count} negative indicators")
        elif positive_count > 0:
            explanation_parts.append(f"Found {positive_count} positive indicators")
        elif negative_count > 0:
            explanation_parts.append(f"Found {negative_count} negative indicators")
        
        # Add top keywords as evidence
        if sorted_keywords:
            top_keywords = [f"{keyword} ({'positive' if weight > 0 else 'negative'})" 
                          for keyword, weight, _ in sorted_keywords[:3]]
            explanation_parts.append(f"Key evidence: {', '.join(top_keywords)}")
        
        return ". ".join(explanation_parts) + "."
    
    def analyze_sentiment(self, text: str) -> SentimentResult:
        """
        Main sentiment analysis method.
        
        Process:
        1. Preprocess text
        2. Find sentiment keywords
        3. Apply intensity modifiers
        4. Calculate sentiment score
        5. Determine confidence
        6. Generate explanation
        
        Args:
            text: Text to analyze (news article, headline, etc.)
            
        Returns:
            SentimentResult with sentiment classification, score, confidence, and explanation
        """
        # Preprocess text
        processed_text = self._preprocess_text(text)
        
        # Find sentiment keywords
        keywords = self._find_sentiment_keywords(processed_text)
        
        # Apply intensity modifiers
        modified_keywords = self._apply_intensity_modifiers(keywords, processed_text)
        
        # Calculate base sentiment score
        sentiment_score = self._calculate_base_sentiment(modified_keywords)
        
        # Calculate confidence
        confidence = self._calculate_confidence(sentiment_score, modified_keywords)
        
        # Determine sentiment classification
        if sentiment_score > 0.1:
            sentiment = "positive"
        elif sentiment_score < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Generate explanation
        explanation = self._generate_explanation(sentiment_score, modified_keywords)
        
        # Extract evidence (top keywords)
        evidence = [f"{keyword}: {abs(weight):.2f}" for keyword, weight, _ in 
                  sorted(modified_keywords, key=lambda x: abs(x[1]), reverse=True)[:5]]
        
        return SentimentResult(
            sentiment=sentiment,
            score=round(sentiment_score, 3),
            confidence=confidence,
            explanation=explanation,
            evidence=evidence,
            processed_at=datetime.now()
        )
    
    def analyze_multiple_texts(self, texts: List[str]) -> Dict[str, Any]:
        """
        Analyze sentiment for multiple texts and aggregate results.
        
        Useful for analyzing multiple news articles about the same stock.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            Dictionary with aggregated sentiment analysis results
        """
        if not texts:
            return {
                "overall_sentiment": "neutral",
                "average_score": 0.0,
                "confidence": 0.0,
                "total_analyzed": 0,
                "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 0},
                "individual_results": []
            }
        
        # Analyze each text
        individual_results = []
        scores = []
        sentiments = []
        confidences = []
        
        for text in texts:
            result = self.analyze_sentiment(text)
            individual_results.append(result)
            scores.append(result.score)
            sentiments.append(result.sentiment)
            confidences.append(result.confidence)
        
        # Calculate aggregate metrics
        avg_score = sum(scores) / len(scores) if scores else 0.0
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Determine overall sentiment
        if avg_score > 0.1:
            overall_sentiment = "positive"
        elif avg_score < -0.1:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"
        
        # Count sentiment distribution
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        for sentiment in sentiments:
            sentiment_counts[sentiment] += 1
        
        return {
            "overall_sentiment": overall_sentiment,
            "average_score": round(avg_score, 3),
            "confidence": round(avg_confidence, 3),
            "total_analyzed": len(texts),
            "sentiment_distribution": sentiment_counts,
            "individual_results": [
                {
                    "sentiment": result.sentiment,
                    "score": result.score,
                    "confidence": result.confidence,
                    "explanation": result.explanation
                }
                for result in individual_results
            ]
        }
