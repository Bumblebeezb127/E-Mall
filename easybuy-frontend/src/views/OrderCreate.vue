<template>
  <div class="order-create-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <h2>创建订单</h2>
          <el-button type="text" @click="goBack" style="color: white">
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
                  <img :src="productInfo.imageUrl || '/placeholder.png'" :alt="productInfo.name" />
                </div>
              </el-col>
              <el-col :span="16">
                <div class="product-info">
                  <h3>{{ productInfo.name }}</h3>
                  <p class="description">{{ productInfo.description || '暂无描述' }}</p>
                  <div class="price-stock">
                    <span class="price">¥{{ productInfo.price }}</span>
                    <span class="stock">库存: {{ productInfo.maxStock }}</span>
                  </div>
                </div>
              </el-col>
            </el-row>
          </div>

          <el-divider />

          <el-form :model="orderForm" :rules="rules" ref="formRef" label-width="100px">
            <el-form-item label="购买数量">
              <el-input-number
                v-model="orderForm.quantity"
                :min="1"
                :max="productInfo?.maxStock || 1"
                size="large"
                @change="calculateTotal"
              />
              <span class="stock-tip">当前库存: {{ productInfo?.maxStock || 0 }}</span>
            </el-form-item>

            <el-form-item label="收货地址">
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
              <span>¥{{ productInfo?.price || 0 }}</span>
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
              <span class="total-price">¥{{ totalAmount.toFixed(2) }}</span>
            </div>
          </div>

          <div class="action-buttons">
            <el-button size="large" @click="goBack">返回</el-button>
            <el-button
              type="primary"
              size="large"
              :loading="submitting"
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/userStore'
import { createOrder } from '@/api/order'

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
  address: [
    { required: true, message: '请输入收货地址', trigger: 'blur' },
    { min: 5, max: 200, message: '地址长度在5-200个字符', trigger: 'blur' }
  ]
}

const totalAmount = computed(() => {
  if (productInfo.value) {
    return parseFloat(productInfo.value.price) * orderForm.quantity
  }
  return 0
})

const calculateTotal = () => {
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        const res = await createOrder({
          userId: userStore.userInfo.id,
          productId: parseInt(productInfo.value.id),
          quantity: orderForm.quantity
        })
        createdOrderNo.value = res.data?.orderNo || res.data?.id || '生成成功'
        successDialogVisible.value = true
      } catch (error) {
        ElMessage.error(error.message || '提交订单失败')
      } finally {
        submitting.value = false
      }
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

onMounted(() => {
  if (route.query.productId) {
    productInfo.value = {
      id: route.query.productId,
      name: route.query.productName || '商品',
      price: parseFloat(route.query.price) || 0,
      maxStock: parseInt(route.query.maxStock) || 0,
      imageUrl: route.query.imageUrl || null,
      description: route.query.description || ''
    }
    orderForm.quantity = 1
  } else {
    ElMessage.warning('商品信息不存在')
    goBack()
  }
})
</script>

<style scoped>
.order-create-container {
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

.el-main {
  max-width: 900px;
  margin: 30px auto;
  padding: 0 20px;
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
  height: 200px;
  background-color: #f0f2f5;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-image img {
  max-width: 100%;
  max-height: 100%;
  object-fit: cover;
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
