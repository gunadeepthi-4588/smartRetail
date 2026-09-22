/**
 * SmartRetail Centralized API Client
 * Manages all REST communication between React and the Flask backend.
 * Never connects directly to MySQL — always routes through Flask REST APIs.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

export async function fetchApi(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    const data = await response.json();

    if (!response.ok) {
      const errorMessage = data.message || data.error || `HTTP Error ${response.status}`;
      throw new Error(errorMessage);
    }

    return data;
  } catch (error) {
    console.error(`[API Error] Request failed for ${url}:`, error.message);
    throw error;
  }
}

// -----------------------------------------------------------------------------
// Health Check APIs
// -----------------------------------------------------------------------------
export const getBackendHealth = () => fetchApi('/health');
export const getDbHealth = () => fetchApi('/health/db');

// -----------------------------------------------------------------------------
// Products APIs
// -----------------------------------------------------------------------------
export const getProducts = (params = {}) => {
  const query = new URLSearchParams();
  if (params.category && params.category !== 'All') query.append('category', params.category);
  if (params.search) query.append('search', params.search);
  if (params.supplier_id) query.append('supplier_id', params.supplier_id);
  
  const queryString = query.toString() ? `?${query.toString()}` : '';
  return fetchApi(`/products${queryString}`);
};

export const getProductById = (productId) => fetchApi(`/products/${productId}`);

// -----------------------------------------------------------------------------
// Inventory APIs
// -----------------------------------------------------------------------------
export const getInventory = (params = {}) => {
  const query = new URLSearchParams();
  if (params.status && params.status !== 'All') query.append('status', params.status);
  if (params.category && params.category !== 'All') query.append('category', params.category);
  if (params.search) query.append('search', params.search);

  const queryString = query.toString() ? `?${query.toString()}` : '';
  return fetchApi(`/inventory${queryString}`);
};

export const getInventoryByProductId = (productId) => fetchApi(`/inventory/${productId}`);

export const updateInventoryStock = (productId, stockData) => {
  return fetchApi(`/inventory/${productId}`, {
    method: 'PUT',
    body: JSON.stringify(stockData),
  });
};

// -----------------------------------------------------------------------------
// Sales & POS APIs
// -----------------------------------------------------------------------------
export const createSale = (saleData) => {
  return fetchApi('/sales', {
    method: 'POST',
    body: JSON.stringify(saleData),
  });
};

export const getSales = (params = {}) => {
  const query = new URLSearchParams();
  if (params.payment_method && params.payment_method !== 'All') query.append('payment_method', params.payment_method);
  if (params.receipt) query.append('receipt', params.receipt);
  if (params.limit) query.append('limit', params.limit);

  const queryString = query.toString() ? `?${query.toString()}` : '';
  return fetchApi(`/sales${queryString}`);
};

export const getSale = (saleId) => fetchApi(`/sales/${saleId}`);

// -----------------------------------------------------------------------------
// Analytics & Business Intelligence APIs
// -----------------------------------------------------------------------------
export const getAnalyticsDashboard = () => fetchApi('/analytics/dashboard');

export const getSalesTrend = (days = 30) => fetchApi(`/analytics/sales-trend?days=${days}`);

export const getTopProducts = (params = {}) => {
  const query = new URLSearchParams();
  if (params.days) query.append('days', params.days);
  if (params.limit) query.append('limit', params.limit);

  const queryString = query.toString() ? `?${query.toString()}` : '';
  return fetchApi(`/analytics/top-products${queryString}`);
};

export const getSlowMovers = (params = {}) => {
  const query = new URLSearchParams();
  if (params.days_threshold) query.append('days_threshold', params.days_threshold);

  const queryString = query.toString() ? `?${query.toString()}` : '';
  return fetchApi(`/analytics/slow-movers${queryString}`);
};

export const getCategoryPerformance = (params = {}) => {
  const query = new URLSearchParams();
  if (params.days) query.append('days', params.days);

  const queryString = query.toString() ? `?${query.toString()}` : '';
  return fetchApi(`/analytics/category-performance${queryString}`);
};

// -----------------------------------------------------------------------------
// Machine Learning Demand Forecasting APIs
// -----------------------------------------------------------------------------
export const generateForecast = (forecastData) => {
  return fetchApi('/forecast', {
    method: 'POST',
    body: JSON.stringify(forecastData),
  });
};

export const getForecasts = (params = {}) => {
  const query = new URLSearchParams();
  if (params.product_id) query.append('product_id', params.product_id);
  if (params.horizon_days) query.append('horizon_days', params.horizon_days);
  if (params.limit) query.append('limit', params.limit);

  const queryString = query.toString() ? `?${query.toString()}` : '';
  return fetchApi(`/forecast${queryString}`);
};

export const getProductForecast = (productId, horizonDays = 7) => {
  return fetchApi(`/forecast/${productId}?horizon_days=${horizonDays}`);
};

export const updateForecastActuals = () => {
  return fetchApi('/forecast/update-actuals', {
    method: 'POST',
  });
};
