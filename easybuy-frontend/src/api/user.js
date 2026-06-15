import request from './request'

export const login = (data) => {
  return request({
    url: '/api/user/login',
    method: 'POST',
    data
  })
}

export const register = (data) => {
  return request({
    url: '/api/user/register',
    method: 'POST',
    data
  })
}

export const getUserInfo = () => {
  return request({
    url: '/api/user/info',
    method: 'GET'
  })
}
