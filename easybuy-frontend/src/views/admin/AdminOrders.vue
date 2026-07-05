<template>
  <div class="admin-orders">
    <div class="toolbar">
      <el-input v-model="query.userId" placeholder="按用户ID" clearable style="width: 140px" @keyup.enter="fetchList" />
      <el-input v-model="query.orderNo" placeholder="按订单号" clearable style="width: 240px" @keyup.enter="fetchList" />
      <el-select v-model="query.status" placeholder="订单状态" clearable style="width: 140px">
        <el-option label="待支付" :value="0" />
        <el-option label="已支付" :value="1" />
        <el-option label="已发货" :value="2" />
        <el-option label="已完成" :value="3" />
        <el-option label="已取消" :value="4" />
      </el-select>
      <el-button type="primary" :icon="Search" @click="fetchList">查询</el-button>
      <el-button :icon="Refresh" @click="resetQuery">重置</el-button>
    </div>

    <div class="stats" v-if="stats.total !== undefined">
      <span class="stat-chip">总数: <b>{{ stats.total }}</b></span>
      <span class="stat-chip status-0">待支付: <b>{{ stats.status_0 }}</b></span>
      <span class="stat-chip status-1">已支付: <b>{{ stats.status_1 }}</b></span>
      <span class="stat-chip status-2">已发货: <b>{{ stats.status_2 }}</b></span>
      <span class="stat-chip status-3">已完成: <b>{{ stats.status_3 }}</b></span>
      <span class="stat-chip status-4">已取消: <b>{{ stats.status_4 }}</b></span>
    </div>

    <el-table :data="records" v-loading="loading" border stripe>
      <el-table-column prop="orderId" label="订单ID" width="80" />
      <el-table-column prop="orderNo" label="订单号" min-width="200" />
      <el-table-column prop="userId" label="用户ID" width="90" />
      <el-table-column label="金额" width="100">
        <template #default="{ row }">¥{{ row.totalAmount }}</template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ row.statusDesc }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="address" label="收货地址" min-width="180" show-overflow-tooltip />
      <el-table-column prop="createdAt" label="创建时间" width="170" />
      <el-table-column label="操作" width="220" fixed="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 0" size="small" type="primary" @click="forcePay(row)">强制支付</el-button>
          <el-button v-if="row.status === 0" size="small" type="warning" @click="forceCancel(row)">强制取消</el-button>
          <el-button size="small" type="danger" @click="confirmDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > 0"
      v-model:current-page="query.page"
      v-model:page-size="query.size"
      :total="total"
      :page-sizes="[20, 50, 100]"
      layout="total, sizes, prev, pager, next"
      style="margin-top: 16px; justify-content: flex-end"
      @current-change="fetchList"
      @size-change="fetchList"
    />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import {
  adminListOrders,
  adminOrderStats,
  adminForceCancelOrder,
  adminForcePayOrder,
  adminDeleteOrder
} from '@/api/admin'

const loading = ref(false)
const records = ref([])
const total = ref(0)
const query = reactive({ page: 1, size: 20, userId: null, orderNo: '', status: null })
const stats = reactive({ total: 0, status_0: 0, status_1: 0, status_2: 0, status_3: 0, status_4: 0 })

function statusType(s) {
  return ['warning', 'success', 'primary', 'info', 'danger'][s] || 'info'
}

async function fetchList() {
  loading.value = true
  try {
    const params = { page: query.page, size: query.size }
    if (query.userId) params.userId = query.userId
    if (query.orderNo) params.orderNo = query.orderNo
    if (query.status !== null && query.status !== '') params.status = query.status
    const res = await adminListOrders(params)
    const data = res.data || {}
    records.value = data.records || []
    total.value = data.total || 0
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

async function fetchStats() {
  try {
    const res = await adminOrderStats()
    Object.assign(stats, res.data || {})
  } catch (e) {
    // 静默
  }
}

function resetQuery() {
  Object.assign(query, { page: 1, size: 20, userId: null, orderNo: '', status: null })
  fetchList()
}

async function forcePay(row) {
  try {
    await ElMessageBox.confirm(`确认将订单 ${row.orderNo} 强制支付？`, '提示', { type: 'warning' })
  } catch { return }
  try {
    await adminForcePayOrder(row.orderId)
    ElMessage.success('已支付')
    fetchList(); fetchStats()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

async function forceCancel(row) {
  try {
    await ElMessageBox.confirm(`确认将订单 ${row.orderNo} 强制取消？将回滚库存`, '提示', { type: 'warning' })
  } catch { return }
  try {
    await adminForceCancelOrder(row.orderId)
    ElMessage.success('已取消')
    fetchList(); fetchStats()
  } catch (e) {
    ElMessage.error(e.message || '操作失败')
  }
}

async function confirmDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除订单 ${row.orderNo}？该操作不可恢复`, '提示', { type: 'warning' })
  } catch { return }
  try {
    await adminDeleteOrder(row.orderId)
    ElMessage.success('已删除')
    fetchList(); fetchStats()
  } catch (e) {
    ElMessage.error(e.message || '删除失败')
  }
}

onMounted(() => { fetchList(); fetchStats() })
</script>

<style scoped>
.admin-orders { background: #fff; padding: 16px; border-radius: 8px; }
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.stats { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.stat-chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 12px; background: #f0f2f5; border-radius: 16px; font-size: 13px; color: #606266;
}
.stat-chip b { color: #303133; }
.stat-chip.status-0 { background: #fdf6ec; color: #e6a23c; }
.stat-chip.status-1 { background: #f0f9eb; color: #67c23a; }
.stat-chip.status-4 { background: #fef0f0; color: #f56c6c; }
</style>
