<template>
  <div class="admin-inventory">
    <div class="toolbar">
      <el-input v-model="query.productId" placeholder="按商品ID搜索" clearable style="width: 200px" @keyup.enter="fetchList" />
      <el-button type="primary" :icon="Search" @click="fetchList">查询</el-button>
      <el-button :icon="Refresh" @click="resetQuery">重置</el-button>
      <el-button type="success" :icon="Plus" @click="openInit">初始化库存</el-button>
    </div>

    <el-table :data="records" v-loading="loading" border stripe>
      <el-table-column prop="productId" label="商品ID" width="100" />
      <el-table-column prop="stock" label="当前库存" width="120" />
      <el-table-column prop="version" label="版本号" width="100" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="openEdit(row)">调整库存</el-button>
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

    <el-dialog v-model="editVisible" title="调整库存" width="420px">
      <el-form :model="editing" label-width="100px">
        <el-form-item label="商品ID">
          <el-input v-model="editing.productId" :disabled="!!editing.id" />
        </el-form-item>
        <el-form-item label="目标库存">
          <el-input-number v-model="editing.stock" :min="0" :step="1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import {
  adminListInventory,
  adminInitInventory,
  adminUpdateInventory
} from '@/api/admin'

const loading = ref(false)
const submitting = ref(false)
const records = ref([])
const total = ref(0)
const editVisible = ref(false)
const editing = reactive({ id: null, productId: null, stock: 0 })
const query = reactive({ page: 1, size: 20, productId: null })

async function fetchList() {
  loading.value = true
  try {
    const params = { page: query.page, size: query.size }
    if (query.productId) params.productId = query.productId
    const res = await adminListInventory(params)
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
  Object.assign(query, { page: 1, size: 20, productId: null })
  fetchList()
}

function openEdit(row) {
  Object.assign(editing, { id: row.productId, productId: row.productId, stock: row.stock })
  editVisible.value = true
}

function openInit() {
  Object.assign(editing, { id: null, productId: null, stock: 0 })
  editVisible.value = true
}

async function submit() {
  if (!editing.productId) {
    ElMessage.warning('请填写商品ID')
    return
  }
  submitting.value = true
  try {
    if (editing.id) {
      await adminUpdateInventory(editing.productId, editing.stock)
      ElMessage.success('已更新')
    } else {
      await adminInitInventory(editing.productId, editing.stock)
      ElMessage.success('已初始化')
    }
    editVisible.value = false
    fetchList()
  } catch (e) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    submitting.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
.admin-inventory { background: #fff; padding: 16px; border-radius: 8px; }
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
</style>
