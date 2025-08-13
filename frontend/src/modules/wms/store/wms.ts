import { create } from 'zustand';
import { Location, StockLocation, CountSession } from '../api/wms';

interface WMSState {
  selectedWarehouse: string;
  locations: Location[];
  stockLocations: StockLocation[];
  countSessions: CountSession[];
  loading: boolean;
  error: string | null;
  
  setSelectedWarehouse: (warehouse: string) => void;
  setLocations: (locations: Location[]) => void;
  setStockLocations: (stockLocations: StockLocation[]) => void;
  setCountSessions: (sessions: CountSession[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useWMSStore = create<WMSState>((set) => ({
  selectedWarehouse: '01',
  locations: [],
  stockLocations: [],
  countSessions: [],
  loading: false,
  error: null,
  
  setSelectedWarehouse: (warehouse) => set({ selectedWarehouse: warehouse }),
  setLocations: (locations) => set({ locations }),
  setStockLocations: (stockLocations) => set({ stockLocations }),
  setCountSessions: (countSessions) => set({ countSessions }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
}));
