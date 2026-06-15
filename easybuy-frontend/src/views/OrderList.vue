<template>
  <div class="order-list-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <h2>我的订单</h2>
          <div class="user-info">
            <span>欢迎，{{ userStore.userInfo.username }}</span>
            <el-button type="primary" size="small" @click="goToProducts">继续购物</el-button>
            <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
          </div>
        </div>
      </el-header>
      <el-main>
        <el-card v-loading="loading">
          <template #header>
            <div class="card-header">
              <span>订单列表</span>
              <el-button text type="primary" @click="fetchOrders">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>

          <el-table
            :data="orders"
            style="width: 100%"
            v-loading="loading"
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
                    <el-table-column prop="price" label="单价" width="120">
                      <template #default="{ row: item }">
                        ¥{{ item.price }}
                      </template>
                    </el-table-column>
                    <el-table-column prop="quantity" label="数量" width="100" />
                    <el-table-column label="小计" width="120">
                      <template #default="{ row: item }">
                        <strong style="color: #f56c6c">¥{{ (item.price * item.quantity).toFixed(2) }}</strong>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="orderId" label="订单ID" width="100" />
            <el-table-column prop="orderNo" label="订单号" min-width="200">
              <template #default="{ row }">
                <span class="order-no">{{ row.orderNo }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="totalAmount" label="订单金额" width="130">
              <template #default="{ row }">
                <span class="total-amount">¥{{ row.totalAmount }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="statusDesc" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ row.statusDesc }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="createdAt" label="下单时间" width="180" />
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" size="small" text @click="viewOrderDetail(row)">
                  查看详情
                </el-button>
                <el-button
                  v-if="row.status === 0"
                  type="danger"
                  size="small"
                  text
                  @click="handleCancel(row)"
                >
                  取消订单
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="!loading && orders.length === 0" description="暂无订单">
            <el-button type="primary" @click="goToProducts">去购物</el-button>
          </el-empty>

          <div class="pagination-container" v-if="orders.length > 0">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.size"
              :total="pagination.total"
              :page-sizes="[5, 10, 20]"
              layout="total, sizes, prev, pager, next"
              @size-change="handleSizeChange"
              @current-change="handlePageChange"
            />
          </div>
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
                  ¥{{ currentOrder.totalAmount }}
                </strong>
              </el-descriptions-item>
            </el-descriptions>

            <el-divider content-position="left">订单项</el-divider>

            <el-table :data="currentOrder.items" border>
              <el-table-column prop="productName" label="商品名称" />
              <el-table-column prop="price" label="单价" width="100">
                <template #default="{ row }">¥{{ row.price }}</template>
              </el-table-column>
              <el-table-column prop="quantity" label="数量" width="80" />
              <el-table-column label="小计" width="120">
                <template #default="{ row }">
                  <strong>¥{{ (row.price * row.quantity).toFixed(2) }}</strong>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/userStore'
import { getOrderList } from '@/api/order'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const orders = ref([])
const expandedRows = ref([])
const detailDialogVisible = ref(false)
const currentOrder = ref(null)

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

const statusMap = {
  0: { type: 'warning', text: '待支付' },
  1: { type: 'success', text: '已支付' },
  2: { type: 'primary', text: '已发货' },
  3: { type: 'info', text: '已完成' },
  4: { type: 'danger', text: '已取消' }
}

const getStatusType = (status) => {
  return statusMap[status]?.type || 'info'
}

const fetchOrders = async () => {
  loading.value = true
  try {
    const res = await getOrderList({
      page: pagination.page,
      size: pagination.size,
      userId: userStore.userInfo.id
    })
    orders.value = res.data || []
    orders.value.forEach(order => {
      order.expanded = false
    })
    pagination.total = res.data?.total || orders.value.length
  } catch (error) {
    ElMessage.error('获取订单列表失败')
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
  try {
    await ElMessageBox.confirm('确定要取消该订单吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    ElMessage.success('订单已取消')
    fetchOrders()
  } catch {
  }
}

const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  fetchOrders()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchOrders()
}

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

const goToProducts = () => {
  router.push('/products')
}

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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
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

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 30px;
}

.order-detail {
  padding: 10px 0;
}
</style>
