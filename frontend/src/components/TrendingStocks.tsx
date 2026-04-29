'use client';

import { useState, useEffect } from 'react';
import { api, TrendingStock } from '@/services/api';

interface TrendingStocksProps {
  onStockSelect: (symbol: string) => void;
}

export function TrendingStocks({ onStockSelect }: TrendingStocksProps) {
  const [stocks, setStocks] = useState<TrendingStock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTrendingStocks = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.getTrendingStocks();

      if (response.status === 'success' && response.data) {
        setStocks(response.data);
      } else {
        setError('Failed to load trending stocks');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrendingStocks();
  }, []);

  /* =======================
     LOADING STATE
  ======================= */
  if (loading) {
    return (
      <div className="bg-[rgb(var(--charcoal))] rounded-xl shadow p-6 border border-white/10">
        <h2 className="text-lg font-semibold text-white mb-4">Trending Stocks</h2>
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="flex items-center justify-between p-3 border border-white/10 rounded-xl bg-white/5"
            >
              <div className="flex-1">
                <div className="h-4 w-20 mb-2 loading-shimmer rounded"></div>
                <div className="h-3 w-32 loading-shimmer rounded"></div>
              </div>
              <div className="text-right">
                <div className="h-4 w-16 mb-1 loading-shimmer rounded"></div>
                <div className="h-3 w-12 loading-shimmer rounded"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  /* =======================
     ERROR STATE
  ======================= */
  if (error) {
    return (
      <div className="bg-[rgb(var(--charcoal))] rounded-xl shadow p-6 border border-white/10">
        <h2 className="text-lg font-semibold text-white mb-4">Trending Stocks</h2>
        <div className="text-center py-8">
          <div className="text-[rgb(var(--soft-red))] mb-2">⚠️ {error}</div>
          <button
            onClick={fetchTrendingStocks}
            className="px-4 py-2 bg-white/5 text-white rounded-lg hover:bg-white/10 transition border border-white/10"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  /* =======================
     MAIN RENDER
  ======================= */
  return (
    <div className="bg-[rgb(var(--charcoal))] rounded-xl shadow p-6 border border-white/10 fade-in">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-white">Trending Stocks</h2>
        <span className="text-xs text-[rgb(var(--blue-gray))]">Tap to load</span>
      </div>

      <div className="space-y-3">
        {stocks.map((stock) => {
          const isGain = stock.change >= 0;
          const arrow = isGain ? '▲' : '▼';

          const pillClass = isGain
            ? 'bg-[rgba(var(--sage),0.18)] text-[rgb(var(--sage))]'
            : 'bg-[rgba(var(--soft-red),0.18)] text-[rgb(var(--soft-red))]';

          const deltaText = isGain
            ? 'text-[rgb(var(--sage))]'
            : 'text-[rgb(var(--soft-red))]';

          return (
            <div
              key={stock.symbol}
              onClick={() => onStockSelect(stock.symbol)}
              className="group flex items-center justify-between p-3 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-md"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-white">{stock.symbol}</span>
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium border border-white/10 ${pillClass}`}
                  >
                    {arrow} {Math.abs(stock.change_percent).toFixed(2)}%
                  </span>
                </div>
                <div className="text-sm text-[rgb(var(--blue-gray))] truncate max-w-[220px]">
                  {stock.name}
                </div>
              </div>

              <div className="text-right">
                <div className="font-semibold text-white">
                  ${stock.price.toFixed(2)}
                </div>
                <div className={`text-xs ${deltaText}`}>
                  {arrow} {Math.abs(stock.change).toFixed(2)}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
