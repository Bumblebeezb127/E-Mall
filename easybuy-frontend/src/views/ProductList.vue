<template>
  <div class="product-list-container">
    <el-container>
      <SideNav />
      <el-container>
        <el-header>
          <div class="header-content">
            <h2>商品列表</h2>
            <span class="header-subtitle">浏览所有商品并下单</span>
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
                <img
                  :src="product.imageUrl || '/placeholder.svg'"
                  :alt="product.name"
                  @error="onImgError($event)"
                />
                <div v-if="(product.stock || 0) <= 0" class="out-of-stock-badge">缺货</div>
              </div>
              <div class="product-info">
                <h3 class="product-name">{{ product.name }}</h3>
                <p class="product-desc">{{ product.description || '暂无描述' }}</p>
                <div class="product-price">
                  <span class="price">¥{{ product.price }}</span>
                  <span class="stock" :class="{ 'low-stock': (product.stock || 0) > 0 && (product.stock || 0) <= 5 }">
                    库存: {{ product.stock || 0 }}
                  </span>
                </div>
                <div class="product-actions">
                  <el-button
                    type="primary"
                    size="small"
                    :disabled="(product.stock || 0) <= 0"
                    @click="handleBuy(product)"
                  >
                    {{ (product.stock || 0) > 0 ? '立即购买' : '已售罄' }}
                  </el-button>
                </div>
              </div>
            </el-card>
          </div>

          <el-empty v-if="!loading && products.length === 0" description="暂无商品" />

          <el-pagination
            v-if="pagination.total > 0"
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
    </el-container>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/userStore'
import { getProductList } from '@/api/product'
import SideNav from '@/components/SideNav.vue'

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

function onImgError(e) {
  // 图片加载失败时使用内联 SVG 占位
  if (e.target && !e.target.dataset.fallback) {
    e.target.dataset.fallback = '1'
    const w = e.target.clientWidth || 200
    const h = e.target.clientHeight || 200
    // 从最近路径找到 alt 文本 (商品名称)
    const alt = e.target.alt || '商品'
    const text = alt.slice(0, 4)
    const colors = ['#409EFF', '#67C23A', '#E6A23C', '#F56C6C', '#909399']
    const color = colors[Math.abs(hashCode(alt)) % colors.length]
    const svg = `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 ${w} ${h}'>
      <rect width='100%' height='100%' fill='#f0f2f5'/>
      <text x='50%' y='50%' text-anchor='middle' dy='.3em'
            font-size='24' fill='${color}' font-family='sans-serif' font-weight='bold'>${text}</text>
    </svg>`
    e.target.src = 'data:image/svg+xml;utf8,' + encodeURIComponent(svg)
  }
}

function hashCode(str) {
  let h = 0
  for (let i = 0; i < str.length; i++) {
    h = ((h << 5) - h) + str.charCodeAt(i)
    h |= 0
  }
  return h
}

const fetchProducts = async () => {
  loading.value = true
  try {
    const res = await getProductList({
      page: pagination.page,
      size: pagination.size,
      keyword: searchKeyword.value || undefined
    })
    if (res.data) {
      products.value = res.data.records || []
      pagination.total = res.data.total || 0
    }
  } catch (error) {
    ElMessage.error('获取商品列表失败: ' + (error.message || ''))
  } finally {
    loading.value = false
  }
}

const handleBuy = (product) => {
  if (!product || (product.stock || 0) <= 0) {
    ElMessage.warning('该商品暂时缺货')
    return
  }
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
  background: white;
  border-bottom: 1px solid #ebeef5;
  height: 64px;
  line-height: 64px;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-content h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  line-height: 64px;
}

.header-subtitle {
  color: #909399;
  font-size: 13px;
}

.el-main {
  padding: 24px;
}

.search-bar {
  margin-bottom: 24px;
  display: flex;
  justify-content: flex-start;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  width: 100%;
  box-sizing: border-box;
}

.product-card {
  border-radius: 12px;
  overflow: hidden;
  transition: transform 0.3s, box-shadow 0.3s;
  min-width: 0;
  box-sizing: border-box;
  width: 100%;
}

@media (max-width: 1199px) {
  .product-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 900px) {
  .product-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .product-grid {
    grid-template-columns: 1fr;
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
  width: 100%;
  height: 200px;
  overflow: hidden;
  background-color: #f0f2f5;
  display: block;
  position: relative;
}

.product-image img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  transition: transform 0.3s;
}

.product-card:hover .product-image img {
  transform: scale(1.05);
}

.out-of-stock-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(245, 108, 108, 0.9);
  color: white;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
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

.stock.low-stock {
  color: #e6a23c;
  font-weight: 600;
}

.product-actions {
  display: flex;
  justify-content: center;
}

.product-actions .el-button {
  width: 100%;
}
</style>
