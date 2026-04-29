'use client';

import { useRef, useState, useEffect } from 'react';
import { api, type StockDetails } from '@/services/api';
import { StockChart } from '@/components/StockChart';

interface StockDetailsProps {
  symbol: string | null;
}

export function StockDetails({ symbol }: StockDetailsProps) {
  const [stockData, setStockData] = useState<StockDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const latestPriceRef = useRef<number>(0);

  const [showChart, setShowChart] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [historyData, setHistoryData] = useState<{ date: string; close: number }[]>([]);

  const fetchStockDetails = async (sym: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.getStockDetails(sym);

      if (response.status === 'success' && response.data) {
        setStockData(response.data);
      } else {
        setError('Failed to load stock details');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!symbol) {
      setStockData(null);
      setError(null);
      setShowChart(false);
      setHistoryError(null);
      setHistoryData([]);
      return;
    }

    // Clear chart data when switching symbols so we don't show stale charts.
    setHistoryError(null);
    setHistoryData([]);

    fetchStockDetails(symbol);
  }, [symbol]);

  useEffect(() => {
    const displayPrice = typeof stockData?.current_price === 'number'
      ? stockData.current_price
      : (typeof stockData?.price === 'number' ? stockData.price : 0);

    if (displayPrice > 0) {
      latestPriceRef.current = displayPrice;
    }
  }, [stockData]);

  const buildMockHistory = (days: number = 30) => {
    const base = latestPriceRef.current > 0 ? latestPriceRef.current : 150;
    const now = new Date();

    const points: { date: string; close: number }[] = [];
    let price = base * 0.92;
    for (let i = days - 1; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(now.getDate() - i);

      // Gentle random walk with a slight drift.
      const drift = 0.0008;
      const noise = (Math.sin(i * 1.7) + Math.cos(i * 0.9)) * 0.002;
      price = price * (1 + drift + noise);

      points.push({
        date: d.toISOString().slice(0, 10),
        close: Number(price.toFixed(2)),
      });
    }
    return points;
  };

  useEffect(() => {
    if (!symbol || !showChart) return;

    let cancelled = false;
    const fetchHistory = async () => {
      try {
        setHistoryLoading(true);
        setHistoryError(null);
        const resp = await api.getStockHistory(symbol, '1mo');
        const points = resp.data?.data || [];
        const mapped = points
          .filter((p) => typeof p.close === 'number' && !!p.date)
          .map((p) => ({ date: p.date, close: p.close }));

        if (!cancelled) {
          setHistoryData(mapped.length > 0 ? mapped : buildMockHistory(30));
        }
      } catch (e) {
        if (!cancelled) {
          setHistoryError(e instanceof Error ? e.message : 'Failed to load chart');
          setHistoryData(buildMockHistory(30));
        }
      } finally {
        if (!cancelled) setHistoryLoading(false);
      }
    };

    fetchHistory();
    return () => {
      cancelled = true;
    };
  }, [symbol, showChart]);

  if (!symbol) {
    return (
      <div className="bg-[rgb(var(--charcoal))] rounded-xl shadow p-6 card-hover will-change-transform border border-white/10">
        <h2 className="text-lg font-semibold text-white mb-4">Stock Details</h2>
        <div className="text-center py-8 text-[rgb(var(--blue-gray))]">
          <div className="text-lg">Select a stock to view details</div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-[rgb(var(--charcoal))] rounded-xl shadow p-6 card-hover will-change-transform border border-white/10">
        <h2 className="text-lg font-semibold text-white mb-4">Stock Details</h2>
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
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[rgb(var(--charcoal))] rounded-xl shadow p-6 card-hover will-change-transform border border-white/10">
        <h2 className="text-lg font-semibold text-white mb-4">Stock Details</h2>
        <div className="text-center py-8">
          <div className="text-[rgb(var(--soft-red))] mb-2">⚠️ {error}</div>
          <button 
            onClick={() => symbol && fetchStockDetails(symbol)}
            className="px-4 py-2 bg-white/5 text-white rounded-lg hover:bg-white/10 active:bg-white/15 transition-colors text-sm border border-white/10"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!stockData) {
    return (
      <div className="bg-[rgb(var(--charcoal))] rounded-xl shadow p-6 card-hover will-change-transform border border-white/10">
        <h2 className="text-lg font-semibold text-white mb-4">Stock Details</h2>
        <div className="text-center py-8 text-[rgb(var(--blue-gray))]">
          <div className="text-lg">No data available</div>
        </div>
      </div>
    );
  }

  const displayPrice = typeof stockData.current_price === 'number'
    ? stockData.current_price
    : (typeof stockData.price === 'number' ? stockData.price : 0);

  const isGain = stockData.change >= 0;
  const changeArrow = isGain ? '▲' : '▼';
  const changeText = isGain ? 'text-[rgb(var(--sage))]' : 'text-[rgb(var(--soft-red))]';
  const changePill = isGain ? 'bg-[rgba(var(--sage),0.18)] text-[rgb(var(--sage))]' : 'bg-[rgba(var(--soft-red),0.18)] text-[rgb(var(--soft-red))]';

  return (
    <div className="bg-[rgb(var(--charcoal))] rounded-xl shadow p-6 card-hover will-change-transform fade-in border border-white/10">
      <h2 className="text-lg font-semibold text-white mb-4">Stock Details</h2>
      
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xl font-bold text-white">{stockData.symbol}</h3>
          <span className={`px-2 py-1 rounded-full text-sm font-medium border border-white/10 ${changePill}`}>
            <span className="mr-1">{changeArrow}</span>
            {Math.abs(stockData.change_percent).toFixed(2)}%
          </span>
        </div>
        <div className="text-sm text-[rgb(var(--blue-gray))] mb-4">{stockData.name}</div>
        
        <div className="text-3xl font-bold text-white mb-1">
          ${displayPrice.toFixed(2)}
        </div>
        <div className={`text-sm ${changeText}`}>
          {changeArrow} {Math.abs(stockData.change).toFixed(2)} ({Math.abs(stockData.change_percent).toFixed(2)}%)
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-white/5 p-4 rounded-xl border border-white/10">
          <div className="text-sm text-[rgb(var(--blue-gray))] mb-1">Volume</div>
          <div className="font-semibold text-white">
            {stockData.volume >= 1000000 
              ? `${(stockData.volume / 1000000).toFixed(1)}M` 
              : stockData.volume.toLocaleString()
            }
          </div>
        </div>
        <div className="bg-white/5 p-4 rounded-xl border border-white/10">
          <div className="text-sm text-[rgb(var(--blue-gray))] mb-1">Market Cap</div>
          <div className="font-semibold text-white">{stockData.market_cap}</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-white/5 p-4 rounded-xl border border-white/10">
          <div className="text-sm text-[rgb(var(--blue-gray))] mb-1">Day Range</div>
          <div className="font-semibold text-white">
            ${stockData.day_low.toFixed(2)} - ${stockData.day_high.toFixed(2)}
          </div>
        </div>
        <div className="bg-white/5 p-4 rounded-xl border border-white/10">
          <div className="text-sm text-[rgb(var(--blue-gray))] mb-1">Previous Close</div>
          <div className="font-semibold text-white">
            ${stockData.previous_close.toFixed(2)}
          </div>
        </div>
      </div>

      {(typeof stockData.pe_ratio === 'number' || typeof stockData.dividend_yield === 'number') && (
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="bg-white/5 p-4 rounded-xl border border-white/10">
            <div className="text-sm text-[rgb(var(--blue-gray))] mb-1">P/E Ratio</div>
            <div className="font-semibold text-white">
              {typeof stockData.pe_ratio === 'number' ? stockData.pe_ratio.toFixed(2) : 'N/A'}
            </div>
          </div>
          <div className="bg-white/5 p-4 rounded-xl border border-white/10">
            <div className="text-sm text-[rgb(var(--blue-gray))] mb-1">Dividend Yield</div>
            <div className="font-semibold text-white">
              {typeof stockData.dividend_yield === 'number' ? `${stockData.dividend_yield.toFixed(2)}%` : 'N/A'}
            </div>
          </div>
        </div>
      )}

      <div className="mt-6 pt-6 border-t border-white/10">
        <div className="text-sm text-[rgb(var(--blue-gray))] mb-3">Quick Actions</div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowChart((v) => !v)}
            className="px-4 py-2 bg-white/5 text-white rounded-lg hover:bg-white/10 active:bg-white/15 transition-all hover:-translate-y-0.5 hover:shadow-md text-sm border border-white/10"
          >
            {showChart ? 'Hide Chart' : 'View Chart'}
          </button>
        </div>
      </div>

      {showChart && (
        <div className="mt-6 pt-6 border-t">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm font-medium text-white">Price History (1M)</div>
            {historyLoading && <div className="text-xs text-[rgb(var(--blue-gray))]">Loading…</div>}
          </div>

          {historyError && (
            <div className="text-sm text-[rgb(var(--soft-red))] mb-3">⚠️ {historyError}</div>
          )}

          {historyLoading && (
            <div className="h-[300px] rounded-xl border border-white/10 bg-white/5 overflow-hidden">
              <div className="h-full w-full loading-shimmer" />
            </div>
          )}

          {!historyLoading && historyData.length > 0 && <StockChart data={historyData} />}
        </div>
      )}
    </div>
  );
}
