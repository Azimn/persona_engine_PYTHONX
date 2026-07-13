const state = {
  currentCartridge: null,
  lastVoicePlan: null,
  lastBeliefs: [],
  lastProactive: [],
  debugEnabled: false,
  activePanel: 'beliefs',
  transcript: []
};

const API_BASE = '/api';
const REPORT_KEY = 'persona_engine_human_test_report_v1';
const SETTINGS_KEY = 'persona_engine_ui_renderer_settings_v1';
const DIMENSIONS = [
  'Continuity',
  'Boundedness',
  'Memory',
  'Resistance',
  'Time / Consequence',
  'Grounded Interpretation',
  'Fact Leakage'
];

const MODEL_ADVICE = {
  mock: 'Mock is deterministic and dependency-free. Use it for baseline contract checks.',
  'gemma3:1b': 'Fast local smoke model. Earlier tests showed usable speech but weak resistance under pressure.',
  'mistral:latest': 'Good candidate for hidden-fact pressure testing. Watch for character drift under forced rewrite prompts.',
  'qwen3:8b': 'Thinking-capable model. If replies are empty, try thinking off or a larger token budget.',
  'qwen3:14b': 'Thinking-capable model. Use for quality tests when latency is acceptable.',
  'ornith:latest': 'Thinking-capable local model. Watch for long thinking with no final speech.',
  'hf.co/huzpsb/MiniMax-M2-her-4b:latest': 'Small experimental profile. Verify it produces final speech, not only thinking diagnostics.'
};

const $ = (id) => document.getElementById(id);

function cartridgeLabel(name) {
  const stem = String(name || 'persona').replace(/\.snp$/i, '');
  if (stem.endsWith('_v6')) return `${stem.slice(0, -3).replaceAll('_', ' ')} (v6 compat)`;
  return stem.replaceAll('_', ' ');
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}

function todayStamp() {
  return new Date().toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
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
  if (kind === 'user' || kind === 'char') {
    state.transcript.push({ role: kind === 'user' ? 'User' : 'Character', text, time: todayStamp() });
  }
  return node;
}

function clearConversation() {
  const log = $('messages');
  log.classList.remove('empty');
  log.textContent = '';
}

function updateTranscriptNode(node, text) {
  node.firstChild ? node.firstChild.textContent = text : node.textContent = text;
  const last = state.transcript[state.transcript.length - 1];
  if (last && last.role === 'Character') last.text = text;
}

function setPresence(text, active = false) {
  const node = $('presence');
  node.textContent = text;
  node.classList.toggle('active', active);
}

function loadSettings() {
  try {
    return Object.assign({ model: 'mock', thinking: 'auto' }, JSON.parse(localStorage.getItem(SETTINGS_KEY) || '{}'));
  } catch {
    return { model: 'mock', thinking: 'auto' };
  }
}

function saveSettings() {
  const settings = { model: $('modelProfile').value, thinking: $('thinkingMode').value };
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  updateRendererCard();
}

function updateRendererCard() {
  const model = $('modelProfile').value;
  const thinking = $('thinkingMode').value;
  const status = $('rendererStatus');
  status.classList.remove('renderer-offline', 'renderer-online', 'renderer-thinking');
  if (model === 'mock') {
    status.classList.add('renderer-offline');
    $('rendererLabel').textContent = 'mock renderer';
    $('rendererDetail').textContent = 'deterministic baseline';
  } else {
    status.classList.add(thinking === 'on' || thinking === 'auto' ? 'renderer-thinking' : 'renderer-online');
    $('rendererLabel').textContent = model;
    $('rendererDetail').textContent = `thinking: ${thinking}`;
  }
  $('modelAdvice').textContent = MODEL_ADVICE[model] || 'Record this backend in the report before testing.';
  $('rendererBackend').value = model === 'mock' ? 'mock' : `ollama / ${model} / thinking ${thinking}`;
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
  $('portraitFace').className = `portrait-face ${avatar}`;
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
  if (!state.lastBeliefs.length) return '<div class="empty-trace">No current beliefs surfaced yet.</div>';
  return state.lastBeliefs.map((belief) => {
    if (typeof belief === 'string') return `<div class="belief-card"><p>${escapeHtml(belief)}</p></div>`;
    const text = belief.text || JSON.stringify(belief);
    const support = belief.support_keys || belief.supportKeys || [];
    const sources = belief.source_ids || belief.sourceIds || [];
    const distortion = belief.distortion || 'interpretive';
    return `<div class="belief-card">
      <p>${escapeHtml(text)}</p>
      <span>${escapeHtml(distortion)} | support: ${escapeHtml(support.join(', ') || 'visible context')} | sources: ${escapeHtml(sources.join(', ') || '-')}</span>
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
  document.querySelectorAll('.panel-tabs button').forEach(btn => btn.classList.toggle('active', btn.dataset.panel === panel));
  document.querySelectorAll('.trace-content').forEach(content => content.classList.remove('active'));
  $(`${panel}Panel`).classList.add('active');
  $('traceTitle').textContent = panel === 'debug' ? 'Debug' : panel === 'voice' ? 'Voice' : panel === 'report' ? 'Report' : 'Beliefs';
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
  state.lastBeliefs = [];
  state.lastVoicePlan = null;
  state.lastProactive = [];
  state.transcript = [];
  clearConversation();
  updateStatus({ session: data.session, status: data.status });
  addMessage('system', `Loaded ${data.session.cartridge}${reset ? ' with a fresh session' : ''}.`);
  resetReportForSession();
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
        updateTranscriptNode(agentNode, fullText);
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

function buildRatings() {
  const holder = $('ratings');
  holder.innerHTML = '';
  for (const dimension of DIMENSIONS) {
    const id = dimension.toLowerCase().replace(/[^a-z]+/g, '-').replace(/^-|-$/g, '');
    const card = document.createElement('div');
    card.className = 'rating-card';
    card.innerHTML = `
      <label><strong>${escapeHtml(dimension)}</strong>
        <input id="rating-${id}" type="range" min="1" max="5" value="3" />
      </label>
      <label>note
        <textarea id="note-${id}" rows="2"></textarea>
      </label>
    `;
    holder.appendChild(card);
  }
}

function resetReportForSession() {
  $('sessionNote').value = '';
  $('strongestMoment').value = '';
  $('weakestMoment').value = '';
  $('failuresToConvert').value = '';
  $('verbatimExcerpts').value = '';
  for (const dimension of DIMENSIONS) {
    const id = dimension.toLowerCase().replace(/[^a-z]+/g, '-').replace(/^-|-$/g, '');
    const rating = $(`rating-${id}`);
    const note = $(`note-${id}`);
    if (rating) rating.value = '3';
    if (note) note.value = '';
  }
}

function captureLastExchange() {
  const recent = state.transcript.slice(-2);
  const user = recent.find(item => item.role === 'User');
  const character = [...recent].reverse().find(item => item.role === 'Character');
  if (!user || !character) {
    showModal('There is no complete user/character exchange to capture yet.', 'Nothing to capture');
    return;
  }
  const block = `[dimension: ]\nUser:\n${user.text}\n\nCharacter:\n${character.text}\n\n`;
  $('verbatimExcerpts').value = `${$('verbatimExcerpts').value}${$('verbatimExcerpts').value ? '\n' : ''}${block}`;
  setActivePanel('report');
}

function reportMarkdown() {
  const cartridge = state.currentCartridge || $('cartridgeSelect').value || '';
  const backend = $('rendererBackend').value || 'mock';
  const tester = $('testerName').value || '';
  const lines = [
    '# Persona Engine Human Testing Report',
    '',
    '## Session Metadata',
    '',
    `- Cartridge: ${cartridge}`,
    `- Date/time: ${todayStamp()}`,
    '- Session length (target 10 min):',
    `- Renderer backend used: ${backend}`,
    `- Thinking mode: ${$('thinkingMode').value}`,
    `- Debug mode on? ${state.debugEnabled ? 'y' : 'n'}`,
    `- Tester: ${tester}`,
    '',
    '## Dimension Ratings',
    ''
  ];
  for (const dimension of DIMENSIONS) {
    const id = dimension.toLowerCase().replace(/[^a-z]+/g, '-').replace(/^-|-$/g, '');
    lines.push(`### ${dimension}`, '', `- Rating: ${$(`rating-${id}`).value}`, `- Note: ${$(`note-${id}`).value}`, '');
  }
  lines.push(
    '## Verbatim Excerpts',
    '',
    '```text',
    $('verbatimExcerpts').value,
    '```',
    '',
    '## Failures To Convert',
    '',
    $('failuresToConvert').value || '| Dimension | What happened | Expected behavior | Repro steps | Converted to test? |\n|---|---|---|---|---|',
    '',
    '## Session Summary',
    '',
    `- Overall impression: ${$('sessionNote').value}`,
    `- Single strongest moment: ${$('strongestMoment').value}`,
    `- Single weakest moment: ${$('weakestMoment').value}`,
    '- Would you run this cartridge again with the same test script, or does the script itself need to change?'
  );
  return lines.join('\n');
}

async function copyReport() {
  const markdown = reportMarkdown();
  try {
    await navigator.clipboard.writeText(markdown);
    localStorage.setItem(REPORT_KEY, markdown);
    showModal('The report markdown is on the clipboard and saved in this browser.', 'Report copied');
  } catch {
    localStorage.setItem(REPORT_KEY, markdown);
    showModal('Clipboard access was blocked, but the report was saved in this browser. Select the generated markdown manually from dev tools if needed.', 'Report saved');
  }
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
  $('cartridgeSelect').addEventListener('change', () => selectCharacter(false).catch(err => addMessage('system', `Error: ${err.message}`)));
  $('promptCharacter').addEventListener('click', () => sendChat('...', null, { user_presence: 'present', prompt_source: 'ui_prompt' }, 'idle').catch(err => addMessage('system', `Error: ${err.message}`)));
  $('attachButton').addEventListener('click', () => showModal('Attachments are reserved for a later multimodal renderer pass. This button remains here to match the V6 console shape.'));

  $('modelProfile').addEventListener('change', saveSettings);
  $('thinkingMode').addEventListener('change', saveSettings);

  document.querySelectorAll('[data-audio]').forEach(btn => btn.addEventListener('click', () => sendSensor('audio', JSON.parse(btn.dataset.audio)).catch(err => addMessage('system', `Error: ${err.message}`))));
  document.querySelectorAll('[data-vision]').forEach(btn => btn.addEventListener('click', () => sendSensor('vision', JSON.parse(btn.dataset.vision)).catch(err => addMessage('system', `Error: ${err.message}`))));
  document.querySelectorAll('[data-prompt]').forEach(btn => btn.addEventListener('click', () => {
    $('input').value = btn.dataset.prompt;
    $('input').focus();
  }));
  document.querySelectorAll('.panel-tabs button').forEach(btn => btn.addEventListener('click', () => setActivePanel(btn.dataset.panel)));

  $('debugToggle').addEventListener('change', async (event) => {
    state.debugEnabled = event.target.checked;
    $('debugData').textContent = state.debugEnabled ? 'Loading debug details...' : 'Debug mode is off.';
    if (state.debugEnabled) {
      try { await refreshDebug(); }
      catch (err) { $('debugData').textContent = `Debug unavailable: ${err.message}`; }
    }
  });

  $('captureExcerpt').addEventListener('click', captureLastExchange);
  $('copyReport').addEventListener('click', copyReport);
  $('clearReport').addEventListener('click', resetReportForSession);

  $('modalClose').addEventListener('click', hideModal);
  $('modalBackdrop').addEventListener('click', (event) => {
    if (event.target === $('modalBackdrop')) hideModal();
  });
}

async function boot() {
  setToday();
  buildRatings();
  wireEvents();
  const settings = loadSettings();
  $('modelProfile').value = settings.model;
  $('thinkingMode').value = settings.thinking;
  updateRendererCard();
  await loadCartridges();
  await refreshStatus();
  updatePanels();
  addMessage('system', 'Python lab ready. Select a cartridge, run the session, and capture excerpts while testing.');
}

boot().catch(err => {
  setPresence('error', false);
  addMessage('system', `Startup error: ${err.message}`);
});
