<template>
  <div class="dashboard">
    <!-- Header -->
    <header class="header">
      <div class="header-left">
        <h1>별풍선 기록기</h1>
        <span class="user-info">{{ auth.nickname }} ({{ auth.soopId }})</span>
      </div>
      <div class="header-right">
        <button class="btn btn-outline" @click="logout">로그아웃</button>
      </div>
    </header>

    <!-- Settings Panel -->
    <section class="panel settings-panel">
      <h2>태그 설정</h2>
      <p class="hint">별풍선 개수에 따라 자동으로 태그를 부여합니다. (예: 200개 = 역팬, 1000개 = 방셀)</p>
      <div class="tag-rules">
        <div v-for="(rule, i) in tagRules" :key="i" class="tag-rule">
          <input
            type="number"
            v-model.number="rule.count"
            placeholder="개수"
            class="input input-sm"
          />
          <span>개 이상 =</span>
          <input
            type="text"
            v-model="rule.label"
            placeholder="태그명"
            class="input input-sm"
          />
          <button class="btn btn-danger btn-xs" @click="removeRule(i)">X</button>
        </div>
        <button class="btn btn-sm" @click="addRule">+ 태그 추가</button>
      </div>
    </section>

    <!-- Recording Control -->
    <section class="panel">
      <div class="record-control">
        <div class="record-status">
          <span :class="['status-dot', recording ? 'active' : '']"></span>
          <span>{{ recording ? '기록 중...' : '대기 중' }}</span>
          <span v-if="recording" class="record-count">수신: {{ receivedCount }}건</span>
        </div>
        <div class="record-buttons">
          <button
            v-if="!recording"
            class="btn btn-primary"
            @click="startRecording"
            :disabled="!auth.accessToken"
          >
            기록 시작
          </button>
          <button
            v-else
            class="btn btn-danger"
            @click="stopRecording"
          >
            기록 중지
          </button>
          <button class="btn btn-outline" @click="saveToServer" :disabled="pendingRecords.length === 0">
            서버 저장 ({{ pendingRecords.length }})
          </button>
        </div>
      </div>
      <p v-if="sdkError" class="error-msg">{{ sdkError }}</p>
    </section>

    <!-- Filters & Actions -->
    <section class="panel">
      <div class="toolbar">
        <div class="filters">
          <select v-model="filterTag" class="input input-sm">
            <option value="">전체 태그</option>
            <option v-for="rule in tagRules" :key="rule.label" :value="rule.label">
              {{ rule.label }} ({{ rule.count }}개+)
            </option>
          </select>
          <button class="btn btn-sm" @click="loadRecords">조회</button>
        </div>
        <div class="actions">
          <button class="btn btn-sm" @click="copyUserNicknames">닉네임 복사 (,구분)</button>
          <button class="btn btn-sm" @click="exportExcel('records')">기록 엑셀</button>
          <button class="btn btn-sm" @click="exportExcel('summary')">요약 엑셀</button>
        </div>
      </div>
    </section>

    <!-- Summary Table -->
    <section class="panel" v-if="summary.length">
      <h2>후원자 요약</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>유저ID</th>
              <th>닉네임</th>
              <th>총 별풍선</th>
              <th>태그</th>
              <th>횟수</th>
              <th>마지막 후원</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in summary" :key="s.user_id">
              <td>{{ s.user_id }}</td>
              <td class="copyable" @click="copyText(s.user_nickname)">{{ s.user_nickname }}</td>
              <td class="num">{{ s.total_count.toLocaleString() }}</td>
              <td>
                <span class="tag" v-if="getTag(s.total_count)">{{ getTag(s.total_count) }}</span>
              </td>
              <td class="num">{{ s.donation_count }}</td>
              <td class="date">{{ formatDate(s.last_donated) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Records Table -->
    <section class="panel">
      <h2>기록 목록 ({{ total }}건)</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>유저ID</th>
              <th>닉네임</th>
              <th>개수</th>
              <th>태그</th>
              <th>메모</th>
              <th>일시</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rec in records" :key="rec.id">
              <td>{{ rec.user_id }}</td>
              <td class="copyable" @click="copyText(rec.user_nickname)">{{ rec.user_nickname }}</td>
              <td class="num">{{ rec.count }}</td>
              <td>
                <span class="tag" v-if="rec.tag">{{ rec.tag }}</span>
              </td>
              <td>
                <input
                  type="text"
                  class="memo-input"
                  :value="rec.memo"
                  @blur="updateMemo(rec.id, $event.target.value)"
                  placeholder="메모 입력..."
                />
              </td>
              <td class="date">{{ formatDate(rec.recorded_at) }}</td>
            </tr>
            <tr v-if="records.length === 0">
              <td colspan="6" class="empty">기록이 없습니다. 기록을 시작하세요.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="pagination" v-if="total > limit">
        <button class="btn btn-xs" :disabled="page <= 1" @click="page--; loadRecords()">이전</button>
        <span>{{ page }} / {{ Math.ceil(total / limit) }}</span>
        <button class="btn btn-xs" :disabled="page * limit >= total" @click="page++; loadRecords()">다음</button>
      </div>
    </section>

    <!-- Pending (unsaved) records -->
    <section class="panel" v-if="pendingRecords.length">
      <h2>미저장 기록 ({{ pendingRecords.length }}건)</h2>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>유저ID</th>
              <th>닉네임</th>
              <th>개수</th>
              <th>태그</th>
              <th>일시</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(rec, i) in pendingRecords" :key="i">
              <td>{{ rec.user_id }}</td>
              <td>{{ rec.user_nickname }}</td>
              <td class="num">{{ rec.count }}</td>
              <td><span class="tag" v-if="rec.tag">{{ rec.tag }}</span></td>
              <td class="date">{{ formatDate(rec.recorded_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Toast -->
    <div v-if="toast" class="toast" :class="toast.type">{{ toast.msg }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { SOOP_CLIENT_ID, SOOP_CLIENT_SECRET, API_BASE } from '../stores/config'

const router = useRouter()
const auth = useAuthStore()

if (!auth.isLoggedIn) {
  router.push('/')
}

// Tag rules
const tagRules = ref(JSON.parse(localStorage.getItem('tag_rules') || '[{"count":200,"label":"역팬"},{"count":1000,"label":"방셀"}]'))

function addRule() {
  tagRules.value.push({ count: 0, label: '' })
}

function removeRule(i) {
  tagRules.value.splice(i, 1)
  saveTagRules()
}

function saveTagRules() {
  localStorage.setItem('tag_rules', JSON.stringify(tagRules.value))
}

function getTag(count) {
  const sorted = [...tagRules.value].filter(r => r.count > 0 && r.label).sort((a, b) => b.count - a.count)
  for (const rule of sorted) {
    if (count >= rule.count) return rule.label
  }
  return ''
}

function getTagForSingle(count) {
  // For individual donation, match the exact tier
  const sorted = [...tagRules.value].filter(r => r.count > 0 && r.label).sort((a, b) => b.count - a.count)
  for (const rule of sorted) {
    if (count >= rule.count) return rule.label
  }
  return ''
}

// Recording state
const recording = ref(false)
const receivedCount = ref(0)
const pendingRecords = ref([])
const sdkError = ref('')
let chatSdk = null

async function startRecording() {
  saveTagRules()
  sdkError.value = ''

  try {
    // ChatSDK is loaded from SOOP's CDN in index.html
    if (typeof ChatSDK === 'undefined') {
      sdkError.value = 'ChatSDK를 로드할 수 없습니다. 페이지를 새로고침하세요.'
      return
    }

    chatSdk = new ChatSDK(SOOP_CLIENT_ID, SOOP_CLIENT_SECRET)
    chatSdk.setAuth(auth.accessToken)

    chatSdk.handleMessageReceived((action, message) => {
      if (action === 'BALLOON_GIFTED') {
        const record = {
          user_id: message.userId || '',
          user_nickname: message.userNickname || '',
          count: message.count || 0,
          tag: getTagForSingle(message.count || 0),
          recorded_at: new Date().toISOString(),
        }
        pendingRecords.value.unshift(record)
        receivedCount.value++
      }
    })

    chatSdk.handleChatClosed(() => {
      recording.value = false
      showToast('채팅 연결이 종료되었습니다.', 'warn')
    })

    chatSdk.handleError((code, message) => {
      sdkError.value = `SDK 오류: ${code} - ${message}`
    })

    await chatSdk.connect()
    recording.value = true
    showToast('기록 시작!', 'ok')
  } catch (e) {
    sdkError.value = '연결 실패: ' + e.message
  }
}

function stopRecording() {
  if (chatSdk) {
    chatSdk.disconnect()
    chatSdk = null
  }
  recording.value = false
  showToast('기록 중지됨', 'warn')
}

// Save pending records to server
async function saveToServer() {
  if (pendingRecords.value.length === 0) return

  try {
    const resp = await fetch(`${API_BASE}/api/balloon`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        streamer_id: parseInt(auth.streamerId),
        records: pendingRecords.value,
      }),
    })
    const data = await resp.json()
    if (data.ok) {
      showToast(`${data.inserted}건 저장 완료`, 'ok')
      pendingRecords.value = []
      loadRecords()
    } else {
      showToast('저장 실패: ' + data.error, 'err')
    }
  } catch (e) {
    showToast('서버 연결 실패', 'err')
  }
}

// Load records
const records = ref([])
const summary = ref([])
const total = ref(0)
const page = ref(1)
const limit = ref(100)
const filterTag = ref('')

async function loadRecords() {
  try {
    let url = `${API_BASE}/api/balloon?streamer_id=${auth.streamerId}&page=${page.value}&limit=${limit.value}`
    if (filterTag.value) url += `&tag=${encodeURIComponent(filterTag.value)}`

    const resp = await fetch(url)
    const data = await resp.json()
    if (data.ok) {
      records.value = data.records
      summary.value = data.summary
      total.value = data.total
    }
  } catch (e) {
    console.error('Load failed:', e)
  }
}

// Memo update
async function updateMemo(recordId, memo) {
  try {
    await fetch(`${API_BASE}/api/memo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ record_id: recordId, memo }),
    })
  } catch (e) {
    console.error('Memo update failed:', e)
  }
}

// Copy user nicknames
function copyUserNicknames() {
  const nicknames = summary.value.map(s => s.user_nickname).join(',')
  navigator.clipboard.writeText(nicknames)
  showToast('닉네임 복사됨!', 'ok')
}

function copyText(text) {
  navigator.clipboard.writeText(text)
  showToast(`${text} 복사됨`, 'ok')
}

// Export Excel
function exportExcel(type) {
  saveTagRules()
  let url = `${API_BASE}/api/export?streamer_id=${auth.streamerId}&type=${type}`
  if (filterTag.value) url += `&tag=${encodeURIComponent(filterTag.value)}`
  window.open(url, '_blank')
}

// Logout
function logout() {
  stopRecording()
  auth.logout()
  router.push('/')
}

// Toast
const toast = ref(null)
let toastTimer = null

function showToast(msg, type = 'ok') {
  toast.value = { msg, type }
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = null }, 3000)
}

// Format date
function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// Auto-save pending records periodically
let autoSaveTimer = null

onMounted(() => {
  if (auth.isLoggedIn) {
    loadRecords()
  }
  autoSaveTimer = setInterval(() => {
    if (pendingRecords.value.length >= 10) {
      saveToServer()
    }
  }, 30000)
})

onUnmounted(() => {
  clearInterval(autoSaveTimer)
  stopRecording()
})
</script>

<style scoped>
.dashboard {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #2a2a4a;
  margin-bottom: 20px;
}

.header h1 {
  font-size: 22px;
  color: #fff;
}

.user-info {
  font-size: 13px;
  color: #888;
  margin-left: 12px;
}

.panel {
  background: #1a1a35;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
}

.panel h2 {
  font-size: 16px;
  margin-bottom: 12px;
  color: #ccc;
}

.hint {
  font-size: 12px;
  color: #666;
  margin-bottom: 12px;
}

/* Tag rules */
.tag-rules {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.tag-rule {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

/* Record control */
.record-control {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.record-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #555;
}

.status-dot.active {
  background: #4caf50;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.record-count {
  color: #4caf50;
  font-size: 13px;
}

.record-buttons {
  display: flex;
  gap: 8px;
}

.error-msg {
  color: #ef5350;
  font-size: 13px;
  margin-top: 8px;
}

/* Toolbar */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.filters, .actions {
  display: flex;
  gap: 6px;
  align-items: center;
}

/* Table */
.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

th {
  text-align: left;
  padding: 10px 8px;
  border-bottom: 2px solid #2a2a4a;
  color: #888;
  font-weight: 600;
  white-space: nowrap;
}

td {
  padding: 8px;
  border-bottom: 1px solid #1e1e3e;
}

.num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.date {
  color: #777;
  white-space: nowrap;
  font-size: 12px;
}

.copyable {
  cursor: pointer;
  color: #7986cb;
}

.copyable:hover {
  text-decoration: underline;
}

.empty {
  text-align: center;
  color: #555;
  padding: 24px;
}

.tag {
  background: #5c6bc0;
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  white-space: nowrap;
}

.memo-input {
  background: transparent;
  border: 1px solid #333;
  color: #ddd;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  width: 100%;
  min-width: 120px;
}

.memo-input:focus {
  border-color: #5c6bc0;
  outline: none;
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  font-size: 13px;
  color: #888;
}

/* Buttons */
.btn {
  background: #2a2a4a;
  color: #ddd;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: background 0.2s;
}

.btn:hover { background: #3a3a5a; }
.btn:disabled { opacity: 0.4; cursor: default; }

.btn-primary { background: #5c6bc0; color: #fff; }
.btn-primary:hover { background: #7986cb; }

.btn-danger { background: #c62828; color: #fff; }
.btn-danger:hover { background: #e53935; }

.btn-outline {
  background: transparent;
  border: 1px solid #444;
  color: #aaa;
}

.btn-sm { padding: 6px 12px; font-size: 12px; }
.btn-xs { padding: 4px 8px; font-size: 11px; }

/* Input */
.input {
  background: #151530;
  border: 1px solid #333;
  color: #ddd;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
}

.input:focus {
  border-color: #5c6bc0;
  outline: none;
}

.input-sm { padding: 6px 10px; font-size: 12px; }

select.input {
  appearance: auto;
}

/* Toast */
.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  color: #fff;
  z-index: 1000;
  animation: slideIn 0.3s;
}

.toast.ok { background: #2e7d32; }
.toast.warn { background: #e65100; }
.toast.err { background: #c62828; }

@keyframes slideIn {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* Settings panel */
.settings-panel .tag-rule span {
  color: #888;
  font-size: 12px;
}

.btn-danger.btn-xs {
  padding: 2px 6px;
  font-size: 11px;
  border-radius: 4px;
}
</style>
