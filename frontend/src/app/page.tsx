'use client';

import { useState, useEffect } from 'react';
import { StockSearch } from '@/components/StockSearch';
import { StockDetails } from '@/components/StockDetails';
import { TrendingStocks } from '@/components/TrendingStocks';
import { NewsPanel } from '@/components/NewsPanel';
import { api } from '@/services/api';

export default function Home() {
  const [selectedStock, setSelectedStock] = useState<string | null>(null);

  const selectSymbol = (symbol: string | null) => {
    if (!symbol) {
      setSelectedStock(null);
      return;
    }
    const sym = symbol.trim().toUpperCase();
    setSelectedStock(sym || null);
  };

  return (
    <div className="min-h-screen bg-[rgb(var(--deep-black))]">
      <header className="bg-[rgb(var(--deep-black))] shadow-sm border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-2xl font-bold text-white">Stock Analysis</h1>
            <p className="text-sm text-[rgb(var(--blue-gray))]">AI-powered market insights</p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column */}
          <div className="lg:col-span-2 space-y-6">
            <StockSearch onStockSelect={(s) => selectSymbol(s)} />

            <StockDetails symbol={selectedStock} />

            <div className="bg-[rgb(var(--charcoal))] rounded-xl shadow p-6 border border-white/10 card-hover will-change-transform">
              <h2 className="text-lg font-semibold text-white mb-4">Trend Prediction</h2>
              <TrendPrediction symbol={selectedStock} />
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-6">
            <TrendingStocks onStockSelect={(s) => selectSymbol(s)} />

            <NewsPanel symbol={selectedStock} />
          </div>
        </div>
      </main>
    </div>
  );
}
// Trend Prediction Component
function TrendPrediction({ symbol }: { symbol: string | null }) {
  const [prediction, setPrediction] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!symbol) {
      setPrediction(null);
      setError(null);
      return;
    }

    const fetchTrendPrediction = async () => {
      try {
        setLoading(true);
        setError(null);

        const data = await api.predictTrend(symbol, 30);
        setPrediction(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
        setPrediction(null);
      } finally {
        setLoading(false);
      }
    };

    fetchTrendPrediction();
  }, [symbol]);

  const getRecommendationPill = (recommendation: string) => {
    switch (recommendation) {
      case 'BUY':
        return {
          bg: 'bg-[rgba(var(--sage),0.18)]',
          text: 'text-[rgb(var(--sage))]',
          icon: '▲',
        };
      case 'SELL':
        return {
          bg: 'bg-[rgba(var(--soft-red),0.18)]',
          text: 'text-[rgb(var(--soft-red))]',
          icon: '▼',
        };
      default:
        return {
          bg: 'bg-white/5',
          text: 'text-[rgb(var(--blue-gray))]',
          icon: '●',
        };
    }
  };

  if (!symbol) {
    return (
      <div className="text-center py-8 text-[rgb(var(--blue-gray))]">
        <div className="text-lg">Select a stock to view trend prediction</div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse">
          <div className="h-8 rounded w-32 mb-2 loading-shimmer"></div>
          <div className="h-4 rounded w-48 mb-4 loading-shimmer"></div>
          <div className="h-12 rounded w-24 mb-2 loading-shimmer"></div>
          <div className="h-4 rounded w-32 loading-shimmer"></div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="h-16 rounded loading-shimmer"></div>
          <div className="h-16 rounded loading-shimmer"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <div className="text-[rgb(var(--soft-red))] mb-2">⚠️ {error}</div>
        <button 
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-white/5 text-white rounded-lg hover:bg-white/10 transition-colors text-sm border border-white/10"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!prediction) {
    return (
      <div className="text-center py-8 text-[rgb(var(--blue-gray))]">
        <div className="text-lg">No prediction available</div>
      </div>
    );
  }

  const recommendation = prediction.recommendation;
  const confidence = prediction.confidence || 0;
  const pill = getRecommendationPill(recommendation);

  return (
    <div className="space-y-6">
      {/* Main Recommendation Card */}
      <div className={`border border-white/10 rounded-xl p-6 bg-white/5`}>
        <div className="text-center">
          <div className="text-2xl font-bold mb-2 text-white">{prediction.symbol}</div>
          <div className="text-4xl font-bold mb-2 flex items-center justify-center gap-2 text-white">
            <span className={`${pill.text}`}>{pill.icon}</span>
            <span>{recommendation}</span>
          </div>
          <div className="text-lg text-[rgb(var(--blue-gray))] mb-4">
            Confidence: {(confidence * 100).toFixed(1)}%
          </div>
          <div className="text-sm text-[rgb(var(--blue-gray))]">
            Risk Level: <span className="text-white">{prediction.risk_level}</span>
          </div>
        </div>
      </div>

      {/* Technical Analysis */}
      <div className="bg-white/5 rounded-xl p-4 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-4">Technical Analysis</h3>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-[rgb(var(--blue-gray))]">Trend Direction</span>
            <span className="text-sm font-semibold text-white">
              {prediction.technical_summary?.trend_direction || 'N/A'}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-[rgb(var(--blue-gray))]">Trend Strength</span>
            <span className="text-sm font-semibold text-white">
              {prediction.technical_summary?.trend_strength ? 
                `${(prediction.technical_summary.trend_strength * 100).toFixed(1)}%` : 'N/A'}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-[rgb(var(--blue-gray))]">Volatility</span>
            <span className="text-sm font-semibold text-white">
              {prediction.technical_summary?.volatility ? 
                `${prediction.technical_summary.volatility.toFixed(2)}%` : 'N/A'}
            </span>
          </div>
        </div>
      </div>

      {/* Reasoning */}
      <div className="bg-white/5 rounded-xl p-4 border border-white/10">
        <h3 className="text-lg font-semibold text-white mb-2">Analysis Reasoning</h3>
        <p className="text-sm text-[rgb(var(--blue-gray))] leading-relaxed">
          {prediction.reasoning}
        </p>
      </div>

      {/* Technical Signals */}
      {prediction.signals && prediction.signals.length > 0 && (
        <div className="bg-white/5 rounded-xl p-4 border border-white/10">
          <h3 className="text-lg font-semibold text-white mb-4">Technical Signals</h3>
          <div className="space-y-2">
            {prediction.signals.map((signal: any, index: number) => (
              <div key={index} className="flex items-center justify-between p-2 bg-[rgb(var(--charcoal))] rounded-xl border border-white/10">
                <div className="flex-1">
                  <div className="text-sm font-medium text-white">{signal.indicator}</div>
                  <div className="text-xs text-[rgb(var(--blue-gray))]">{signal.explanation}</div>
                </div>
                <div className="text-right">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    signal.direction === 'bullish' ? 'bg-[rgba(var(--sage),0.18)] text-[rgb(var(--sage))] border border-white/10' : 
                    signal.direction === 'bearish' ? 'bg-[rgba(var(--soft-red),0.18)] text-[rgb(var(--soft-red))] border border-white/10' : 
                    'bg-white/5 text-[rgb(var(--blue-gray))] border border-white/10'
                  }`}>
                    {signal.direction === 'bullish' ? '▲ bullish' : signal.direction === 'bearish' ? '▼ bearish' : '● neutral'}
                  </span>
                  <div className="text-xs text-[rgb(var(--blue-gray))] mt-1">
                    {(signal.strength * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}