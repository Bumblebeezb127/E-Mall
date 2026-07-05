import request from './request'

// ============== Products ==============
export const adminListProducts = (params) =>
  request({ url: '/api/product/admin/list', method: 'GET', params })

export const adminCreateProduct = (data) =>
  request({ url: '/api/product/admin/create', method: 'POST', data })

export const adminUpdateProduct = (id, data) =>
  request({ url: `/api/product/admin/update/${id}`, method: 'PUT', data })

export const adminDeleteProduct = (id) =>
  request({ url: `/api/product/admin/delete/${id}`, method: 'DELETE' })

// ============== Inventory ==============
export const adminListInventory = (params) =>
  request({ url: '/api/inventory/admin/list', method: 'GET', params })

export const adminInitInventory = (productId, stock) =>
  request({ url: '/api/inventory/admin/init', method: 'POST', params: { productId, stock } })

export const adminUpdateInventory = (productId, stock) =>
  request({ url: '/api/inventory/admin/update', method: 'PUT', params: { productId, stock } })

// ============== Users ==============
export const adminListUsers = (params) =>
  request({ url: '/api/user/admin/list', method: 'GET', params })

export const adminUpdateUserRole = (id, roleValue) =>
  request({ url: `/api/user/admin/role/${id}`, method: 'PUT', params: { roleValue } })

export const adminDeleteUser = (id) =>
  request({ url: `/api/user/admin/${id}`, method: 'DELETE' })

// ============== Orders ==============
export const adminListOrders = (params) =>
  request({ url: '/api/order/admin/list', method: 'GET', params })

export const adminOrderStats = () =>
  request({ url: '/api/order/admin/stats', method: 'GET' })

export const adminForceCancelOrder = (orderId) =>
  request({ url: `/api/order/admin/cancel/${orderId}`, method: 'PUT' })

export const adminForcePayOrder = (orderId) =>
  request({ url: `/api/order/admin/pay/${orderId}`, method: 'PUT' })

export const adminDeleteOrder = (orderId) =>
  request({ url: `/api/order/admin/delete/${orderId}`, method: 'DELETE' })

// ============== Logs ==============
export const adminListLogFiles = () =>
  request({ url: '/api/log/files', method: 'GET' })

export const adminTailLog = (file, lines = 200) =>
  request({ url: '/api/log/tail', method: 'GET', params: { file, lines } })

export const adminSearchLog = (file, keyword, max = 200) =>
  request({ url: '/api/log/search', method: 'GET', params: { file, keyword, max } })

export const adminLogDownloadUrl = (file) =>
  `/api/log/download?file=${encodeURIComponent(file)}`
