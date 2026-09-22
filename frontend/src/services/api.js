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
