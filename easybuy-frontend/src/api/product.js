import request from './request'

export const getProductList = (params) => {
  return request({
    url: '/api/product/list',
    method: 'GET',
    params
  })
}

export const getProductDetail = (id) => {
  return request({
    url: `/api/product/detail/${id}`,
    method: 'GET'
  })
}

export const addProduct = (data) => {
  return request({
    url: '/api/product/add',
    method: 'POST',
    data
  })
}
