import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const streamerId = ref(localStorage.getItem('streamer_id') || '')
  const soopId = ref(localStorage.getItem('soop_id') || '')
  const nickname = ref(localStorage.getItem('nickname') || '')
  const accessToken = ref(localStorage.getItem('access_token') || '')

  const isLoggedIn = computed(() => !!accessToken.value)

  function setAuth(data) {
    streamerId.value = String(data.streamer_id)
    soopId.value = data.soop_id
    nickname.value = data.nickname
    accessToken.value = data.access_token
    localStorage.setItem('streamer_id', String(data.streamer_id))
    localStorage.setItem('soop_id', data.soop_id)
    localStorage.setItem('nickname', data.nickname)
    localStorage.setItem('access_token', data.access_token)
  }

  function logout() {
    streamerId.value = ''
    soopId.value = ''
    nickname.value = ''
    accessToken.value = ''
    localStorage.clear()
  }

  return { streamerId, soopId, nickname, accessToken, isLoggedIn, setAuth, logout }
})
