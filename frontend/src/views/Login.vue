<template>
  <div class="login-page">
    <div class="login-card">
      <h1>SOOP 별풍선 기록기</h1>
      <p class="desc">방송 중 별풍선 후원 내역을 실시간으로 기록합니다.</p>
      <button class="btn-login" @click="login">SOOP 로그인</button>
      <p v-if="auth.isLoggedIn" class="already">
        이미 로그인됨: {{ auth.nickname }}
        <button class="btn-sm" @click="$router.push('/dashboard')">대시보드로</button>
      </p>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import { SOOP_CLIENT_ID, SOOP_REDIRECT_URI } from '../stores/config'

const auth = useAuthStore()
const router = useRouter()

if (auth.isLoggedIn) {
  router.push('/dashboard')
}

function login() {
  const url = `https://openapi.sooplive.co.kr/auth/authorize?client_id=${SOOP_CLIENT_ID}&redirect_uri=${encodeURIComponent(SOOP_REDIRECT_URI)}&response_type=code`
  window.location.href = url
}
</script>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 100%);
}

.login-card {
  background: #1e1e3a;
  border-radius: 16px;
  padding: 48px;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  max-width: 420px;
  width: 90%;
}

h1 {
  font-size: 28px;
  margin-bottom: 12px;
  color: #fff;
}

.desc {
  color: #888;
  margin-bottom: 32px;
  font-size: 14px;
}

.btn-login {
  background: #5c6bc0;
  color: #fff;
  border: none;
  padding: 14px 40px;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-login:hover {
  background: #7986cb;
}

.already {
  margin-top: 24px;
  font-size: 14px;
  color: #aaa;
}

.btn-sm {
  margin-left: 8px;
  background: #333;
  color: #fff;
  border: none;
  padding: 6px 14px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}
</style>
