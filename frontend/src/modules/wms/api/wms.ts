import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1/wms`,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface Location {
  id: number;
  whs_code: string;
  code: string;
  name?: string;
  section?: string;
  aisle?: string;
  rack?: string;
  level?: string;
  bin?: string;
  type?: string;
  capacity_qty?: number;
  capacity_uom?: string;
  is_active: boolean;
}

export interface StockLocation {
  id: number;
  whs_code: string;
  location_id: number;
  item_code: string;
  item_name?: string;
  lot_no?: string;
  qty: number;
  uom?: string;
  last_updated: string;
}

export interface BulkGenerateRequest {
  pattern: string;
  type?: string;
  attributes?: Record<string, any>;
}

export interface MovementRequest {
  whs: string;
  lines: Array<{
    item: string;
    lot?: string;
    qty: number;
    toLocationId?: number;
    fromLocationId?: number;
  }>;
}

export interface CountSession {
  id: number;
  whs_code: string;
  status: string;
  created_by: string;
  created_at: string;
  closed_at?: string;
}

export const wmsApi = {
  locations: {
    bulkGenerate: (whs: string, request: BulkGenerateRequest) =>
      api.post(`/warehouses/${whs}/locations/bulk-generate`, request),
    
    getByWarehouse: (whs: string, params?: { code_like?: string; type?: string }) =>
      api.get(`/warehouses/${whs}/locations`, { params }),
    
    getById: (locationId: number) =>
      api.get(`/locations/${locationId}`),
    
    update: (locationId: number, data: Partial<Location>) =>
      api.put(`/locations/${locationId}`, data),
  },

  bins: {
    search: (params: { q: string; whs?: string; type?: string; limit?: number }) =>
      api.get('/bins/search', { params }),
    
    getCapacity: (binId: number) =>
      api.get(`/bins/${binId}/capacity`),
  },

  stock: {
    byLocation: (locationId: number) =>
      api.get(`/stock/by-location/${locationId}`),
    
    byItem: (whs: string, item: string) =>
      api.get('/stock/by-item', { params: { whs, item } }),
    
    summary: (whs: string, item: string) =>
      api.get('/stock/summary', { params: { whs, item } }),
    
    lowStock: (params?: { whs?: string; threshold_pct?: number }) =>
      api.get('/stock/low-stock', { params }),
  },

  movements: {
    putaway: (request: MovementRequest) =>
      api.post('/operations/putaway', request),
    
    issue: (request: any) =>
      api.post('/operations/issue', request),
    
    moveInternal: (request: any) =>
      api.post('/operations/move-internal', request),
    
    transferWarehouse: (request: any) =>
      api.post('/operations/transfer-warehouse', request),
  },

  counts: {
    create: (request: { whs: string; scope: any }) =>
      api.post('/counts', request),
    
    getById: (countId: number) =>
      api.get(`/counts/${countId}`),
    
    getDetails: (countId: number) =>
      api.get(`/counts/${countId}/details`),
    
    enterCounts: (countId: number, counts: Array<{ detailId: number; countedQty: number }>) =>
      api.put(`/counts/${countId}/enter`, counts),
    
    apply: (countId: number, request: { createSapAdjustments: boolean; comment?: string }) =>
      api.post(`/counts/${countId}/apply`, request),
    
    list: (params?: { whs?: string; status?: string; limit?: number }) =>
      api.get('/counts', { params }),
  },

  labels: {
    generate: (locationId: number, format: string = 'zpl') =>
      api.post(`/locations/${locationId}/label`, { locationId, format }),
    
    preview: (locationId: number, format: string = 'pdf') =>
      api.get(`/labels/preview/${locationId}`, { params: { format } }),
    
    listPrinters: () =>
      api.get('/labels/printers'),
  },

  picking: {
    getSuggestions: (params: { whs: string; item: string; qty: number; policy?: string }) =>
      api.get('/picking/suggestions', { params }),
    
    confirm: (request: any) =>
      api.post('/picking/confirm', request),
  },
};

export default wmsApi;
