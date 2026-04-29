import { useState, useCallback } from 'react';
import { PredictionResponse, PredictionState } from '@/types/prediction';
import { api } from '@/lib/api';

export const usePrediction = () => {
  const [state, setState] = useState<PredictionState>({
    prediction: null,
    loading: false,
    error: null,
  });

  const getPrediction = useCallback(async (symbol: string) => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const prediction = await api.getPrediction(symbol);
      setState({
        prediction,
        loading: false,
        error: null,
      });
      return prediction;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch prediction';
      setState(prev => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
      throw error;
    }
  }, []);

  const clearPrediction = useCallback(() => {
    setState({
      prediction: null,
      loading: false,
      error: null,
    });
  }, []);

  return {
    ...state,
    getPrediction,
    clearPrediction,
  };
};
