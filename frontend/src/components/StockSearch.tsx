/* eslint-disable react-hooks/exhaustive-deps */

'use client';

import { useEffect, useMemo, useRef, useState } from "react";
import { api, type StockSearchResult } from "@/services/api";

interface StockSearchProps {
  onStockSelect: (symbol: string) => void;
}

export function StockSearch({ onStockSelect }: StockSearchProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<StockSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const lastRequestIdRef = useRef(0);

  const trimmedQuery = useMemo(() => query.trim(), [query]);

  const handleSelect = (symbol: string) => {
    const sym = symbol.trim().toUpperCase();
    if (!sym) return;
    onStockSelect(sym);
    setQuery(sym);
    setOpen(false);
  };

  useEffect(() => {
    let cancelled = false;
    const requestId = ++lastRequestIdRef.current;

    const run = async () => {
      if (trimmedQuery.length < 1) {
        setResults([]);
        setError(null);
        setLoading(false);
        return;
      }

      setLoading(true);

      try {
        setError(null);
        const resp = await api.searchStocks(trimmedQuery, 10);
        if (!cancelled && requestId === lastRequestIdRef.current) {
          setResults(resp.data?.results || []);
          setOpen(true);
        }
      } catch (e) {
        if (!cancelled && requestId === lastRequestIdRef.current) {
          setError(e instanceof Error ? e.message : "Failed to search stocks");
          setResults([]);
          setOpen(true);
        }
      } finally {
        if (!cancelled && requestId === lastRequestIdRef.current) setLoading(false);
      }
    };

    // Debounce: gives a smoother autocomplete experience.
    const timer = setTimeout(() => {
      if (!cancelled) {
        run();
      }
    }, 180);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [trimmedQuery]);

  return (
    <div className="bg-[rgb(var(--charcoal))] rounded-lg shadow p-6 card-hover will-change-transform border border-white/10">
      <h2 className="text-lg font-semibold text-white mb-4">Stock Search</h2>

      <div className="relative">
        <div className="flex gap-3">
          <input
            type="text"
            autoComplete="off"
            spellCheck={false}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setOpen(true)}
            onBlur={() => {
              setTimeout(() => setOpen(false), 120);
            }}
            placeholder="Search by symbol or company (AAPL, Tesla, Reliance...)"
            className="flex-1 px-4 py-3 border border-white/10 rounded-lg text-lg bg-[rgba(0,0,0,0.22)] text-white placeholder:text-[rgba(var(--blue-gray),0.9)] caret-[rgb(var(--blue-gray))] focus:outline-none focus:ring-2 focus:ring-[rgba(var(--blue-gray),0.35)] focus:border-[rgba(var(--blue-gray),0.35)] transition-shadow"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                if (results.length > 0) {
                  handleSelect(results[0].symbol);
                } else {
                  handleSelect(query);
                }
              }
              if (e.key === 'Escape') {
                setOpen(false);
              }
            }}
          />

          <button
            onClick={() => handleSelect(query)}
            className="px-6 py-3 bg-[rgba(var(--sage),0.18)] text-white rounded-lg hover:bg-[rgba(var(--sage),0.26)] active:bg-[rgba(var(--sage),0.32)] transition-colors font-medium border border-white/10"
          >
            {loading ? 'Searching…' : 'Search'}
          </button>
        </div>

        {open && (loading || error || results.length > 0 || trimmedQuery.length > 0) && (
          <div className="absolute z-10 mt-2 w-full bg-[rgb(var(--charcoal))] border border-white/10 rounded-lg shadow-lg overflow-hidden origin-top transition-all will-change-transform">
            {error && (
              <div className="px-4 py-3 text-sm text-[rgb(var(--soft-red))]">
                {error}
              </div>
            )}

            {!error && loading && (
              <div className="px-4 py-3 text-sm text-[rgb(var(--blue-gray))]">Searching…</div>
            )}

            {false && (
              <div className="px-4 py-3 text-sm text-[rgb(var(--blue-gray))]">
                No matches. Press Enter to search "{trimmedQuery.toUpperCase()}".
              </div>
            )}

            {!error && !loading && results.length > 0 && (
              <div className="max-h-72 overflow-auto">
                {results.map((r) => (
                  <button
                    key={`${r.symbol}-${r.exchange || ''}-${r.type || ''}`}
                    type="button"
                    onClick={() => handleSelect(r.symbol)}
                    className="w-full text-left px-4 py-3 hover:bg-white/5 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="font-semibold text-white">{r.symbol}</div>
                      <div className="text-xs text-[rgb(var(--blue-gray))]">{r.exchange || r.type || ''}</div>
                    </div>
                    <div className="text-sm text-[rgba(var(--blue-gray),0.9)] truncate">{r.name}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
