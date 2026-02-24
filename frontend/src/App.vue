<template>
  <div class="app">
    <!-- Login Screen -->
    <div v-if="!authenticated" class="login-screen">
      <div class="login-card">
        <img src="/favicon.png" alt="크랙" class="login-logo" />
        <h1 class="login-title">크랙 미션 매니저</h1>
        <p class="login-sub">비밀번호를 입력하세요</p>
        <form @submit.prevent="doLogin" class="login-form">
          <input
            v-model="loginPassword"
            type="password"
            class="login-input"
            placeholder="비밀번호"
            autofocus
          />
          <button class="login-btn" type="submit" :disabled="loginLoading">
            {{ loginLoading ? '...' : '로그인' }}
          </button>
        </form>
        <p v-if="loginError" class="login-error">{{ loginError }}</p>
      </div>
    </div>

    <!-- Main App (authenticated) -->
    <template v-else>

    <!-- Header -->
    <header class="header">
      <div class="header-left">
        <div class="logo">
          <img src="/favicon.png" alt="크랙" class="logo-img" />
          <h1>크랙 미션 매니저</h1>
        </div>
      </div>
      <div class="header-center">
        <div class="connect-bar">
          <div :class="['status-led', connected ? 'on' : '']"></div>
          <span v-if="connected" class="connected-label">{{ streamerId }} 연결됨</span>
          <input
            v-model="inputId"
            class="input-streamer"
            placeholder="스트리머 ID 입력"
            @keyup.enter="connectStreamer"
            :disabled="connecting"
          />
          <button v-if="!connected" class="btn-connect" @click="connectStreamer" :disabled="connecting || !inputId.trim()">
            {{ connecting ? '...' : '연결' }}
          </button>
          <button v-else class="btn-disconnect" @click="disconnectStreamer">해제</button>
        </div>
      </div>
      <div class="header-right">
        <button class="btn-icon sim-btn" @click="simulateResults" title="시뮬레이션">
          <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
        </button>
        <button class="btn-icon" @click="showSettings = true" title="설정">
          <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 15a3 3 0 100-6 3 3 0 000 6z"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
        </button>
        <button class="btn-icon" @click="showLogs = !showLogs" title="로그">
          <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 6h10M4 10h10M4 14h6"/></svg>
        </button>
      </div>
    </header>

    <!-- Stats -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-label">전체</div>
        <div class="stat-num accent">{{ stats.total }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">진행중</div>
        <div class="stat-num orange">{{ stats.in_progress }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">완료</div>
        <div class="stat-num green">{{ stats.done }}</div>
      </div>
    </div>

    <!-- Global Gauge & Countdown -->
    <section class="global-gauge-card">
      <div class="global-gauge-top">
        <div class="global-gauge-left">
          <div class="global-remaining-wrap">
            <span class="global-icon">🔥</span>
            <template v-if="totalCompleted">
              <span class="global-remaining-num done">달성!</span>
            </template>
            <template v-else>
              <span :class="['global-remaining-num', totalRemaining <= 10 && totalRemaining > 0 && 'urgent']">
                {{ totalRemaining }}
              </span>
              <span class="global-remaining-label">개 남음</span>
            </template>
          </div>
          <div class="global-sub">
            {{ totalMatched }}<span class="global-sub-dim"> / </span>
            <span v-if="!globalTargetEditing" class="global-target-val" @click="globalTargetEditing = true" title="클릭하여 목표 수정">{{ globalTargetCount }}</span>
            <input
              v-else
              type="number"
              v-model.number="globalTargetCount"
              class="global-target-input"
              min="1"
              @blur="globalTargetEditing = false"
              @keyup.enter="globalTargetEditing = false"
              autofocus
            />
          </div>
        </div>
        <div class="global-gauge-right">
          <div class="global-timer-wrap">
            <span class="global-icon">⏱</span>
            <template v-if="globalTimerRunning && globalRemainingSeconds >= 0">
              <span :class="['global-timer-num', globalRemainingSeconds <= 60 && 'critical', globalRemainingSeconds > 60 && globalRemainingSeconds <= 180 && 'warning']">
                {{ formatCountdown(globalRemainingSeconds) }}
              </span>
              <button class="global-timer-btn stop" @click="stopGlobalTimer" title="타이머 정지">■</button>
              <button class="global-timer-btn reset" @click="resetGlobalTimer" title="타이머 리셋">↺</button>
            </template>
            <template v-else-if="globalTimerRunning && globalRemainingSeconds === 0">
              <span class="global-timer-expired">시간 종료!</span>
              <button class="global-timer-btn reset" @click="resetGlobalTimer">↺</button>
            </template>
            <template v-else>
              <div class="global-timer-set">
                <input
                  type="number"
                  v-model.number="globalTimerMinutes"
                  class="global-timer-input"
                  min="1"
                  max="999"
                  @keyup.enter="startGlobalTimer"
                />
                <span class="global-timer-unit">분</span>
              </div>
              <button class="global-timer-btn start" @click="startGlobalTimer" :disabled="!globalTimerMinutes || globalTimerMinutes <= 0">▶</button>
            </template>
          </div>
        </div>
      </div>
      <div class="global-gauge-bar-wrap">
        <div class="global-gauge-bar">
          <div
            class="global-gauge-fill"
            :style="{ width: totalProgress + '%' }"
            :class="{ full: totalCompleted }"
          ></div>
        </div>
        <span class="global-gauge-pct">{{ Math.round(totalProgress) }}%</span>
      </div>
      <div v-if="globalTimerRunning && globalRemainingSeconds >= 0" class="global-timer-bar-wrap">
        <div class="global-timer-bar">
          <div
            class="global-timer-fill"
            :style="{ width: (globalRemainingSeconds / (globalTimerMinutes * 60) * 100) + '%' }"
            :class="{ warning: globalRemainingSeconds <= 180 && globalRemainingSeconds > 60, critical: globalRemainingSeconds <= 60 }"
          ></div>
        </div>
      </div>
    </section>

    <!-- Mission Registration -->
    <section class="card">
      <div class="card-header">
        <h2>미션 등록</h2>
      </div>

      <!-- Auto threshold -->
      <div class="auto-row">
        <span class="auto-badge">자동등록</span>
        <input type="number" v-model.number="autoThreshold" class="input-sm num-input" min="0" />
        <span class="sub-text">개 이상이면 템플릿 없어도 자동등록</span>
        <button class="btn-sm btn-accent" @click="saveConfig">적용</button>
        <button class="btn-sm btn-muted" @click="autoThreshold = 0; saveConfig()">끄기</button>
        <span class="sub-text dim">현재: {{ autoThreshold > 0 ? autoThreshold + '개' : '비활성' }}</span>
      </div>

      <!-- Add template -->
      <div class="template-form">
        <div class="form-group">
          <label>미션 이름</label>
          <input v-model="newTmpl.name" class="input-sm" placeholder="역팬, 방셀 등" />
        </div>
        <div class="form-group">
          <label>개수 (정확히)</label>
          <input type="number" v-model.number="newTmpl.count" class="input-sm num-input" min="1" />
        </div>
        <div class="form-group">
          <label>타입</label>
          <div class="type-btns">
            <button :class="['type-btn', newTmpl.type === 'all' && 'active']" @click="newTmpl.type='all'">전체</button>
            <button :class="['type-btn star', newTmpl.type === 'balloon' && 'active']" @click="newTmpl.type='balloon'">별풍</button>
            <button :class="['type-btn ad', newTmpl.type === 'adballoon' && 'active']" @click="newTmpl.type='adballoon'">애드</button>
            <button :class="['type-btn mission', newTmpl.type === 'mission' && 'active']" @click="newTmpl.type='mission'">대결</button>
          </div>
        </div>
        <div class="form-group chk-group">
          <label class="chk"><input type="checkbox" v-model="newTmpl.collect_message" /> 메시지 수집</label>
        </div>
        <button class="btn-add" @click="addTemplate" :disabled="!newTmpl.name || !newTmpl.count">+ 등록</button>
      </div>

      <div class="notice-box">
        <p>• 소원권은 현금이나 상품 등 금전적·물질적 제공은 어려운 점 양해 부탁드립니다.</p>
        <p>• 요청 내용은 상식적인 범위와 실행 가능한 선에서 진행됩니다.</p>
        <p>• 일정은 서로의 상황을 고려하여 최대한 조율해보겠습니다.</p>
      </div>

      <!-- Template list -->
      <div class="template-list" v-if="templates.length">
        <div v-for="t in templates" :key="t.id"
          :class="['template-item', !t.active && 'paused', filterTemplate === t.name && 'selected', templateCompleted(t) && 'completed']"
          @click="toggleFilterTemplate(t.name)"
          style="cursor: pointer;"
        >
          <div class="tmpl-top-row">
            <div class="tmpl-info">
              <span class="tmpl-name">{{ t.name }}</span>
              <span class="tmpl-count">{{ t.count }}개</span>
              <span :class="['tmpl-type', t.type]">{{ typeLabel(t.type) }}</span>
              <span v-if="t.collect_message" class="tmpl-opt">메시지</span>
              <span v-if="t.duration > 0" class="tmpl-opt timer-opt">{{ t.duration }}분</span>
            </div>
            <div class="tmpl-actions" @click.stop>
              <button class="btn-icon-sm" @click="toggleTemplate(t)" :title="t.active ? '일시정지' : '활성화'">
                {{ t.active ? '⏸' : '▶' }}
              </button>
              <button class="btn-icon-sm del" @click="deleteTemplate(t.id)">✕</button>
            </div>
          </div>

        </div>
      </div>
    </section>

    <!-- Results -->
    <section class="card">
      <div class="card-header">
        <h2>미션 현황 <span v-if="filterTemplate" class="filter-badge" @click="filterTemplate=''">{{ filterTemplate }} ✕</span></h2>
        <div class="result-actions">
          <div class="filter-tabs">
            <button :class="['tab', filterTab === '' && 'active']" @click="filterTab=''">전체</button>
            <button :class="['tab', filterTab === 'pending' && 'active']" @click="filterTab='pending'">진행중</button>
            <button :class="['tab', filterTab === 'done' && 'active']" @click="filterTab='done'">완료</button>
            <span class="tab-sep"></span>
            <button :class="['tab type-tab', filterType === '' && 'active']" @click="filterType=''">모든타입</button>
            <button :class="['tab type-tab mission', filterType === 'mission' && 'active']" @click="filterType='mission'">대결미션</button>
            <button :class="['tab type-tab balloon', filterType === 'balloon' && 'active']" @click="filterType='balloon'">별풍선</button>
            <button :class="['tab type-tab adballoon', filterType === 'adballoon' && 'active']" @click="filterType='adballoon'">애드벌룬</button>
          </div>
          <div class="export-btns">
            <button class="btn-sm btn-outline" @click="copyNicknames">닉네임복사</button>
            <button class="btn-sm btn-outline roulette-btn" @click="openRoulette">🎰 1명 뽑기</button>
            <button class="btn-sm btn-outline" @click="exportExcel">엑셀</button>
            <button class="btn-sm btn-danger" @click="clearResults">초기화</button>
          </div>
        </div>
      </div>

      <div class="results-list">
        <div v-for="r in pagedResults" :key="r.id" :class="['result-item-wrap', r.done && 'done', r.type]">
          <div class="result-item">
            <div class="result-left">
              <span :class="['result-badge', r.type]">
                {{ typeIcon(r.type) }}{{ r.count }} {{ r.matched_template || '' }}
              </span>
              <div class="result-user-info">
                <span class="result-nickname copyable" @click="copyText(r.user_nickname)">{{ r.user_nickname }}</span>
                <span class="result-id copyable" @click="copyText(r.user_id)">{{ r.user_id }}</span>
              </div>
              <span v-if="r.matched_template" class="result-match">매칭</span>
              <button v-if="r.message" class="btn-msg-toggle" @click="toggleMessage(r.id)" title="메시지 보기">
                💬
              </button>
            </div>
            <div class="result-center">
              <input
                class="memo-input"
                :value="r.memo"
                placeholder="메모..."
                @keyup.enter="saveMemo(r.id, $event.target.value)"
                @blur="saveMemo(r.id, $event.target.value)"
              />
            </div>
            <div class="result-right">
              <span class="result-time">{{ r.time }}</span>
              <a class="btn-station" :href="'https://www.sooplive.co.kr/station/' + r.user_id" target="_blank" title="방송국 이동">방송국→</a>
              <a class="btn-fan" :href="'https://st.sooplive.co.kr/app/gift_starballoon.php?szBjId=' + r.user_id + '&szWork=BJ_STATION&sys_type=web&location=station'" target="_blank" title="역팬하기">역팬★</a>
              <button :class="['btn-icon-sm', r.done ? 'done-btn' : 'check-btn']" @click="toggleResult(r.id)">
                {{ r.done ? '↩' : '✓' }}
              </button>
              <button class="btn-icon-sm del" @click="deleteResult(r.id)">✕</button>
            </div>
          </div>
          <div v-if="r.message && expandedMessages.has(r.id)" class="result-message">
            <span class="msg-label">💬 채팅:</span> {{ r.message }}
          </div>
        </div>
        <div v-if="filteredResults.length === 0" class="empty-state">
          <p>{{ connected ? '이벤트 대기 중...' : '스트리머를 연결하세요' }}</p>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="pagination">
        <button class="page-btn" :disabled="currentPage <= 1" @click="currentPage = 1">«</button>
        <button class="page-btn" :disabled="currentPage <= 1" @click="currentPage--">‹</button>
        <template v-for="p in totalPages" :key="p">
          <button
            v-if="p === 1 || p === totalPages || (p >= currentPage - 2 && p <= currentPage + 2)"
            :class="['page-btn', p === currentPage && 'active']"
            @click="currentPage = p"
          >{{ p }}</button>
          <span v-else-if="p === currentPage - 3 || p === currentPage + 3" class="page-dots">…</span>
        </template>
        <button class="page-btn" :disabled="currentPage >= totalPages" @click="currentPage++">›</button>
        <button class="page-btn" :disabled="currentPage >= totalPages" @click="currentPage = totalPages">»</button>
        <span class="page-info">{{ filteredResults.length }}건 중 {{ (currentPage-1)*pageSize+1 }}~{{ Math.min(currentPage*pageSize, filteredResults.length) }}</span>
      </div>
    </section>

    <!-- Log Panel (Slide) -->
    <div :class="['log-panel', showLogs && 'open']">
      <div class="log-header">
        <h3>실시간 로그</h3>
        <button class="btn-icon-sm" @click="showLogs = false">✕</button>
      </div>
      <div class="log-list">
        <div v-for="(log, i) in logs" :key="i" :class="['log-item', log.type]">
          <span class="log-time">{{ log.time }}</span>
          <span class="log-msg">{{ log.message }}</span>
        </div>
      </div>
    </div>

    <!-- Roulette Modal -->
    <Teleport to="body">
      <div v-if="roulette.show" class="roulette-overlay" @click.self="closeRoulette">
        <div class="roulette-modal">
          <div class="roulette-title">🎰 1명 뽑기</div>
          <div class="roulette-viewport">
            <div class="roulette-highlight"></div>
            <div class="roulette-track" ref="rouletteTrack">
              <div
                v-for="(item, i) in roulette.items"
                :key="i"
                :class="['roulette-cell', roulette.done && roulette.winnerIdx === i && 'winner']"
              >
                <span class="roulette-nick">{{ item.nickname }}</span>
                <span class="roulette-uid">{{ item.id }}</span>
              </div>
            </div>
          </div>
          <div v-if="roulette.phase === 'countdown'" class="roulette-countdown">
            <span class="countdown-text">도전!</span>
          </div>
          <div v-if="roulette.done" class="roulette-result">
            <div class="roulette-confetti">🎉🎊✨🎊🎉</div>
            <div class="roulette-winner-label">WINNER</div>
            <div class="roulette-winner-name">{{ roulette.winner?.nickname }}</div>
            <div class="roulette-winner-id">{{ roulette.winner?.id }}</div>
          </div>
          <div v-else-if="roulette.phase === 'slowing'" class="roulette-tension">
            <span class="tension-dot">.</span><span class="tension-dot d2">.</span><span class="tension-dot d3">.</span>
          </div>
          <div class="roulette-btns">
            <button v-if="roulette.done" class="btn-sm btn-accent" @click="copyText(roulette.winner?.nickname); showToast('당첨자 닉네임 복사됨', 'ok')">닉네임 복사</button>
            <button v-if="roulette.done" class="btn-sm btn-outline" @click="startRoulette">다시 뽑기</button>
            <button class="btn-sm btn-muted" @click="closeRoulette">닫기</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Settings Modal -->
    <Teleport to="body">
      <div v-if="showSettings" class="roulette-overlay" @click.self="showSettings = false">
        <div class="settings-modal">
          <div class="settings-header">
            <h2>설정</h2>
            <button class="btn-icon-sm" @click="showSettings = false">✕</button>
          </div>
          <div class="settings-section">
            <h3>비밀번호 변경</h3>
            <div class="settings-form">
              <input v-model="pwForm.current" type="password" class="input-sm" placeholder="현재 비밀번호" />
              <input v-model="pwForm.newPw" type="password" class="input-sm" placeholder="새 비밀번호" />
              <input v-model="pwForm.confirm" type="password" class="input-sm" placeholder="새 비밀번호 확인" />
              <button class="btn-sm btn-accent" @click="changePassword" :disabled="!pwForm.current || !pwForm.newPw">변경</button>
              <p v-if="pwError" class="pw-error">{{ pwError }}</p>
            </div>
          </div>
          <div class="settings-footer">
            <button class="btn-sm btn-danger" @click="doLogout">로그아웃</button>
          </div>
        </div>
      </div>
    </Teleport>

    </template><!-- end v-else (authenticated) -->

    <!-- Toast -->
    <Transition name="toast">
      <div v-if="toast" :class="['toast', toast.type]">{{ toast.msg }}</div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'

const API = ''

// ─── Auth State ───
const authenticated = ref(false)
const loginPassword = ref('')
const loginLoading = ref(false)
const loginError = ref('')
const showSettings = ref(false)
const pwForm = ref({ current: '', newPw: '', confirm: '' })
const pwError = ref('')

async function checkAuth() {
  try {
    const resp = await fetch(`${API}/api/auth-check`, { credentials: 'include' })
    const data = await resp.json()
    authenticated.value = data.ok === true
  } catch { authenticated.value = false }
}

async function doLogin() {
  loginLoading.value = true
  loginError.value = ''
  try {
    const resp = await fetch(`${API}/api/login`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: loginPassword.value }),
      credentials: 'include',
    })
    const data = await resp.json()
    if (data.ok) {
      authenticated.value = true
      loginPassword.value = ''
      nextTick(() => connectSSE())
    } else {
      loginError.value = data.error || '로그인 실패'
    }
  } catch { loginError.value = '서버 연결 실패' }
  loginLoading.value = false
}

async function doLogout() {
  await fetch(`${API}/api/logout`, { method: 'POST', credentials: 'include' })
  authenticated.value = false
  showSettings.value = false
  if (eventSource) eventSource.close()
}

async function changePassword() {
  pwError.value = ''
  if (pwForm.value.newPw !== pwForm.value.confirm) {
    pwError.value = '새 비밀번호가 일치하지 않습니다'
    return
  }
  if (pwForm.value.newPw.length < 4) {
    pwError.value = '비밀번호는 최소 4자 이상이어야 합니다'
    return
  }
  try {
    const resp = await fetch(`${API}/api/change-password`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current_password: pwForm.value.current, new_password: pwForm.value.newPw }),
      credentials: 'include',
    })
    const data = await resp.json()
    if (data.ok) {
      showToast('비밀번호가 변경되었습니다', 'ok')
      pwForm.value = { current: '', newPw: '', confirm: '' }
      showSettings.value = false
    } else {
      pwError.value = data.error || '변경 실패'
    }
  } catch { pwError.value = '서버 연결 실패' }
}

// State
const inputId = ref('')
const streamerId = ref('')
const connected = ref(false)
const connecting = ref(false)
const stats = ref({ total: 0, in_progress: 0, done: 0 })
const templates = ref([])
const results = ref([])
const logs = ref([])
const showLogs = ref(false)
const autoThreshold = ref(0)
const filterTab = ref('')
const filterType = ref('')
const filterTemplate = ref('')  // 미션 이름 필터

const currentPage = ref(1)
const pageSize = 20

const filteredResults = computed(() => {
  let list = results.value
  if (filterTab.value === 'pending') list = list.filter(r => !r.done)
  if (filterTab.value === 'done') list = list.filter(r => r.done)
  if (filterType.value) list = list.filter(r => r.type === filterType.value)
  if (filterTemplate.value) list = list.filter(r => r.matched_template === filterTemplate.value)
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredResults.value.length / pageSize)))
const pagedResults = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredResults.value.slice(start, start + pageSize)
})

// 필터 변경 시 페이지 리셋
watch([filterTab, filterType, filterTemplate], () => { currentPage.value = 1 })

const expandedMessages = ref(new Set())
const newTmpl = ref({ name: '', count: 500, type: 'all', collect_message: true, duration: 0 })
const now = ref(Date.now())
let nowTimer = null

// ─── Global Gauge & Countdown ───
const globalTimerMinutes = ref(30)
const globalTimerStartedAt = ref(null)
const globalTimerRunning = ref(false)
const globalTargetCount = ref(30000)
const globalTargetEditing = ref(false)

const totalMatched = computed(() => results.value.reduce((sum, r) => sum + (r.count || 0), 0))
const totalRemaining = computed(() => Math.max(0, globalTargetCount.value - totalMatched.value))
const totalProgress = computed(() => globalTargetCount.value > 0 ? Math.min(100, (totalMatched.value / globalTargetCount.value) * 100) : 0)
const totalCompleted = computed(() => globalTargetCount.value > 0 && totalMatched.value >= globalTargetCount.value)

const globalRemainingSeconds = computed(() => {
  if (!globalTimerStartedAt.value || !globalTimerRunning.value) return -1
  const elapsed = (now.value / 1000) - globalTimerStartedAt.value
  return Math.max(0, (globalTimerMinutes.value * 60) - elapsed)
})

function startGlobalTimer() {
  globalTimerStartedAt.value = Date.now() / 1000
  globalTimerRunning.value = true
  globalTimerEditing.value = false
}

function stopGlobalTimer() {
  globalTimerRunning.value = false
  globalTimerStartedAt.value = null
}

function resetGlobalTimer() {
  globalTimerRunning.value = false
  globalTimerStartedAt.value = null
  globalTimerEditing.value = false
}

// SSE
let eventSource = null

function connectSSE() {
  if (eventSource) eventSource.close()
  eventSource = new EventSource(`${API}/api/events`, { withCredentials: true })
  eventSource.onmessage = (e) => {
    try { handleSSE(JSON.parse(e.data)) } catch {}
  }
  eventSource.onerror = () => { setTimeout(connectSSE, 3000) }
}

function handleSSE(payload) {
  const { event, data } = payload
  switch (event) {
    case 'status':
      connected.value = data.connected
      streamerId.value = data.streamer_id || ''
      if (data.stats) stats.value = data.stats
      connecting.value = false
      break
    case 'templates': templates.value = data; break
    case 'results': results.value = data; break
    case 'result': results.value.unshift(data); break
    case 'result_update':
      const idx = results.value.findIndex(r => r.id === data.id)
      if (idx >= 0) results.value[idx] = data
      break
    case 'stats': stats.value = data; break
    case 'log':
      logs.value.unshift(data)
      if (logs.value.length > 200) logs.value.length = 200
      break
  }
}

// Actions
async function connectStreamer() {
  if (!inputId.value.trim()) return
  connecting.value = true
  try {
    const resp = await fetch(`${API}/api/connect`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ streamer_id: inputId.value.trim() }),
      credentials: 'include',
    })
    const data = await resp.json()
    if (!data.ok) { showToast(data.error, 'err'); connecting.value = false }
  } catch { showToast('서버 연결 실패', 'err'); connecting.value = false }
}

async function disconnectStreamer() {
  await fetch(`${API}/api/disconnect`, { method: 'POST', credentials: 'include' })
}

async function addTemplate() {
  if (!newTmpl.value.name || !newTmpl.value.count) return
  await fetch(`${API}/api/templates`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(newTmpl.value),
    credentials: 'include',
  })
  newTmpl.value = { name: '', count: 500, type: 'all', collect_message: true, duration: 0 }
}

async function toggleTemplate(t) {
  await fetch(`${API}/api/templates/update`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: t.id, active: !t.active }),
    credentials: 'include',
  })
}

async function deleteTemplate(id) {
  await fetch(`${API}/api/templates/delete`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id }),
    credentials: 'include',
  })
}

async function toggleResult(id) {
  await fetch(`${API}/api/results/toggle`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id }),
    credentials: 'include',
  })
}

async function saveMemo(id, memo) {
  await fetch(`${API}/api/results/memo`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id, memo }),
    credentials: 'include',
  })
}

async function deleteResult(id) {
  await fetch(`${API}/api/results/delete`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id }),
    credentials: 'include',
  })
}

async function clearResults() {
  if (!confirm('모든 결과를 초기화하시겠습니까?')) return
  await fetch(`${API}/api/results/clear`, { method: 'POST', credentials: 'include' })
}

async function saveConfig() {
  await fetch(`${API}/api/config`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ auto_threshold: autoThreshold.value }),
    credentials: 'include',
  })
  showToast(`자동등록: ${autoThreshold.value > 0 ? autoThreshold.value + '개' : '끔'}`, 'ok')
}

async function copyNicknames() {
  const nicknames = filteredResults.value.map(r => r.user_nickname)
  if (nicknames.length === 0) { showToast('복사할 닉네임이 없습니다', 'warn'); return }
  navigator.clipboard.writeText(nicknames.join(','))
  showToast(`${nicknames.length}개 닉네임 복사됨 (중복 포함)`, 'ok')
}

function toggleMessage(id) {
  if (expandedMessages.value.has(id)) {
    expandedMessages.value.delete(id)
  } else {
    expandedMessages.value.add(id)
  }
}

function toggleFilterTemplate(name) {
  filterTemplate.value = filterTemplate.value === name ? '' : name
}

function templateResultCount(name) {
  return results.value.filter(r => r.matched_template === name).length
}

// ─── Sound Effects (Web Audio API) ───
let audioCtx = null
function getAudioCtx() {
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)()
  return audioCtx
}

function playTick(pitch = 800, vol = 0.08) {
  try {
    const ctx = getAudioCtx()
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'sine'
    osc.frequency.value = pitch
    gain.gain.value = vol
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.06)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start()
    osc.stop(ctx.currentTime + 0.06)
  } catch {}
}

let spinAudio = null

function playSpinSound() {
  try {
    stopSpinSound()
    spinAudio = new Audio('/crack2.mp3')
    spinAudio.volume = 0.7
    spinAudio.play()
  } catch {}
}

function stopSpinSound() {
  if (spinAudio) {
    spinAudio.pause()
    spinAudio.currentTime = 0
    spinAudio = null
  }
}

function playWinSound() {
  stopSpinSound()
  try {
    const audio = new Audio('/crack.mp3')
    audio.volume = 0.7
    audio.play()
  } catch {}
}

// ─── Roulette ───
const rouletteTrack = ref(null)
const roulette = ref({ show: false, items: [], done: false, winner: null, winnerIdx: -1, phase: 'idle' })
let rouletteAnim = null

function openRoulette() {
  const pool = filteredResults.value.map(r => ({ id: r.user_id, nickname: r.user_nickname }))
  const uniqueUsers = new Set(pool.map(p => p.id))
  if (uniqueUsers.size < 2) { showToast('최소 2명 이상 필요합니다', 'warn'); return }

  const REPEAT = Math.max(10, Math.ceil(60 / pool.length))
  const items = []
  for (let i = 0; i < REPEAT; i++) {
    const shuffled = [...pool].sort(() => Math.random() - 0.5)
    items.push(...shuffled)
  }

  roulette.value = { show: true, items, done: false, winner: null, winnerIdx: -1, phase: 'countdown' }
  playSpinSound()
  setTimeout(() => {
    roulette.value.phase = 'spinning'
    nextTick(() => doSpin())
  }, 1200)
}

function startRoulette() {
  if (rouletteAnim) cancelAnimationFrame(rouletteAnim)
  roulette.value.done = false
  roulette.value.winner = null
  roulette.value.winnerIdx = -1
  roulette.value.phase = 'countdown'
  playSpinSound()
  setTimeout(() => {
    roulette.value.phase = 'spinning'
    nextTick(() => doSpin())
  }, 1200)
}

function doSpin() {
  // 다시 뽑기: 아이템 새로 셔플 (중복 허용 - 많이 쏜 사람 확률 높음)
  const pool = filteredResults.value.map(r => ({ id: r.user_id, nickname: r.user_nickname }))
  const REPEAT = Math.max(10, Math.ceil(60 / pool.length))
  const newItems = []
  for (let i = 0; i < REPEAT; i++) {
    const shuffled = [...pool].sort(() => Math.random() - 0.5)
    newItems.push(...shuffled)
  }
  roulette.value.items = newItems

  const track = rouletteTrack.value
  if (!track) return
  track.style.transition = ''

  const cellH = 56
  const items = roulette.value.items
  const viewportCenter = 140

  const winIdx = Math.floor(items.length * 0.7) + Math.floor(Math.random() * (items.length * 0.2))
  const targetOffset = winIdx * cellH - viewportCenter + cellH / 2

  const totalDuration = 4900
  const startTime = performance.now()
  let lastCellIdx = 0

  track.style.transform = `translateY(0px)`

  function easeOutQuart(t) { return 1 - Math.pow(1 - t, 4) }

  function animate(now) {
    const elapsed = now - startTime
    const progress = Math.min(elapsed / totalDuration, 1)
    const ease = easeOutQuart(progress)
    const currentOffset = targetOffset * ease
    track.style.transform = `translateY(${-currentOffset}px)`

    // 틱 사운드: 셀이 바뀔 때마다
    const currentCellIdx = Math.floor(currentOffset / cellH)
    if (currentCellIdx !== lastCellIdx) {
      lastCellIdx = currentCellIdx
      const pitch = 600 + (progress > 0.7 ? 400 : 200) * (1 + Math.random() * 0.3)
      const vol = progress > 0.7 ? 0.12 : 0.06
      playTick(pitch, vol)
    }

    if (progress > 0.75 && roulette.value.phase === 'spinning') {
      roulette.value.phase = 'slowing'
    }

    if (progress < 1) {
      rouletteAnim = requestAnimationFrame(animate)
    } else {
      roulette.value.phase = 'done'
      roulette.value.done = true
      roulette.value.winnerIdx = winIdx
      roulette.value.winner = items[winIdx]
      playWinSound()
    }
  }

  rouletteAnim = requestAnimationFrame(animate)
}

function closeRoulette() {
  if (rouletteAnim) cancelAnimationFrame(rouletteAnim)
  stopSpinSound()
  roulette.value.show = false
}

function copyText(text) { navigator.clipboard.writeText(text); showToast(`${text} 복사됨`, 'ok') }
function exportExcel() {
  const params = new URLSearchParams()
  if (filterType.value) params.set('type_filter', filterType.value)
  if (filterTemplate.value) params.set('template_filter', filterTemplate.value)
  window.open(`${API}/api/export-excel?${params.toString()}`, '_blank')
}

function typeLabel(t) { return { all: '전체', balloon: '별풍', adballoon: '애드', mission: '대결' }[t] || t }
function typeIcon(t) { return { balloon: '★', adballoon: '◆', mission: '⚔' }[t] || '●' }

// ─── 시뮬레이션 ───
async function simulateResults() {
  try {
    const resp = await fetch(`${API}/api/simulate`, {
      method: 'POST',
      credentials: 'include',
    })
    const data = await resp.json()
    if (data.ok) {
      showToast(`시뮬레이션: ${data.count}건 생성됨`, 'ok')
    } else {
      showToast(data.error || '시뮬레이션 실패', 'warn')
    }
  } catch { showToast('서버 연결 실패', 'err') }
}

const toast = ref(null)
let toastTimer = null
function showToast(msg, type = 'ok') {
  toast.value = { msg, type }
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = null }, 2500)
}

// 템플릿별 매칭된 결과 수
function templateMatchedCount(name) {
  return results.value.filter(r => r.matched_template === name).length
}

// 템플릿별 남은 수치
function templateRemaining(t) {
  return Math.max(0, t.count - templateMatchedCount(t.name))
}

// 템플릿별 진행률 (0~100)
function templateProgress(t) {
  if (t.count <= 0) return 0
  return Math.min(100, (templateMatchedCount(t.name) / t.count) * 100)
}

// 카운트다운: 남은 시간 (초)
function templateRemainingSeconds(t) {
  if (!t.duration || t.duration <= 0) return -1  // 무제한
  const elapsed = (now.value / 1000) - t.started_at
  const remaining = (t.duration * 60) - elapsed
  return Math.max(0, remaining)
}

// 초를 MM:SS 포맷으로
function formatCountdown(secs) {
  if (secs < 0) return ''
  const m = Math.floor(secs / 60)
  const s = Math.floor(secs % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

// 미션 완료 여부 (목표 달성)
function templateCompleted(t) {
  return templateMatchedCount(t.name) >= t.count
}

onMounted(async () => {
  await checkAuth()
  if (authenticated.value) connectSSE()
  // 1초마다 now 갱신 (카운트다운용)
  nowTimer = setInterval(() => { now.value = Date.now() }, 1000)
})
onUnmounted(() => {
  if (eventSource) eventSource.close()
  if (nowTimer) clearInterval(nowTimer)
})
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
  --bg: #0c0c1d;
  --card: #13132b;
  --card-border: #1e1e3f;
  --surface: #191938;
  --text: #e8e8f0;
  --text-dim: #6b6b8a;
  --accent: #6c5ce7;
  --green: #00d2a0;
  --orange: #ff9f43;
  --red: #ff6b6b;
  --purple: #a29bfe;
  --star: #ffd32a;
  --ad: #ff6b81;
  --mission-color: #1dd1a1;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
}

body::before {
  content: '';
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background-image:
    linear-gradient(rgba(108,92,231,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(108,92,231,0.03) 1px, transparent 1px);
  background-size: 48px 48px;
  pointer-events: none; z-index: 0;
}

.app { max-width: 1200px; margin: 0 auto; padding: 0 20px 40px; position: relative; z-index: 1; }

/* Header */
.header { display: flex; align-items: center; justify-content: space-between; padding: 16px 0; border-bottom: 1px solid var(--card-border); margin-bottom: 20px; gap: 16px; }
.logo { display: flex; align-items: center; gap: 10px; }
.logo-img { width: 36px; height: 36px; border-radius: 10px; object-fit: cover; }
.header h1 { font-size: 18px; font-weight: 700; color: #fff; white-space: nowrap; }

.connect-bar { display: flex; align-items: center; gap: 8px; background: var(--card); border: 1px solid var(--card-border); border-radius: 12px; padding: 6px 12px; }
.status-led { width: 8px; height: 8px; border-radius: 50%; background: #444; flex-shrink: 0; }
.status-led.on { background: var(--green); box-shadow: 0 0 8px var(--green); animation: ledPulse 2s infinite; }
@keyframes ledPulse { 0%,100% { box-shadow: 0 0 4px var(--green); } 50% { box-shadow: 0 0 12px var(--green); } }
.connected-label { font-size: 12px; color: var(--green); font-weight: 600; white-space: nowrap; }
.input-streamer { background: var(--surface); border: 1px solid var(--card-border); border-radius: 8px; padding: 7px 12px; color: var(--text); font-size: 13px; width: 160px; outline: none; }
.input-streamer:focus { border-color: var(--accent); }
.btn-connect { background: var(--accent); color: #fff; border: none; padding: 7px 16px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; }
.btn-connect:hover { filter: brightness(1.15); }
.btn-connect:disabled { opacity: 0.5; cursor: default; }
.btn-disconnect { background: transparent; color: var(--red); border: 1px solid var(--red); padding: 7px 14px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer; }
.btn-icon { background: transparent; border: 1px solid var(--card-border); border-radius: 8px; padding: 6px 8px; color: var(--text-dim); cursor: pointer; }
.btn-icon:hover { color: var(--text); border-color: var(--accent); }
.btn-icon.sim-btn { border-color: var(--orange); color: var(--orange); }
.btn-icon.sim-btn:hover { background: rgba(255,159,67,0.12); }

/* Stats */
.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px; }
.stat-card { background: var(--card); border: 1px solid var(--card-border); border-radius: 12px; padding: 16px 20px; }
.stat-label { font-size: 12px; color: var(--text-dim); margin-bottom: 4px; }
.stat-num { font-size: 28px; font-weight: 800; }
.stat-num.accent { color: var(--accent); }
.stat-num.orange { color: var(--orange); }
.stat-num.green { color: var(--green); }
.stat-num.purple { color: var(--purple); }

/* Card */
.card { background: var(--card); border: 1px solid var(--card-border); border-radius: 16px; padding: 24px; margin-bottom: 20px; }
.card-header { margin-bottom: 16px; }
.card-header h2 { font-size: 15px; font-weight: 700; color: #fff; }

/* Auto Row */
.auto-row { display: flex; align-items: center; gap: 8px; padding: 12px 16px; background: var(--surface); border: 1px solid var(--card-border); border-radius: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.auto-badge { background: var(--orange); color: #000; font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 6px; }
.sub-text { font-size: 12px; color: var(--text-dim); }
.sub-text.dim { color: #555; }

/* Template Form */
.template-form { display: flex; align-items: flex-end; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
.notice-box { background: rgba(255,255,255,0.03); border: 1px solid var(--card-border); border-radius: 10px; padding: 12px 16px; margin-bottom: 16px; }
.notice-box p { margin: 0; padding: 2px 0; font-size: 12px; color: var(--text-dim); line-height: 1.6; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-group label { font-size: 11px; color: var(--text-dim); font-weight: 500; }
.input-sm { background: var(--surface); border: 1px solid var(--card-border); border-radius: 8px; padding: 7px 10px; color: var(--text); font-size: 13px; outline: none; }
.input-sm:focus { border-color: var(--accent); }
.num-input { width: 80px; text-align: center; }
.type-btns { display: flex; gap: 4px; }
.type-btn { background: var(--surface); border: 1px solid var(--card-border); color: var(--text-dim); padding: 6px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; }
.type-btn.active { border-color: var(--accent); color: #fff; background: rgba(108,92,231,0.15); }
.type-btn.star.active { border-color: var(--star); color: var(--star); }
.type-btn.ad.active { border-color: var(--ad); color: var(--ad); }
.type-btn.mission.active { border-color: var(--mission-color); color: var(--mission-color); }
.chk-group { flex-direction: row; gap: 12px; align-items: center; padding-top: 20px; }
.chk { font-size: 12px; color: var(--text-dim); display: flex; align-items: center; gap: 4px; cursor: pointer; }
.chk input { accent-color: var(--green); }
.btn-add { background: var(--green); color: #000; border: none; padding: 8px 20px; border-radius: 8px; font-size: 13px; font-weight: 700; cursor: pointer; }
.btn-add:hover { filter: brightness(1.1); }
.btn-add:disabled { opacity: 0.4; cursor: default; }

/* Templates */
.template-list { display: flex; flex-direction: column; gap: 6px; }
.template-item { display: flex; flex-direction: column; gap: 8px; background: var(--surface); border: 1px solid var(--card-border); border-radius: 8px; padding: 10px 14px; }
.template-item.completed { border-color: var(--green); background: rgba(0,210,160,0.05); }
.tmpl-top-row { display: flex; justify-content: space-between; align-items: center; }
.template-item.paused { opacity: 0.4; }
.tmpl-info { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.tmpl-name { font-weight: 600; font-size: 14px; }
.tmpl-count { background: var(--accent); color: #fff; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; }
.tmpl-type { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.tmpl-type.all { background: #333; color: #aaa; }
.tmpl-type.balloon { background: rgba(255,211,42,0.15); color: var(--star); }
.tmpl-type.adballoon { background: rgba(255,107,129,0.15); color: var(--ad); }
.tmpl-type.mission { background: rgba(29,209,161,0.15); color: var(--mission-color); }
.tmpl-opt { font-size: 10px; padding: 2px 6px; border-radius: 4px; background: rgba(108,92,231,0.15); color: var(--purple); }
.tmpl-result-count { font-size: 11px; color: var(--text-dim); margin-left: auto; font-weight: 600; }
.template-item.selected { border-color: var(--accent); background: rgba(108,92,231,0.1); }
.filter-badge { font-size: 12px; background: var(--accent); color: #fff; padding: 2px 10px; border-radius: 6px; cursor: pointer; font-weight: 600; margin-left: 8px; }
.tmpl-actions { display: flex; gap: 4px; }
.btn-icon-sm { background: transparent; border: 1px solid var(--card-border); color: var(--text-dim); width: 28px; height: 28px; border-radius: 6px; cursor: pointer; font-size: 12px; display: flex; align-items: center; justify-content: center; }
.btn-icon-sm:hover { border-color: var(--accent); color: var(--text); }
.btn-icon-sm.del:hover { border-color: var(--red); color: var(--red); }
.btn-icon-sm.check-btn { border-color: var(--green); color: var(--green); }
.btn-icon-sm.done-btn { border-color: var(--text-dim); color: var(--text-dim); }

/* Results */
.result-actions { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.filter-tabs { display: flex; gap: 4px; flex-wrap: wrap; align-items: center; }
.tab { background: transparent; border: 1px solid var(--card-border); color: var(--text-dim); padding: 5px 12px; border-radius: 6px; font-size: 12px; cursor: pointer; }
.tab.active { border-color: var(--accent); color: #fff; background: rgba(108,92,231,0.12); }
.tab.type-tab.mission.active { border-color: var(--mission-color); color: var(--mission-color); }
.tab.type-tab.balloon.active { border-color: var(--star); color: var(--star); }
.tab.type-tab.adballoon.active { border-color: var(--ad); color: var(--ad); }
.tab-sep { width: 1px; height: 20px; background: var(--card-border); margin: 0 4px; }
.export-btns { display: flex; gap: 4px; }
.btn-sm { padding: 5px 12px; border-radius: 6px; font-size: 11px; font-weight: 600; cursor: pointer; border: none; }
.btn-sm.btn-accent { background: var(--accent); color: #fff; }
.btn-sm.btn-muted { background: #333; color: #888; }
.btn-sm.btn-outline { background: transparent; border: 1px solid var(--card-border); color: var(--text-dim); }
.btn-sm.btn-outline:hover { border-color: var(--accent); color: var(--text); }
.btn-sm.btn-danger { background: transparent; border: 1px solid var(--red); color: var(--red); }

/* Result Items */
.results-list { display: flex; flex-direction: column; gap: 6px; margin-top: 12px; }
.result-item-wrap { background: var(--surface); border: 1px solid var(--card-border); border-left: 3px solid var(--accent); border-radius: 8px; overflow: hidden; }
.result-item-wrap.done { opacity: 0.45; border-left-color: var(--green); }
.result-item-wrap.balloon { border-left-color: var(--star); }
.result-item-wrap.adballoon { border-left-color: var(--ad); }
.result-item-wrap.mission { border-left-color: var(--mission-color); }
.result-item { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; gap: 12px; }
.result-message { padding: 6px 14px 10px 14px; font-size: 12px; color: var(--text); background: rgba(108,92,231,0.06); border-top: 1px solid var(--card-border); }
.msg-label { color: var(--text-dim); font-weight: 600; }
.btn-msg-toggle { background: transparent; border: none; cursor: pointer; font-size: 14px; padding: 2px 4px; border-radius: 4px; opacity: 0.7; transition: opacity 0.15s; }
.btn-msg-toggle:hover { opacity: 1; }
.result-left { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.result-badge { font-size: 12px; font-weight: 700; padding: 3px 10px; border-radius: 6px; white-space: nowrap; }
.result-badge.balloon { background: rgba(255,211,42,0.15); color: var(--star); }
.result-badge.adballoon { background: rgba(255,107,129,0.15); color: var(--ad); }
.result-badge.mission { background: rgba(29,209,161,0.15); color: var(--mission-color); }
.result-user-info { display: flex; flex-direction: column; gap: 1px; }
.result-nickname { font-weight: 600; font-size: 14px; cursor: pointer; color: var(--text); }
.result-nickname:hover { color: var(--accent); }
.result-id { font-size: 11px; color: var(--text-dim); cursor: pointer; font-family: monospace; }
.result-id:hover { color: var(--accent); }
.btn-station { font-size: 11px; color: var(--accent); text-decoration: none; border: 1px solid var(--accent); padding: 3px 8px; border-radius: 5px; white-space: nowrap; transition: all 0.15s; }
.btn-station:hover { background: rgba(108,92,231,0.15); color: #fff; }
.btn-fan { font-size: 11px; color: var(--star); text-decoration: none; border: 1px solid var(--star); padding: 3px 8px; border-radius: 5px; white-space: nowrap; transition: all 0.15s; }
.btn-fan:hover { background: rgba(255,211,42,0.15); color: #fff; }
.result-match { font-size: 10px; background: var(--green); color: #000; padding: 1px 6px; border-radius: 4px; font-weight: 700; }
.result-center { flex: 1; min-width: 0; }
.memo-input { width: 100%; background: transparent; border: 1px solid transparent; border-radius: 6px; padding: 5px 8px; color: var(--text-dim); font-size: 12px; outline: none; }
.memo-input:hover { border-color: var(--card-border); }
.memo-input:focus { border-color: var(--accent); color: var(--text); }
.result-right { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.result-time { font-size: 11px; color: var(--text-dim); white-space: nowrap; }
.empty-state { text-align: center; padding: 48px 20px; color: var(--text-dim); font-size: 14px; }

/* Pagination */
.pagination { display: flex; align-items: center; justify-content: center; gap: 4px; margin-top: 16px; flex-wrap: wrap; }
.page-btn { background: var(--surface); border: 1px solid var(--card-border); color: var(--text-dim); width: 32px; height: 32px; border-radius: 6px; font-size: 13px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.15s; }
.page-btn:hover:not(:disabled) { border-color: var(--accent); color: var(--text); }
.page-btn.active { background: var(--accent); border-color: var(--accent); color: #fff; font-weight: 700; }
.page-btn:disabled { opacity: 0.3; cursor: default; }
.page-dots { color: var(--text-dim); font-size: 13px; padding: 0 2px; }
.page-info { font-size: 11px; color: var(--text-dim); margin-left: 8px; }

/* Log Panel */
.log-panel { position: fixed; top: 0; right: -380px; width: 380px; height: 100vh; background: var(--card); border-left: 1px solid var(--card-border); z-index: 100; transition: right 0.3s ease; display: flex; flex-direction: column; }
.log-panel.open { right: 0; }
.log-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--card-border); }
.log-header h3 { font-size: 14px; font-weight: 600; }
.log-list { flex: 1; overflow-y: auto; padding: 12px; }
.log-item { padding: 6px 10px; border-radius: 6px; margin-bottom: 4px; font-size: 12px; display: flex; gap: 8px; align-items: baseline; }
.log-item.success { background: rgba(0,210,160,0.08); }
.log-item.error { background: rgba(255,107,107,0.08); }
.log-item.warn { background: rgba(255,159,67,0.08); }
.log-item.balloon { background: rgba(255,211,42,0.08); }
.log-item.adballoon { background: rgba(255,107,129,0.08); }
.log-item.mission { background: rgba(29,209,161,0.08); }
.log-time { color: var(--text-dim); font-size: 10px; white-space: nowrap; flex-shrink: 0; }
.log-msg { color: var(--text); word-break: break-all; }

/* Toast */
.toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); padding: 10px 28px; border-radius: 10px; font-size: 13px; font-weight: 600; color: #fff; z-index: 200; }
.toast.ok { background: rgba(0,210,160,0.85); }
.toast.warn { background: rgba(255,159,67,0.85); }
.toast.err { background: rgba(255,107,107,0.85); }
.toast-enter-active { animation: toastIn 0.3s; }
.toast-leave-active { animation: toastIn 0.2s reverse; }
@keyframes toastIn { from { opacity: 0; transform: translateX(-50%) translateY(12px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }

/* Login Screen */
.login-screen { display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }
.login-card { background: var(--card); border: 1px solid var(--card-border); border-radius: 20px; padding: 48px 40px; width: 360px; max-width: 100%; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
.login-logo { width: 64px; height: 64px; border-radius: 16px; margin-bottom: 16px; }
.login-title { font-size: 22px; font-weight: 800; color: #fff; margin-bottom: 6px; }
.login-sub { font-size: 13px; color: var(--text-dim); margin-bottom: 28px; }
.login-form { display: flex; flex-direction: column; gap: 12px; }
.login-input { background: var(--surface); border: 1px solid var(--card-border); border-radius: 10px; padding: 12px 16px; color: var(--text); font-size: 15px; outline: none; text-align: center; }
.login-input:focus { border-color: var(--accent); }
.login-btn { background: var(--accent); color: #fff; border: none; padding: 12px; border-radius: 10px; font-size: 15px; font-weight: 700; cursor: pointer; transition: filter 0.15s; }
.login-btn:hover { filter: brightness(1.15); }
.login-btn:disabled { opacity: 0.5; cursor: default; }
.login-error { color: var(--red); font-size: 13px; margin-top: 12px; }

/* Settings Modal */
.settings-modal { background: var(--card); border: 1px solid var(--card-border); border-radius: 20px; padding: 28px; width: 400px; max-width: 90vw; box-shadow: 0 20px 60px rgba(0,0,0,0.5); }
.settings-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.settings-header h2 { font-size: 18px; font-weight: 700; color: #fff; }
.settings-section { margin-bottom: 24px; }
.settings-section h3 { font-size: 13px; color: var(--text-dim); margin-bottom: 12px; font-weight: 600; }
.settings-form { display: flex; flex-direction: column; gap: 10px; }
.settings-form .input-sm { padding: 10px 12px; font-size: 13px; }
.pw-error { color: var(--red); font-size: 12px; }
.settings-footer { border-top: 1px solid var(--card-border); padding-top: 16px; display: flex; justify-content: flex-end; }

/* Roulette */
.roulette-btn { border-color: var(--orange) !important; color: var(--orange) !important; }
.roulette-btn:hover { background: rgba(255,159,67,0.12) !important; }
.roulette-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.75); z-index: 300; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(6px); }
.roulette-modal { background: var(--card); border: 1px solid var(--card-border); border-radius: 20px; padding: 32px; width: 420px; max-width: 90vw; text-align: center; box-shadow: 0 24px 80px rgba(108,92,231,0.2), 0 0 0 1px rgba(108,92,231,0.1); }
.roulette-title { font-size: 22px; font-weight: 800; color: #fff; margin-bottom: 20px; letter-spacing: 2px; }
.roulette-viewport { position: relative; height: 280px; overflow: hidden; border-radius: 14px; background: var(--surface); border: 2px solid var(--card-border); margin-bottom: 20px;
  mask-image: linear-gradient(to bottom, transparent 0%, black 20%, black 80%, transparent 100%);
  -webkit-mask-image: linear-gradient(to bottom, transparent 0%, black 20%, black 80%, transparent 100%);
}
.roulette-highlight { position: absolute; top: 50%; left: 0; right: 0; height: 58px; transform: translateY(-50%); border-top: 2px solid var(--accent); border-bottom: 2px solid var(--accent); background: rgba(108,92,231,0.12); z-index: 2; pointer-events: none; box-shadow: 0 0 20px rgba(108,92,231,0.15); }
.roulette-track { position: relative; z-index: 1; will-change: transform; }
.roulette-cell { height: 56px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; padding: 0 16px; }
.roulette-cell.winner { background: rgba(108,92,231,0.35); animation: winnerFlash 0.5s ease 3; }
@keyframes winnerFlash {
  0%, 100% { background: rgba(108,92,231,0.35); }
  50% { background: rgba(255,211,42,0.3); }
}
.roulette-nick { font-size: 16px; font-weight: 700; color: var(--text); }
.roulette-uid { font-size: 11px; color: var(--text-dim); font-family: monospace; }

/* Countdown */
.roulette-countdown { display: flex; align-items: center; justify-content: center; padding: 24px 0; }
.countdown-text { font-size: 48px; font-weight: 900; color: var(--orange); letter-spacing: 6px; text-shadow: 0 0 30px rgba(255,159,67,0.5); animation: countdownPop 1.2s ease forwards; }
@keyframes countdownPop {
  0% { transform: scale(0); opacity: 0; }
  30% { transform: scale(1.4); opacity: 1; }
  50% { transform: scale(1); }
  80% { transform: scale(1.1); opacity: 1; }
  100% { transform: scale(1); opacity: 0; }
}

/* Tension dots */
.roulette-tension { padding: 10px 0; font-size: 24px; color: var(--orange); letter-spacing: 8px; font-weight: 900; }
.tension-dot { animation: tensionBlink 0.5s infinite; }
.tension-dot.d2 { animation-delay: 0.15s; }
.tension-dot.d3 { animation-delay: 0.3s; }
@keyframes tensionBlink { 0%,100% { opacity: 0.2; } 50% { opacity: 1; } }

/* Winner result - 화려한 결과 */
.roulette-result {
  background: linear-gradient(135deg, rgba(108,92,231,0.2), rgba(255,211,42,0.12));
  border: 2px solid var(--accent);
  border-radius: 16px;
  padding: 28px 20px;
  margin-bottom: 16px;
  animation: resultPop 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  position: relative;
  overflow: hidden;
}
.roulette-result::before {
  content: '';
  position: absolute; inset: 0;
  background: linear-gradient(45deg, transparent 40%, rgba(255,255,255,0.06) 50%, transparent 60%);
  animation: resultShine 2s ease infinite;
}
@keyframes resultPop { from { opacity: 0; transform: scale(0.6); } to { opacity: 1; transform: scale(1); } }
@keyframes resultShine { 0% { transform: translateX(-100%); } 100% { transform: translateX(100%); } }
.roulette-confetti { font-size: 30px; margin-bottom: 10px; animation: confettiBounce 0.7s ease; letter-spacing: 6px; }
@keyframes confettiBounce { 0% { transform: scale(0); } 60% { transform: scale(1.2); } 100% { transform: scale(1); } }
.roulette-winner-label { font-size: 12px; color: var(--orange); text-transform: uppercase; letter-spacing: 6px; font-weight: 800; margin-bottom: 10px; }
.roulette-winner-name { font-size: 30px; font-weight: 900; color: #fff; text-shadow: 0 0 20px rgba(108,92,231,0.5); animation: nameGlow 1.5s ease infinite alternate; }
@keyframes nameGlow { from { text-shadow: 0 0 10px rgba(108,92,231,0.3); } to { text-shadow: 0 0 30px rgba(108,92,231,0.7), 0 0 60px rgba(108,92,231,0.2); } }
.roulette-winner-id { font-size: 14px; color: var(--accent); font-family: monospace; margin-top: 8px; font-weight: 600; }
.roulette-btns { display: flex; gap: 8px; justify-content: center; }

/* ─── Global Gauge & Countdown ─── */
.global-gauge-card {
  background: linear-gradient(135deg, var(--card) 0%, rgba(108,92,231,0.08) 100%);
  border: 1px solid var(--accent);
  border-radius: 16px;
  padding: 20px 24px 16px;
  margin-bottom: 20px;
  box-shadow: 0 0 24px rgba(108,92,231,0.08);
}
.global-gauge-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.global-gauge-left { display: flex; align-items: baseline; gap: 12px; }
.global-remaining-wrap { display: flex; align-items: baseline; gap: 6px; }
.global-icon { font-size: 20px; }
.global-remaining-num {
  font-size: 36px;
  font-weight: 900;
  color: var(--orange);
  font-variant-numeric: tabular-nums;
  line-height: 1;
  animation: remainPulse 2s ease infinite;
}
.global-remaining-num.urgent { color: var(--red); animation: remainPulse 1s ease infinite; }
.global-remaining-num.done { color: var(--green); animation: none; font-size: 28px; }
.global-remaining-label { font-size: 16px; font-weight: 700; color: var(--text-dim); }
.global-sub { font-size: 13px; color: var(--text-dim); font-weight: 600; font-variant-numeric: tabular-nums; display: flex; align-items: center; gap: 0; }
.global-sub-dim { color: #555; }
.global-target-val { color: var(--accent); cursor: pointer; border-bottom: 1px dashed var(--accent); padding: 0 2px; transition: color 0.15s; }
.global-target-val:hover { color: var(--purple); }
.global-target-input { width: 60px; background: var(--surface); border: 1px solid var(--accent); border-radius: 6px; padding: 2px 6px; color: var(--text); font-size: 13px; font-weight: 700; text-align: center; outline: none; font-variant-numeric: tabular-nums; }

.global-gauge-right { display: flex; align-items: center; }
.global-timer-wrap { display: flex; align-items: center; gap: 8px; }
.global-timer-num {
  font-size: 32px;
  font-weight: 900;
  font-family: 'SF Mono', 'Fira Code', monospace;
  color: var(--text);
  font-variant-numeric: tabular-nums;
  line-height: 1;
  padding: 4px 12px;
  background: rgba(255,255,255,0.06);
  border-radius: 10px;
}
.global-timer-num.warning { color: var(--orange); background: rgba(255,159,67,0.12); }
.global-timer-num.critical { color: var(--red); background: rgba(255,107,107,0.15); animation: countdownBlink 1s ease infinite; }
.global-timer-expired {
  font-size: 20px;
  font-weight: 800;
  color: var(--red);
  background: rgba(255,107,107,0.15);
  padding: 4px 14px;
  border-radius: 10px;
  animation: countdownBlink 1s ease infinite;
}
.global-timer-set { display: flex; align-items: center; gap: 4px; }
.global-timer-input {
  width: 64px;
  background: var(--surface);
  border: 1px solid var(--card-border);
  border-radius: 8px;
  padding: 6px 8px;
  color: var(--text);
  font-size: 18px;
  font-weight: 700;
  text-align: center;
  outline: none;
  font-variant-numeric: tabular-nums;
}
.global-timer-input:focus { border-color: var(--accent); }
.global-timer-unit { font-size: 14px; color: var(--text-dim); font-weight: 600; }
.global-timer-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid var(--card-border);
  background: var(--surface);
  color: var(--text-dim);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}
.global-timer-btn.start { border-color: var(--green); color: var(--green); }
.global-timer-btn.start:hover { background: rgba(0,210,160,0.15); }
.global-timer-btn.start:disabled { opacity: 0.3; cursor: default; }
.global-timer-btn.stop { border-color: var(--red); color: var(--red); }
.global-timer-btn.stop:hover { background: rgba(255,107,107,0.15); }
.global-timer-btn.reset { border-color: var(--text-dim); color: var(--text-dim); }
.global-timer-btn.reset:hover { border-color: var(--accent); color: var(--accent); }

.global-gauge-bar-wrap { display: flex; align-items: center; gap: 10px; }
.global-gauge-bar { flex: 1; height: 10px; background: rgba(255,255,255,0.06); border-radius: 5px; overflow: hidden; }
.global-gauge-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--purple));
  border-radius: 5px;
  transition: width 0.5s ease;
}
.global-gauge-fill.full { background: linear-gradient(90deg, var(--green), #00e6b0); }
.global-gauge-pct { font-size: 13px; font-weight: 800; color: var(--text-dim); min-width: 36px; text-align: right; font-variant-numeric: tabular-nums; }

.global-timer-bar-wrap { margin-top: 8px; }
.global-timer-bar { height: 4px; background: rgba(255,255,255,0.06); border-radius: 2px; overflow: hidden; }
.global-timer-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
  transition: width 1s linear;
}
.global-timer-fill.warning { background: var(--orange); }
.global-timer-fill.critical { background: var(--red); }

.timer-opt { background: rgba(162,155,254,0.15); color: var(--purple); }
@keyframes remainPulse { 0%,100% { opacity: 1; } 50% { opacity: 0.6; } }
@keyframes countdownBlink { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }

@media (max-width: 768px) {
  .stats-row { grid-template-columns: repeat(3, 1fr); }
  .header { flex-wrap: wrap; }
  .connect-bar { width: 100%; }
  .template-form { flex-direction: column; align-items: stretch; }
  .result-actions { flex-direction: column; }
}
</style>
