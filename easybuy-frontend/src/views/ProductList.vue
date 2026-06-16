<template>
  <div class="product-list-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <h2>商品列表</h2>
          <div class="user-info">
            <span>欢迎，{{ userStore.userInfo.username }}</span>
            <el-button type="primary" size="small" @click="goToOrders">我的订单</el-button>
            <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
          </div>
        </div>
      </el-header>
      <el-main>
        <div class="search-bar">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索商品名称"
            style="width: 300px"
            clearable
            @clear="fetchProducts"
            @keyup.enter="fetchProducts"
          >
            <template #append>
              <el-button icon="Search" @click="fetchProducts" />
            </template>
          </el-input>
        </div>

        <div class="product-grid" v-loading="loading">
          <el-card
            v-for="product in products"
            :key="product.id"
            class="product-card"
            shadow="hover"
          >
            <div class="product-image">
              <img :src="product.imageUrl || '/placeholder.png'" :alt="product.name" />
            </div>
            <div class="product-info">
              <h3 class="product-name">{{ product.name }}</h3>
              <p class="product-desc">{{ product.description }}</p>
              <div class="product-price">
                <span class="price">¥{{ product.price }}</span>
                <span class="stock">库存: {{ product.stock }}</span>
              </div>
              <div class="product-actions">
                <el-button type="primary" size="small" @click="handleBuy(product)">
                  立即购买
                </el-button>
              </div>
            </div>
          </el-card>
        </div>

        <el-empty v-if="!loading && products.length === 0" description="暂无商品" />

        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[8, 12, 20, 40]"
          layout="total, sizes, prev, pager, next"
          style="margin-top: 30px; justify-content: center"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/userStore'
import { getProductList } from '@/api/product'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const searchKeyword = ref('')
const products = ref([])

const pagination = reactive({
  page: 1,
  size: 12,
  total: 0
})

const fetchProducts = async () => {
  loading.value = true
  try {
    const res = await getProductList({
      page: pagination.page,
      size: pagination.size
    })
    products.value = res.data.records
    pagination.total = res.data.total
  } catch (error) {
    ElMessage.error('获取商品列表失败')
  } finally {
    loading.value = false
  }
}

const handleBuy = (product) => {
  router.push({
    name: 'OrderCreate',
    query: {
      productId: product.id,
      productName: product.name,
      price: product.price,
      maxStock: product.stock
    }
  })
}

const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  fetchProducts()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchProducts()
}

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

const goToOrders = () => {
  router.push('/orders')
}

onMounted(() => {
  fetchProducts()
})
</script>

<style scoped>
.product-list-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.el-header {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  line-height: 60px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h2 {
  margin: 0;
  font-weight: 600;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.el-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 20px;
}

.search-bar {
  margin-bottom: 30px;
  display: flex;
  justify-content: center;
}

.product-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  width: 100%;
  box-sizing: border-box;
}

.product-card {
  flex: 0 0 calc((100% - 60px) / 4);  /* 桌面 4 列: 3 个 gap = 60px */
  max-width: calc((100% - 60px) / 4);
  border-radius: 12px;
  overflow: hidden;
  transition: transform 0.3s, box-shadow 0.3s;
  min-width: 0;
  box-sizing: border-box;
}

@media (max-width: 1199px) {
  .product-card {
    flex: 0 0 calc((100% - 40px) / 3);
    max-width: calc((100% - 40px) / 3);
  }
}

@media (max-width: 900px) {
  .product-card {
    flex: 0 0 calc((100% - 20px) / 2);
    max-width: calc((100% - 20px) / 2);
  }
}

@media (max-width: 600px) {
  .product-card {
    flex: 0 0 100%;
    max-width: 100%;
  }
}

.product-card :deep(.el-card) {
  width: 100%;
  border: none;
}

.product-card :deep(.el-card__body) {
  padding: 0;
  width: 100%;
  box-sizing: border-box;
}

.product-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
}

.product-image {
  height: 180px;
  overflow: hidden;
  background-color: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-image img {
  max-width: 100%;
  max-height: 100%;
  object-fit: cover;
}

.product-info {
  padding: 15px;
}

.product-name {
  margin: 0 0 10px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  word-break: break-all;
  min-width: 0;
}

.product-desc {
  margin: 0 0 15px;
  font-size: 13px;
  color: #909399;
  height: 40px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.product-price {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.price {
  font-size: 20px;
  font-weight: bold;
  color: #f56c6c;
}

.stock {
  font-size: 13px;
  color: #909399;
}

.product-actions {
  display: flex;
  justify-content: center;
}

.product-actions .el-button {
  width: 100%;
}
</style>
