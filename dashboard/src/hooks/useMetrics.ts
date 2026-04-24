import { useQuery } from '@tanstack/react-query';
import { fetchOverview, fetchLatencyTimeseries, fetchTokenTimeseries, fetchDriftScores, fetchHallucinationScores } from '../api/client';

export function useOverview(window = '24h') {
  return useQuery({
    queryKey: ['overview', window],
    queryFn: () => fetchOverview(window),
  });
}

export function useLatency(bucket = '5m') {
  return useQuery({
    queryKey: ['latency', bucket],
    queryFn: () => fetchLatencyTimeseries({ bucket }),
  });
}

export function useTokens() {
  return useQuery({
    queryKey: ['tokens'],
    queryFn: () => fetchTokenTimeseries(),
  });
}

export function useDrift(modelName?: string) {
  return useQuery({
    queryKey: ['drift', modelName],
    queryFn: () => fetchDriftScores({ model_name: modelName }),
  });
}

export function useHallucinations() {
  return useQuery({
    queryKey: ['hallucinations'],
    queryFn: () => fetchHallucinationScores(),
  });
}
