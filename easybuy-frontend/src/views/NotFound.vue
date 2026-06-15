<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <h1 class="error-code">404</h1>
      <h2 class="error-title">页面未找到</h2>
      <p class="error-desc">抱歉，您访问的页面不存在或已被删除</p>
      <el-button type="primary" size="large" @click="goHome">
        返回首页
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'

const router = useRouter()
const userStore = useUserStore()

const goHome = () => {
  if (userStore.isLoggedIn) {
    router.push('/products')
  } else {
    router.push('/login')
  }
}
</script>

<style scoped>
.not-found-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.not-found-content {
  text-align: center;
  color: white;
}

.error-code {
  font-size: 150px;
  font-weight: bold;
  margin: 0;
  text-shadow: 2px 2px 10px rgba(0, 0, 0, 0.3);
}

.error-title {
  font-size: 36px;
  margin: 20px 0;
  font-weight: 600;
}

.error-desc {
  font-size: 18px;
  margin-bottom: 40px;
  opacity: 0.9;
}
</style>
