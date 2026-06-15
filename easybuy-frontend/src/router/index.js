import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/products'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false, title: '用户登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { requiresAuth: false, title: '用户注册' }
  },
  {
    path: '/products',
    name: 'Products',
    component: () => import('@/views/ProductList.vue'),
    meta: { requiresAuth: true, title: '商品列表' }
  },
  {
    path: '/order/create',
    name: 'OrderCreate',
    component: () => import('@/views/OrderCreate.vue'),
    meta: { requiresAuth: true, title: '创建订单' }
  },
  {
    path: '/orders',
    name: 'Orders',
    component: () => import('@/views/OrderList.vue'),
    meta: { requiresAuth: true, title: '我的订单' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { requiresAuth: false, title: '404 Not Found' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('token')
  const requiresAuth = to.meta.requiresAuth

  if (requiresAuth && !token) {
    next({
      path: '/login',
      query: { redirect: to.fullPath }
    })
    return
  }

  if ((to.path === '/login' || to.path === '/register') && token) {
    next('/products')
    return
  }

  if (to.meta.title) {
    document.title = `${to.meta.title} - 易购商城`
  }

  next()
})

export default router
