import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface LearningMaterial {
  id: string
  title: string
  description: string
  type: 'note' | 'file' | 'link'
  category: string
  fileName?: string
  fileSize?: number
  fileType?: string
  blobUrl?: string
  linkUrl?: string
  createdAt: string
}

export interface KnowledgeCollection {
  id: string
  name: string
  items: string[]
}

const STORAGE_KEY = 'shuzhi_learning_materials'
const COLLECTIONS_KEY = 'shuzhi_knowledge_collections'

const DEFAULT_KNOWLEDGE_POINTS = [
  'Linux 基础命令',
  'SQL 基础查询',
  'Python 编程基础',
  'Scala 语言入门',
  '大数据概述',
  '分布式系统原理',
  'CAP 理论与一致性',
  'HDFS 架构设计',
  'HDFS 读写流程',
  'NameNode 与 DataNode',
  'MapReduce 编程模型',
  'MapReduce Shuffle 过程',
  'MapReduce 性能优化',
  'YARN 资源调度',
  'YARN 架构组件',
  'Hive 数据仓库',
  'Hive SQL 优化',
  'HBase 列式数据库',
  'HBase 数据模型设计',
  'ZooKeeper 协调服务',
  'ZooKeeper 选举机制',
  'Spark Core 核心原理',
  'RDD 弹性分布式数据集',
  'Spark 内存管理与调优',
  'Spark SQL 数据处理',
  'DataFrame 与 DataSet API',
  'Spark Streaming 流处理',
  'Structured Streaming 结构化流',
  'Kafka 消息系统',
  'Kafka 分区与副本机制',
  'Kafka 可靠性投递',
  'Flink 实时计算引擎',
  'Flink Checkpoint 容错机制',
  'Flink 窗口计算与水位线',
  '数据仓库建模',
  '维度建模与星型模型',
  '数据湖架构设计',
  'Delta Lake 数据湖',
  'ETL 数据管道工程',
  '数据集成与调度',
  '机器学习基础',
  '特征工程',
  '模型评估与超参调优',
  '深度学习入门',
  '神经网络与反向传播',
  '数据挖掘方法论',
  '聚类与分类算法',
  '大数据项目实战',
  '性能调优与排错',
]

function genId(): string {
  return `mat_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

function loadFromStorage(): LearningMaterial[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const data = JSON.parse(raw)
      if (Array.isArray(data)) return data
    }
  } catch {}
  return []
}

function saveToStorage(materials: LearningMaterial[]) {
  try {
    const toSave = materials.map(m => ({ ...m, blobUrl: undefined }))
    localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave))
  } catch {}
}

function loadCollections(): KnowledgeCollection[] {
  try {
    const raw = localStorage.getItem(COLLECTIONS_KEY)
    if (raw) {
      const data = JSON.parse(raw)
      if (Array.isArray(data)) return data
    }
  } catch {}
  return []
}

function saveCollections(collections: KnowledgeCollection[]) {
  try {
    localStorage.setItem(COLLECTIONS_KEY, JSON.stringify(collections))
  } catch {}
}

export const useLearningMaterialsStore = defineStore('learningMaterials', () => {
  const materials = ref<LearningMaterial[]>(loadFromStorage())
  const collections = ref<KnowledgeCollection[]>(loadCollections())
  const selectedScope = ref<string[]>(['Linux 基础命令', 'SQL 基础查询', 'Python 编程基础', '大数据概述', '分布式系统原理'])

  const allKnowledgePoints = computed(() => DEFAULT_KNOWLEDGE_POINTS)

  const scopeOptions = computed(() => {
    const individual = DEFAULT_KNOWLEDGE_POINTS.map(p => ({ label: p, key: p, type: 'point' as const }))
    const grouped = collections.value.map(c => ({ label: c.name, key: c.id, type: 'collection' as const }))
    return [...individual, ...grouped]
  })

  function resolveScope(): string[] {
    const resolved = new Set<string>()
    for (const item of selectedScope.value) {
      const col = collections.value.find(c => c.id === item)
      if (col) {
        for (const pt of col.items) resolved.add(pt)
      } else {
        resolved.add(item)
      }
    }
    return [...resolved]
  }

  const scopedMaterials = computed(() => {
    const scope = resolveScope()
    return materials.value.filter(m => scope.includes(m.category))
  })

  const materialsByCategory = computed(() => {
    const map = new Map<string, LearningMaterial[]>()
    for (const cat of DEFAULT_KNOWLEDGE_POINTS) {
      map.set(cat, materials.value.filter(m => m.category === cat))
    }
    return map
  })

  const totalSize = computed(() =>
    materials.value.reduce((sum, m) => sum + (m.fileSize || 0), 0)
  )

  function addMaterial(mat: Omit<LearningMaterial, 'id' | 'createdAt'>) {
    const item: LearningMaterial = { ...mat, id: genId(), createdAt: new Date().toISOString() }
    materials.value.push(item)
    saveToStorage(materials.value)
    return item
  }

  function removeMaterial(id: string) {
    const idx = materials.value.findIndex(m => m.id === id)
    if (idx >= 0) {
      const m = materials.value[idx]
      if (m.blobUrl) URL.revokeObjectURL(m.blobUrl)
      materials.value.splice(idx, 1)
      saveToStorage(materials.value)
    }
  }

  function updateMaterial(id: string, updates: Partial<LearningMaterial>) {
    const m = materials.value.find(x => x.id === id)
    if (m) {
      Object.assign(m, updates)
      saveToStorage(materials.value)
    }
  }

  function addCollection(name: string, items: string[]) {
    const col: KnowledgeCollection = { id: genId(), name: name.trim(), items }
    collections.value.push(col)
    saveCollections(collections.value)
    return col
  }

  function updateCollection(id: string, name: string, items: string[]) {
    const col = collections.value.find(c => c.id === id)
    if (col) {
      col.name = name.trim()
      col.items = items
      saveCollections(collections.value)
    }
  }

  function removeCollection(id: string) {
    const idx = collections.value.findIndex(c => c.id === id)
    if (idx >= 0) {
      collections.value.splice(idx, 1)
      selectedScope.value = selectedScope.value.filter(s => s !== id)
      saveCollections(collections.value)
    }
  }

  function toggleScope(key: string) {
    const idx = selectedScope.value.indexOf(key)
    if (idx >= 0) {
      selectedScope.value.splice(idx, 1)
    } else {
      selectedScope.value.push(key)
    }
  }

  function isScopeSelected(key: string): boolean {
    return selectedScope.value.includes(key)
  }

  function setScope(keys: string[]) {
    selectedScope.value = [...keys]
  }

  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / 1048576).toFixed(1) + ' MB'
  }

  return {
    materials,
    collections,
    selectedScope,
    allKnowledgePoints,
    scopeOptions,
    scopedMaterials,
    materialsByCategory,
    totalSize,
    addMaterial,
    removeMaterial,
    updateMaterial,
    addCollection,
    updateCollection,
    removeCollection,
    toggleScope,
    isScopeSelected,
    setScope,
    formatFileSize,
  }
})
