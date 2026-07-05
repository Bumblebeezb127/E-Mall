<template>
  <div class="profile-container">
    <el-container>
      <SideNav />
      <el-container>
        <el-header>
          <div class="header-content">
            <h2>个人中心</h2>
            <span class="header-subtitle">查看你的账号信息</span>
          </div>
        </el-header>

        <el-main>
          <el-card v-loading="loading" class="profile-card">
            <template #header>
              <div class="card-header">
                <span>
                  <el-icon><User /></el-icon>
                  账号信息
                </span>
                <el-button text type="primary" @click="fetchProfile">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </template>

            <div v-if="profile" class="profile-content">
              <div class="avatar-row">
                <el-avatar :size="72" class="avatar">{{ avatarChar }}</el-avatar>
                <div class="avatar-meta">
                  <div class="username">{{ profile.username }}</div>
                  <div class="user-id">用户 ID: {{ profile.id }}</div>
                </div>
              </div>

              <el-divider />

              <el-descriptions :column="1" border>
                <el-descriptions-item label="用户名">
                  {{ profile.username }}
                </el-descriptions-item>
                <el-descriptions-item label="用户 ID">
                  {{ profile.id }}
                </el-descriptions-item>
                <el-descriptions-item label="注册时间">
                  {{ profile.createdAt || '—' }}
                </el-descriptions-item>
              </el-descriptions>

              <div class="action-row">
                <el-button type="danger" :icon="SwitchButton" @click="handleLogout">
                  退出登录
                </el-button>
              </div>
            </div>

            <el-empty v-else-if="!loading" description="未能加载用户信息" />
          </el-card>
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/userStore'
import SideNav from '@/components/SideNav.vue'

const router = useRouter()
const userStore = useUserStore()

const profile = ref(null)
const loading = ref(false)

const avatarChar = computed(() => {
  const name = profile.value?.username || userStore.username || 'U'
  return name.slice(0, 1).toUpperCase()
})

async function fetchProfile() {
  loading.value = true
  try {
    const res = await userStore.getUserInfo()
    profile.value = res.data || null
  } catch (e) {
    profile.value = null
    ElMessage.error(e.message || '加载用户信息失败')
  } finally {
    loading.value = false
  }
}

async function handleLogout() {
  await userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

onMounted(() => {
  if (!userStore.isLoggedIn) {
    router.push('/login')
    return
  }
  fetchProfile()
})
</script>

<style scoped>
.profile-container {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.header-content {
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100%;
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

.profile-card {
  max-width: 720px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 500;
}

.profile-content {
  padding: 8px 0;
}

.avatar-row {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 8px 4px 0;
}

.avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-size: 28px;
  font-weight: 600;
}

.avatar-meta .username {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.avatar-meta .user-id {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.action-row {
  margin-top: 24px;
  text-align: right;
}
</style>
