import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import client from '@/api/client'

export interface LearningStage {
  stageId: number
  title: string
  topics: string[]
  activities?: string[]
  estimatedDays: number
  status: 'locked' | 'available' | 'in_progress' | 'completed'
  progress: number
}

export interface LearningPath {
  pathId: number
  subject: string
  title: string
  totalStages: number
  estimatedDuration: string
  currentStage: number
  overallProgress: number
  totalStudyHours: number
  stages: LearningStage[]
}

export interface TopicMastery {
  topicId: string
  name: string
  category: string
  masteryLevel: number
  status: 'mastered' | 'learning' | 'locked'
  positionX: number
  positionY: number
}

export interface KnowledgeEdge {
  fromTopic: string
  toTopic: string
  relationType: string
  strength: number
}

export interface ReviewItem {
  id: string
  topicId: string
  topicName: string
  priority: 'high' | 'medium' | 'low'
  retentionRate: number
  lastReviewedAt: string
  dueReason: string
}

function mapStatus(masteryLevel: number, nodeStatus?: string): TopicMastery['status'] {
  if (nodeStatus === 'mastered' || masteryLevel >= 0.85) return 'mastered'
  if (nodeStatus === 'learning' || masteryLevel > 0) return 'learning'
  return 'locked'
}

function getUserId(): string {
  return localStorage.getItem('user_id') || 'default_user'
}

function mapPriority(priority: number): ReviewItem['priority'] {
  if (priority >= 70) return 'high'
  if (priority >= 40) return 'medium'
  return 'low'
}

export const useLearningStore = defineStore('learning', () => {
  const currentPath = ref<LearningPath | null>(null)
  const topicMasteryList = ref<TopicMastery[]>([])
  const reviewItems = ref<ReviewItem[]>([])
  const flowState = ref<'flow' | 'engaged' | 'bored' | 'frustrated'>('engaged')
  const curiosityIndex = ref(75)
  const streakDays = ref(0)
  const todayMinutes = ref(0)
  const knowledgeEdges = ref<KnowledgeEdge[]>([])
  const isLoading = ref(false)

  const overallProgress = computed(() => currentPath.value?.overallProgress ?? 0)
  const masteredCount = computed(() => topicMasteryList.value.filter(t => t.status === 'mastered').length)
  const totalTopics = computed(() => topicMasteryList.value.length)
  const urgentReviews = computed(() => reviewItems.value.filter(r => r.priority === 'high'))

  // Demo fallback data
  const demoPath: LearningPath = {
    pathId: 1, subject: '大数据', title: '大数据工程师成长之路',
    totalStages: 5, estimatedDuration: '90天', currentStage: 2,
    overallProgress: 35.5, totalStudyHours: 45.5,
    stages: [
      { stageId: 1, title: '阶段1: 大数据基础', topics: ['大数据概述', 'Linux基础', 'SQL基础'], estimatedDays: 15, status: 'completed', progress: 100 },
      { stageId: 2, title: '阶段2: Hadoop核心', topics: ['HDFS', 'MapReduce', 'YARN'], estimatedDays: 20, status: 'in_progress', progress: 45 },
      { stageId: 3, title: '阶段3: Spark生态', topics: ['Spark Core', 'Spark SQL', 'Spark Streaming'], estimatedDays: 25, status: 'available', progress: 0 },
      { stageId: 4, title: '阶段4: 实时计算', topics: ['Kafka', 'Flink', 'HBase'], estimatedDays: 20, status: 'locked', progress: 0 },
      { stageId: 5, title: '阶段5: 综合实战', topics: ['数据仓库', '数据湖', '项目实战'], estimatedDays: 10, status: 'locked', progress: 0 },
    ],
  }

  const demoTopicMastery: TopicMastery[] = [
    { topicId: 'sql', name: 'SQL基础', category: 'foundation', masteryLevel: 0.95, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'linux', name: 'Linux基础', category: 'foundation', masteryLevel: 0.88, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'hdfs', name: 'HDFS', category: 'core', masteryLevel: 0.72, status: 'learning', positionX: 0, positionY: 0 },
    { topicId: 'mapreduce', name: 'MapReduce', category: 'core', masteryLevel: 0.45, status: 'learning', positionX: 0, positionY: 0 },
    { topicId: 'yarn', name: 'YARN', category: 'core', masteryLevel: 0.30, status: 'learning', positionX: 0, positionY: 0 },
    { topicId: 'spark_core', name: 'Spark Core', category: 'advanced', masteryLevel: 0.00, status: 'locked', positionX: 0, positionY: 0 },
    { topicId: 'spark_sql', name: 'Spark SQL', category: 'advanced', masteryLevel: 0.00, status: 'locked', positionX: 0, positionY: 0 },
    { topicId: 'kafka', name: 'Kafka', category: 'advanced', masteryLevel: 0.00, status: 'locked', positionX: 0, positionY: 0 },
  ]

  function daysAgo(n: number): string {
    const d = new Date()
    d.setDate(d.getDate() - n)
    return d.toISOString().split('T')[0]
  }

  const demoReviews: ReviewItem[] = [
    { id: '1', topicId: 'mapreduce', topicName: 'MapReduce 编程模型', priority: 'high', retentionRate: 28, lastReviewedAt: daysAgo(12), dueReason: '保留率低于30%，建议立即复习' },
    { id: '2', topicId: 'hdfs', topicName: 'HDFS 数据块', priority: 'high', retentionRate: 25, lastReviewedAt: daysAgo(14), dueReason: '遗忘曲线显示需要巩固' },
    { id: '3', topicId: 'yarn', topicName: 'YARN 资源调度', priority: 'medium', retentionRate: 45, lastReviewedAt: daysAgo(5), dueReason: '2天后复习效果最佳' },
    { id: '4', topicId: 'linux', topicName: 'Linux 基础命令', priority: 'low', retentionRate: 62, lastReviewedAt: daysAgo(3), dueReason: '明天复习巩固' },
    { id: '5', topicId: 'spark_core', topicName: 'Spark Core 核心', priority: 'medium', retentionRate: 55, lastReviewedAt: daysAgo(4), dueReason: '掌握较好，建议回顾' },
    { id: '6', topicId: 'hive', topicName: 'Hive 数据仓库', priority: 'low', retentionRate: 78, lastReviewedAt: daysAgo(2), dueReason: '近期已复习，保持即可' },
    { id: '7', topicId: 'kafka', topicName: 'Kafka 消息引擎', priority: 'high', retentionRate: 22, lastReviewedAt: daysAgo(18), dueReason: '长时间未复习，遗忘严重' },
  ]

  // Admin (大数据高手) demo data — everything mastered
  const adminDemoPath: LearningPath = {
    pathId: 1, subject: '大数据', title: '大数据工程师成长之路',
    totalStages: 5, estimatedDuration: '已完成', currentStage: 5,
    overallProgress: 100, totalStudyHours: 730,
    stages: [
      { stageId: 1, title: '阶段1: 大数据基础', topics: ['大数据概述', 'Linux基础', 'SQL基础', 'Python编程'], estimatedDays: 15, status: 'completed', progress: 100 },
      { stageId: 2, title: '阶段2: Hadoop核心', topics: ['HDFS', 'MapReduce', 'YARN', 'Hive'], estimatedDays: 20, status: 'completed', progress: 100 },
      { stageId: 3, title: '阶段3: Spark生态', topics: ['Spark Core', 'Spark SQL', 'Spark Streaming'], estimatedDays: 25, status: 'completed', progress: 100 },
      { stageId: 4, title: '阶段4: 实时计算', topics: ['Kafka', 'Flink', 'HBase', 'ZooKeeper'], estimatedDays: 20, status: 'completed', progress: 100 },
      { stageId: 5, title: '阶段5: 综合实战', topics: ['数据仓库', '数据湖', '机器学习', '深度学习', 'ETL数据管道'], estimatedDays: 10, status: 'completed', progress: 100 },
    ],
  }

  const adminDemoTopicMastery: TopicMastery[] = [
    { topicId: 'linux', name: 'Linux基础', category: 'foundation', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'sql', name: 'SQL基础', category: 'foundation', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'python', name: 'Python编程', category: 'foundation', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'scala', name: 'Scala入门', category: 'foundation', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'hadoop', name: 'Hadoop概述', category: 'core', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'hdfs', name: 'HDFS分布式文件系统', category: 'core', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'mapreduce', name: 'MapReduce编程模型', category: 'core', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'yarn', name: 'YARN资源调度', category: 'core', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'hbase', name: 'HBase列式数据库', category: 'core', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'hive', name: 'Hive数据仓库', category: 'core', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'zookeeper', name: 'ZooKeeper协调服务', category: 'core', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'spark_core', name: 'Spark Core核心', category: 'advanced', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'spark_sql', name: 'Spark SQL数据处理', category: 'advanced', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'spark_streaming', name: 'Spark Streaming流处理', category: 'advanced', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'kafka', name: 'Kafka消息队列', category: 'advanced', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'flink', name: 'Flink实时计算', category: 'advanced', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'data_warehouse', name: '数据仓库设计', category: 'advanced', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'data_lake', name: '数据湖架构', category: 'advanced', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'machine_learning', name: '机器学习基础', category: 'advanced', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'deep_learning', name: '深度学习入门', category: 'advanced', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'data_mining', name: '数据挖掘方法', category: 'advanced', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'etl', name: 'ETL数据管道', category: 'advanced', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
    { topicId: 'data_pipeline', name: '数据管道工程', category: 'advanced', masteryLevel: 1.0, status: 'mastered', positionX: 0, positionY: 0 },
  ]

  const demoEdges: KnowledgeEdge[] = [
    { fromTopic: 'sql', toTopic: 'hdfs', relationType: 'prerequisite', strength: 0.8 },
    { fromTopic: 'linux', toTopic: 'hdfs', relationType: 'prerequisite', strength: 0.7 },
    { fromTopic: 'hdfs', toTopic: 'mapreduce', relationType: 'prerequisite', strength: 0.9 },
    { fromTopic: 'mapreduce', toTopic: 'yarn', relationType: 'prerequisite', strength: 0.75 },
    { fromTopic: 'yarn', toTopic: 'spark_core', relationType: 'prerequisite', strength: 0.7 },
    { fromTopic: 'spark_core', toTopic: 'spark_sql', relationType: 'prerequisite', strength: 0.85 },
    { fromTopic: 'spark_core', toTopic: 'kafka', relationType: 'prerequisite', strength: 0.6 },
    { fromTopic: 'hdfs', toTopic: 'yarn', relationType: 'association', strength: 0.4 },
  ]

  const adminDemoEdges: KnowledgeEdge[] = [
    { fromTopic: 'linux', toTopic: 'hadoop', relationType: 'prerequisite', strength: 0.9 },
    { fromTopic: 'sql', toTopic: 'hive', relationType: 'prerequisite', strength: 0.85 },
    { fromTopic: 'python', toTopic: 'spark_core', relationType: 'prerequisite', strength: 0.8 },
    { fromTopic: 'scala', toTopic: 'spark_core', relationType: 'prerequisite', strength: 0.75 },
    { fromTopic: 'hadoop', toTopic: 'hdfs', relationType: 'prerequisite', strength: 0.95 },
    { fromTopic: 'hdfs', toTopic: 'mapreduce', relationType: 'prerequisite', strength: 0.9 },
    { fromTopic: 'mapreduce', toTopic: 'yarn', relationType: 'prerequisite', strength: 0.85 },
    { fromTopic: 'yarn', toTopic: 'spark_core', relationType: 'prerequisite', strength: 0.8 },
    { fromTopic: 'hdfs', toTopic: 'hbase', relationType: 'prerequisite', strength: 0.7 },
    { fromTopic: 'hive', toTopic: 'spark_sql', relationType: 'prerequisite', strength: 0.75 },
    { fromTopic: 'spark_core', toTopic: 'spark_sql', relationType: 'prerequisite', strength: 0.9 },
    { fromTopic: 'spark_core', toTopic: 'spark_streaming', relationType: 'prerequisite', strength: 0.85 },
    { fromTopic: 'kafka', toTopic: 'spark_streaming', relationType: 'prerequisite', strength: 0.8 },
    { fromTopic: 'kafka', toTopic: 'flink', relationType: 'prerequisite', strength: 0.85 },
    { fromTopic: 'spark_streaming', toTopic: 'flink', relationType: 'association', strength: 0.6 },
    { fromTopic: 'hbase', toTopic: 'data_warehouse', relationType: 'prerequisite', strength: 0.7 },
    { fromTopic: 'hive', toTopic: 'data_warehouse', relationType: 'prerequisite', strength: 0.75 },
    { fromTopic: 'data_warehouse', toTopic: 'data_lake', relationType: 'prerequisite', strength: 0.8 },
    { fromTopic: 'data_lake', toTopic: 'etl', relationType: 'prerequisite', strength: 0.7 },
    { fromTopic: 'etl', toTopic: 'data_pipeline', relationType: 'prerequisite', strength: 0.75 },
    { fromTopic: 'spark_core', toTopic: 'machine_learning', relationType: 'prerequisite', strength: 0.7 },
    { fromTopic: 'python', toTopic: 'machine_learning', relationType: 'prerequisite', strength: 0.85 },
    { fromTopic: 'machine_learning', toTopic: 'deep_learning', relationType: 'prerequisite', strength: 0.9 },
    { fromTopic: 'machine_learning', toTopic: 'data_mining', relationType: 'prerequisite', strength: 0.8 },
    { fromTopic: 'zookeeper', toTopic: 'kafka', relationType: 'prerequisite', strength: 0.7 },
    { fromTopic: 'zookeeper', toTopic: 'hbase', relationType: 'prerequisite', strength: 0.65 },
    { fromTopic: 'hadoop', toTopic: 'zookeeper', relationType: 'association', strength: 0.5 },
  ]

  const adminDemoReviews: ReviewItem[] = [
    { id: 'a1', topicId: 'mapreduce', topicName: 'MapReduce Shuffle 过程', priority: 'high', retentionRate: 32, lastReviewedAt: daysAgo(10), dueReason: '保留率接近危险线，建议复习' },
    { id: 'a2', topicId: 'hdfs', topicName: 'HDFS 读写流程', priority: 'high', retentionRate: 18, lastReviewedAt: daysAgo(21), dueReason: '遗忘曲线显示严重衰退' },
    { id: 'a3', topicId: 'spark_core', topicName: 'Spark 内存管理', priority: 'medium', retentionRate: 52, lastReviewedAt: daysAgo(6), dueReason: '掌握一般，建议深入巩固' },
    { id: 'a4', topicId: 'flink', topicName: 'Flink Checkpoint 机制', priority: 'medium', retentionRate: 48, lastReviewedAt: daysAgo(8), dueReason: '关键概念需时常回顾' },
    { id: 'a5', topicId: 'kafka', topicName: 'Kafka 分区策略', priority: 'high', retentionRate: 26, lastReviewedAt: daysAgo(15), dueReason: '长时间未复习，需立即巩固' },
    { id: 'a6', topicId: 'hive', topicName: 'Hive SQL 优化', priority: 'low', retentionRate: 71, lastReviewedAt: daysAgo(2), dueReason: '近期复习效果良好' },
    { id: 'a7', topicId: 'zookeeper', topicName: 'ZooKeeper 选举机制', priority: 'medium', retentionRate: 56, lastReviewedAt: daysAgo(5), dueReason: '理解较好，建议加深记忆' },
  ]

  async function fetchLearningPath() {
    isLoading.value = true
    try {
      const data = await client.get('/api/v1/learning/paths') as any
      if (Array.isArray(data) && data.length > 0) {
        const p = data[0]
        currentPath.value = {
          pathId: p.id || '1',
          subject: p.subject || '大数据',
          title: p.subject || '学习路径',
          totalStages: p.total_stages || p.stages?.length || 5,
          estimatedDuration: p.estimated_duration || '90天',
          currentStage: p.current_stage || 1,
          overallProgress: p.current_stage ? (p.current_stage / (p.total_stages || 5)) * 100 : 0,
          totalStudyHours: 0,
          stages: (p.stages || []).map((s: any, i: number) => ({
            stageId: s.stage_number || i + 1,
            title: s.title || `阶段${i + 1}`,
            topics: s.topics || [],
            activities: s.activities || [],
            estimatedDays: 15,
            status: s.is_completed ? 'completed' as const : (i + 1 === p.current_stage ? 'in_progress' as const : (i + 1 < (p.current_stage || 1) ? 'completed' as const : (i + 1 === (p.current_stage || 1) + 1 ? 'available' as const : 'locked' as const))),
            progress: s.completion_rate || 0,
          })),
        }
        return
      }
    } catch { /* use demo data */ }
    currentPath.value = getUserId() === 'admin_user' ? adminDemoPath : demoPath
    isLoading.value = false
  }

  async function fetchTopicMastery() {
    try {
      const data = await client.get('/api/v1/knowledge/nodes') as any
      if (Array.isArray(data)) {
        topicMasteryList.value = data.map((n: any) => ({
          topicId: n.topic_id || n.id,
          name: n.topic_name || n.name || '未命名',
          category: n.category || 'general',
          masteryLevel: (n.mastery_level || 0) / 5,
          status: mapStatus((n.mastery_level || 0) / 5, n.status),
          positionX: n.position_x || 0,
          positionY: n.position_y || 0,
        }))
        return
      }
    } catch { /* use demo data */ }
    topicMasteryList.value = getUserId() === 'admin_user' ? adminDemoTopicMastery : demoTopicMastery
  }

  async function fetchKnowledgeEdges() {
    try {
      const data = await client.get('/api/v1/knowledge/graph') as any
      if (data?.edges && Array.isArray(data.edges)) {
        knowledgeEdges.value = data.edges.map((e: any) => ({
          fromTopic: e.from_topic || '',
          toTopic: e.to_topic || '',
          relationType: e.relation_type || 'prerequisite',
          strength: (e.strength || 50) / 100,
        }))
        return
      }
    } catch { /* use demo data */ }
    knowledgeEdges.value = getUserId() === 'admin_user' ? adminDemoEdges : demoEdges
  }

  async function fetchReviews() {
    try {
      const [reviewData, statsData] = await Promise.all([
        client.get('/api/v1/learning/reviews?limit=20') as any,
        client.get('/api/v1/learning/reviews/stats') as any,
      ])
      const items = Array.isArray(reviewData) ? reviewData.map((r: any) => ({
        id: r.id || '',
        topicId: r.topic_id || '',
        topicName: r.topic_name || r.topic_id || '未知',
        priority: mapPriority(r.priority || 0),
        retentionRate: r.retention_rate || 50,
        lastReviewedAt: r.last_reviewed_at || '',
        dueReason: r.reason || '需要复习',
      })) : null
      // Reject low-quality data: uniform retention rates or no review dates indicate mock data
      if (items && items.length > 0) {
        const rates = new Set(items.map(i => i.retentionRate))
        const datesCount = items.filter(i => i.lastReviewedAt).length
        const rateSpread = rates.size > 1 ? Math.max(...rates) - Math.min(...rates) : 0
        if (rateSpread >= 30 || datesCount > items.length * 0.3) {
          reviewItems.value = items
        } else {
          throw new Error('Low quality review data')
        }
      } else {
        throw new Error('Empty or invalid review data')
      }
      if (statsData) {
        streakDays.value = statsData.current_streak || 0
      }
      return
    } catch { /* use demo data */ }
    if (getUserId() === 'admin_user') {
      reviewItems.value = adminDemoReviews
      streakDays.value = 365
      todayMinutes.value = 120
      curiosityIndex.value = 95
      flowState.value = 'flow'
    } else {
      reviewItems.value = demoReviews
      streakDays.value = 7
      todayMinutes.value = 85
      curiosityIndex.value = 78
      flowState.value = 'flow'
    }
  }

  async function updateTopicMastery(topicId: string, level: number) {
    // level is 0-5 scale from backend, 0-1 normalized for display
    const backendLevel = level <= 1 ? Math.round(level * 5) : level

    // Update locally first
    const topic = topicMasteryList.value.find(t => t.topicId === topicId)
    if (topic) {
      topic.masteryLevel = level
      if (backendLevel >= 4) topic.status = 'mastered'
      else if (backendLevel > 0) topic.status = 'learning'
    }

    // Sync to backend (send 0-5 scale)
    try {
      await client.put(`/api/v1/knowledge/nodes/${topicId}/mastery`, {
        mastery_level: backendLevel,
      })
    } catch { /* backend unavailable, local update is fine */ }
  }

  return {
    currentPath, topicMasteryList, reviewItems, flowState, curiosityIndex,
    streakDays, todayMinutes, knowledgeEdges, isLoading,
    overallProgress, masteredCount, totalTopics, urgentReviews,
    fetchLearningPath, fetchTopicMastery, fetchReviews, fetchKnowledgeEdges, updateTopicMastery,
  }
})
