<template>
  <div class="admin-products">
    <div class="toolbar">
      <el-input v-model="query.keyword" placeholder="按商品名称搜索" clearable style="width: 220px" @keyup.enter="fetchList" />
      <el-input v-model="query.category" placeholder="分类" clearable style="width: 160px" @keyup.enter="fetchList" />
      <el-select v-model="query.status" placeholder="状态" clearable style="width: 120px">
        <el-option label="在售" :value="1" />
        <el-option label="下架" :value="0" />
      </el-select>
      <el-button type="primary" :icon="Search" @click="fetchList">查询</el-button>
      <el-button :icon="Refresh" @click="resetQuery">重置</el-button>
      <el-button type="success" :icon="Plus" @click="openCreate">新增商品</el-button>
    </div>

    <el-table :data="records" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="图片" width="90">
        <template #default="{ row }">
          <img :src="row.imageUrl || ''" class="thumb" @error="onImgError" />
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名称" min-width="180" />
      <el-table-column prop="category" label="分类" width="110" />
      <el-table-column label="价格" width="100">
        <template #default="{ row }">¥{{ row.price }}</template>
      </el-table-column>
      <el-table-column prop="stock" label="库存" width="80" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
            {{ row.status === 1 ? '在售' : '下架' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
      <el-table-column label="操作" width="170" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="openEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="confirmDelete(row)">删除</el-button>
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

    <el-dialog v-model="dialogVisible" :title="editing.id ? '编辑商品' : '新增商品'" width="520px">
      <el-form :model="editing" label-width="80px" :rules="formRules" ref="formRef">
        <el-form-item label="名称" prop="name">
          <el-input v-model="editing.name" />
        </el-form-item>
        <el-form-item label="价格" prop="price">
          <el-input-number v-model="editing.price" :min="0" :precision="2" :step="1" />
        </el-form-item>
        <el-form-item label="库存" prop="stock">
          <el-input-number v-model="editing.stock" :min="0" :step="1" />
        </el-form-item>
        <el-form-item label="分类" prop="category">
          <el-input v-model="editing.category" />
        </el-form-item>
        <el-form-item label="图片URL" prop="imageUrl">
          <el-input v-model="editing.imageUrl" placeholder="https://..." />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="editing.status">
            <el-radio :value="1">在售</el-radio>
            <el-radio :value="0">下架</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="editing.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus } from '@element-plus/icons-vue'
import {
  adminListProducts,
  adminCreateProduct,
  adminUpdateProduct,
  adminDeleteProduct
} from '@/api/admin'

const loading = ref(false)
const submitting = ref(false)
const records = ref([])
const total = ref(0)
const dialogVisible = ref(false)
const formRef = ref(null)

const query = reactive({ page: 1, size: 20, keyword: '', category: '', status: null })
const editing = reactive({ id: null, name: '', price: 0, stock: 0, category: '', imageUrl: '', status: 1, description: '' })

const formRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  price: [{ required: true, message: '请输入价格', trigger: 'blur' }],
  stock: [{ required: true, message: '请输入库存', trigger: 'blur' }]
}

async function fetchList() {
  loading.value = true
  try {
    const res = await adminListProducts(query)
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
  Object.assign(query, { page: 1, size: 20, keyword: '', category: '', status: null })
  fetchList()
}

function openCreate() {
  Object.assign(editing, { id: null, name: '', price: 0, stock: 0, category: '', imageUrl: '', status: 1, description: '' })
  dialogVisible.value = true
}

function openEdit(row) {
  Object.assign(editing, { ...row })
  dialogVisible.value = true
}

async function submit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    if (editing.id) {
      await adminUpdateProduct(editing.id, editing)
      ElMessage.success('已更新')
    } else {
      await adminCreateProduct(editing)
      ElMessage.success('已创建')
    }
    dialogVisible.value = false
    fetchList()
  } catch (e) {
    ElMessage.error(e.message || '保存失败')
  } finally {
    submitting.value = false
  }
}

async function confirmDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除商品 "${row.name}"？`, '提示', { type: 'warning' })
  } catch { return }
  try {
    await adminDeleteProduct(row.id)
    ElMessage.success('已删除')
    fetchList()
  } catch (e) {
    ElMessage.error(e.message || '删除失败')
  }
}

function onImgError(e) {
  e.target.src = 'data:image/svg+xml;utf8,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80"><rect width="80" height="80" fill="#eee"/><text x="50%" y="50%" text-anchor="middle" dy=".3em" font-size="14" fill="#999">无图</text></svg>')
}

onMounted(fetchList)
</script>

<style scoped>
.admin-products { background: #fff; padding: 16px; border-radius: 8px; }
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.thumb { width: 56px; height: 56px; object-fit: cover; border-radius: 4px; }
</style>
