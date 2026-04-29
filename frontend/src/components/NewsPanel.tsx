'use client';

import { useState, useEffect } from 'react';
import { api, type NewsArticle, type NewsResponse } from '@/services/api';

interface NewsPanelProps {
  symbol: string | null;
}

export function NewsPanel({ symbol }: NewsPanelProps) {
  const [news, setNews] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchNews = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = symbol
        ? await api.getStockNews(symbol, 5)
        : await api.getMarketNews(5);

      if (symbol) {
        const newsResponse = response as NewsResponse;
        if (newsResponse.status === 'success') {
          setNews(newsResponse.articles);
        } else {
          setNews([]);
          setError('Failed to load news');
        }
      } else {
        const marketResponse = response as any;
        if (marketResponse.status === 'success' && marketResponse.articles) {
          setNews(marketResponse.articles);
        } else {
          setNews([]);
          setError('Failed to load market news');
        }
      }
    } catch (err) {
      setNews([]);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNews();
  }, [symbol]);

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'bg-[rgba(var(--sage),0.18)] text-white border border-white/10';
      case 'negative': return 'bg-[rgba(var(--soft-red),0.18)] text-white border border-white/10';
      default: return 'bg-white/5 text-[rgb(var(--blue-gray))] border border-white/10';
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return '📈';
      case 'negative': return '📉';
      default: return '➡️';
    }
  };

  const formatTimeAgo = (publishedAt: string) => {
    const date = new Date(publishedAt);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    if (!Number.isFinite(diffMs) || diffMs < 0) return '';

    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes} minutes ago`;

    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours} hours ago`;

    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays} days ago`;
  };

  if (loading) {
    return (
      <div className="bg-[rgb(var(--charcoal))] rounded-lg shadow p-6 card-hover will-change-transform border border-white/10">
        <h2 className="text-lg font-semibold text-white mb-4">
          Market News {symbol && `- ${symbol}`}
        </h2>
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="border-b pb-3 last:border-b-0 last:pb-0">
              <div className="h-4 rounded w-3/4 mb-2 loading-shimmer"></div>
              <div className="h-3 rounded w-full mb-1 loading-shimmer"></div>
              <div className="h-3 rounded w-1/2 loading-shimmer"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[rgb(var(--charcoal))] rounded-lg shadow p-6 card-hover will-change-transform border border-white/10">
        <h2 className="text-lg font-semibold text-white mb-4">
          Market News {symbol && `- ${symbol}`}
        </h2>
        <div className="text-center py-8">
          <div className="text-[rgb(var(--soft-red))] mb-2">⚠️ {error}</div>
          <button 
            onClick={fetchNews}
            className="px-4 py-2 bg-white/5 text-white rounded-lg hover:bg-white/10 active:bg-white/15 transition-colors text-sm border border-white/10"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[rgb(var(--charcoal))] rounded-lg shadow p-6 card-hover will-change-transform fade-in border border-white/10">
      <h2 className="text-lg font-semibold text-white mb-4">
        Market News {symbol && `- ${symbol}`}
      </h2>
      
      <div className="space-y-3">
        {symbol && news.length === 0 && (
          <div className="text-sm text-[rgb(var(--blue-gray))] py-6 text-center">
            No recent news available for this stock.
          </div>
        )}

        {news.map((article) => (
          <div key={article.id} className="border-b pb-3 last:border-b-0 last:pb-0">
            <div className="flex items-start justify-between mb-2">
              <h3 className="font-medium text-white text-sm leading-tight flex-1">
                {article.title}
              </h3>
              <span className={`ml-2 px-2 py-1 rounded text-xs font-medium ${getSentimentColor(article.sentiment)}`}>
                {getSentimentIcon(article.sentiment)}
              </span>
            </div>
            
            <p className="text-sm text-[rgba(var(--blue-gray),0.92)] mb-2 line-clamp-2">
              {article.summary}
            </p>
            
            <div className="flex items-center justify-between text-xs text-[rgb(var(--blue-gray))]">
              <span>{article.source}</span>
              <span>{formatTimeAgo(article.published_at)}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t">
        <button className="w-full px-4 py-2 bg-white/5 text-[rgb(var(--blue-gray))] rounded-lg hover:bg-white/10 transition-colors text-sm font-medium border border-white/10">
          View All News
        </button>
      </div>
    </div>
  );
}
