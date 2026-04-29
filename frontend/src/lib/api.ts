import { PredictionResponse } from '@/types/prediction';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export type DemoStock = {
  symbol: string;
  name: string;
  sector?: string;
  market_cap?: string;
  description?: string;
};

export const api = {
  async getPrediction(symbol: string): Promise<PredictionResponse> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/predictions/${symbol.toUpperCase()}`
    );

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  },

  async getDemoStocks(): Promise<{ stocks: DemoStock[] }> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/demo/stocks`
    );

    if (!response.ok) {
      throw new Error(`Demo stocks fetch failed: ${response.status}`);
    }

    return response.json();
  },

  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${API_BASE_URL}/health`);

    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    return response.json();
  }
};
