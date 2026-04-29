"""
Trend-based prediction service for stock recommendations.

This service analyzes historical price data and technical indicators to generate
Buy/Hold/Sell recommendations without predicting exact prices. The approach is based on
technical analysis principles and is designed to be explainable for interviews/viva.

Key Components:
1. Technical Indicators: Moving Averages, RSI, MACD
2. Trend Analysis: Short-term, medium-term, long-term trends
3. Momentum Analysis: Price momentum and volume patterns
4. Risk Assessment: Volatility and trend strength
5. Confidence Scoring: Evidence-based confidence calculation

The prediction logic follows standard technical analysis principles:
- Buy signals: Bullish crossovers, oversold conditions, strong uptrends
- Hold signals: Neutral conditions, consolidation phases
- Sell signals: Bearish crossovers, overbought conditions, downtrends
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

class Recommendation(Enum):
    """Trading recommendation types"""
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"

@dataclass
class TrendSignal:
    """Data class for individual trend signals"""
    signal_type: str
    strength: float  # 0.0 to 1.0
    direction: str  # "bullish" or "bearish"
    indicator: str
    explanation: str
    value: float

@dataclass
class PredictionResult:
    """Data class for prediction results"""
    symbol: str
    recommendation: Recommendation
    confidence: float  # 0.0 to 1.0
    reasoning: str
    signals: List[TrendSignal]
    technical_summary: Dict[str, Any]
    risk_level: str
    prediction_date: datetime

class TrendPredictionService:
    """
    Trend-based prediction service using technical analysis.
    
    This service implements standard technical analysis principles to generate
    Buy/Hold/Sell recommendations based on:
    1. Moving Average Crossovers
    2. Relative Strength Index (RSI)
    3. MACD (Moving Average Convergence Divergence)
    4. Trend Analysis
    5. Volume Analysis
    6. Volatility Assessment
    
    The approach is designed to be explainable and follows established
    technical analysis methodologies.
    """
    
    def __init__(self):
        """Initialize the trend prediction service"""
        self.min_data_points = 20  # Minimum data points for analysis
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.rsi_period = 14
        
    def calculate_sma(self, prices: List[float], period: int) -> List[float]:
        """
        Calculate Simple Moving Average (SMA).
        
        SMA is the arithmetic mean of a given set of prices over a specified period.
        It smooths out price data to identify trends.
        
        Args:
            prices: List of closing prices
            period: Period for SMA calculation
            
        Returns:
            List of SMA values
        """
        if len(prices) < period:
            return []
        
        sma_values = []
        for i in range(period - 1, len(prices)):
            sma = sum(prices[i - period + 1:i + 1]) / period
            sma_values.append(sma)
        
        return sma_values
    
    def calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """
        Calculate Exponential Moving Average (EMA).
        
        EMA gives more weight to recent prices and reacts more quickly to price changes
        compared to SMA. It's commonly used for short-term trend analysis.
        
        Args:
            prices: List of closing prices
            period: Period for EMA calculation
            
        Returns:
            List of EMA values
        """
        if len(prices) < period:
            return []
        
        # Calculate smoothing factor
        smoothing = 2 / (period + 1)
        
        ema_values = []
        ema = prices[0]  # Start with first price
        
        for price in prices:
            ema = (price * smoothing) + (ema * (1 - smoothing))
            ema_values.append(ema)
        
        return ema_values
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """
        Calculate Relative Strength Index (RSI).
        
        RSI is a momentum oscillator that measures the speed and change of price movements.
        It ranges from 0 to 100 and is typically used to identify overbought/oversold conditions.
        
        Calculation:
        1. Calculate price changes
        2. Separate gains and losses
        3. Calculate average gains and losses
        4. Calculate RS (Relative Strength)
        5. Calculate RSI = 100 - (100 / (1 + RS))
        
        Args:
            prices: List of closing prices
            period: Period for RSI calculation (default: 14)
            
        Returns:
            List of RSI values
        """
        if len(prices) < period + 1:
            return []
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]
        
        rsi_values = []
        
        for i in range(period, len(gains)):
            avg_gain = np.mean(gains[i-period:i])
            avg_loss = np.mean(losses[i-period:i])
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
        
        return rsi_values
    
    def calculate_macd(self, prices: List[float], fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Dict[str, List[float]]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        MACD is a trend-following momentum indicator that shows the relationship between
        two moving averages of prices. It consists of:
        - MACD line: EMA(fast) - EMA(slow)
        - Signal line: EMA of MACD line
        - Histogram: MACD line - Signal line
        
        Args:
            prices: List of closing prices
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line EMA period (default: 9)
            
        Returns:
            Dictionary containing MACD line, signal line, and histogram
        """
        if len(prices) < slow_period:
            return {"macd": [], "signal": [], "histogram": []}
        
        # Calculate EMAs
        ema_fast = self.calculate_ema(prices, fast_period)
        ema_slow = self.calculate_ema(prices, slow_period)
        
        # Calculate MACD line
        macd_line = [ema_fast[i] - ema_slow[i] for i in range(min(len(ema_fast), len(ema_slow)))]
        
        # Calculate Signal line
        signal_line = self.calculate_ema(macd_line, signal_period)
        
        # Calculate Histogram
        histogram = [macd_line[i] - signal_line[i] for i in range(min(len(macd_line), len(signal_line)))]
        
        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }
    
    def analyze_ma_crossovers(self, prices: List[float]) -> List[TrendSignal]:
        """
        Analyze moving average crossovers for trading signals.
        
        Golden Cross (50-day SMA crosses above 200-day SMA): Bullish signal
        Death Cross (50-day SMA crosses below 200-day SMA): Bearish signal
        
        Args:
            prices: List of closing prices
            
        Returns:
            List of trend signals from MA crossovers
        """
        signals = []
        
        # Calculate moving averages
        sma_50 = self.calculate_sma(prices, 50)
        sma_200 = self.calculate_sma(prices, 200)
        
        if len(sma_50) < 2 or len(sma_200) < 2:
            return signals
        
        # Check for crossovers
        for i in range(1, len(sma_50)):
            # Golden Cross: 50-day SMA crosses above 200-day SMA
            if (sma_50[i-1] <= sma_200[i-1] and sma_50[i] > sma_200[i] and 
                sma_50[i-1] != sma_200[i-1]):  # Ensure it's an actual crossover
                strength = min(1.0, abs(sma_50[i] - sma_200[i]) / sma_200[i] * 10)
                signals.append(TrendSignal(
                    signal_type="MA_Crossover",
                    strength=strength,
                    direction="bullish",
                    indicator="Golden Cross",
                    explanation=f"50-day SMA ({sma_50[i]:.2f}) crossed above 200-day SMA ({sma_200[i]:.2f})",
                    value=sma_50[i] - sma_200[i]
                ))
            
            # Death Cross: 50-day SMA crosses below 200-day SMA
            elif (sma_50[i-1] >= sma_200[i-1] and sma_50[i] < sma_200[i] and 
                  sma_50[i-1] != sma_200[i-1]):  # Ensure it's an actual crossover
                strength = min(1.0, abs(sma_200[i] - sma_50[i]) / sma_200[i] * 10)
                signals.append(TrendSignal(
                    signal_type="MA_Crossover",
                    strength=strength,
                    direction="bearish",
                    indicator="Death Cross",
                    explanation=f"50-day SMA ({sma_50[i]:.2f}) crossed below 200-day SMA ({sma_200[i]:.2f})",
                    value=sma_50[i] - sma_200[i]
                ))
        
        return signals
    
    def analyze_rsi_signals(self, prices: List[float]) -> List[TrendSignal]:
        """
        Analyze RSI for overbought/oversold conditions.
        
        RSI > 70: Overbought (potential sell signal)
        RSI < 30: Oversold (potential buy signal)
        RSI crossing above 50: Bullish momentum
        RSI crossing below 50: Bearish momentum
        
        Args:
            prices: List of closing prices
            
        Returns:
            List of trend signals from RSI analysis
        """
        signals = []
        
        rsi_values = self.calculate_rsi(prices, self.rsi_period)
        
        if len(rsi_values) < 2:
            return signals
        
        # Check for overbought/oversold conditions
        current_rsi = rsi_values[-1]
        
        if current_rsi > self.rsi_overbought:
            strength = min(1.0, (current_rsi - self.rsi_overbought) / 30)
            signals.append(TrendSignal(
                signal_type="RSI",
                strength=strength,
                direction="bearish",
                indicator="Overbought",
                explanation=f"RSI is {current_rsi:.1f} (overbought threshold: {self.rsi_overbought})",
                value=current_rsi
            ))
        elif current_rsi < self.rsi_oversold:
            strength = min(1.0, (self.rsi_oversold - current_rsi) / 30)
            signals.append(TrendSignal(
                signal_type="RSI",
                strength=strength,
                direction="bullish",
                indicator="Oversold",
                explanation=f"RSI is {current_rsi:.1f} (oversold threshold: {self.rsi_oversold})",
                value=current_rsi
            ))
        
        # Check for momentum changes (RSI crossing 50)
        for i in range(1, len(rsi_values)):
            if rsi_values[i-1] <= 50 and rsi_values[i] > 50 and rsi_values[i-1] != 50:
                strength = min(1.0, (rsi_values[i] - 50) / 50)
                signals.append(TrendSignal(
                    signal_type="RSI_Momentum",
                    strength=strength,
                    direction="bullish",
                    indicator="RSI Above 50",
                    explanation=f"RSI crossed above 50, indicating bullish momentum",
                    value=rsi_values[i]
                ))
            elif rsi_values[i-1] >= 50 and rsi_values[i] < 50 and rsi_values[i-1] != 50:
                strength = min(1.0, (50 - rsi_values[i]) / 50)
                signals.append(TrendSignal(
                    signal_type="RSI_Momentum",
                    strength=strength,
                    direction="bearish",
                    indicator="RSI Below 50",
                    explanation=f"RSI crossed below 50, indicating bearish momentum",
                    value=rsi_values[i]
                ))
        
        return signals
    
    def analyze_macd_signals(self, prices: List[float]) -> List[TrendSignal]:
        """
        Analyze MACD for trend signals.
        
        MACD line crossing above Signal line: Bullish signal
        MACD line crossing below Signal line: Bearish signal
        Histogram divergence: Trend weakening/strengthening
        
        Args:
            prices: List of closing prices
            
        Returns:
            List of trend signals from MACD analysis
        """
        signals = []
        
        macd_data = self.calculate_macd(prices)
        macd_line = macd_data["macd"]
        signal_line = macd_data["signal"]
        histogram = macd_data["histogram"]
        
        if len(macd_line) < 2 or len(signal_line) < 2:
            return signals
        
        # Check for MACD line crossing Signal line
        for i in range(1, len(signal_line)):
            if macd_line[i-1] <= signal_line[i-1] and macd_line[i] > signal_line[i] and macd_line[i-1] != signal_line[i-1]:
                # Bullish crossover
                strength = min(1.0, abs(macd_line[i] - signal_line[i]) / abs(signal_line[i]) * 5)
                signals.append(TrendSignal(
                    signal_type="MACD_Crossover",
                    strength=strength,
                    direction="bullish",
                    indicator="MACD Above Signal",
                    explanation=f"MACD ({macd_line[i]:.4f}) crossed above Signal line ({signal_line[i]:.4f})",
                    value=macd_line[i] - signal_line[i]
                ))
            elif macd_line[i-1] >= signal_line[i-1] and macd_line[i] < signal_line[i] and macd_line[i-1] != signal_line[i-1]:
                # Bearish crossover
                strength = min(1.0, abs(signal_line[i] - macd_line[i]) / abs(macd_line[i]) * 5)
                signals.append(TrendSignal(
                    signal_type="MACD_Crossover",
                    strength=strength,
                    direction="bearish",
                    indicator="MACD Below Signal",
                    explanation=f"MACD ({macd_line[i]:.4f}) crossed below Signal line ({signal_line[i]:.4f})",
                    value=macd_line[i] - signal_line[i]
                ))
        
        # Check histogram for momentum
        if len(histogram) > 0:
            current_histogram = histogram[-1]
            if current_histogram > 0:
                strength = min(1.0, current_histogram / 0.5)
                signals.append(TrendSignal(
                    signal_type="MACD_Histogram",
                    strength=strength,
                    direction="bullish",
                    indicator="Positive Histogram",
                    explanation=f"MACD histogram is positive ({current_histogram:.4f}), indicating bullish momentum",
                    value=current_histogram
                ))
            elif current_histogram < 0:
                strength = min(1.0, abs(current_histogram) / 0.5)
                signals.append(TrendSignal(
                    signal_type="MACD_Histogram",
                    strength=strength,
                    direction="bearish",
                    indicator="Negative Histogram",
                    explanation=f"MACD histogram is negative ({current_histogram:.4f}), indicating bearish momentum",
                    value=current_histogram
                ))
        
        return signals
    
    def analyze_trend_strength(self, prices: List[float]) -> Dict[str, Any]:
        """
        Analyze the strength and direction of the current trend.
        
        Uses linear regression to determine trend direction and strength.
        R-squared value indicates trend reliability.
        
        Args:
            prices: List of closing prices
            
        Returns:
            Dictionary containing trend analysis results
        """
        if len(prices) < 10:
            return {
                "trend_direction": "neutral",
                "trend_strength": 0.0,
                "r_squared": 0.0,
                "slope": 0.0,
                "explanation": "Insufficient data for trend analysis"
            }
        
        # Linear regression to find trend
        x = np.arange(len(prices))
        y = np.array(prices)
        
        # Calculate regression coefficients
        coeffs = np.polyfit(x, y, 1)
        slope = coeffs[0]
        
        # Calculate R-squared
        y_pred = np.polyval(coeffs, x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        
        # Determine trend direction
        if slope > 0.01:
            trend_direction = "uptrend"
        elif slope < -0.01:
            trend_direction = "downtrend"
        else:
            trend_direction = "neutral"
        
        # Calculate trend strength based on slope and R-squared
        trend_strength = min(1.0, abs(slope) / np.mean(prices) * 100 * r_squared)
        
        return {
            "trend_direction": trend_direction,
            "trend_strength": trend_strength,
            "r_squared": r_squared,
            "slope": slope,
            "explanation": f"Trend direction: {trend_direction}, strength: {trend_strength:.2f}, R²: {r_squared:.2f}"
        }
    
    def calculate_volatility(self, prices: List[float], period: int = 20) -> float:
        """
        Calculate price volatility using standard deviation.
        
        Higher volatility indicates higher risk and uncertainty.
        
        Args:
            prices: List of closing prices
            period: Period for volatility calculation
            
        Returns:
            Volatility as a percentage
        """
        if len(prices) < period:
            return 0.0
        
        # Calculate daily returns
        returns = [prices[i] / prices[i-1] - 1 for i in range(1, len(prices))]
        
        # Calculate standard deviation of returns
        volatility = np.std(returns) * 100
        
        return volatility
    
    def assess_risk_level(self, volatility: float, trend_strength: float) -> str:
        """
        Assess risk level based on volatility and trend strength.
        
        Risk assessment considers:
        - Volatility: Higher volatility = higher risk
        - Trend strength: Weak trends = higher risk
        
        Args:
            volatility: Volatility percentage
            trend_strength: Trend strength (0-1)
            
        Returns:
            Risk level classification
        """
        if volatility > 5.0:
            return "HIGH"
        elif volatility > 2.5 or trend_strength < 0.3:
            return "MEDIUM"
        else:
            return "LOW"
    
    def calculate_confidence(self, signals: List[TrendSignal], trend_strength: float, r_squared: float) -> float:
        """
        Calculate confidence score based on signal consensus and evidence strength.
        
        Confidence factors:
        - Signal consensus: More signals in same direction = higher confidence
        - Signal strength: Stronger signals = higher confidence
        - Trend reliability: Higher R-squared = higher confidence
        - Number of signals: More signals = higher confidence
        
        Args:
            signals: List of trend signals
            trend_strength: Trend strength (0-1)
            r_squared: R-squared value from trend analysis
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not signals:
            return 0.0
        
        # Calculate signal consensus
        bullish_signals = [s for s in signals if s.direction == "bullish"]
        bearish_signals = [s for s in signals if s.direction == "bearish"]
        
        total_signals = len(signals)
        consensus_score = 0.0
        bullish_count = len(bullish_signals)
        bearish_count = len(bearish_signals)
        
        if bullish_count > bearish_count:
            consensus_score = bullish_count / total_signals
        elif bearish_count > bullish_count:
            consensus_score = bearish_count / total_signals
        else:
            consensus_score = 0.5  # Neutral consensus
        
        # Calculate average signal strength
        avg_signal_strength = np.mean([s.strength for s in signals])
        
        # Combine factors for confidence
        confidence = (
            0.4 * consensus_score +      # 40% weight on consensus
            0.3 * avg_signal_strength +   # 30% weight on signal strength
            0.2 * trend_strength +         # 20% weight on trend strength
            0.1 * r_squared               # 10% weight on trend reliability
        )
        
        return min(1.0, max(0.0, confidence))
    
    def generate_recommendation(self, signals: List[TrendSignal], trend_analysis: Dict[str, Any], volatility: float) -> Tuple[Recommendation, str]:
        """
        Generate final recommendation based on all signals and analysis.
        
        Decision Logic:
        - BUY: Multiple bullish signals, strong uptrend, low volatility
        - HOLD: Mixed signals, neutral trend, moderate volatility
        - SELL: Multiple bearish signals, downtrend, high volatility
        
        Args:
            signals: List of trend signals
            trend_analysis: Trend analysis results
            volatility: Volatility percentage
            
        Returns:
            Tuple of (Recommendation, reasoning)
        """
        bullish_signals = [s for s in signals if s.direction == "bullish"]
        bearish_signals = [s for s in signals if s.direction == "bearish"]
        
        total_signals = len(signals)
        trend_direction = trend_analysis["trend_direction"]
        trend_strength = trend_analysis["trend_strength"]
        
        # Generate reasoning
        reasoning_parts = []
        
        # Count signals
        if total_signals > 0:
            reasoning_parts.append(f"Found {total_signals} technical signals")
            reasoning_parts.append(f"Bullish: {len(bullish_signals)}, Bearish: {len(bearish_signals)}")
        
        # Add trend analysis
        reasoning_parts.append(f"Trend direction: {trend_direction}")
        reasoning_parts.append(f"Trend strength: {trend_strength:.2f}")
        reasoning_parts.append(f"Volatility: {volatility:.2f}%")
        
        # Decision logic
        if (len(bullish_signals) >= 2 and 
            trend_direction in ["uptrend"] and 
            volatility < 3.0 and
            trend_strength > 0.5):
            recommendation = Recommendation.BUY
            reasoning_parts.append("Strong bullish consensus with uptrend and low volatility")
        
        elif (len(bearish_signals) >= 2 and 
              trend_direction in ["downtrend"] and
              volatility > 2.0):
            recommendation = Recommendation.SELL
            reasoning_parts.append("Strong bearish consensus with downtrend and high volatility")
        
        elif (len(bullish_signals) == len(bearish_signals) or 
              trend_direction == "neutral" or
              volatility > 4.0):
            recommendation = Recommendation.HOLD
            reasoning_parts.append("Mixed signals or high uncertainty")
        
        elif len(bullish_signals) > len(bearish_signals):
            recommendation = Recommendation.BUY
            reasoning_parts.append("Bullish bias with moderate signals")
        
        elif len(bearish_signals) > len(bullish_signals):
            recommendation = Recommendation.SELL
            reasoning_parts.append("Bearish bias with moderate signals")
        
        else:
            recommendation = Recommendation.HOLD
            reasoning_parts.append("Insufficient clear signals")
        
        return recommendation, ". ".join(reasoning_parts) + "."
    
    def predict_trend(self, symbol: str, historical_data: List[Dict[str, Any]]) -> PredictionResult:
        """
        Main prediction method that analyzes historical data and generates recommendation.
        
        Process:
        1. Extract closing prices from historical data
        2. Analyze technical indicators (MA, RSI, MACD)
        3. Analyze trend strength and direction
        4. Calculate volatility and risk
        5. Generate recommendation with confidence
        6. Provide detailed reasoning
        
        Args:
            symbol: Stock symbol
            historical_data: Historical price data with OHLCV
            
        Returns:
            PredictionResult with recommendation and analysis
        """
        if len(historical_data) < self.min_data_points:
            return PredictionResult(
                symbol=symbol,
                recommendation=Recommendation.HOLD,
                confidence=0.0,
                reasoning=f"Insufficient data: only {len(historical_data)} data points (minimum {self.min_data_points} required)",
                signals=[],
                technical_summary={},
                risk_level="UNKNOWN",
                prediction_date=datetime.now()
            )
        
        # Extract closing prices
        prices = [float(item["close"]) for item in historical_data]
        
        # Analyze technical indicators
        ma_signals = self.analyze_ma_crossovers(prices)
        rsi_signals = self.analyze_rsi_signals(prices)
        macd_signals = self.analyze_macd_signals(prices)
        
        # Combine all signals
        all_signals = ma_signals + rsi_signals + macd_signals
        
        # Analyze trend
        trend_analysis = self.analyze_trend_strength(prices)
        
        # Calculate volatility
        volatility = self.calculate_volatility(prices)
        
        # Assess risk level
        risk_level = self.assess_risk_level(volatility, trend_analysis["trend_strength"])
        
        # Calculate confidence
        confidence = self.calculate_confidence(all_signals, trend_analysis["trend_strength"], trend_analysis["r_squared"])
        
        # Generate recommendation
        recommendation, reasoning = self.generate_recommendation(all_signals, trend_analysis, volatility)
        
        # Create technical summary
        technical_summary = {
            "trend_direction": trend_analysis["trend_direction"],
            "trend_strength": trend_analysis["trend_strength"],
            "volatility": volatility,
            "risk_level": risk_level,
            "signal_count": {
                "total": len(all_signals),
                "bullish": len([s for s in all_signals if s.direction == "bullish"]),
                "bearish": len([s for s in all_signals if s.direction == "bearish"])
            },
            "indicators": {
                "ma_crossovers": len(ma_signals),
                "rsi_signals": len(rsi_signals),
                "macd_signals": len(macd_signals)
            }
        }
        
        return PredictionResult(
            symbol=symbol,
            recommendation=recommendation,
            confidence=confidence,
            reasoning=reasoning,
            signals=all_signals,
            technical_summary=technical_summary,
            risk_level=risk_level,
            prediction_date=datetime.now()
        )
