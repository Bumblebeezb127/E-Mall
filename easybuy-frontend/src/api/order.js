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
