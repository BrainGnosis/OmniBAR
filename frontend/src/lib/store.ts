import { create } from 'zustand';

type StatusFilter = 'all' | 'passing' | 'failing';

type UIState = {
  devMode: boolean;
  setDevMode: (devMode: boolean) => void;
};

type FilterState = {
  status: StatusFilter;
  q: string;
  setStatus: (status: StatusFilter) => void;
  setQuery: (q: string) => void;
};

type SelectionState = {
  selectedBenchmarkId?: string;
  setSelectedBenchmarkId: (id?: string) => void;
};

type StoreState = UIState & FilterState & SelectionState;

export const useAppStore = create<StoreState>((set) => ({
  devMode: false,
  setDevMode: (devMode) => set({ devMode }),
  status: 'all',
  q: '',
  setStatus: (status) => set({ status }),
  setQuery: (q) => set({ q }),
  selectedBenchmarkId: undefined,
  setSelectedBenchmarkId: (id) => set({ selectedBenchmarkId: id }),
}));
