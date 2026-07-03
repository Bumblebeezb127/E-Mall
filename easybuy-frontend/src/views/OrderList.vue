<template>
  <div class="order-list-container">
    <el-container>
      <SideNav />
      <el-container>
        <el-header>
          <div class="header-content">
            <h2>我的订单</h2>
            <span class="header-subtitle">查看与处理你的所有订单</span>
          </div>
        </el-header>
        <el-main>
          <!-- 状态统计卡片 -->
          <div class="status-cards">
          <div
            v-for="tab in tabs"
            :key="tab.status"
            class="status-card"
            :class="{ active: currentStatus === tab.status }"
            @click="switchTab(tab.status)"
          >
            <div class="status-label">{{ tab.label }}</div>
            <div class="status-count">
              <span class="num">{{ countByStatus(tab.status) }}</span>
              <span class="unit">单</span>
            </div>
          </div>
        </div>

        <el-card v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>
                <el-icon><Tickets /></el-icon>
                {{ currentTabLabel }} 订单
                <span class="total-hint">(当前页 {{ pagedOrders.length }} / 共 {{ filteredOrders.length }} 单)</span>
              </span>
              <div class="header-actions">
                <el-button
                  v-if="currentStatus === 0 && filteredOrders.length > 0"
                  type="warning"
                  :loading="payingAll"
                  @click="handlePayAll"
                >
                  <el-icon><CreditCard /></el-icon>
                  一键支付所有 ({{ filteredOrders.length }} 单, 共 ¥{{ totalPendingAmount }})
                </el-button>
                <el-button text type="primary" @click="fetchOrders">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </div>
          </template>

          <el-table
            v-if="pagedOrders.length > 0"
            :data="pagedOrders"
            style="width: 100%"
            stripe
            @expand-change="handleExpand"
            :expand-row-keys="expandedRows"
            row-key="orderId"
          >
            <el-table-column type="expand" width="50">
              <template #default="{ row }">
                <div class="order-items-container" v-if="row.expanded">
                  <el-table :data="row.items" border style="width: 100%">
                    <el-table-column prop="productName" label="商品名称" />
                    <el-table-column label="单价" width="120">
                      <template #default="{ row: item }">
                        ¥{{ formatPrice(item.price) }}
                      </template>
                    </el-table-column>
                    <el-table-column prop="quantity" label="数量" width="100" />
                    <el-table-column label="小计" width="120">
                      <template #default="{ row: item }">
                        <strong style="color: #f56c6c">¥{{ formatPrice((item.price || 0) * (item.quantity || 0)) }}</strong>
                      </template>
                    </el-table-column>
                  </el-table>
                  <div v-if="row.address" class="order-extra">
                    <p><strong>收货地址:</strong> {{ row.address }}</p>
                    <p v-if="row.remark"><strong>备注:</strong> {{ row.remark }}</p>
                  </div>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="orderId" label="订单ID" width="100" />
            <el-table-column prop="orderNo" label="订单号" min-width="200">
              <template #default="{ row }">
                <span class="order-no">{{ row.orderNo }}</span>
              </template>
            </el-table-column>
            <el-table-column label="订单金额" width="130">
              <template #default="{ row }">
                <span class="total-amount">¥{{ formatPrice(row.totalAmount) }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="statusDesc" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ row.statusDesc || '未知' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="createdAt" label="下单时间" width="180" />
            <el-table-column label="操作" width="220" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" size="small" text @click="viewOrderDetail(row)">
                  查看详情
                </el-button>
                <el-button
                  v-if="row.status === 0"
                  type="warning"
                  size="small"
                  text
                  :loading="paying[row.orderId]"
                  @click="handlePay(row)"
                >
                  立即支付
                </el-button>
                <el-button
                  v-if="row.status === 0"
                  type="danger"
                  size="small"
                  text
                  :loading="cancelling[row.orderId]"
                  @click="handleCancel(row)"
                >
                  取消订单
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="!loading && pagedOrders.length === 0" :description="emptyDescription">
            <el-button type="primary" @click="goToProducts">去购物</el-button>
          </el-empty>

          <!-- 分页 -->
          <el-pagination
            v-if="filteredOrders.length > 0"
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.size"
            :total="filteredOrders.length"
            :page-sizes="[5, 10, 20]"
            :pager-count="5"
            layout="total, sizes, prev, pager, next, jumper"
            class="pagination"
            background
            @size-change="(s) => { pagination.size = s; pagination.page = 1; }"
            @current-change="(p) => pagination.page = p"
          />
        </el-card>

        <el-dialog
          v-model="detailDialogVisible"
          title="订单详情"
          width="600px"
        >
          <div v-if="currentOrder" class="order-detail">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="订单ID">
                {{ currentOrder.orderId }}
              </el-descriptions-item>
              <el-descriptions-item label="订单号">
                {{ currentOrder.orderNo }}
              </el-descriptions-item>
              <el-descriptions-item label="订单状态">
                <el-tag :type="getStatusType(currentOrder.status)">
                  {{ currentOrder.statusDesc }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="下单时间">
                {{ currentOrder.createdAt }}
              </el-descriptions-item>
              <el-descriptions-item label="订单金额" :span="2">
                <strong style="color: #f56c6c; font-size: 18px">
                  ¥{{ formatPrice(currentOrder.totalAmount) }}
                </strong>
              </el-descriptions-item>
            </el-descriptions>

            <el-divider content-position="left">订单项</el-divider>

            <el-table :data="currentOrder.items" border>
              <el-table-column prop="productName" label="商品名称" />
              <el-table-column label="单价" width="100">
                <template #default="{ row }">¥{{ formatPrice(row.price) }}</template>
              </el-table-column>
              <el-table-column prop="quantity" label="数量" width="80" />
              <el-table-column label="小计" width="120">
                <template #default="{ row }">
                  <strong>¥{{ formatPrice((row.price || 0) * (row.quantity || 0)) }}</strong>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <template #footer>
            <el-button @click="detailDialogVisible = false">关闭</el-button>
          </template>
        </el-dialog>
      </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Tickets, Refresh, CreditCard } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/userStore'
import { getOrderList, cancelOrder, payOrder } from '@/api/order'
import SideNav from '@/components/SideNav.vue'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const orders = ref([])
const expandedRows = ref([])
const detailDialogVisible = ref(false)
const currentOrder = ref(null)
const cancelling = reactive({})
const paying = reactive({})
const payingAll = ref(false)

// 状态 Tab 定义: -1=全部, 0=待支付, 1=已支付, 2=已发货, 3=已完成, 4=已取消
const tabs = [
  { status: -1, label: '全部订单' },
  { status: 0,  label: '待支付' },
  { status: 1,  label: '已支付' },
  { status: 2,  label: '已发货' },
  { status: 3,  label: '已完成' },
  { status: 4,  label: '已取消' }
]

const currentStatus = ref(-1)
const pagination = reactive({ page: 1, size: 5 })

const statusMap = {
  0: { type: 'warning', text: '待支付' },
  1: { type: 'success', text: '已支付' },
  2: { type: 'primary', text: '已发货' },
  3: { type: 'info',    text: '已完成' },
  4: { type: 'danger',  text: '已取消' }
}

const getStatusType = (status) => statusMap[status]?.type || 'info'

function formatPrice(p) { return parseFloat(p || 0).toFixed(2) }

// 按状态分页后的订单
const filteredOrders = computed(() => {
  if (currentStatus.value === -1) return orders.value
  return orders.value.filter(o => o.status === currentStatus.value)
})

const pagedOrders = computed(() => {
  const start = (pagination.page - 1) * pagination.size
  return filteredOrders.value.slice(start, start + pagination.size)
})

const currentTabLabel = computed(() => {
  return tabs.find(t => t.status === currentStatus.value)?.label || '全部'
})

const emptyDescription = computed(() => {
  if (orders.value.length === 0) return '您还没有任何订单, 赶紧去下单吧'
  return `暂无"${currentTabLabel.value}"订单`
})

const totalPendingAmount = computed(() => {
  return formatPrice(
    filteredOrders.value.reduce((s, o) => s + parseFloat(o.totalAmount || 0), 0)
  )
})

function countByStatus(status) {
  if (status === -1) return orders.value.length
  return orders.value.filter(o => o.status === status).length
}

function switchTab(status) {
  currentStatus.value = status
  pagination.page = 1
  expandedRows.value = []
}

watch(currentStatus, () => {
  pagination.page = 1
})

const fetchOrders = async () => {
  const userId = userStore.userId || userStore.userInfo?.id
  if (!userId) {
    ElMessage.error('用户身份信息缺失, 请重新登录')
    router.push({ path: '/login', query: { redirect: '/orders' } })
    return
  }
  loading.value = true
  try {
    const res = await getOrderList({ userId })
    if (Array.isArray(res.data)) {
      orders.value = res.data.map(o => ({ ...o, expanded: false }))
    } else {
      orders.value = []
    }
  } catch (error) {
    ElMessage.error('获取订单列表失败: ' + (error?.message || ''))
  } finally {
    loading.value = false
  }
}

const handleExpand = (row, expanded) => {
  row.expanded = expanded
  if (expanded) {
    expandedRows.value = [row.orderId]
  } else {
    expandedRows.value = []
  }
}

const viewOrderDetail = (order) => {
  currentOrder.value = order
  detailDialogVisible.value = true
}

const handleCancel = async (order) => {
  const userId = userStore.userId || userStore.userInfo?.id
  if (!userId) return
  try {
    await ElMessageBox.confirm('确定要取消订单 ' + order.orderNo + ' 吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '再想想',
      type: 'warning'
    })
  } catch {
    return
  }
  cancelling[order.orderId] = true
  try {
    await cancelOrder(order.orderId, userId)
    ElMessage.success('订单已取消')
    await fetchOrders()
  } catch (error) {
    ElMessage.error('取消订单失败: ' + (error?.message || ''))
  } finally {
    cancelling[order.orderId] = false
  }
}

const handlePay = async (order) => {
  const userId = userStore.userId || userStore.userInfo?.id
  if (!userId) return
  paying[order.orderId] = true
  try {
    await payOrder(order.orderId, userId)
    ElMessage.success('支付成功')
    await fetchOrders()
  } catch (error) {
    ElMessage.error('支付失败: ' + (error?.message || ''))
  } finally {
    paying[order.orderId] = false
  }
}

// 一键支付所有待支付订单
const handlePayAll = async () => {
  const userId = userStore.userId || userStore.userInfo?.id
  if (!userId) return
  const pending = filteredOrders.value
  if (pending.length === 0) {
    ElMessage.info('当前没有待支付订单')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认一键支付全部 ${pending.length} 单 (共 ¥${totalPendingAmount.value}) 吗？`,
      '一键支付确认',
      {
        confirmButtonText: '确认支付',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--warning'
      }
    )
  } catch {
    return
  }
  payingAll.value = true
  let success = 0
  let failed = 0
  const failedOrders = []
  // 串行支付避免并发, 也可改成 Promise.all 并发
  for (const order of pending) {
    try {
      await payOrder(order.orderId, userId)
      success++
    } catch (err) {
      failed++
      failedOrders.push(order.orderNo)
    }
  }
  payingAll.value = false
  if (failed === 0) {
    ElMessage.success(`支付成功! 共支付 ${success} 单`)
  } else {
    ElMessage.warning(`支付完成: 成功 ${success} 单, 失败 ${failed} 单${failedOrders.length ? ' (' + failedOrders.join(', ') + ')' : ''}`)
  }
  await fetchOrders()
}

const goToProducts = () => router.push('/products')

onMounted(() => {
  fetchOrders()
})
</script>

<style scoped>
.order-list-container {
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

.status-cards {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.status-card {
  background: white;
  border-radius: 10px;
  padding: 18px 16px;
  cursor: pointer;
  transition: all 0.25s;
  border: 2px solid transparent;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.status-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.status-card.active {
  border-color: #409eff;
  background: linear-gradient(135deg, #ecf5ff 0%, #ffffff 100%);
}

.status-label {
  font-size: 13px;
  color: #606266;
}

.status-card.active .status-label {
  color: #409eff;
  font-weight: 600;
}

.status-count {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.status-count .num {
  font-size: 26px;
  font-weight: 700;
  color: #303133;
}

.status-card.active .status-count .num {
  color: #409eff;
}

.status-count .unit {
  font-size: 12px;
  color: #909399;
}

@media (max-width: 900px) {
  .status-cards {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 600px) {
  .status-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  gap: 12px;
  flex-wrap: wrap;
}

.card-header .total-hint {
  font-size: 12px;
  color: #909399;
  font-weight: normal;
  margin-left: 8px;
}

.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.order-no {
  font-family: 'Courier New', monospace;
  color: #409eff;
}

.total-amount {
  font-weight: bold;
  color: #f56c6c;
  font-size: 16px;
}

.order-items-container {
  padding: 20px 40px;
  background-color: #fafafa;
}

.order-extra {
  margin-top: 15px;
  padding: 12px;
  background: #fff;
  border-radius: 6px;
  color: #606266;
  font-size: 13px;
}

.order-extra p {
  margin: 5px 0;
}

.order-detail {
  padding: 10px 0;
}

.pagination {
  margin-top: 20px;
  justify-content: center;
  display: flex;
}
</style>
