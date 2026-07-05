<template>
  <el-aside class="side-nav" :width="asideWidth">
    <div class="brand">
      <div class="brand-logo">E</div>
      <div class="brand-text" v-show="!collapsed">
        <div class="brand-title">E-Mall</div>
        <div class="brand-subtitle">微服务商城</div>
      </div>
    </div>

    <div class="user-card" v-if="userStore.isLoggedIn">
      <el-avatar :size="40" class="avatar">{{ avatarChar }}</el-avatar>
      <div class="user-meta" v-show="!collapsed">
        <div class="user-name">{{ displayName }}</div>
        <div class="user-hint">已登录</div>
      </div>
    </div>

    <el-menu
      :default-active="activeMenu"
      class="nav-menu"
      background-color="transparent"
      text-color="rgba(255,255,255,0.85)"
      active-text-color="#ffd04b"
      :collapse="collapsed"
      :collapse-transition="false"
      router
    >
      <template v-if="userStore.isLoggedIn">
        <el-menu-item index="/products">
          <el-icon><Goods /></el-icon>
          <template #title>商品列表</template>
        </el-menu-item>
        <el-menu-item index="/orders">
          <el-icon><Tickets /></el-icon>
          <template #title>我的订单</template>
        </el-menu-item>
        <el-menu-item index="/profile">
          <el-icon><User /></el-icon>
          <template #title>个人中心</template>
        </el-menu-item>
      </template>
      <template v-else>
        <el-menu-item index="/login">
          <el-icon><User /></el-icon>
          <template #title>登录</template>
        </el-menu-item>
        <el-menu-item index="/register">
          <el-icon><EditPen /></el-icon>
          <template #title>注册</template>
        </el-menu-item>
      </template>
    </el-menu>

    <div class="nav-footer">
      <el-button
        v-if="userStore.isLoggedIn"
        type="danger"
        :icon="SwitchButton"
        class="logout-btn"
        :size="collapsed ? 'small' : 'default'"
        @click="handleLogout"
      >
        <span v-show="!collapsed">退出登录</span>
      </el-button>
      <el-button
        text
        class="collapse-btn"
        @click="toggleCollapsed"
      >
        <el-icon><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
        <span v-show="!collapsed">收起</span>
      </el-button>
    </div>
  </el-aside>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Goods, Tickets, User, EditPen, SwitchButton, Fold, Expand } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/userStore'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const collapsed = ref(false)
const asideWidth = computed(() => (collapsed.value ? '64px' : '220px'))

const displayName = computed(() => userStore.username || userStore.userInfo?.username || '用户')
const avatarChar = computed(() => (displayName.value || 'U').slice(0, 1).toUpperCase())
const activeMenu = computed(() => route.path)

function toggleCollapsed() {
  collapsed.value = !collapsed.value
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '退出',
      cancelButtonText: '再想想',
      type: 'warning'
    })
  } catch {
    return
  }
  await userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.side-nav {
  background: linear-gradient(180deg, #2c3e50 0%, #1f2d3d 100%);
  color: white;
  height: 100vh;
  position: sticky;
  top: 0;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  transition: width 0.25s ease;
  overflow: hidden;
  flex-shrink: 0;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.brand-logo {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 700;
  color: white;
  flex-shrink: 0;
}

.brand-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand-title {
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 0.5px;
  line-height: 1.2;
}

.brand-subtitle {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.55);
  margin-top: 2px;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.avatar {
  background: linear-gradient(135deg, #f56c6c 0%, #ff9a8b 100%);
  color: white;
  font-weight: 700;
  flex-shrink: 0;
}

.user-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: white;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-hint {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 2px;
}

.nav-menu {
  flex: 1;
  border-right: none;
  padding: 8px 0;
}

.nav-menu :deep(.el-menu-item) {
  height: 48px;
  line-height: 48px;
  margin: 4px 8px;
  border-radius: 6px;
  font-size: 14px;
}

.nav-menu :deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.06) !important;
  color: white !important;
}

.nav-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(64, 158, 255, 0.18) 0%, rgba(64, 158, 255, 0.05) 100%) !important;
  color: #ffd04b !important;
  font-weight: 600;
}

.nav-menu :deep(.el-menu-item .el-icon) {
  font-size: 18px;
  margin-right: 10px;
}

.nav-footer {
  padding: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.logout-btn {
  width: 100%;
  font-weight: 500;
}

.collapse-btn {
  width: 100%;
  color: rgba(255, 255, 255, 0.65);
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.collapse-btn:hover {
  color: white;
}
</style>
