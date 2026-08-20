<template>
  <div class="space-y-6 animate-fade-in-up">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-space-800"><img :src="planListIcon" class="icon-title" alt="" /> 考试中心</h1>
        <p class="text-gray-400 text-sm mt-1">选择试卷开始考试，检验你的学习成果</p>
      </div>
      <button
        v-if="isAdmin"
        class="px-5 py-2.5 bg-brand-500 text-white rounded-xl font-medium text-sm hover:bg-brand-600 transition-all shadow-lg shadow-brand-500/25 active:scale-[0.98] flex items-center gap-2"
        @click="openCreateForm"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
        创建试卷
      </button>
    </div>

    <!-- Tabs -->
    <div class="flex gap-1 bg-gray-100 rounded-xl p-1 w-fit">
      <button
        class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
        :class="activeTab === 'papers' ? 'bg-white text-space-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
        @click="activeTab = 'papers'"
      >{{ isAdmin ? '试卷管理' : '可用试卷' }}</button>
      <button
        class="px-4 py-2 rounded-lg text-sm font-medium transition-all"
        :class="activeTab === 'history' ? 'bg-white text-space-700 shadow-sm' : 'text-gray-500 hover:text-gray-700'"
        @click="activeTab = 'history'; fetchHistory()"
      >历史考试</button>
    </div>

    <!-- Papers tab -->
    <div v-if="activeTab === 'papers'">
      <!-- Loading -->
      <div v-if="examStore.papersLoading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div v-for="i in 6" :key="i" class="glass-card rounded-2xl p-5 h-56 animate-pulse">
          <div class="h-5 bg-gray-200 rounded w-2/3 mb-3" />
          <div class="h-4 bg-gray-100 rounded w-full mb-2" />
          <div class="h-4 bg-gray-100 rounded w-3/4 mb-4" />
          <div class="grid grid-cols-2 gap-2 mb-4">
            <div class="h-4 bg-gray-100 rounded" />
            <div class="h-4 bg-gray-100 rounded" />
          </div>
          <div class="h-10 bg-gray-200 rounded-xl" />
        </div>
      </div>

      <!-- Papers grid -->
      <div v-else-if="examStore.papers.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <PaperCard
          v-for="paper in examStore.papers"
          :key="paper.id"
          :paper="paper"
          :is-admin="isAdmin"
          @start="startExam(paper.id)"
          @edit="openEditForm(paper)"
          @delete="confirmDelete(paper)"
          @toggle-publish="handleTogglePublish(paper)"
        />
      </div>

      <!-- Empty -->
      <div v-else class="glass-card rounded-2xl p-12 text-center">
        <img :src="planListIcon" class="icon-empty mx-auto mb-4" alt="" />
        <h3 class="text-lg font-semibold text-gray-600 mb-2">暂无试卷</h3>
        <p class="text-sm text-gray-400 mb-4">{{ isAdmin ? '点击上方按钮创建第一张试卷' : '请联系管理员创建试卷' }}</p>
        <button
          v-if="isAdmin"
          class="px-5 py-2.5 bg-brand-500 text-white rounded-xl font-medium text-sm hover:bg-brand-600 transition-all shadow-lg shadow-brand-500/25 active:scale-[0.98]"
          @click="openCreateForm"
        >创建试卷</button>
      </div>
    </div>

    <!-- History tab -->
    <div v-if="activeTab === 'history'">
      <div v-if="examStore.historyLoading" class="space-y-3">
        <div v-for="i in 5" :key="i" class="glass-card rounded-xl p-4 h-16 animate-pulse">
          <div class="h-4 bg-gray-200 rounded w-1/3" />
        </div>
      </div>

      <div v-else-if="examStore.history.length > 0" class="space-y-3">
        <div
          v-for="item in examStore.history"
          :key="item.session_id"
          class="glass-card rounded-xl p-4 flex items-center gap-4 cursor-pointer hover:shadow-md transition-all"
          @click="router.push(`/exam/${item.session_id}/result`)"
        >
          <div class="w-12 h-12 rounded-xl flex items-center justify-center text-xl shrink-0"
            :class="item.is_passed ? 'bg-mint-50' : 'bg-rose-50'">
            {{ item.is_passed ? '✅' : '❌' }}
          </div>
          <div class="flex-1 min-w-0">
            <h4 class="text-sm font-semibold text-space-800 truncate">{{ item.paper_title }}</h4>
            <p class="text-xs text-gray-400">
              {{ formatDate(item.started_at) }}
              <template v-if="item.status === 'in_progress'">
                · <span class="text-amber-500 font-medium">未完成</span>
              </template>
            </p>
          </div>
          <div class="text-right shrink-0">
            <div class="text-lg font-bold tabular-nums" :class="item.is_passed ? 'text-mint-600' : 'text-rose-600'">
              {{ item.total_score }}
            </div>
            <div class="text-xs text-gray-400">{{ item.accuracy }}% · {{ item.correct_count }}/{{ item.total_questions }}</div>
          </div>
          <div class="text-gray-400 text-lg">›</div>
        </div>
      </div>

      <div v-else class="glass-card rounded-2xl p-12 text-center">
        <img :src="pieChartIcon" class="icon-empty mx-auto mb-4" alt="" />
        <h3 class="text-lg font-semibold text-gray-600 mb-2">暂无考试记录</h3>
        <p class="text-sm text-gray-400">完成一场考试后，记录将显示在这里</p>
      </div>
    </div>

    <!-- Paper form modal -->
    <PaperForm
      v-if="showPaperForm"
      :paper="editingPaper"
      @close="closePaperForm"
      @saved="onPaperSaved"
    />

    <!-- Start confirm modal -->
    <Teleport to="body">
      <div
        v-if="showStartModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click.self="showStartModal = false"
      >
        <div class="bg-white rounded-2xl p-6 w-full max-w-md mx-4 shadow-2xl animate-scale-in">
          <h3 class="text-lg font-semibold text-space-800 mb-2">确认开始考试</h3>
          <div class="text-sm text-gray-500 space-y-1 mb-4">
            <p><strong class="text-gray-700">试卷：</strong>{{ selectedPaper?.title }}</p>
            <p><strong class="text-gray-700">题目数：</strong>{{ selectedPaper?.total_questions }} 题</p>
            <p><strong class="text-gray-700">考试时长：</strong>{{ selectedPaper?.time_limit }} 分钟</p>
            <p><strong class="text-gray-700">及格线：</strong>{{ selectedPaper?.passing_score }}%</p>
            <p class="text-amber-600 mt-2">⚠️ 开始后计时将立即启动，请合理安排时间</p>
          </div>
          <div class="flex gap-3">
            <button
              class="flex-1 py-3 border border-gray-200 text-gray-600 rounded-xl font-medium text-sm hover:bg-gray-50 transition-colors"
              @click="showStartModal = false"
            >取消</button>
            <button
              class="flex-1 py-3 bg-brand-500 text-white rounded-xl font-medium text-sm hover:bg-brand-600 transition-all shadow-lg shadow-brand-500/25 active:scale-[0.98]"
              :disabled="starting"
              @click="confirmStart"
            >
              <span v-if="starting" class="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
              {{ starting ? '加载中...' : '开始考试' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Delete confirm modal -->
    <Teleport to="body">
      <div
        v-if="showDeleteModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click.self="showDeleteModal = false"
      >
        <div class="bg-white rounded-2xl p-6 w-full max-w-md mx-4 shadow-2xl animate-scale-in">
          <h3 class="text-lg font-semibold text-space-800 mb-2">确认删除</h3>
          <p class="text-sm text-gray-500 mb-4">
            确定要删除试卷 <strong class="text-gray-700">"{{ deletingPaper?.title }}"</strong> 吗？此操作不可撤销。
          </p>
          <div class="flex gap-3">
            <button
              class="flex-1 py-3 border border-gray-200 text-gray-600 rounded-xl font-medium text-sm hover:bg-gray-50 transition-colors"
              @click="showDeleteModal = false"
            >取消</button>
            <button
              class="flex-1 py-3 bg-rose-500 text-white rounded-xl font-medium text-sm hover:bg-rose-600 transition-all shadow-lg shadow-rose-500/25 active:scale-[0.98]"
              :disabled="deleting"
              @click="handleDelete"
            >
              <span v-if="deleting" class="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
              {{ deleting ? '删除中...' : '确认删除' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useExamStore, type ExamPaper } from '@/stores/exam'
import PaperCard from '@/components/exam/PaperCard.vue'
import PaperForm from '@/components/exam/PaperForm.vue'
import planListIcon from '@/assets/icons/blue/plan-list-svgrepo-com.svg'
import pieChartIcon from '@/assets/icons/jian/pie-chart-svgrepo-com.svg'

const router = useRouter()
const examStore = useExamStore()

const activeTab = ref<'papers' | 'history'>('papers')
const showStartModal = ref(false)
const selectedPaper = ref<ExamPaper | null>(null)
const starting = ref(false)

// Admin state
const isAdmin = computed(() => localStorage.getItem('user_id') === 'admin_user')
const showPaperForm = ref(false)
const editingPaper = ref<ExamPaper | null>(null)
const showDeleteModal = ref(false)
const deletingPaper = ref<ExamPaper | null>(null)
const deleting = ref(false)

onMounted(() => {
  // Admin sees all papers, students only see active ones
  examStore.fetchPapers(!isAdmin.value)
})

async function startExam(paperId: string) {
  const paper = examStore.papers.find(p => p.id === paperId)
  if (!paper) return
  selectedPaper.value = paper
  showStartModal.value = true
}

async function confirmStart() {
  if (!selectedPaper.value) return
  starting.value = true
  try {
    await examStore.startExam(selectedPaper.value.id)
    showStartModal.value = false
    router.push(`/exam/${examStore.session?.session_id}`)
  } catch (e: any) {
    alert('开始考试失败: ' + (e.message || '请稍后重试'))
  } finally {
    starting.value = false
  }
}

// Admin actions
function openCreateForm() {
  editingPaper.value = null
  showPaperForm.value = true
}

function openEditForm(paper: ExamPaper) {
  editingPaper.value = paper
  showPaperForm.value = true
}

function closePaperForm() {
  showPaperForm.value = false
  editingPaper.value = null
}

function onPaperSaved() {
  // Refresh papers list after save
  examStore.fetchPapers(!isAdmin.value)
}

function confirmDelete(paper: ExamPaper) {
  deletingPaper.value = paper
  showDeleteModal.value = true
}

async function handleDelete() {
  if (!deletingPaper.value) return
  deleting.value = true
  try {
    await examStore.deletePaper(deletingPaper.value.id)
    showDeleteModal.value = false
    deletingPaper.value = null
  } catch (e: any) {
    alert('删除失败: ' + (e.message || '请稍后重试'))
  } finally {
    deleting.value = false
  }
}

async function handleTogglePublish(paper: ExamPaper) {
  try {
    await examStore.togglePublish(paper.id, !paper.is_active)
  } catch (e: any) {
    alert('操作失败: ' + (e.message || '请稍后重试'))
  }
}

function fetchHistory() {
  examStore.fetchHistory()
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}
</script>

<style scoped>
.icon-title {
  width: 1.5em;
  height: 1.5em;
  display: inline-block;
  vertical-align: middle;
}

.icon-empty {
  width: 3em;
  height: 3em;
  display: block;
}
</style>
