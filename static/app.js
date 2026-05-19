/* ============================================================
   TeamUp 控制台 · 浏览器逻辑
   - WebSocket 接收事件流
   - 更新五个 agent 卡片状态
   - 动态绘制 SVG 流动线（任务委派 / 回报）
   - 聊天 + 文件 + 事件日志
   ============================================================ */

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const STATE = {
  currentClient: null,
  currentSession: null,
  flowLines: new Map(), // 当前活跃的 SVG line: key="A->B" -> {el, expiresAt}
};

// ────────────────────────────────────────────────────────────
// 初始化
// ────────────────────────────────────────────────────────────

async function init() {
  await refreshState();
  bindUI();
  connectWS();
  // 定时清理过期的流动线
  setInterval(cleanupFlowLines, 500);
  // 监听窗口 resize 重绘箭头
  window.addEventListener("resize", () => {
    for (const [key, info] of STATE.flowLines) {
      const [from, to] = key.split("→");
      updateLinePath(info.el, from, to);
    }
  });
}

async function refreshState() {
  const r = await fetch("/api/state");
  const s = await r.json();
  const select = $("#clientSelect");
  select.innerHTML = '<option value="">— 请选择 —</option>';
  for (const c of s.clients) {
    const opt = document.createElement("option");
    opt.value = c; opt.textContent = c;
    select.appendChild(opt);
  }
  if (s.current_client) {
    select.value = s.current_client;
    STATE.currentClient = s.current_client;
    STATE.currentSession = s.current_session;
    updateSessionPill(true, s.current_session);
  }
  // 应用上次的 agent 状态
  for (const [name, info] of Object.entries(s.agent_status || {})) {
    updateAgentStatus(name, info.status, info.activity);
  }
  // 拉一次文件
  refreshFiles();
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

  $("#chatForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    sendMessage();
  });

  $("#chatInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  $("#refreshFilesBtn").addEventListener("click", refreshFiles);
}

async function selectClient(name) {
  const r = await fetch("/api/client/select", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  const data = await r.json();
  STATE.currentClient = name;
  STATE.currentSession = data.session_id;
  updateSessionPill(true, data.session_id);
  addChat("system", `已切换到客户「${name}」 — session: ${data.session_id}`);
  await refreshState();
}

async function sendMessage() {
  const text = $("#chatInput").value.trim();
  if (!text) return;
  if (!STATE.currentClient) { alert("请先选择客户"); return; }
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
  ws.onmessage = (e) => {
    try { handleEvent(JSON.parse(e.data)); } catch {}
  };
}

function handleEvent(msg) {
  const t = msg.type;

  if (t === "hello") {
    return;
  }

  if (t === "user_message") {
    // 服务端 echo 的用户消息：UI 已经显示，跳过
    return;
  }

  if (t === "turn_started") {
    addEvent("system", `▶ 新一轮：${truncate(msg.user_text, 30)}`);
    updateAgentStatus("唐僧", "thinking", "理解需求");
    return;
  }

  if (t === "turn_ended") {
    addEvent("system", "■ 本轮结束");
    return;
  }

  if (t === "agent_text") {
    // 唐僧的文本（流式追加）
    appendAgentChat(msg.agent, msg.text);
    return;
  }

  if (t === "agent_status") {
    updateAgentStatus(msg.agent, msg.status, msg.activity);
    return;
  }

  if (t === "thread_created") {
    addEvent("delegation", `🪷 唐僧召见 <span class="who">${msg.agent}</span>`);
    return;
  }

  if (t === "delegation") {
    addEvent("delegation",
      `<span class="who">唐僧</span>→ <span class="who">${msg.to_agent}</span>: ${truncate(msg.text, 50)}`);
    drawFlow("唐僧", msg.to_agent, "outbound");
    addChat("agent", `[唐僧 → ${msg.to_agent}]\n${truncate(msg.text, 200)}`, "唐僧");
    return;
  }

  if (t === "delegation_reply") {
    addEvent("reply",
      `<span class="who">${msg.from_agent}</span> 交付 → <span class="who">唐僧</span>: ${truncate(msg.text, 50)}`);
    drawFlow(msg.from_agent, "唐僧", "inbound");
    addChat("agent", `[${msg.from_agent} → 唐僧]\n${truncate(msg.text, 200)}`, msg.from_agent);
    return;
  }

  if (t === "tool_use") {
    addEvent("tool", `<span class="who">${msg.agent}</span> 🔧 ${msg.tool}`);
    return;
  }

  if (t === "files_updated") {
    renderFiles(msg.files || []);
    return;
  }

  if (t === "compacted") {
    addEvent("system", "💾 上下文已压缩");
    return;
  }

  if (t === "session_idle") {
    addEvent("system", "✓ 取经队伍待命中");
    return;
  }

  if (t === "session_terminated") {
    addEvent("error", "Session 已终止");
    updateSessionPill(false);
    return;
  }

  if (t === "error") {
    addEvent("error", "❌ " + (msg.message || "未知错误"));
    addChat("system", "错误: " + msg.message);
    return;
  }

  if (t === "client_selected") {
    addEvent("system", `客户 ${msg.client} session=${msg.session_id}`);
    return;
  }
}

// ────────────────────────────────────────────────────────────
// Agent 卡片状态
// ────────────────────────────────────────────────────────────

const STATUS_LABEL = {
  idle: "待命",
  thinking: "思考中",
  working: "工作中",
  delegating: "派任务",
  speaking: "回话中",
  delivered: "已交付",
};

function updateAgentStatus(name, status, activity) {
  const card = document.querySelector(`.agent-card[data-agent="${name}"]`);
  if (!card) return;
  const statusEl = card.querySelector(".agent-status");
  const actEl = card.querySelector(".agent-activity");

  // 重置 class，再加新的
  statusEl.className = "agent-status " + (status || "idle");
  statusEl.textContent = STATUS_LABEL[status] || status || "待命";

  if (typeof activity === "string") actEl.textContent = activity;

  if (status && status !== "idle") {
    card.classList.add("active");
  } else {
    card.classList.remove("active");
  }
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
    const line = document.createElementNS(SVG_NS, "path");
    line.classList.add("flow-line", direction);
    svg.appendChild(line);
    info = { el: line, expiresAt: 0 };
    STATE.flowLines.set(key, info);
  }
  info.expiresAt = Date.now() + 4000;
  updateLinePath(info.el, from, to);
}

function updateLinePath(pathEl, fromName, toName) {
  const svg = $("#flowSvg");
  const svgBox = svg.getBoundingClientRect();
  const fromCard = document.querySelector(`.agent-card[data-agent="${fromName}"]`);
  const toCard = document.querySelector(`.agent-card[data-agent="${toName}"]`);
  if (!fromCard || !toCard) return;
  const a = centerOf(fromCard, svgBox);
  const b = centerOf(toCard, svgBox);
  // 用贝塞尔曲线让线条有水墨般的弯度
  const dx = b.x - a.x, dy = b.y - a.y;
  const cx = (a.x + b.x) / 2 + dy * 0.2;
  const cy = (a.y + b.y) / 2 - dx * 0.2;
  pathEl.setAttribute("d", `M ${a.x} ${a.y} Q ${cx} ${cy} ${b.x} ${b.y}`);

  // 设置 SVG viewBox 匹配真实尺寸（首次绘制时）
  svg.setAttribute("viewBox", `0 0 ${svgBox.width} ${svgBox.height}`);
}

function centerOf(el, svgBox) {
  const r = el.getBoundingClientRect();
  return {
    x: r.left + r.width / 2 - svgBox.left,
    y: r.top + r.height / 2 - svgBox.top,
  };
}

function cleanupFlowLines() {
  const now = Date.now();
  for (const [key, info] of STATE.flowLines) {
    if (now > info.expiresAt) {
      info.el.classList.add("fading");
      setTimeout(() => {
        info.el.remove();
        STATE.flowLines.delete(key);
      }, 1000);
      info.expiresAt = Infinity;
    }
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
  const t = document.createElement("div");
  t.textContent = text;
  el.appendChild(t);
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
  lastAgentMsgEl = null; // 普通追加后流式重置
  return el;
}

function appendAgentChat(who, text) {
  // 同一位 agent 的连续 text 累加到一条
  const log = $("#chatLog");
  if (!lastAgentMsgEl || lastAgentMsgName !== who) {
    const el = document.createElement("div");
    el.className = "msg agent";
    const w = document.createElement("div");
    w.className = "who"; w.textContent = who;
    el.appendChild(w);
    const t = document.createElement("div");
    t.className = "body"; t.textContent = text;
    el.appendChild(t);
    log.appendChild(el);
    lastAgentMsgEl = t;
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
    const r = await fetch("/api/files");
    const files = await r.json();
    renderFiles(files);
  } catch (e) {}
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
    el.innerHTML = `
      <span class="file-name">${escapeHtml(f.name)}</span>
      <span>
        <span class="file-size">${formatSize(f.size)}</span>
        <a href="/api/file/${encodeURIComponent(f.id)}" download="${escapeHtml(f.name)}">下载</a>
      </span>
    `;
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
  // 保持最多 40 条，且自动滚到右侧
  while (strip.children.length > 40) strip.removeChild(strip.firstChild);
  strip.scrollLeft = strip.scrollWidth;
}

// ────────────────────────────────────────────────────────────
// 工具
// ────────────────────────────────────────────────────────────

function updateSessionPill(active, sid) {
  const pill = $("#sessionPill");
  if (active) {
    pill.classList.add("active");
    pill.textContent = sid ? `session · ${sid.slice(-6)}` : "运行中";
  } else {
    pill.classList.remove("active");
    pill.textContent = "未开始";
  }
}

function truncate(text, n) {
  if (!text) return "";
  text = String(text).replace(/\s+/g, " ");
  return text.length > n ? text.slice(0, n) + "…" : text;
}

function formatSize(n) {
  if (!n) return "—";
  if (n < 1024) return n + " B";
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
  return (n / 1024 / 1024).toFixed(1) + " MB";
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

init();
