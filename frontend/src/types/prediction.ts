export interface PredictionResponse {
  symbol: string;
  prediction: 'BUY' | 'HOLD' | 'SELL';
  confidence: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  sentiment_score: number;
  features: {
    avg_return: number;
    avg_volatility: number;
    sentiment: number;
  };
  generated_at: string;
  data_points: number;
  error?: string;
}

export interface PredictionState {
  prediction: PredictionResponse | null;
  loading: boolean;
  error: string | null;
}
