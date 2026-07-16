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

function applyRendererStatus(renderer = {}) {
  const config = renderer.config || {};
  const runtime = renderer.runtime || {};
  const requested = runtime.requested_provider || config.provider || 'offline';
  const actual = runtime.actual_provider || 'offline';
  const model = runtime.model_name || config.model_name || 'offline-template';
  const status = $('rendererStatus');
  status.classList.remove('renderer-offline', 'renderer-online', 'renderer-thinking');
  if (actual === 'offline') {
    status.classList.add('renderer-offline');
    $('rendererLabel').textContent = 'offline renderer';
  } else {
    status.classList.add(config.thinking_mode === 'on' || config.thinking_mode === 'auto' ? 'renderer-thinking' : 'renderer-online');
    $('rendererLabel').textContent = model;
  }
  const fallback = runtime.fallback_reason;
  $('rendererDetail').textContent = fallback ? `${requested} fell back: ${fallback}` : `${actual} | thinking: ${config.thinking_mode || 'auto'}`;
  $('modelAdvice').textContent = fallback || MODEL_ADVICE[model] || (actual === 'offline' ? 'Deterministic dependency-free renderer.' : 'Server-confirmed local renderer.');
  $('rendererBackend').value = `${actual} / ${model} / thinking ${config.thinking_mode || 'auto'}`;
}

function showModelCapabilities(applyDefaults = false) {
  const provider = $('rendererProvider').value;
  const entry = (state.rendererDiscovery?.providers || []).find(item => item.provider === provider);
  const model = $('modelProfile').value;
  const capability = entry?.model_capabilities?.[model];
  if (!capability) {
    $('modelCapabilities').textContent = 'No capability profile is available for this model.';
    $('thinkingMode').disabled = false;
    return;
  }
  if (applyDefaults) {
    $('thinkingMode').value = capability.recommended_thinking || 'auto';
    $('rendererTimeout').value = capability.practical_timeout_seconds || 60;
    $('rendererTokens').value = capability.recommended_token_budget || 256;
  }
  $('thinkingMode').disabled = capability.supports_thinking === false;
  const thinking = capability.supports_thinking === null ? 'unknown' : capability.supports_thinking ? 'supported' : 'not supported';
  const context = capability.context_size ? `${Number(capability.context_size).toLocaleString()} tokens` : 'not applicable / unknown';
  $('modelCapabilities').innerHTML = `
    <div><strong>thinking</strong><span>${escapeHtml(thinking)} | recommended ${escapeHtml(capability.recommended_thinking)}</span></div>
    <div><strong>cognition JSON</strong><span>${escapeHtml(capability.private_cognition_json_reliability)}</span></div>
    <div><strong>context</strong><span>${escapeHtml(context)}</span></div>
    <div><strong>final answer</strong><span>${escapeHtml(capability.final_answer_behavior)}</span></div>
  `;
}

function populateModels(discovery, selectedModel, applyDefaults = false) {
  const provider = $('rendererProvider').value;
  const entry = (discovery.providers || []).find(item => item.provider === provider);
  const select = $('modelProfile');
  select.innerHTML = '';
  for (const model of (entry?.models || [])) {
    const option = document.createElement('option');
    option.value = model;
    option.textContent = model;
    select.appendChild(option);
  }
  if (selectedModel && [...select.options].some(option => option.value === selectedModel)) select.value = selectedModel;
  select.disabled = !entry?.available || select.options.length === 0;
  $('applyRenderer').disabled = !entry?.available;
  $('modelAdvice').textContent = entry?.detail || 'Renderer provider unavailable.';
  showModelCapabilities(applyDefaults);
}

async function loadRendererControls() {
  const discovery = await api('/renderers');
  state.rendererDiscovery = discovery;
  const config = discovery.current?.config || {};
  $('rendererProvider').value = config.provider || 'offline';
  populateModels(discovery, config.model_name);
  $('thinkingMode').value = config.thinking_mode || 'auto';
  $('rendererTimeout').value = config.timeout_seconds || 60;
  $('rendererTokens').value = config.token_budget || 256;
  showModelCapabilities(false);
  applyRendererStatus(discovery.current);
}

async function applyRendererConfig() {
  const payload = {
    provider: $('rendererProvider').value,
    model_name: $('modelProfile').value,
    thinking_mode: $('thinkingMode').value,
    timeout_seconds: Number($('rendererTimeout').value),
    token_budget: Number($('rendererTokens').value)
  };
  const renderer = await api('/renderer/config', { method: 'POST', body: JSON.stringify(payload) });
  applyRendererStatus(renderer);
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
    const sessionMode = status.session?.mode || 'active';
    $('chatSubtitle').textContent = `${cartridge} | ${sessionMode} local Python session`;
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
  if (status.renderer) applyRendererStatus(status.renderer);
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
  if (data.renderer) applyRendererStatus(data.renderer);
  await loadRendererControls();
  const modeLabel = data.session.mode === 'resumed' ? 'Resumed' : data.session.mode === 'fresh' ? 'Started fresh' : 'Started';
  addMessage('system', `${modeLabel} ${data.session.cartridge}.`);
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
      if (event.type === 'performance') {
        const performance = event.performance || {};
        const act = (performance.acts || [])[0] || {};
        const visibleAction = act.function === 'none' ? 'withheld response' : `${act.function || 'continues'}${act.target ? ` ${act.target}` : ''}`;
        fullText = `*${visibleAction}*`;
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
        if (event.renderer) applyRendererStatus(event.renderer);
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
  renderLifeInspector(data.life_inspector || {});
  $('debugData').textContent = JSON.stringify(data, null, 2);
}

function renderLifeInspector(inspector) {
  const holder = $('lifeInspector');
  const life = inspector.state || {};
  const events = inspector.objective_events || [];
  const experiences = inspector.subjective_experiences || [];
  const retrievals = inspector.retrievals || [];
  const lifeEvents = life.events || [];
  const artifacts = inspector.learning_artifacts || [];
  const synthesis = inspector.synthesis || {};
  const completion = inspector.action_completion || {};
  const intrinsic = inspector.intrinsic || {};
  const actionDecision = intrinsic.action_decision || {};
  const semantic = inspector.semantic_activation || {};
  const lifeEventRows = lifeEvents.slice(-5).reverse().map(item => `<p><strong>${escapeHtml(item.category)}</strong> ${escapeHtml(item.action)} <small>${escapeHtml(item.origin)}</small></p>`).join('');
  const artifactRows = artifacts.slice(-4).reverse().map(item => `<p><strong>${escapeHtml(item.kind)}</strong> ${escapeHtml(item.content)} <small>tier ${item.source_tier} · ${escapeHtml(item.verification_state)}</small></p>`).join('');
  holder.hidden = false;
  holder.innerHTML = `
    <section class="life-summary">
      <div><span>activity</span><strong>${escapeHtml(life.current_activity || 'unknown')}</strong></div>
      <div><span>intention</span><strong>${escapeHtml(life.current_intention || 'none')}</strong></div>
      <div><span>attention</span><strong>${escapeHtml(life.attention_target || 'none')}</strong></div>
      <div><span>status</span><strong>${escapeHtml(life.activity_status || 'unknown')}</strong></div>
      <div><span>integration</span><strong>${Number(synthesis.integration_capacity || 0).toFixed(2)}</strong></div>
      <div><span>field width</span><strong>${escapeHtml(String(synthesis.field_width || 0))}</strong></div>
    </section>
    <section class="life-list"><h3>Intrinsic action</h3>${actionDecision.decision_id ? `<article><strong>${escapeHtml(actionDecision.activity_description)} · ${escapeHtml(actionDecision.action_type)}</strong><p>want: ${escapeHtml(actionDecision.want_id)} · intention: ${escapeHtml(actionDecision.intention)}</p><p>target: ${escapeHtml(actionDecision.target)} · renderer required: ${escapeHtml(String(actionDecision.requires_renderer))}</p><p>${(actionDecision.selection_reason || []).map(escapeHtml).join(' · ')}</p></article>` : '<p class="empty-state">No intrinsic action selected yet.</p>'}</section>
    <section class="life-list"><h3>Situated synthesis</h3>${synthesis.synthesis_id ? `<article><strong>${escapeHtml(synthesis.selected_intention_id || synthesis.selected_habit_id || 'no selected tendency')}</strong><p>considered: ${(synthesis.considered_influences || []).map(item => escapeHtml(item.influence_id)).join(' · ') || 'none'}</p><p>inhibited: ${(synthesis.inhibited_influences || []).map(item => escapeHtml(item.influence_id)).join(' · ') || 'none'}</p><p>conflicts: ${(synthesis.unresolved_conflicts || []).map(escapeHtml).join(' · ') || 'none'}</p></article>` : '<p class="empty-state">No synthesis recorded yet.</p>'}</section>
    <section class="life-list"><h3>Semantic candidates</h3>${(semantic.concepts || []).length ? `<article><strong>${semantic.concepts.map(item => escapeHtml(item.name)).join(' · ')}</strong><p>features: ${(semantic.features || []).map(item => `${escapeHtml(item.feature_name)}=${escapeHtml(item.value)}`).join(' · ') || 'none'}</p><p>affordances: ${(semantic.affordances || []).map(item => `${escapeHtml(item.action)} ${escapeHtml(item.target_name)}`).join(' · ') || 'none'}</p><p>unknowns: ${(semantic.unresolved_questions || []).map(escapeHtml).join(' · ') || 'none'} · candidates only, never world facts</p></article>` : '<p class="empty-state">No structured concepts were observed.</p>'}</section>
    <section class="life-list"><h3>Action completion</h3>${completion.world_event_id ? `<article><strong>${escapeHtml(completion.attempted_action)} · ${escapeHtml(completion.outcome_status)}</strong><p>expected: ${escapeHtml(completion.expected_outcome)} · actual: ${escapeHtml(completion.actual_outcome)}</p><p>world: ${escapeHtml(completion.world_event_id)} · subjective: ${escapeHtml(completion.subjective_interpretation_reference || 'none')}</p></article>` : '<p class="empty-state">No completed action yet.</p>'}</section>
    <section class="life-list"><h3>World and experience</h3>${events.slice(0, 5).map(event => {
      const versions = experiences.filter(item => item.world_event_id === event.event_id);
      return `<article><strong>World: ${escapeHtml(event.outcome || event.action)}</strong>${versions.map(item => `<p>${escapeHtml(item.character_id)}: ${escapeHtml(item.perceived_summary)} <small>${escapeHtml(item.emotional_residue)} · ${Number(item.confidence || 0).toFixed(2)}</small></p>`).join('')}</article>`;
    }).join('') || '<p class="empty-state">No objective events yet.</p>'}</section>
    <section class="life-list"><h3>Recall reasons</h3>${retrievals.slice(0, 4).map(item => `<article><strong>${escapeHtml(item.content || item.memory_id)}</strong><p>${Object.entries(item.reasons || {}).filter(([, value]) => Number(value) > 0 || value === 'available').map(([key, value]) => `${escapeHtml(key)}: ${escapeHtml(String(value))}`).join(' · ')}</p></article>`).join('') || '<p class="empty-state">No memories recalled yet.</p>'}</section>
    <section class="life-list"><h3>Life events and learning</h3>${lifeEventRows || artifactRows ? lifeEventRows + artifactRows : '<p class="empty-state">No life events or artifacts yet.</p>'}</section>`;
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

function downloadJson(payload, filename) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

async function exportSessionBundle() {
  const bundle = await api('/session/export', {
    method: 'POST',
    body: JSON.stringify({ transcript: state.transcript, report_markdown: reportMarkdown() })
  });
  const stem = String(bundle.cartridge || 'session').replace(/\.snp$/i, '');
  downloadJson(bundle, `${stem}-persona-session.json`);
  showModal(`Exported ${bundle.canonical_events.length} replayable events with checksum ${bundle.checksum.slice(0, 12)}.`, 'Session exported');
}

function restoreTranscript(transcript) {
  state.transcript = [];
  clearConversation();
  for (const item of transcript || []) {
    if (item.role === 'User') addMessage('user', item.text || '');
    if (item.role === 'Character') addMessage('char', item.text || '');
  }
  state.transcript = (transcript || [])
    .filter(item => item && (item.role === 'User' || item.role === 'Character'))
    .map(item => ({ role: item.role, text: String(item.text || ''), time: item.time || '' }));
}

async function importReplayFile(file) {
  if (!file) return;
  if (file.size > 10 * 1024 * 1024) throw new Error('Replay bundle exceeds the 10 MB UI limit.');
  const bundle = JSON.parse(await file.text());
  const result = await api('/session/replay', { method: 'POST', body: JSON.stringify(bundle) });
  state.currentCartridge = result.session.cartridge;
  $('cartridgeSelect').value = result.session.cartridge;
  restoreTranscript(result.transcript || []);
  if (result.report_markdown) localStorage.setItem(REPORT_KEY, result.report_markdown);
  updateStatus({ session: result.session, status: result.status, renderer: result.renderer });
  applyRendererStatus(result.renderer);
  await loadRendererControls();
  await refreshStatus();
  const digest = result.digest_matches ? 'State digest matched.' : 'State digest differs; inspect the replay trace.';
  addMessage('system', `Replayed ${result.events_replayed} canonical events in an isolated session. ${digest}`);
  showModal(digest, 'Replay complete');
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

  $('rendererProvider').addEventListener('change', () => populateModels(state.rendererDiscovery || {}, null, true));
  $('modelProfile').addEventListener('change', () => showModelCapabilities(true));
  $('applyRenderer').addEventListener('click', () => applyRendererConfig().catch(err => showModal(err.message, 'Renderer configuration failed')));

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
    $('lifeInspector').hidden = !state.debugEnabled;
    if (state.debugEnabled) {
      try { await refreshDebug(); }
      catch (err) { $('debugData').textContent = `Debug unavailable: ${err.message}`; }
    }
  });

  $('captureExcerpt').addEventListener('click', captureLastExchange);
  $('copyReport').addEventListener('click', copyReport);
  $('exportSession').addEventListener('click', () => exportSessionBundle().catch(err => showModal(err.message, 'Session export failed')));
  $('importReplay').addEventListener('click', () => $('replayFile').click());
  $('replayFile').addEventListener('change', (event) => {
    const file = event.target.files?.[0];
    importReplayFile(file).catch(err => showModal(err.message, 'Replay import failed'));
    event.target.value = '';
  });
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
  await loadCartridges();
  await loadRendererControls();
  await refreshStatus();
  updatePanels();
  addMessage('system', 'Python lab ready. Select a cartridge, run the session, and capture excerpts while testing.');
}

boot().catch(err => {
  setPresence('error', false);
  addMessage('system', `Startup error: ${err.message}`);
});
