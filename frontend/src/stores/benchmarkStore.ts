import { create } from 'zustand';

import {
  type BenchmarkRecord,
  type BenchmarkSummary,
  type FailureInsight,
  type LiveRun,
  type Recommendation,
  type RunBenchmarkSuiteResponse
} from '@/types/benchmarks';
import { runBenchmarkSuite } from '@/lib/api';

type BenchmarkStore = {
  benchmarks: BenchmarkRecord[];
  filteredBenchmarks: BenchmarkRecord[];
  summary: BenchmarkSummary;
  liveRuns: LiveRun[];
  failureInsights: FailureInsight[];
  recommendations: Recommendation[];
  loading: boolean;
  error?: string;
  filterText: string;
  fetchBenchmarks: (suite?: string) => Promise<void>;
  setFilterText: (value: string) => void;
};

const initialSummary: BenchmarkSummary = {
  total: 0,
  success: 0,
  failed: 0
};

export const useBenchmarkStore = create<BenchmarkStore>((set, get) => ({
  benchmarks: [],
  filteredBenchmarks: [],
  summary: initialSummary,
  liveRuns: [],
  failureInsights: [],
  recommendations: [],
  loading: false,
  filterText: '',
  async fetchBenchmarks(suite?: string) {
    set({ loading: true, error: undefined });
    try {
      const data: RunBenchmarkSuiteResponse = await runBenchmarkSuite(suite);

      if (data.message) {
        set({
          loading: false,
          error: data.message,
          benchmarks: [],
          filteredBenchmarks: [],
          summary: initialSummary,
          liveRuns: [],
          failureInsights: [],
          recommendations: []
        });
        return;
      }

      const filter = get().filterText.toLowerCase();
      const filteredBenchmarks = filter
        ? data.benchmarks.filter((record) => record.name.toLowerCase().includes(filter))
        : data.benchmarks;

      set({
        benchmarks: data.benchmarks,
        filteredBenchmarks,
        summary: data.summary,
        liveRuns: data.liveRuns,
        failureInsights: data.failureInsights,
        recommendations: data.recommendations,
        loading: false,
        error: undefined
      });
    } catch (error) {
      set({
        loading: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  },
  setFilterText(value) {
    const filter = value.toLowerCase();
    const filteredBenchmarks = get().benchmarks.filter((record) =>
      record.name.toLowerCase().includes(filter)
    );

    set({ filterText: value, filteredBenchmarks });
  }
}));
