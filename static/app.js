/* ============================================================
   TeamUp 控制台 · 浏览器逻辑
   ============================================================ */

const $ = (sel) => document.querySelector(sel);

const STATE = {
  currentClient: null,
  currentSession: null,
  activeTurn: false,
  currentStage: "intake",
  lastHandoff: "等待任务",
  stageActivity: "尚未开始",
  flowLines: new Map(), // key="A→B" → {el, expiresAt}
};

const PIPELINE = [
  { key: "intake", label: "需求进线", owner: "你 / 唐僧" },
  { key: "plan", label: "方案定界", owner: "唐僧" },
  { key: "product", label: "产品定型", owner: "八戒" },
  { key: "build", label: "工程生产", owner: "猴哥" },
  { key: "qa", label: "质量门禁", owner: "沙僧" },
  { key: "success", label: "客户回流", owner: "白龙马" },
  { key: "done", label: "交付收口", owner: "唐僧" },
];

const AGENT_STAGE = {
  "唐僧": "plan",
  "八戒": "product",
  "猴哥": "build",
  "沙僧": "qa",
  "白龙马": "success",
};

// ────────────────────────────────────────────────────────────
// 初始化
// ────────────────────────────────────────────────────────────

async function init() {
  try {
    await refreshState();
  } catch (e) {
    setPipelineStage("intake", "等待连接真实后端");
  }
  bindUI();
  try {
    connectWS();
  } catch (e) {
    addEvent("error", "未连接后端，当前仅预览界面");
  }
  renderPipeline();
  setInterval(cleanupFlowLines, 500);
  window.addEventListener("resize", redrawFlowLines);
}

async function refreshState() {
  const r = await fetch("/api/state");
  const s = await r.json();
  populateClientSelect(s.clients, s.current_client);
  if (s.current_client) {
    STATE.currentClient = s.current_client;
    STATE.currentSession = s.current_session;
    updateSessionPill(true, s.current_session);
  }
  for (const [name, info] of Object.entries(s.agent_status || {})) {
    updateAgentStatus(name, info.status, info.activity);
  }
  setTurnActive(s.active_turn || false);
  refreshFiles();
}

function populateClientSelect(clients, selected) {
  const sel = $("#clientSelect");
  const prev = sel.value;
  sel.innerHTML = '<option value="">— 请选择 —</option>';
  for (const c of (clients || [])) {
    const opt = document.createElement("option");
    opt.value = c; opt.textContent = c;
    sel.appendChild(opt);
  }
  sel.value = selected || prev || "";
}

function bindUI() {
  $("#clientSelect").addEventListener("change", async (e) => {
    const name = e.target.value;
    if (!name) return;
    await selectClient(name);
  });

  $("#newClientBtn").addEventListener("click", async () => {
    const name = $("#newClientInput").value.trim();
    if (!name) { alert("请输入客户名"); return; }
    await selectClient(name);
    $("#newClientInput").value = "";
  });

  $("#newSessionBtn").addEventListener("click", async () => {
    if (!STATE.currentClient) { alert("请先选择一个客户"); return; }
    if (STATE.activeTurn) { alert("团队正在取经，请稍候再开新局"); return; }
    if (!confirm(`为「${STATE.currentClient}」开启全新 session？\n当前 session 将不再使用（历史记忆仍保留）。`)) return;
    await newSession(STATE.currentClient);
  });

  $("#chatForm").addEventListener("submit", (e) => { e.preventDefault(); sendMessage(); });
  $("#chatInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  });
  $("#refreshFilesBtn").addEventListener("click", refreshFiles);
}

async function selectClient(name) {
  const r = await fetch("/api/client/select", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!r.ok) { addChat("system", `选择客户失败: ${await r.text()}`); return; }
  const data = await r.json();
  _applyClientSelected(name, data.session_id);
}

async function newSession(name) {
  const r = await fetch("/api/client/new", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!r.ok) { addChat("system", `开新局失败: ${await r.text()}`); return; }
  const data = await r.json();
  _applyClientSelected(name, data.session_id);
  addChat("system", `已为「${name}」开启新局 ✦`);
}

function _applyClientSelected(name, sessionId) {
  STATE.currentClient = name;
  STATE.currentSession = sessionId;
  updateSessionPill(true, sessionId);
  setPipelineStage("intake", `客户：${name}`);
  // 确保客户出现在下拉菜单中
  const sel = $("#clientSelect");
  if (!Array.from(sel.options).find(o => o.value === name)) {
    const opt = document.createElement("option");
    opt.value = name; opt.textContent = name;
    sel.appendChild(opt);
  }
  sel.value = name;
}

async function sendMessage() {
  const text = $("#chatInput").value.trim();
  if (!text) return;
  if (!STATE.currentClient) { alert("请先选择客户"); return; }
  if (STATE.activeTurn) { alert("团队还在取经，请稍候再发"); return; }
  $("#chatInput").value = "";
  addChat("user", text);
  try {
    const r = await fetch("/api/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (!r.ok) {
      const err = await r.text();
      addChat("system", `发送失败: ${err}`);
    }
  } catch (e) {
    addChat("system", `网络错误: ${e}`);
  }
}

// ────────────────────────────────────────────────────────────
// WebSocket
// ────────────────────────────────────────────────────────────

function connectWS() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws`);
  ws.onopen = () => addEvent("system", "已连接控制台");
  ws.onclose = () => {
    addEvent("error", "连接断开，3 秒后重连…");
    setTimeout(connectWS, 3000);
  };
  ws.onerror = () => {};
  ws.onmessage = (e) => { try { handleEvent(JSON.parse(e.data)); } catch {} };
}

function handleEvent(msg) {
  const t = msg.type;

  if (t === "hello") {
    // 恢复服务端最新状态（重载页面后用）
    const s = msg.state || {};
    populateClientSelect(msg.clients || [], s.current_client);
    if (s.current_client) {
      STATE.currentClient = s.current_client;
      STATE.currentSession = s.current_session;
      updateSessionPill(true, s.current_session);
    }
    for (const [name, info] of Object.entries(s.agent_status || {})) {
      updateAgentStatus(name, info.status, info.activity);
    }
    setTurnActive(msg.active_turn || false);
    return;
  }

  if (t === "user_message") return; // 已在 sendMessage 里显示

  if (t === "turn_started") {
    setTurnActive(true);
    setPipelineStage("plan", truncate(msg.user_text, 42));
    addEvent("system", `▶ 新一轮：${truncate(msg.user_text, 30)}`);
    updateAgentStatus("唐僧", "thinking", "理解需求");
    lastAgentMsgEl = null; lastAgentMsgName = null;
    return;
  }

  if (t === "turn_ended") {
    setTurnActive(false);
    setPipelineStage("done", "本轮结束，等待验收或下一轮");
    addEvent("system", "■ 本轮结束");
    return;
  }

  if (t === "agent_text") {
    appendAgentChat(msg.agent, msg.text);
    return;
  }

  if (t === "agent_status") {
    updateAgentStatus(msg.agent, msg.status, msg.activity);
    setStageFromAgent(msg.agent, msg.status, msg.activity);
    return;
  }

  if (t === "thread_created") {
    setStageFromAgent(msg.agent, "working", `唐僧召见 ${msg.agent}`);
    addEvent("delegation", `🪷 唐僧召见 <span class="who">${esc(msg.agent)}</span>`);
    return;
  }

  if (t === "delegation") {
    setStageFromAgent(msg.to_agent, "working", msg.text);
    STATE.lastHandoff = `唐僧 → ${msg.to_agent}`;
    renderPipeline();
    addEvent("delegation",
      `<span class="who">唐僧</span> → <span class="who">${esc(msg.to_agent)}</span>: ${esc(truncate(msg.text, 50))}`);
    drawFlow("唐僧", msg.to_agent, "outbound");
    addChat("agent", `唐僧 → ${msg.to_agent}\n${truncate(msg.text, 300)}`, "唐僧");
    return;
  }

  if (t === "delegation_reply") {
    setStageFromAgent(msg.from_agent, "delivered", msg.text);
    STATE.lastHandoff = `${msg.from_agent} → 唐僧`;
    renderPipeline();
    addEvent("reply",
      `<span class="who">${esc(msg.from_agent)}</span> 交付 → <span class="who">唐僧</span>: ${esc(truncate(msg.text, 50))}`);
    drawFlow(msg.from_agent, "唐僧", "inbound");
    addChat("agent", `${msg.from_agent} → 唐僧\n${truncate(msg.text, 300)}`, msg.from_agent);
    return;
  }

  if (t === "tool_use") {
    setStageFromAgent(msg.agent, "working", `使用 ${msg.tool}`);
    addEvent("tool", `<span class="who">${esc(msg.agent)}</span> 🔧 ${esc(msg.tool)}`);
    return;
  }

  if (t === "files_updated") {
    renderFiles(msg.files || []);
    setPipelineStage("done", `交付物更新：${(msg.files || []).length} 个文件`);
    return;
  }

  if (t === "compacted") {
    addEvent("system", "💾 上下文已压缩");
    return;
  }

  if (t === "session_idle") {
    setTurnActive(false);
    setPipelineStage("done", "队伍待命，等待下一条指令");
    addEvent("system", "✓ 取经队伍待命中");
    return;
  }

  if (t === "session_terminated") {
    setTurnActive(false);
    setPipelineStage("done", "Session 已终止");
    addEvent("error", "Session 已终止");
    updateSessionPill(false);
    return;
  }

  if (t === "error") {
    setTurnActive(false);
    addEvent("error", "❌ " + esc(msg.message || "未知错误"));
    addChat("system", "错误: " + (msg.message || ""));
    return;
  }

  if (t === "client_selected") {
    addEvent("system", `客户「${esc(msg.client)}」session ···${(msg.session_id || "").slice(-6)}`);
    return;
  }
}

// ────────────────────────────────────────────────────────────
// 发送锁定
// ────────────────────────────────────────────────────────────

function setTurnActive(active) {
  STATE.activeTurn = active;
  const btn = $("#sendBtn");
  const ta = $("#chatInput");
  btn.disabled = active;
  btn.textContent = active ? "取经中…" : "送上路";
  ta.placeholder = active
    ? "团队正在取经，请等候…"
    : "向唐僧描述客户需求…\n或粘贴录音文字稿，唐僧会派徒弟们各司其职。";
}

function setStageFromAgent(agent, status, activity) {
  const stage = AGENT_STAGE[agent];
  if (!stage) return;
  if (status === "idle") return;
  if (status === "delivered" && agent !== "唐僧") {
    setPipelineStage(stage, `${agent} 已交付给唐僧`);
    return;
  }
  setPipelineStage(stage, activity || `${agent} ${STATUS_LABEL[status] || status || "工作中"}`);
}

function setPipelineStage(stage, activity) {
  STATE.currentStage = stage || STATE.currentStage;
  STATE.stageActivity = activity || STATE.stageActivity;
  renderPipeline();
}

function renderPipeline() {
  const currentIndex = PIPELINE.findIndex((item) => item.key === STATE.currentStage);
  const html = `
    <div class="production-head">
      <span>生产线</span>
      <strong>${esc(STATE.lastHandoff)}</strong>
    </div>
    <div class="production-rail">
      ${PIPELINE.map((item, index) => {
        const state = index < currentIndex ? "done" : index === currentIndex ? "current" : "future";
        return `<div class="production-step ${state}">
          <span>${index + 1}</span>
          <strong>${esc(item.label)}</strong>
          <em>${esc(item.owner)}</em>
        </div>`;
      }).join("")}
    </div>
    <div class="production-note">${esc(STATE.stageActivity)}</div>
  `;
  for (const el of [$("#productionStrip"), $("#productionSidebar")]) {
    if (el) el.innerHTML = html;
  }
}

// ────────────────────────────────────────────────────────────
// Agent 卡片状态
// ────────────────────────────────────────────────────────────

const STATUS_LABEL = {
  idle: "待命", thinking: "思考中", working: "工作中",
  delegating: "派任务", speaking: "回话中", delivered: "已交付",
};

function updateAgentStatus(name, status, activity) {
  const card = document.querySelector(`.agent-card[data-agent="${name}"]`);
  if (!card) return;
  const statusEl = card.querySelector(".agent-status");
  const actEl = card.querySelector(".agent-activity");
  statusEl.className = "agent-status " + (status || "idle");
  statusEl.textContent = STATUS_LABEL[status] || status || "待命";
  if (typeof activity === "string") actEl.textContent = activity;
  card.classList.toggle("active", !!(status && status !== "idle"));
}

// ────────────────────────────────────────────────────────────
// SVG 流动线
// ────────────────────────────────────────────────────────────

const SVG_NS = "http://www.w3.org/2000/svg";

function drawFlow(from, to, direction) {
  const key = `${from}→${to}`;
  let info = STATE.flowLines.get(key);
  if (!info) {
    const svg = $("#flowSvg");
    const path = document.createElementNS(SVG_NS, "path");
    path.classList.add("flow-line", direction);
    svg.appendChild(path);
    info = { el: path, direction, from, to, expiresAt: 0, fading: false };
    STATE.flowLines.set(key, info);
  }
  info.direction = direction;
  info.el.className.baseVal = "flow-line " + direction; // refresh class if direction changed
  info.expiresAt = Date.now() + 5000;
  info.fading = false;
  _updatePath(info.el, from, to);
}

function _updatePath(pathEl, fromName, toName) {
  const svg = $("#flowSvg");
  const svgBox = svg.getBoundingClientRect();
  const fromCard = document.querySelector(`.agent-card[data-agent="${fromName}"]`);
  const toCard = document.querySelector(`.agent-card[data-agent="${toName}"]`);
  if (!fromCard || !toCard || !svgBox.width) return;
  svg.setAttribute("viewBox", `0 0 ${svgBox.width} ${svgBox.height}`);
  const a = cardCenter(fromCard, svgBox);
  const b = cardCenter(toCard, svgBox);
  // 贝塞尔曲线 — 弯度像水墨笔触
  const dx = b.x - a.x, dy = b.y - a.y;
  const cx = (a.x + b.x) / 2 + dy * 0.25;
  const cy = (a.y + b.y) / 2 - dx * 0.25;
  pathEl.setAttribute("d", `M ${a.x} ${a.y} Q ${cx} ${cy} ${b.x} ${b.y}`);
}

function cardCenter(el, svgBox) {
  const r = el.getBoundingClientRect();
  return { x: r.left + r.width / 2 - svgBox.left, y: r.top + r.height / 2 - svgBox.top };
}

function cleanupFlowLines() {
  const now = Date.now();
  for (const [key, info] of STATE.flowLines) {
    if (!info.fading && now > info.expiresAt) {
      info.fading = true;
      info.el.style.transition = "opacity 1s";
      info.el.style.opacity = "0";
      setTimeout(() => {
        info.el.remove();
        STATE.flowLines.delete(key);
      }, 1000);
    }
  }
}

function redrawFlowLines() {
  for (const [key, info] of STATE.flowLines) {
    _updatePath(info.el, info.from, info.to);
  }
}

// ────────────────────────────────────────────────────────────
// 聊天
// ────────────────────────────────────────────────────────────

let lastAgentMsgEl = null;
let lastAgentMsgName = null;

function addChat(kind, text, who) {
  const log = $("#chatLog");
  const el = document.createElement("div");
  el.className = "msg " + kind;
  if (who) {
    const w = document.createElement("div");
    w.className = "who"; w.textContent = who;
    el.appendChild(w);
  }
  const body = document.createElement("div");
  body.className = "body"; body.textContent = text;
  el.appendChild(body);
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
  // 普通消息之后清空流式引用
  lastAgentMsgEl = null; lastAgentMsgName = null;
}

function appendAgentChat(who, text) {
  const log = $("#chatLog");
  if (!lastAgentMsgEl || lastAgentMsgName !== who) {
    const el = document.createElement("div");
    el.className = "msg agent";
    const w = document.createElement("div");
    w.className = "who"; w.textContent = who;
    el.appendChild(w);
    const body = document.createElement("div");
    body.className = "body"; body.textContent = text;
    el.appendChild(body);
    log.appendChild(el);
    lastAgentMsgEl = body;
    lastAgentMsgName = who;
  } else {
    lastAgentMsgEl.textContent += text;
  }
  log.scrollTop = log.scrollHeight;
}

// ────────────────────────────────────────────────────────────
// 文件
// ────────────────────────────────────────────────────────────

async function refreshFiles() {
  if (!STATE.currentSession) return;
  try {
    const files = await fetch("/api/files").then(r => r.json());
    renderFiles(files);
  } catch {}
}

function renderFiles(files) {
  const list = $("#fileList");
  list.innerHTML = "";
  if (!files.length) {
    list.innerHTML = '<div class="empty-hint">还未取得真经</div>';
    return;
  }
  for (const f of files) {
    const el = document.createElement("div");
    el.className = "file-item";
    const url = `/api/file/${encodeURIComponent(f.id)}?filename=${encodeURIComponent(f.name)}`;
    el.innerHTML =
      `<span class="file-name">${esc(f.name)}</span>` +
      `<span><span class="file-size">${fmtSize(f.size)}</span>` +
      ` <a href="${url}" download="${esc(f.name)}">下载</a></span>`;
    list.appendChild(el);
  }
}

// ────────────────────────────────────────────────────────────
// 事件流条
// ────────────────────────────────────────────────────────────

function addEvent(kind, html) {
  const strip = $("#eventStrip");
  const el = document.createElement("div");
  el.className = "strip-event " + kind;
  const ts = document.createElement("span");
  ts.className = "ts";
  ts.textContent = new Date().toLocaleTimeString("zh-CN", { hour12: false });
  el.appendChild(ts);
  const body = document.createElement("span");
  body.innerHTML = html;
  el.appendChild(body);
  strip.appendChild(el);
  while (strip.children.length > 60) strip.removeChild(strip.firstChild);
  strip.scrollLeft = strip.scrollWidth;
}

// ────────────────────────────────────────────────────────────
// 工具函数
// ────────────────────────────────────────────────────────────

function updateSessionPill(active, sid) {
  const pill = $("#sessionPill");
  pill.classList.toggle("active", !!active);
  pill.textContent = active ? `session · ${(sid || "").slice(-6)}` : "未开始";
}

function truncate(text, n) {
  if (!text) return "";
  text = String(text).replace(/\s+/g, " ").trim();
  return text.length > n ? text.slice(0, n) + "…" : text;
}

function fmtSize(n) {
  if (!n) return "—";
  if (n < 1024) return n + " B";
  if (n < 1048576) return (n / 1024).toFixed(1) + " KB";
  return (n / 1048576).toFixed(1) + " MB";
}

function esc(s) {
  return String(s || "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

init();
