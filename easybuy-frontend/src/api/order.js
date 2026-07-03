import request from './request'

export const createOrder = (data) => {
  return request({
    url: '/api/order/create',
    method: 'POST',
    data
  })
}

export const getOrderList = (params) => {
  return request({
    url: '/api/order/list',
    method: 'GET',
    params
  })
}

export const getOrderDetail = (orderId, userId) => {
  return request({
    url: `/api/order/detail/${orderId}`,
    method: 'GET',
    params: { userId }
  })
}

export const cancelOrder = (orderId, userId) => {
  return request({
    url: `/api/order/cancel/${orderId}`,
    method: 'PUT',
    params: { userId }
  })
}

export const payOrder = (orderId, userId) => {
  return request({
    url: `/api/order/pay/${orderId}`,
    method: 'PUT',
    params: { userId }
  })
}
