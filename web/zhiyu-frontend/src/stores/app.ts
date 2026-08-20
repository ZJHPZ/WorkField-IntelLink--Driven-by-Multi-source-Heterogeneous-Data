import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export type AppRole = 'enterprise' | 'personal'

export const useAppStore = defineStore('app', () => {
  const role = ref<AppRole>(
    (localStorage.getItem('app_role') as AppRole) || 'enterprise'
  )

  const isEnterprise = computed(() => role.value === 'enterprise')
  const isPersonal = computed(() => role.value === 'personal')

  function switchRole(r: AppRole) {
    role.value = r
    localStorage.setItem('app_role', r)
  }

  return { role, isEnterprise, isPersonal, switchRole }
})
