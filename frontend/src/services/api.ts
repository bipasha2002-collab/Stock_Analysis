const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface TrendingStock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  market_cap: string;
  sector?: string;
  currency?: string;
  exchange?: string;
}

export interface StockDetails {
  symbol: string;
  name: string;
  price?: number;
  current_price: number;
  previous_close: number;
  change: number;
  change_percent: number;
  volume: number;
  market_cap: string;
  day_high: number;
  day_low: number;
  week_52_high?: number;
  week_52_low?: number;
  pe_ratio?: number;
  dividend_yield?: number;
  sector?: string;
  currency?: string;
  exchange?: string;
  updated_at: string;
}

export interface StockSearchResult {
  symbol: string;
  name: string;
  exchange?: string;
  type?: string;
}

export interface StockHistory {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface NewsArticle {
  id: number;
  title: string;
  summary: string;
  content: string;
  source: string;
  author: string;
  url: string;
  published_at: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  sentiment_score: number;
  relevance_score: number;
  tags: string[];
}

export interface NewsResponse {
  status: string;
  symbol: string;
  articles: NewsArticle[];
  summary: {
    total_articles: number;
    overall_sentiment: string;
    average_sentiment_score: number;
    sentiment_distribution: {
      positive: number;
      negative: number;
      neutral: number;
    };
  };
  updated_at: string;
}

export interface ApiResponse<T> {
  status: string;
  data?: T;
  message?: string;
  error?: string;
}

export const api = {
  async getTrendingStocks(): Promise<ApiResponse<TrendingStock[]>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/stocks/trending`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch trending stocks: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  },

  async predictTrend(symbol: string, days: number = 30): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/v1/trends/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        symbol: symbol.toUpperCase(),
        days,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch trend prediction: ${response.status} ${response.statusText}`);
    }

    return response.json();
  },

  async searchStocks(query: string, limit: number = 10): Promise<ApiResponse<{ query: string; results: StockSearchResult[]; total: number }>> {
    const qs = new URLSearchParams({ q: query, limit: String(limit) });
    const response = await fetch(`${API_BASE_URL}/api/v1/stocks/search?${qs.toString()}`);

    if (!response.ok) {
      throw new Error(`Failed to search stocks: ${response.status} ${response.statusText}`);
    }

    return response.json();
  },

  async getStockDetails(symbol: string): Promise<ApiResponse<StockDetails>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/stocks/${symbol.toUpperCase()}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch stock details: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  },

  async getStockHistory(symbol: string, period: string = '1mo'): Promise<ApiResponse<{symbol: string; period: string; data: StockHistory[]; total_points: number}>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/stocks/${symbol.toUpperCase()}/history?period=${period}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch stock history: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  },

  async getStockNews(symbol: string, limit: number = 10): Promise<NewsResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/news/${symbol.toUpperCase()}?limit=${limit}`, {
      cache: 'no-store',
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch stock news: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  },

  async getMarketNews(limit: number = 20): Promise<ApiResponse<{articles: NewsArticle[]; total: number}>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/news/market/latest?limit=${limit}`, {
      cache: 'no-store',
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch market news: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  },

  async getStockSentiment(symbol: string): Promise<ApiResponse<{symbol: string; sentiment: string; sentiment_score: number; confidence: number; analysis: string}>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/news/${symbol.toUpperCase()}/sentiment`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch stock sentiment: ${response.status} ${response.statusText}`);
    }
    
    return response.json();
  },

  async healthCheck(): Promise<{ status: string; service: string }> {
    const response = await fetch(`${API_BASE_URL}/health`);
    
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }
    
    return response.json();
  }
};
