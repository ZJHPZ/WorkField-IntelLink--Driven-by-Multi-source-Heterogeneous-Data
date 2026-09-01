<template>
  <span class="seal-chip" :class="variantClass">{{ label }}</span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ status: string }>()

// 企业侧语义 → 印章形态
//  base(coral) = 待决策/亮点 · navy = 已确认权威 · dim = 中性 · faded = 衰退(删除线)
const MAP: Record<string, { cls: string; label: string }> = {
  // positions
  confirmed: { cls: 'seal-chip--navy', label: '已确认' },
  emerging:  { cls: '', label: '新兴' },
  stable:    { cls: 'seal-chip--dim', label: '稳定' },
  declining: { cls: 'seal-chip--faded', label: '衰退' },
  // candidates
  candidate: { cls: '', label: '待验证' },
  rejected:  { cls: 'seal-chip--faded', label: '已驳回' },
  // diagnoses
  healthy:   { cls: 'seal-chip--navy', label: '健康' },
  warning:   { cls: '', label: '需关注' },
  critical:  { cls: 'seal-chip--faded', label: '严重' },
  // 人才库 HR 状态（盖章推进）
  '':            { cls: 'seal-chip--dim', label: '未标注' },
  shortlisted:   { cls: 'seal-chip--navy', label: '已筛选' },
  interviewing:  { cls: '', label: '面试中' },
  offered:       { cls: '', label: '已Offer' },
  archived:      { cls: 'seal-chip--faded', label: '已归档' },
}

const variantClass = computed(() => MAP[props.status]?.cls ?? 'seal-chip--dim')
const label = computed(() => MAP[props.status]?.label ?? props.status)
</script>
