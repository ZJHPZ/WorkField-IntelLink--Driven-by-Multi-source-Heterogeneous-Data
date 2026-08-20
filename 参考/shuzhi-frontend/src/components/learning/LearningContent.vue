<template>
  <div class="space-y-6">
    <div class="glass-card rounded-2xl p-5">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-base font-semibold text-space-800">
          学习范围
          <span class="text-xs font-normal ml-2" style="color: var(--text-muted);">
            选择知识点或自定义集合来过滤学习资料
          </span>
        </h3>
        <button
          @click="showCollectionBuilder = !showCollectionBuilder"
          class="px-3.5 py-2 text-sm font-medium rounded-xl transition-all active:scale-[0.97]"
          :class="showCollectionBuilder ? 'bg-gray-100 text-gray-600 hover:bg-gray-200' : 'bg-brand-500 text-white hover:bg-brand-600 shadow-md shadow-brand-500/20'"
        >
          {{ showCollectionBuilder ? '完成' : '+ 自定义集合' }}
        </button>
      </div>

      <div class="flex flex-wrap gap-1.5 max-h-48 overflow-y-auto py-1">
        <button
          v-for="opt in store.scopeOptions"
          :key="opt.key"
          @click="store.toggleScope(opt.key)"
          class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 border whitespace-nowrap"
          :class="store.isScopeSelected(opt.key)
            ? 'bg-brand-500 text-white border-brand-500 shadow-sm shadow-brand-500/15'
            : opt.type === 'collection'
              ? 'bg-purple-50 text-purple-600 border-purple-200 hover:border-purple-400'
              : 'bg-white text-gray-500 border-gray-200 hover:border-brand-300 hover:text-brand-600'"
        >
          <span v-if="opt.type === 'collection'" class="mr-0.5">📁</span>
          {{ opt.label }}
          <span
            v-if="opt.type === 'collection'"
            class="ml-1 text-[10px] opacity-60"
          >({{ getCollectionItemCount(opt.key) }})</span>
        </button>
      </div>
    </div>

    <Transition name="slide-form">
      <div v-if="showCollectionBuilder" class="glass-card rounded-2xl p-5">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-base font-semibold text-space-800">
            🗂️ 自定义知识集合
          </h3>
          <span class="text-xs" style="color: var(--text-muted);">
            {{ store.collections.length }} 个集合
          </span>
        </div>

        <div class="space-y-3 mb-5">
          <div
            v-for="col in store.collections"
            :key="col.id"
            class="flex items-start gap-3 p-3 rounded-xl border border-gray-100 hover:border-purple-200 transition-colors"
          >
            <span class="text-lg shrink-0 mt-0.5">📁</span>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium" style="color: var(--text-primary);">{{ col.name }}</p>
              <p class="text-[11px] mt-0.5 line-clamp-2" style="color: var(--text-muted);">
                {{ col.items.join('、') }}
              </p>
            </div>
            <div class="flex items-center gap-1 shrink-0">
              <button
                @click="editCollection(col)"
                class="w-6 h-6 rounded-lg flex items-center justify-center text-xs hover:bg-purple-100 transition-colors"
                style="color: var(--text-muted);"
              >✎</button>
              <button
                @click="store.removeCollection(col.id)"
                class="w-6 h-6 rounded-lg flex items-center justify-center text-xs hover:bg-red-100 transition-colors"
                style="color: var(--text-muted);"
              >✕</button>
            </div>
          </div>
          <div v-if="store.collections.length === 0" class="text-center py-4">
            <p class="text-xs" style="color: var(--text-muted);">尚未创建集合，在下方选择知识点并命名即可创建</p>
          </div>
        </div>

        <div class="border-t pt-4" style="border-color: var(--sidebar-border);">
          <p class="text-xs font-medium mb-2" style="color: var(--text-secondary);">
            {{ editingCollection ? '编辑集合: ' + editingCollection.name : '新建集合' }}
          </p>
          <div class="flex flex-wrap gap-1 max-h-40 overflow-y-auto mb-3 p-2 rounded-xl border border-gray-100" style="background: var(--bg-primary);">
            <button
              v-for="pt in store.allKnowledgePoints"
              :key="pt"
              @click="toggleCollectionItem(pt)"
              class="px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all duration-200 border whitespace-nowrap"
              :class="pendingItems.includes(pt)
                ? 'bg-purple-500 text-white border-purple-500 shadow-sm'
                : 'bg-white text-gray-400 border-gray-150 hover:border-purple-300 hover:text-purple-500'"
            >
              {{ pt }}
            </button>
          </div>
          <div class="text-xs mb-3" style="color: var(--text-muted);">
            已选 <b style="color: #8b5cf6;">{{ pendingItems.length }}</b> 个知识点
          </div>
          <div class="flex items-center gap-2">
            <input
              v-model="collectionName"
              @keydown.enter="saveCollection"
              placeholder="输入集合名称..."
              class="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-400"
              style="background: var(--bg-card); color: var(--text-primary);"
            />
            <button
              @click="saveCollection"
              :disabled="!collectionName.trim() || pendingItems.length === 0"
              class="px-4 py-2 text-sm font-medium bg-purple-500 text-white rounded-xl hover:bg-purple-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
            >
              {{ editingCollection ? '更新' : '保存集合' }}
            </button>
            <button
              v-if="editingCollection"
              @click="cancelEdit"
              class="px-3 py-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
            >取消</button>
          </div>
        </div>
      </div>
    </Transition>

    <div class="glass-card rounded-2xl p-5">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-base font-semibold text-space-800">
          学习资料
          <span class="text-xs font-normal ml-2" style="color: var(--text-muted);">
            {{ store.materials.length }} 份资料 · {{ store.formatFileSize(store.totalSize) }}
          </span>
        </h3>
        <button
          @click="toggleAddForm"
          class="px-4 py-2 text-sm font-medium bg-brand-500 text-white rounded-xl hover:bg-brand-600 transition-all shadow-md shadow-brand-500/20 active:scale-[0.97]"
        >
          {{ showAddForm ? '取消' : '+ 新增资料' }}
        </button>
      </div>

      <Transition name="slide-form">
        <div v-if="showAddForm" class="mb-5 p-4 rounded-xl border" style="background: var(--bg-primary); border-color: var(--sidebar-border);">
          <div class="space-y-3">
            <div>
              <label class="block text-xs font-medium mb-1.5" style="color: var(--text-secondary);">资料类型</label>
              <div class="flex gap-2">
                <button
                  v-for="t in materialTypes" :key="t.key"
                  @click="formData.type = t.key"
                  class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all border"
                  :class="formData.type === t.key
                    ? 'bg-brand-50 text-brand-600 border-brand-300'
                    : 'bg-white text-gray-500 border-gray-200 hover:border-gray-300'"
                >{{ t.label }}</button>
              </div>
            </div>

            <div>
              <label class="block text-xs font-medium mb-1.5" style="color: var(--text-secondary);">所属知识点</label>
              <select
                v-model="formData.category"
                class="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400"
                style="background: var(--bg-card); color: var(--text-primary);"
              >
                <optgroup v-if="scopedKnowledgePoints.length" label="当前学习范围">
                  <option v-for="pt in scopedKnowledgePoints" :key="pt" :value="pt">{{ pt }}</option>
                </optgroup>
                <optgroup label="全部知识点">
                  <option v-for="pt in otherKnowledgePoints" :key="pt" :value="pt">{{ pt }}</option>
                </optgroup>
              </select>
            </div>

            <div>
              <label class="block text-xs font-medium mb-1.5" style="color: var(--text-secondary);">标题</label>
              <input
                v-model="formData.title"
                placeholder="资料名称..."
                class="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400"
                style="background: var(--bg-card); color: var(--text-primary);"
              />
            </div>

            <div>
              <label class="block text-xs font-medium mb-1.5" style="color: var(--text-secondary);">描述</label>
              <textarea
                v-model="formData.description"
                rows="2"
                placeholder="简要说明..."
                class="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400"
                style="background: var(--bg-card); color: var(--text-primary);"
              ></textarea>
            </div>

            <div v-if="formData.type === 'file'">
              <label class="block text-xs font-medium mb-1.5" style="color: var(--text-secondary);">上传文件</label>
              <div
                class="border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all hover:border-brand-400 hover:bg-brand-50/30"
                :class="dragOver ? 'border-brand-400 bg-brand-50/40' : 'border-gray-200'"
                style="background: var(--bg-card);"
                @click="triggerFileInput"
                @dragover.prevent="dragOver = true"
                @dragleave.prevent="dragOver = false"
                @drop.prevent="onFileDrop"
              >
                <input ref="fileInput" type="file" class="hidden" @change="onFileSelected" />
                <span class="text-3xl block mb-2">{{ selectedFile ? '📄' : '📁' }}</span>
                <p v-if="selectedFile" class="text-sm font-medium" style="color: var(--text-primary);">
                  {{ selectedFile.name }}
                  <span class="text-xs ml-1" style="color: var(--text-muted);">({{ store.formatFileSize(selectedFile.size) }})</span>
                </p>
                <p v-else class="text-sm" style="color: var(--text-muted);">点击选择文件或拖拽到此处</p>
                <p class="text-xs mt-1" style="color: var(--text-muted); opacity: 0.6;">支持 PDF、Word、PPT、Excel、Markdown、文本及图片文件</p>
              </div>
            </div>

            <div v-if="formData.type === 'link'">
              <label class="block text-xs font-medium mb-1.5" style="color: var(--text-secondary);">链接地址</label>
              <input
                v-model="formData.linkUrl"
                placeholder="https://..."
                class="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-400"
                style="background: var(--bg-card); color: var(--text-primary);"
              />
            </div>

            <button
              @click="submitMaterial"
              :disabled="!canSubmit"
              class="w-full py-2.5 text-sm font-medium bg-brand-500 text-white rounded-xl hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md shadow-brand-500/20"
            >保存资料</button>
          </div>
        </div>
      </Transition>

      <div v-if="store.scopedMaterials.length === 0 && store.materials.length === 0" class="text-center py-10">
        <span class="text-4xl block mb-3">📚</span>
        <p class="text-sm" style="color: var(--text-muted);">还没有学习资料，点击"+ 新增资料"开始创建</p>
      </div>

      <div v-else-if="store.scopedMaterials.length === 0 && store.materials.length > 0" class="text-center py-8">
        <p class="text-sm" style="color: var(--text-muted);">当前选择的学习范围内暂无资料，请调整上方的学习范围</p>
      </div>

      <div v-else class="space-y-2">
        <div
          v-for="mat in store.scopedMaterials"
          :key="mat.id"
          class="flex items-start gap-3 p-3.5 rounded-xl transition-all duration-200 group"
          :class="expandedId === mat.id ? 'bg-brand-50/60 border border-brand-200' : 'hover:bg-gray-50 border border-transparent'"
        >
          <span class="text-2xl shrink-0 mt-0.5">
            {{ mat.type === 'file' ? (isImageFile(mat) ? '🖼️' : fileIcon(mat)) : mat.type === 'link' ? '🔗' : '📝' }}
          </span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <p class="text-sm font-medium truncate" style="color: var(--text-primary);">{{ mat.title }}</p>
              <span class="text-[10px] px-1.5 py-0.5 rounded-full shrink-0 font-medium" :class="typeBadgeClass(mat.type)">{{ typeLabel(mat.type) }}</span>
              <span class="text-[10px] px-1.5 py-0.5 rounded-full bg-gray-100 text-gray-500 shrink-0">{{ mat.category }}</span>
            </div>
            <p v-if="mat.description" class="text-xs mt-1 line-clamp-2" style="color: var(--text-muted);">{{ mat.description }}</p>
            <div class="flex items-center gap-3 mt-1.5 text-[10px]" style="color: var(--text-muted);">
              <span>{{ formatDate(mat.createdAt) }}</span>
              <span v-if="mat.fileSize">{{ store.formatFileSize(mat.fileSize) }}</span>
            </div>

            <div v-if="expandedId === mat.id" class="mt-3 pt-3 border-t border-gray-100">
              <div v-if="mat.type === 'file' && mat.blobUrl">
                <div v-if="isImageFile(mat)" class="rounded-xl overflow-hidden border border-gray-100">
                  <img :src="mat.blobUrl" class="max-w-full max-h-64 object-contain" :alt="mat.title" />
                </div>
                <div v-else-if="isPdfFile(mat)" class="rounded-xl overflow-hidden border border-gray-100">
                  <iframe :src="mat.blobUrl" class="w-full h-96 rounded-xl" frameborder="0"></iframe>
                </div>
                <div v-else class="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                  <span class="text-2xl">{{ fileIcon(mat) }}</span>
                  <div>
                    <p class="text-sm font-medium" style="color: var(--text-primary);">{{ mat.fileName }}</p>
                    <p class="text-xs" style="color: var(--text-muted);">{{ mat.fileType }} · {{ store.formatFileSize(mat.fileSize || 0) }}</p>
                  </div>
                  <a :href="mat.blobUrl" :download="mat.fileName" class="ml-auto px-3 py-1.5 text-xs font-medium bg-brand-500 text-white rounded-lg hover:bg-brand-600 transition-colors no-underline">下载</a>
                </div>
              </div>
              <div v-if="mat.type === 'link' && mat.linkUrl" class="flex items-center gap-2">
                <a :href="mat.linkUrl" target="_blank" rel="noopener" class="text-sm text-brand-500 hover:text-brand-600 underline truncate">{{ mat.linkUrl }}</a>
              </div>
              <div v-if="mat.type === 'note'" class="text-sm leading-relaxed whitespace-pre-line" style="color: var(--text-secondary);">{{ mat.description }}</div>
            </div>
          </div>

          <div class="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              @click="expandedId = expandedId === mat.id ? null : mat.id"
              class="w-7 h-7 rounded-lg flex items-center justify-center text-sm hover:bg-brand-100 transition-colors"
              :style="{ color: 'var(--text-muted)' }"
              :title="expandedId === mat.id ? '收起' : '展开'"
            >{{ expandedId === mat.id ? '▴' : '▾' }}</button>
            <button
              @click="removeMaterial(mat.id)"
              class="w-7 h-7 rounded-lg flex items-center justify-center text-sm hover:bg-red-100 transition-colors"
              style="color: var(--text-muted);"
              title="删除"
            >✕</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useLearningMaterialsStore } from '@/stores/learningMaterials'
import type { LearningMaterial, KnowledgeCollection } from '@/stores/learningMaterials'

const store = useLearningMaterialsStore()

const showAddForm = ref(false)
const showCollectionBuilder = ref(false)
const expandedId = ref<string | null>(null)
const dragOver = ref(false)
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const collectionName = ref('')
const pendingItems = ref<string[]>([])
const editingCollection = ref<KnowledgeCollection | null>(null)

const materialTypes = [
  { key: 'note' as const, label: '学习笔记' },
  { key: 'file' as const, label: '文件资料' },
  { key: 'link' as const, label: '外部链接' },
]

const formData = reactive({
  type: 'note' as 'note' | 'file' | 'link',
  category: store.allKnowledgePoints[0],
  title: '',
  description: '',
  linkUrl: '',
})

const resolvedScope = computed(() => {
  const scope = new Set<string>()
  for (const item of store.selectedScope) {
    const col = store.collections.find(c => c.id === item)
    if (col) {
      for (const pt of col.items) scope.add(pt)
    } else {
      scope.add(item)
    }
  }
  return [...scope]
})

const scopedKnowledgePoints = computed(() =>
  resolvedScope.value.filter(pt => store.allKnowledgePoints.includes(pt))
)

const otherKnowledgePoints = computed(() =>
  store.allKnowledgePoints.filter(pt => !resolvedScope.value.includes(pt))
)

const canSubmit = computed(() =>
  formData.title.trim().length > 0 && formData.category.length > 0 &&
  (formData.type !== 'file' || selectedFile.value !== null) &&
  (formData.type !== 'link' || formData.linkUrl.trim().length > 0)
)

function getCollectionItemCount(key: string): number {
  const col = store.collections.find(c => c.id === key)
  return col ? col.items.length : 0
}

function toggleCollectionItem(point: string) {
  const idx = pendingItems.value.indexOf(point)
  if (idx >= 0) {
    pendingItems.value.splice(idx, 1)
  } else {
    pendingItems.value.push(point)
  }
}

function saveCollection() {
  if (!collectionName.value.trim() || pendingItems.value.length === 0) return
  if (editingCollection.value) {
    store.updateCollection(editingCollection.value.id, collectionName.value, [...pendingItems.value])
    editingCollection.value = null
  } else {
    store.addCollection(collectionName.value, [...pendingItems.value])
  }
  collectionName.value = ''
  pendingItems.value = []
}

function editCollection(col: KnowledgeCollection) {
  editingCollection.value = col
  collectionName.value = col.name
  pendingItems.value = [...col.items]
  showCollectionBuilder.value = true
}

function cancelEdit() {
  editingCollection.value = null
  collectionName.value = ''
  pendingItems.value = []
}

function toggleAddForm() {
  showAddForm.value = !showAddForm.value
  if (showAddForm.value && scopedKnowledgePoints.value.length > 0) {
    formData.category = scopedKnowledgePoints.value[0]
  }
}

function triggerFileInput() {
  fileInput.value?.click()
}

function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    selectedFile.value = input.files[0]
    if (!formData.title) {
      formData.title = input.files[0].name.replace(/\.[^/.]+$/, '')
    }
  }
}

function onFileDrop(e: DragEvent) {
  dragOver.value = false
  if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
    selectedFile.value = e.dataTransfer.files[0]
    if (!formData.title) {
      formData.title = e.dataTransfer.files[0].name.replace(/\.[^/.]+$/, '')
    }
  }
}

async function submitMaterial() {
  if (!canSubmit.value) return
  if (formData.type === 'file' && selectedFile.value) {
    const blobUrl = URL.createObjectURL(selectedFile.value)
    store.addMaterial({
      title: formData.title,
      description: formData.description,
      type: 'file',
      category: formData.category,
      fileName: selectedFile.value.name,
      fileSize: selectedFile.value.size,
      fileType: selectedFile.value.type || 'unknown',
      blobUrl,
    })
    selectedFile.value = null
  } else if (formData.type === 'link') {
    store.addMaterial({
      title: formData.title,
      description: formData.description,
      type: 'link',
      category: formData.category,
      linkUrl: formData.linkUrl,
    })
  } else {
    store.addMaterial({
      title: formData.title,
      description: formData.description,
      type: 'note',
      category: formData.category,
    })
  }
  formData.title = ''
  formData.description = ''
  formData.linkUrl = ''
  showAddForm.value = false
}

function removeMaterial(id: string) {
  if (expandedId.value === id) expandedId.value = null
  store.removeMaterial(id)
}

function typeLabel(type: string): string {
  const map: Record<string, string> = { note: '笔记', file: '文件', link: '链接' }
  return map[type] || type
}

function typeBadgeClass(type: string): string {
  const map: Record<string, string> = {
    note: 'bg-blue-50 text-blue-600',
    file: 'bg-amber-50 text-amber-600',
    link: 'bg-purple-50 text-purple-600',
  }
  return map[type] || 'bg-gray-50 text-gray-500'
}

function isImageFile(mat: LearningMaterial): boolean {
  return mat.fileType?.startsWith('image/') || /\.(png|jpg|jpeg|gif|svg|webp)$/i.test(mat.fileName || '')
}

function isPdfFile(mat: LearningMaterial): boolean {
  return mat.fileType === 'application/pdf' || /\.pdf$/i.test(mat.fileName || '')
}

function fileIcon(mat: LearningMaterial): string {
  const name = (mat.fileName || '').toLowerCase()
  if (/\.(doc|docx)$/i.test(name)) return '📄'
  if (/\.(xls|xlsx|csv)$/i.test(name)) return '📊'
  if (/\.(ppt|pptx)$/i.test(name)) return '📽️'
  if (/\.md$/i.test(name)) return '📋'
  if (/\.(zip|rar|7z|tar|gz)$/i.test(name)) return '📦'
  if (/\.(py|java|scala|js|ts|go|rs)$/i.test(name)) return '💻'
  return '📎'
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  } catch { return iso }
}
</script>

<style scoped>
.slide-form-enter-active,
.slide-form-leave-active {
  transition: all 0.3s ease;
}
.slide-form-enter-from,
.slide-form-leave-to {
  opacity: 0;
  transform: translateY(-8px);
  max-height: 0;
}
.slide-form-enter-to,
.slide-form-leave-from {
  max-height: 800px;
}
</style>
