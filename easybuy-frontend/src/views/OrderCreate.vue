<template>
  <div class="order-create-container">
    <el-container>
      <SideNav />
      <el-container>
        <el-header>
          <div class="header-content">
            <h2>创建订单</h2>
            <el-button type="text" @click="goBack">
              <el-icon><ArrowLeft /></el-icon>
              返回商品列表
            </el-button>
          </div>
        </el-header>
        <el-main>
        <el-card class="order-card" v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>订单信息</span>
            </div>
          </template>

          <div class="product-detail" v-if="productInfo">
            <el-row :gutter="20">
              <el-col :span="8">
                <div class="product-image">
                  <img
                    :src="productInfo.imageUrl || '/placeholder.svg'"
                    :alt="productInfo.name"
                    @error="onImgError($event)"
                  />
                </div>
              </el-col>
              <el-col :span="16">
                <div class="product-info">
                  <h3>{{ productInfo.name }}</h3>
                  <p class="description">{{ productInfo.description || '暂无描述' }}</p>
                  <div class="price-stock">
                    <span class="price">¥{{ formatPrice(productInfo.price) }}</span>
                    <span class="stock" :class="{ 'low-stock': (productInfo.maxStock || 0) <= 5 }">
                      库存: {{ productInfo.maxStock || 0 }}
                    </span>
                  </div>
                </div>
              </el-col>
            </el-row>
          </div>

          <el-divider />

          <el-form :model="orderForm" :rules="rules" ref="formRef" label-width="100px">
            <el-form-item label="购买数量" prop="quantity">
              <el-input-number
                v-model="orderForm.quantity"
                :min="1"
                :max="productInfo?.maxStock || 1"
                size="large"
                @change="calculateTotal"
              />
              <span class="stock-tip">当前库存: {{ productInfo?.maxStock || 0 }}</span>
            </el-form-item>

            <el-form-item label="收货地址" prop="address">
              <el-input
                v-model="orderForm.address"
                type="textarea"
                :rows="3"
                placeholder="请输入收货地址"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>

            <el-form-item label="备注">
              <el-input
                v-model="orderForm.remark"
                type="textarea"
                :rows="2"
                placeholder="选填，可添加备注信息"
                maxlength="100"
                show-word-limit
              />
            </el-form-item>
          </el-form>

          <el-divider />

          <div class="order-summary">
            <div class="summary-row">
              <span>商品金额:</span>
              <span>¥{{ formatPrice(productInfo?.price) }}</span>
            </div>
            <div class="summary-row">
              <span>购买数量:</span>
              <span>x {{ orderForm.quantity }}</span>
            </div>
            <div class="summary-row">
              <span>运费:</span>
              <span>免运费</span>
            </div>
            <el-divider style="margin: 15px 0" />
            <div class="summary-row total">
              <span>应付总额:</span>
              <span class="total-price">¥{{ formatPrice(totalAmount) }}</span>
            </div>
          </div>

          <div class="action-buttons">
            <el-button size="large" @click="goBack">返回</el-button>
            <el-button
              type="primary"
              size="large"
              :loading="submitting"
              :disabled="!canSubmit"
              @click="handleSubmit"
            >
              提交订单
            </el-button>
          </div>
        </el-card>

        <el-dialog
          v-model="successDialogVisible"
          title="下单成功"
          width="400px"
          :close-on-click-modal="false"
          :show-close="false"
        >
          <div class="success-content">
            <el-icon class="success-icon" :size="60"><CheckCircle /></el-icon>
            <p class="success-title">订单提交成功!</p>
            <p class="order-no">订单号: <strong>{{ createdOrderNo }}</strong></p>
            <p class="success-tip">请在订单详情中查看订单状态</p>
          </div>
          <template #footer>
            <el-button type="primary" @click="goToOrders">查看订单</el-button>
            <el-button @click="goToProducts">继续购物</el-button>
          </template>
        </el-dialog>
      </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/userStore'
import { getProductDetail } from '@/api/product'
import { createOrder } from '@/api/order'
import SideNav from '@/components/SideNav.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref(null)
const loading = ref(false)
const submitting = ref(false)
const successDialogVisible = ref(false)
const createdOrderNo = ref('')

const productInfo = ref(null)

const orderForm = reactive({
  quantity: 1,
  address: '',
  remark: ''
})

const rules = {
  quantity: [
    { required: true, message: '请选择购买数量', trigger: 'change' }
  ],
  address: [
    { required: true, message: '请输入收货地址', trigger: 'blur' },
    { min: 5, max: 200, message: '地址长度在5-200个字符', trigger: 'blur' }
  ]
}

const totalAmount = computed(() => {
  if (productInfo.value) {
    return parseFloat(productInfo.value.price || 0) * orderForm.quantity
  }
  return 0
})

const canSubmit = computed(() => {
  // 只做基础存在性检查, 具体校验交给 form rules 和 handleSubmit
  return !!productInfo.value
    && productInfo.value.id != null
    && orderForm.quantity > 0
    && !submitting.value
})

function formatPrice(p) {
  return parseFloat(p || 0).toFixed(2)
}

function onImgError(e) {
  // 图片加载失败时使用内联 SVG 占位
  if (e.target && !e.target.dataset.fallback) {
    e.target.dataset.fallback = '1'
    const w = e.target.clientWidth || 200
    const h = e.target.clientHeight || 200
    const text = (productInfo.value?.name || '商品').slice(0, 4)
    const svg = `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 ${w} ${h}'>
      <rect width='100%' height='100%' fill='#f0f2f5'/>
      <text x='50%' y='50%' text-anchor='middle' dy='.3em'
            font-size='20' fill='#909399' font-family='sans-serif'>${text}</text>
    </svg>`
    e.target.src = 'data:image/svg+xml;utf8,' + encodeURIComponent(svg)
  }
}

const calculateTotal = () => {}

const handleSubmit = async () => {
  if (!formRef.value) return

  // 安全获取 userId (JWT payload 兜底)
  const userId = userStore.userId || userStore.userInfo?.id
  if (!userId) {
    ElMessage.error('用户身份信息缺失, 请重新登录')
    userStore.clearAuth()
    router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }

  // 校验 productId
  const productId = parseInt(productInfo.value?.id)
  if (!productId || isNaN(productId)) {
    ElMessage.error('商品信息异常, 请返回重试')
    return
  }

  // 校验库存
  if (orderForm.quantity > (productInfo.value.maxStock || 0)) {
    ElMessage.error('购买数量超过库存')
    return
  }

  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      const res = await createOrder({
        userId: userId,
        productId: productId,
        quantity: orderForm.quantity,
        address: orderForm.address,
        remark: orderForm.remark || ''
      })
      // 兼容不同返回层级
      const orderNo = res?.data?.orderNo || res?.orderNo || res?.data?.id || '生成成功'
      createdOrderNo.value = orderNo
      successDialogVisible.value = true
    } catch (error) {
      const msg = error?.response?.data?.message || error.message || '提交订单失败'
      ElMessage.error(msg)
    } finally {
      submitting.value = false
    }
  })
}

const goBack = () => {
  router.push('/products')
}

const goToOrders = () => {
  successDialogVisible.value = false
  router.push('/orders')
}

const goToProducts = () => {
  successDialogVisible.value = false
  router.push('/products')
}

async function loadProductFromQuery() {
  // 优先使用 query 中的快速数据
  if (route.query.productId) {
    const productId = parseInt(route.query.productId)
    if (!productId || isNaN(productId)) {
      ElMessage.warning('商品信息不存在')
      goBack()
      return
    }

    productInfo.value = {
      id: productId,
      name: route.query.productName || '商品',
      price: parseFloat(route.query.price) || 0,
      maxStock: parseInt(route.query.maxStock) || 0,
      imageUrl: route.query.imageUrl || null,
      description: route.query.description || ''
    }
    orderForm.quantity = 1

    // 异步从 API 拉取最新数据, 避免使用过期快照
    try {
      const res = await getProductDetail(productId)
      if (res?.data) {
        const p = res.data
        // 查询最新库存 (直接调 inventory service 会触发鉴权, 这里用 product 的 stock 字段作为展示)
        productInfo.value = {
          id: p.id,
          name: p.name,
          price: p.price,
          maxStock: p.stock || productInfo.value.maxStock,
          imageUrl: p.imageUrl,
          description: p.description
        }
        if ((p.stock || 0) <= 0) {
          ElMessage.warning('该商品暂时缺货, 无法下单')
        }
      }
    } catch (e) {
      // 拉取最新数据失败, 继续使用 query 数据
      console.warn('加载商品详情失败:', e?.message)
    }
  } else {
    ElMessage.warning('商品信息不存在')
    goBack()
  }
}

onMounted(async () => {
  await loadProductFromQuery()
})
</script>

<style scoped>
.order-create-container {
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
  justify-content: space-between;
  gap: 16px;
}

.header-content h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  line-height: 64px;
}

.el-main {
  padding: 24px;
}

.order-card {
  border-radius: 12px;
}

.card-header {
  font-size: 18px;
  font-weight: 600;
}

.product-detail {
  padding: 10px 0;
}

.product-image {
  width: 100%;
  height: 220px;
  background-color: #f0f2f5;
  border-radius: 8px;
  overflow: hidden;
  display: block;
  position: relative;
}

.product-image img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
}

.product-info h3 {
  margin: 0 0 15px;
  font-size: 20px;
  color: #303133;
}

.description {
  color: #909399;
  margin-bottom: 20px;
  line-height: 1.6;
}

.price-stock {
  display: flex;
  gap: 20px;
  align-items: center;
}

.price {
  font-size: 24px;
  font-weight: bold;
  color: #f56c6c;
}

.stock {
  color: #909399;
  font-size: 14px;
}

.stock.low-stock {
  color: #e6a23c;
  font-weight: 600;
}

.stock-tip {
  margin-left: 15px;
  color: #909399;
  font-size: 13px;
}

.order-summary {
  padding: 20px;
  background-color: #fafafa;
  border-radius: 8px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  color: #606266;
}

.summary-row.total {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 0;
}

.total-price {
  font-size: 24px;
  color: #f56c6c;
}

.action-buttons {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 30px;
}

.success-content {
  text-align: center;
  padding: 20px 0;
}

.success-icon {
  color: #67c23a;
  margin-bottom: 20px;
}

.success-title {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 15px;
  color: #303133;
}

.order-no {
  font-size: 16px;
  margin-bottom: 10px;
  color: #606266;
}

.order-no strong {
  color: #409eff;
  font-size: 18px;
}

.success-tip {
  color: #909399;
  font-size: 14px;
}
</style>
