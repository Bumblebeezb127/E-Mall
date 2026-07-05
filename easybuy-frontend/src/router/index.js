import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/userStore'

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
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { requiresAuth: true, title: '个人中心' }
  },
  {
    path: '/admin',
    component: () => import('@/views/AdminLayout.vue'),
    meta: { requiresAuth: true, requiresAdmin: true, title: '管理控制台' },
    children: [
      { path: '', redirect: '/admin/products' },
      { path: 'products', name: 'admin-products', component: () => import('@/views/admin/AdminProducts.vue') },
      { path: 'inventory', name: 'admin-inventory', component: () => import('@/views/admin/AdminInventory.vue') },
      { path: 'users', name: 'admin-users', component: () => import('@/views/admin/AdminUsers.vue') },
      { path: 'orders', name: 'admin-orders', component: () => import('@/views/admin/AdminOrders.vue') },
      { path: 'logs', name: 'admin-logs', component: () => import('@/views/admin/AdminLogs.vue') }
    ]
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
  const userStore = useUserStore()
  const token = userStore.token
  const requiresAuth = to.meta.requiresAuth
  const requiresAdmin = to.meta.requiresAdmin

  // 1. 主动检查 token 是否过期 (避免带着过期 token 访问受保护页面)
  if (token && userStore.isTokenExpired()) {
    userStore.clearAuth()
    ElMessage?.warning?.('登录已过期，请重新登录')
    if (to.path !== '/login') {
      return next({ path: '/login', query: { redirect: to.fullPath } })
    }
  }

  // 2. 需要登录但没有 token (或 token 刚被清除)
  if (requiresAuth && !userStore.token) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  // 3. 需要 ADMIN 角色
  if (requiresAdmin) {
    const role = userStore.userInfo?.role
    if (role !== 'ADMIN' && role !== 'admin') {
      ElMessage?.error?.('该页面仅管理员可见')
      return next({ path: '/products' })
    }
  }

  // 4. 已登录访问 /login 或 /register
  if ((to.path === '/login' || to.path === '/register') && userStore.token) {
    return next('/products')
  }

  // 5. 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 易购商城`
  }

  next()
})

export default router
