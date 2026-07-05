<template>
  <div class="admin-users">
    <div class="toolbar">
      <el-input v-model="query.keyword" placeholder="按用户名搜索" clearable style="width: 240px" @keyup.enter="fetchList" />
      <el-button type="primary" :icon="Search" @click="fetchList">查询</el-button>
      <el-button :icon="Refresh" @click="resetQuery">重置</el-button>
    </div>

    <el-table :data="records" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" min-width="160" />
      <el-table-column label="角色" width="120">
        <template #default="{ row }">
          <el-tag :type="row.role === 'ADMIN' ? 'danger' : 'info'" size="small">
            {{ row.role }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createdAt" label="注册时间" min-width="200" />
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <el-button size="small" :disabled="row.username === 'admin'" @click="changeRole(row)">
            {{ row.role === 'ADMIN' ? '降为 USER' : '升为 ADMIN' }}
          </el-button>
          <el-button size="small" type="danger" :disabled="row.username === 'admin'" @click="confirmDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-if="total > 0"
      v-model:current-page="query.page"
      v-model:page-size="query.size"
      :total="total"
      :page-sizes="[10, 20, 50]"
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
import { adminListUsers, adminUpdateUserRole, adminDeleteUser } from '@/api/admin'

const loading = ref(false)
const records = ref([])
const total = ref(0)
const query = reactive({ page: 1, size: 20, keyword: '' })

async function fetchList() {
  loading.value = true
  try {
    const res = await adminListUsers(query)
    const data = res.data || {}
    records.value = data.records || []
    total.value = data.total || 0
  } catch (e) {
    ElMessage.error(e.message || '加载失败')
  } finally {
    loading.value = false
  }
}

function resetQuery() {
  Object.assign(query, { page: 1, size: 20, keyword: '' })
  fetchList()
}

async function changeRole(row) {
  const newRole = row.role === 'ADMIN' ? 'USER' : 'ADMIN'
  try {
    await ElMessageBox.confirm(`确认将 ${row.username} 的角色改为 ${newRole}？`, '提示', { type: 'warning' })
  } catch { return }
  try {
    await adminUpdateUserRole(row.id, newRole)
    ElMessage.success('已更新')
    fetchList()
  } catch (e) {
    ElMessage.error(e.message || '更新失败')
  }
}

async function confirmDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除用户 ${row.username}？`, '提示', { type: 'warning' })
  } catch { return }
  try {
    await adminDeleteUser(row.id)
    ElMessage.success('已删除')
    fetchList()
  } catch (e) {
    ElMessage.error(e.message || '删除失败')
  }
}

onMounted(fetchList)
</script>

<style scoped>
.admin-users { background: #fff; padding: 16px; border-radius: 8px; }
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; }
</style>
