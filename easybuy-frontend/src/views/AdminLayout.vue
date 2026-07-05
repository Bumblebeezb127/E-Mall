<template>
  <div class="admin-layout">
    <el-container>
      <SideNav />
      <el-container>
        <el-header>
          <div class="header-content">
            <h2>{{ pageTitle }}</h2>
            <span class="header-subtitle">管理员控制台 · 仅 ADMIN 角色可见</span>
          </div>
          <el-tag type="warning" effect="dark" size="small">ADMIN</el-tag>
        </el-header>
        <el-main>
          <div class="admin-tabs">
            <el-tabs v-model="activeTab" @tab-change="onTabChange">
              <el-tab-pane label="商品管理" name="products" />
              <el-tab-pane label="库存管理" name="inventory" />
              <el-tab-pane label="用户管理" name="users" />
              <el-tab-pane label="订单管理" name="orders" />
              <el-tab-pane label="系统日志" name="logs" />
            </el-tabs>
          </div>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import { ElMessage } from 'element-plus'
import SideNav from '@/components/SideNav.vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const tabMap = {
  products: '商品管理',
  inventory: '库存管理',
  users: '用户管理',
  orders: '订单管理',
  logs: '系统日志'
}

const activeTab = ref(route.params.tab || 'products')
const pageTitle = computed(() => tabMap[activeTab.value] || '管理控制台')

function onTabChange(name) {
  router.push({ name: `admin-${name}` })
  activeTab.value = name
}

watch(
  () => route.params.tab,
  (val) => {
    if (val && tabMap[val]) activeTab.value = val
  }
)

// 角色校验: 非 ADMIN 强制退出
if (!userStore.isLoggedIn) {
  ElMessage.warning('请先登录')
  router.replace({ path: '/login' })
} else if (userStore.userInfo?.role !== 'ADMIN' && userStore.userInfo?.role !== 'admin') {
  ElMessage.error('该页面仅管理员可见')
  router.replace({ path: '/products' })
}
</script>

<style scoped>
.admin-layout {
  min-height: 100vh;
  background-color: #f5f5f5;
}
.header-content {
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100%;
  flex: 1;
}
.header-content h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}
.header-subtitle {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}
.el-header {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
}
.admin-tabs {
  background: #fff;
  padding: 0 16px;
  margin-bottom: 16px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
</style>
