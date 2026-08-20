import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAnalysisStore = defineStore('analysis', () => {
  const analysisResult = ref('')
  const floatingVisible = ref(false)
  const floatingCollapsed = ref(false)
  const floatingFileName = ref('')

  function showFloatingWindow(result: string, fileName: string = '') {
    analysisResult.value = result
    floatingFileName.value = fileName
    floatingVisible.value = true
    floatingCollapsed.value = false
  }

  function toggleFloating() {
    floatingCollapsed.value = !floatingCollapsed.value
  }

  function closeFloating() {
    floatingVisible.value = false
    floatingCollapsed.value = false
  }

  return {
    analysisResult,
    floatingVisible,
    floatingCollapsed,
    floatingFileName,
    showFloatingWindow,
    toggleFloating,
    closeFloating,
  }
})
