const state = {
  currentCartridge: null,
  lastVoicePlan: null,
  lastBeliefs: [],
  lastProactive: [],
  debugEnabled: false,
  activePanel: 'beliefs'
};

const API_BASE = '/api';
const $ = (id) => document.getElementById(id);

function cartridgeLabel(name) {
  return String(name || 'persona').replace(/\.snp$/i, '').replaceAll('_', ' ');
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}

function showModal(message, title = 'Feature unavailable') {
  $('modalTitle').textContent = title;
  $('modalMessage').textContent = message;
  $('modalBackdrop').hidden = false;
}

function hideModal() {
  $('modalBackdrop').hidden = true;
}

function setToday() {
  $('todayLabel').textContent = new Date().toLocaleDateString(undefined, {
    weekday: 'long',
    month: 'short',
    day: 'numeric'
  });
}

async function api(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

function addMessage(kind, text, extras = []) {
  const log = $('messages');
  if (log.classList.contains('empty')) {
    log.classList.remove('empty');
    log.textContent = '';
  }
  const node = document.createElement('div');
  node.className = `msg ${kind}`;
  node.textContent = text;
  for (const extra of extras) {
    const meta = document.createElement('div');
    meta.className = 'meta';
    meta.textContent = extra;
    node.appendChild(meta);
  }
  log.appendChild(node);
  log.scrollTop = log.scrollHeight;
  return node;
}

function setPresence(text, active = false) {
  const node = $('presence');
  node.textContent = text;
  node.classList.toggle('active', active);
}

function rendererStatus(mode = 'mock') {
  const status = $('rendererStatus');
  status.classList.remove('renderer-offline', 'renderer-online', 'renderer-api');
  if (mode === 'ollama' || mode === 'local') {
    status.classList.add('renderer-online');
    $('rendererLabel').textContent = 'local renderer';
    $('rendererDetail').textContent = 'optional model connected';
  } else {
    status.classList.add('renderer-offline');
    $('rendererLabel').textContent = 'mock renderer';
    $('rendererDetail').textContent = 'Python package runtime';
  }
}

function pct(value, fallback = 0) {
  const n = Number(value);
  if (!Number.isFinite(n)) return fallback;
  return Math.max(0, Math.min(100, Math.round(n * 100)));
}

function thoughtFromStatus(payload = {}) {
  const mode = payload.current_mode || 'settled';
  const attention = payload.attention || 'unknown';
  const noise = payload.noise || 'unknown';
  if (noise === 'high') return 'listening toward a sudden change';
  if (mode === 'guarded') return 'holding a boundary';
  if (attention !== 'unknown') return `attention: ${attention}`;
  return 'waiting for a visible turn';
}

function updateStatus(status = {}) {
  const payload = status.status || status;
  const cartridge = status.session?.cartridge || state.currentCartridge;
  if (cartridge) {
    const label = cartridgeLabel(cartridge);
    $('characterName').textContent = label;
    $('chatTitle').textContent = label;
    $('portraitInitial').textContent = label.trim().charAt(0).toUpperCase() || '?';
    $('chatSubtitle').textContent = `${cartridge} | private local Python session`;
  }

  const avatar = payload.avatar_state || 'neutral';
  $('avatarFace').className = `avatar-face ${avatar}`;
  $('statePresence').textContent = payload.presence ?? 'unknown';
  $('stateAttention').textContent = payload.attention ?? 'unknown';
  $('stateMode').textContent = payload.current_mode ?? 'settled';
  $('stateWorld').textContent = payload.world ?? 'unknown';
  $('stateLight').textContent = payload.light ?? 'unknown';
  $('stateNoise').textContent = payload.noise ?? 'unknown';
  $('currentThought').textContent = thoughtFromStatus(payload);
  $('needEnergy').style.width = `${pct(payload.energy, 70)}%`;
  $('needTension').style.width = `${pct(payload.tension, 20)}%`;
  $('needComfort').style.width = `${pct(payload.comfort, 70)}%`;
  setPresence(payload.presence ? String(payload.presence) : 'offline-ready', false);
}

function beliefMarkup() {
  if (!state.lastBeliefs.length) {
    return '<div class="empty-trace">No current beliefs surfaced yet.</div>';
  }
  return state.lastBeliefs.map((belief) => {
    if (typeof belief === 'string') {
      return `<div class="belief-card"><p>${escapeHtml(belief)}</p></div>`;
    }
    const text = belief.text || JSON.stringify(belief);
    const support = belief.support_keys || belief.supportKeys || [];
    const distortion = belief.distortion || 'interpretive';
    return `<div class="belief-card">
      <p>${escapeHtml(text)}</p>
      <span>${escapeHtml(distortion)} | support: ${escapeHtml(support.join(', ') || 'visible context')}</span>
    </div>`;
  }).join('');
}

function voiceMarkup() {
  if (!state.lastVoicePlan) return '<div class="empty-trace">No voice-plan state yet.</div>';
  return Object.entries(state.lastVoicePlan)
    .map(([key, value]) => `<div class="kv"><strong>${escapeHtml(key)}</strong><span>${escapeHtml(String(value))}</span></div>`)
    .join('');
}

function proactiveMarkup() {
  if (!state.lastProactive.length) return '<div class="empty-trace">No proactive proposal currently surfaced.</div>';
  return state.lastProactive
    .map((item) => `<div class="belief-card"><p>${escapeHtml(item.text || item.reason || JSON.stringify(item))}</p></div>`)
    .join('');
}

function updatePanels() {
  $('beliefsPanel').innerHTML = beliefMarkup() + `<div class="trace-section"><strong>Proactive</strong>${proactiveMarkup()}</div>`;
  $('voicePanel').innerHTML = voiceMarkup();
}

function setActivePanel(panel) {
  state.activePanel = panel;
  document.querySelectorAll('.header-button').forEach(btn => btn.classList.toggle('active', btn.dataset.panel === panel));
  document.querySelectorAll('.trace-content').forEach(content => content.classList.remove('active'));
  $(`${panel}Panel`).classList.add('active');
  $('traceTitle').textContent = panel === 'debug' ? 'Debug' : panel === 'voice' ? 'Voice' : 'Beliefs';
  if (panel === 'debug' && state.debugEnabled) refreshDebug().catch(err => {
    $('debugData').textContent = `Debug unavailable: ${err.message}`;
  });
}

async function loadCartridges() {
  const data = await api('/cartridges');
  const select = $('cartridgeSelect');
  select.innerHTML = '';
  for (const item of data.cartridges) {
    const option = document.createElement('option');
    option.value = item.name;
    option.textContent = cartridgeLabel(item.name);
    if (item.name === data.current) option.selected = true;
    select.appendChild(option);
  }
  state.currentCartridge = data.current;
  updateStatus({ session: { cartridge: data.current }, status: {} });
}

async function refreshStatus() {
  const status = await api('/status');
  updateStatus(status);
  const proactive = await api('/proactive');
  state.lastProactive = proactive.events || [];
  updatePanels();
  if (state.debugEnabled) await refreshDebug();
}

async function selectCharacter(reset = false) {
  const cartridge = $('cartridgeSelect').value;
  const data = await api('/session/select', {
    method: 'POST',
    body: JSON.stringify({ cartridge, reset })
  });
  state.currentCartridge = data.session.cartridge;
  updateStatus({ session: data.session, status: data.status });
  addMessage('system', `Loaded ${data.session.cartridge}${reset ? ' with a fresh session' : ''}.`);
  await refreshStatus();
}

async function sendChat(text, serverTruth = null, visibleContext = null, kind = 'user') {
  setPresence('thinking', true);
  addMessage(kind, text);
  const agentNode = addMessage('char', '');
  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, server_truth: serverTruth, visible_context: visibleContext })
  });
  if (!response.ok || !response.body) throw new Error(`stream failed: ${response.status}`);

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let fullText = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split('\n\n');
    buffer = parts.pop() || '';
    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith('data:')) continue;
      const payload = line.slice(5).trim();
      if (payload === '[DONE]') continue;
      const event = JSON.parse(payload);
      if (event.type === 'status') updateStatus(event.status);
      if (event.type === 'token') {
        fullText += event.token;
        agentNode.firstChild ? agentNode.firstChild.textContent = fullText : agentNode.textContent = fullText;
      }
      if (event.type === 'second_thought') {
        const meta = document.createElement('div');
        meta.className = 'meta';
        meta.textContent = event.text;
        agentNode.appendChild(meta);
      }
      if (event.type === 'complete') {
        state.lastVoicePlan = event.voice_plan;
        state.lastBeliefs = event.beliefs || [];
        updatePanels();
      }
    }
  }
  setPresence('offline-ready', false);
  await refreshStatus();
}

async function sendSensor(kind, payload) {
  const endpoint = kind === 'audio' ? '/sensor/audio' : '/sensor/vision';
  const result = await api(endpoint, { method: 'POST', body: JSON.stringify(payload) });
  $('sensorResult').textContent = `${kind} event accepted: ${result.accepted}. Facts: ${(result.facts || []).length}.`;
  await refreshStatus();
}

async function refreshDebug() {
  const data = await api('/debug');
  $('debugData').textContent = JSON.stringify(data, null, 2);
}

function wireEvents() {
  $('inputForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const text = $('input').value.trim();
    if (!text) return;
    $('input').value = '';
    try { await sendChat(text); }
    catch (err) { addMessage('system', `Error: ${err.message}`); setPresence('error', false); }
  });

  $('quickSilence').addEventListener('click', async () => {
    try {
      await sendChat('...', null, { user_absent_minutes: 47, user_presence: 'returned', room_sound: 'quiet' }, 'idle');
    } catch (err) { addMessage('system', `Error: ${err.message}`); }
  });

  $('loadCharacter').addEventListener('click', () => selectCharacter(false).catch(err => addMessage('system', `Error: ${err.message}`)));
  $('resetSession').addEventListener('click', () => selectCharacter(true).catch(err => addMessage('system', `Error: ${err.message}`)));
  $('promptCharacter').addEventListener('click', () => sendChat('...', null, { user_presence: 'present', prompt_source: 'ui_prompt' }, 'idle').catch(err => addMessage('system', `Error: ${err.message}`)));
  $('connectModel').addEventListener('click', () => showModal('Local model rendering is optional in this Python lab. Start the backend with the optional renderer configured, then reload this page.'));
  $('attachButton').addEventListener('click', () => showModal('Attachments are reserved for a later multimodal renderer pass. This button remains here to match the V6 console shape.'));

  document.querySelectorAll('[data-audio]').forEach(btn => btn.addEventListener('click', () => sendSensor('audio', JSON.parse(btn.dataset.audio)).catch(err => addMessage('system', `Error: ${err.message}`))));
  document.querySelectorAll('[data-vision]').forEach(btn => btn.addEventListener('click', () => sendSensor('vision', JSON.parse(btn.dataset.vision)).catch(err => addMessage('system', `Error: ${err.message}`))));
  document.querySelectorAll('.header-button').forEach(btn => btn.addEventListener('click', () => setActivePanel(btn.dataset.panel)));

  $('debugToggle').addEventListener('change', async (event) => {
    state.debugEnabled = event.target.checked;
    $('debugData').textContent = state.debugEnabled ? 'Loading debug details...' : 'Debug mode is off.';
    if (state.debugEnabled) {
      try { await refreshDebug(); }
      catch (err) { $('debugData').textContent = `Debug unavailable: ${err.message}`; }
    }
  });

  $('modalClose').addEventListener('click', hideModal);
  $('modalBackdrop').addEventListener('click', (event) => {
    if (event.target === $('modalBackdrop')) hideModal();
  });
}

async function boot() {
  setToday();
  rendererStatus('mock');
  wireEvents();
  await loadCartridges();
  await refreshStatus();
  updatePanels();
  addMessage('system', 'Python lab ready. Select a character, then begin a session.');
}

boot().catch(err => {
  setPresence('error', false);
  addMessage('system', `Startup error: ${err.message}`);
});
