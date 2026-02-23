<template>
  <div class="redirect-page">
    <div class="card">
      <p v-if="loading">인증 처리 중...</p>
      <p v-else-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { API_BASE } from '../stores/config'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  const params = new URLSearchParams(window.location.search)
  const code = params.get('code')

  if (!code) {
    error.value = '인증 코드가 없습니다.'
    loading.value = false
    return
  }

  try {
    const resp = await fetch(`${API_BASE}/api/auth`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    })
    const data = await resp.json()

    if (data.ok) {
      auth.setAuth(data)
      router.push('/dashboard')
    } else {
      error.value = data.error || '인증 실패'
    }
  } catch (e) {
    error.value = '서버 연결 실패: ' + e.message
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.redirect-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}

.card {
  background: #1e1e3a;
  padding: 40px;
  border-radius: 12px;
  text-align: center;
}

.error {
  color: #ef5350;
}
</style>
