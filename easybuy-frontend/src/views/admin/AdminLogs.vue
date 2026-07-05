<template>
  <div class="admin-logs">
    <div class="toolbar">
      <el-select v-model="currentFile" placeholder="选择日志文件" filterable style="width: 360px" @change="onFileChange">
        <el-option-group
          v-for="group in groupedFiles"
          :key="group.service"
          :label="group.service"
        >
          <el-option
            v-for="f in group.files"
            :key="f.path"
            :value="f.path"
            :label="`${f.name} (${formatSize(f.size)})`"
          />
        </el-option-group>
      </el-select>
      <el-input-number v-model="tailLines" :min="50" :max="5000" :step="100" style="width: 140px" />
      <el-button type="primary" :icon="Refresh" @click="loadTail">刷新尾部</el-button>
      <el-button :icon="Search" @click="openSearch">搜索</el-button>
      <el-button :icon="Download" @click="downloadFile">下载</el-button>
    </div>

    <el-card v-loading="loading" shadow="never" class="log-card">
      <template #header>
        <div class="card-header">
          <span class="file-name">{{ currentFileName }}</span>
          <span class="meta" v-if="meta.size !== undefined">
            大小: {{ formatSize(meta.size) }} | 行数: {{ meta.lines || 0 }}
          </span>
        </div>
      </template>
      <pre v-if="contentLines.length" class="log-content">{{ contentLines.join('\n') }}</pre>
      <el-empty v-else description="请选择日志文件" />
    </el-card>

    <el-dialog v-model="searchVisible" title="搜索日志" width="520px">
      <el-form :model="searchForm" label-width="80px">
        <el-form-item label="文件">
          <el-input v-model="searchForm.file" disabled />
        </el-form-item>
        <el-form-item label="关键词">
          <el-input v-model="searchForm.keyword" placeholder="例如: ERROR" />
        </el-form-item>
        <el-form-item label="最多结果">
          <el-input-number v-model="searchForm.max" :min="10" :max="2000" :step="50" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="searchVisible = false">取消</el-button>
        <el-button type="primary" :loading="searching" @click="doSearch">搜索</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="resultVisible" :title="`搜索结果 (${searchResults.length} 条)`" width="80%">
      <el-table :data="searchResults" max-height="60vh" border>
        <el-table-column prop="line" label="行号" width="80" />
        <el-table-column prop="content" label="内容" />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Search, Download } from '@element-plus/icons-vue'
import {
  adminListLogFiles,
  adminTailLog,
  adminSearchLog,
  adminLogDownloadUrl
} from '@/api/admin'
import { useUserStore } from '@/stores/userStore'

const userStore = useUserStore()

const loading = ref(false)
const searching = ref(false)
const files = ref([])
const currentFile = ref('')
const currentFileName = computed(() => {
  if (!currentFile.value) return ''
  const idx = currentFile.value.lastIndexOf('\\')
  return idx >= 0 ? currentFile.value.substring(idx + 1) : currentFile.value
})
const tailLines = ref(200)
const contentLines = ref([])
const meta = reactive({ size: 0, lines: 0 })

const searchVisible = ref(false)
const resultVisible = ref(false)
const searchResults = ref([])
const searchForm = reactive({ file: '', keyword: '', max: 200 })

const groupedFiles = computed(() => {
  const groups = {}
  for (const f of files.value) {
    const svc = f.service || 'other'
    if (!groups[svc]) groups[svc] = []
    groups[svc].push(f)
  }
  return Object.keys(groups).sort().map(k => ({ service: k, files: groups[k] }))
})

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(2) + ' MB'
}

async function loadFiles() {
  try {
    const res = await adminListLogFiles()
    files.value = res.data?.files || []
    if (files.value.length && !currentFile.value) {
      // 默认选第一个 gateway 的日志
      const gateway = files.value.find(f => f.service === 'gateway')
      currentFile.value = (gateway || files.value[0]).path
      loadTail()
    }
  } catch (e) {
    ElMessage.error(e.message || '加载文件列表失败')
  }
}

async function loadTail() {
  if (!currentFile.value) return
  loading.value = true
  try {
    const res = await adminTailLog(currentFile.value, tailLines.value)
    contentLines.value = res.data?.content || []
    meta.size = res.data?.size || 0
    meta.lines = contentLines.value.length
  } catch (e) {
    ElMessage.error(e.message || '加载日志失败')
  } finally {
    loading.value = false
  }
}

function onFileChange() {
  loadTail()
}

function openSearch() {
  if (!currentFile.value) {
    ElMessage.warning('请先选择日志文件')
    return
  }
  Object.assign(searchForm, { file: currentFileName.value, keyword: '', max: 200 })
  searchVisible.value = true
}

async function doSearch() {
  if (!searchForm.keyword) {
    ElMessage.warning('请输入关键词')
    return
  }
  searching.value = true
  try {
    const res = await adminSearchLog(currentFile.value, searchForm.keyword, searchForm.max)
    searchResults.value = res.data?.hits || []
    resultVisible.value = true
    searchVisible.value = false
  } catch (e) {
    ElMessage.error(e.message || '搜索失败')
  } finally {
    searching.value = false
  }
}

function downloadFile() {
  if (!currentFile.value) {
    ElMessage.warning('请先选择日志文件')
    return
  }
  const url = adminLogDownloadUrl(currentFile.value)
  // 带上 token
  const token = userStore.token
  const a = document.createElement('a')
  a.href = token ? `${url}&_t=${encodeURIComponent(token)}` : url
  // 通过 axios + blob 下载更稳
  import('@/api/request').then(({ default: req }) => {
    req({ url, method: 'GET', responseType: 'blob' })
      .then(blob => {
        const blobUrl = URL.createObjectURL(new Blob([blob]))
        const link = document.createElement('a')
        link.href = blobUrl
        link.download = currentFileName.value
        link.click()
        URL.revokeObjectURL(blobUrl)
      })
      .catch(err => ElMessage.error(err.message || '下载失败'))
  })
}

onMounted(loadFiles)
</script>

<style scoped>
.admin-logs { background: #fff; padding: 16px; border-radius: 8px; }
.toolbar { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; align-items: center; }
.log-card { border-radius: 8px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.file-name { font-family: 'Consolas', monospace; font-weight: 600; }
.meta { color: #909399; font-size: 12px; }
.log-content {
  background: #1e1e1e; color: #d4d4d4; padding: 12px; border-radius: 4px;
  max-height: 60vh; overflow: auto; font-family: 'Consolas', monospace;
  font-size: 12px; line-height: 1.5; white-space: pre;
}
</style>
