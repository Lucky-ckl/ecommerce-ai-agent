/* ============================================================
   app.js
   动漫风客服界面逻辑
   ============================================================ */

const messagesEl = document.getElementById('messages');
const input = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const welcome = document.getElementById('welcome');
const newChatBtn = document.getElementById('newChatBtn');
const devPanel = document.getElementById('devPanel');
const devToggle = document.getElementById('devToggle');
const devClose = document.getElementById('devClose');

let busy = false;
let currentSessionId = null;


/* ============================================================
   看板娘：原创手绘 SVG
   不用 Live2D，是因为它 GPL 且模型版权不明，
   放在求职作品集里有风险；这个形象可商用、离线可用。
   ============================================================ */

function mascotSvg() {
  return `
  <svg viewBox="0 0 64 64" class="mascot" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="hairGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#7b6bff"/>
        <stop offset="100%" stop-color="#4b3fd6"/>
      </linearGradient>
      <linearGradient id="clothGrad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#ffffff"/>
        <stop offset="100%" stop-color="#ece7ff"/>
      </linearGradient>
    </defs>

    <!-- 双马尾 -->
    <path d="M12 28c-5 7-5 18 1 25 4-9 7-15 11-18z" fill="url(#hairGrad)"/>
    <path d="M52 28c5 7 5 18-1 25-4-9-7-15-11-18z" fill="url(#hairGrad)"/>

    <!-- 后发 -->
    <path d="M14 28c0-14 9-20 18-20s18 6 18 20c0 5-1 9-1 9H15s-1-4-1-9z" fill="url(#hairGrad)"/>

    <!-- 身体 / 制服 -->
    <path d="M22 56c0-9 4-14 10-14s10 5 10 14z" fill="url(#clothGrad)"/>
    <path d="M28 42l4 5 4-5-4-3z" fill="#ff9fbb"/>

    <!-- 脸 -->
    <ellipse cx="32" cy="33" rx="16" ry="15" fill="#ffe9e3"/>

    <!-- 刘海 -->
    <path d="M16 27c1-11 8-15 16-15s15 4 16 15c-4-7-9-9-16-9s-12 2-16 9z" fill="url(#hairGrad)"/>

    <!-- 耳机（客服） -->
    <circle cx="14" cy="33" r="5.5" fill="#fff" stroke="#d9d3ff" stroke-width="2"/>
    <circle cx="50" cy="33" r="5.5" fill="#fff" stroke="#d9d3ff" stroke-width="2"/>
    <path d="M14 27.5a16 16 0 0 1 36 0" stroke="#d9d3ff" stroke-width="2" fill="none"/>

    <!-- 眼睛（会眨） -->
    <g class="mascot-eyes">
      <ellipse cx="26" cy="35" rx="3.6" ry="4.4" fill="#4a3b8f"/>
      <ellipse cx="38" cy="35" rx="3.6" ry="4.4" fill="#4a3b8f"/>
      <circle cx="27.4" cy="33.4" r="1.3" fill="#fff"/>
      <circle cx="39.4" cy="33.4" r="1.3" fill="#fff"/>
    </g>

    <!-- 腮红 -->
    <ellipse cx="23" cy="40" rx="3" ry="1.8" fill="#ffb3c8" opacity="0.75"/>
    <ellipse cx="41" cy="40" rx="3" ry="1.8" fill="#ffb3c8" opacity="0.75"/>

    <!-- 嘴 -->
    <path d="M30 41q2 2.4 4 0" stroke="#d4708c" stroke-width="1.4" fill="none" stroke-linecap="round"/>
  </svg>`;
}


/* ============================================================
   基础渲染
   ============================================================ */

function scrollBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function aiAvatar() {
  const box = document.createElement('div');
  box.className = 'avatar ai';
  box.innerHTML = mascotSvg();
  return box;
}

function addMessage(role, content) {
  if (welcome) welcome.style.display = 'none';

  const row = document.createElement('div');
  row.className = `message-row ${role}`;

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = content;

  if (role === 'ai') {
    row.appendChild(aiAvatar());
    row.appendChild(bubble);
  } else {
    const avatar = document.createElement('div');
    avatar.className = 'avatar user';
    avatar.textContent = '你';
    row.appendChild(bubble);
    row.appendChild(avatar);
  }

  messagesEl.appendChild(row);
  scrollBottom();
}

function addOrderCard(order) {
  if (welcome) welcome.style.display = 'none';

  const row = document.createElement('div');
  row.className = 'message-row ai';

  const card = document.createElement('div');
  card.className = 'order-card';
  card.innerHTML = `
    <div class="order-card-title">📦 订单信息</div>
    <div class="order-card-row"><span>订单号</span><strong>${escapeHtml(order.order_id)}</strong></div>
    <div class="order-card-row"><span>商品</span><strong>${escapeHtml(order.product_name)}</strong></div>
    <div class="order-card-row"><span>状态</span><strong class="order-status">${escapeHtml(order.status)}</strong></div>
  `;

  row.appendChild(aiAvatar());
  row.appendChild(card);
  messagesEl.appendChild(row);
  scrollBottom();
}

function addConfirmationCard(result) {
  if (welcome) welcome.style.display = 'none';

  const row = document.createElement('div');
  row.className = 'message-row ai';

  const card = document.createElement('div');
  card.className = 'confirm-card';

  const action = result.action || {};
  const orderId = action.arguments?.order_id;

  card.innerHTML = `
    <div class="confirm-title">⚠️ 需要你确认</div>
    <div class="confirm-text">${escapeHtml(action.message || '该操作需要用户确认')}</div>
    ${orderId !== undefined ? `<div class="confirm-detail">即将取消订单 <strong>${escapeHtml(orderId)}</strong></div>` : ''}
    <div class="confirm-actions">
      <button class="confirm-btn" data-confirm="确认">确认操作</button>
      <button class="cancel-btn" data-confirm="取消">取消</button>
    </div>
  `;

  card.querySelectorAll('[data-confirm]').forEach((button) => {
    button.addEventListener('click', () => {
      sendMessage(button.dataset.confirm);
    });
  });

  row.appendChild(aiAvatar());
  row.appendChild(card);
  messagesEl.appendChild(row);
  scrollBottom();
}

function addErrorCard(message) {
  addMessage('ai', `⚠️ ${message}`);
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function renderAgentResult(result) {
  if (typeof result === 'string') {
    addMessage('ai', result);
    return;
  }

  if (!result || typeof result !== 'object') {
    addErrorCard('AI 返回了无法识别的结果。');
    return;
  }

  if (result.status === 'confirmation_required') {
    addConfirmationCard(result);
    return;
  }

  if (result.status === 'success') {
    const order = result.data?.order;
    if (order) {
      addOrderCard(order);
      return;
    }

    const cancelledOrderId = result.data?.order_id;
    if (cancelledOrderId !== undefined && result.data?.status) {
      addMessage('ai', `订单 ${cancelledOrderId} 已处理，当前状态：${result.data.status}`);
      return;
    }

    addMessage('ai', JSON.stringify(result.data ?? {}, null, 2));
    return;
  }

  if (result.status === 'error') {
    addErrorCard(result.error?.message || '请求处理失败。');
    return;
  }

  if (result.status === 'cancelled' || result.status === 'waiting_for_confirmation') {
    addMessage('ai', result.message || '操作已处理。');
    return;
  }

  addErrorCard(result.message || 'AI 返回了暂时无法展示的结果。');
}

function addTyping() {
  const row = document.createElement('div');
  row.className = 'message-row ai';
  row.id = 'typingRow';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.innerHTML = '<span class="typing"><i></i><i></i><i></i></span>';

  row.appendChild(aiAvatar());
  row.appendChild(bubble);
  messagesEl.appendChild(row);
  scrollBottom();
}

function removeTyping() {
  document.getElementById('typingRow')?.remove();
}


/* ============================================================
   会话管理
   历史会话存在 SQLite，新建会话只是换 session_id，不会删历史
   ============================================================ */

function setActiveSession(sessionId) {
  currentSessionId = sessionId;
  document.querySelectorAll('.session-item').forEach((el) => {
    el.classList.toggle('active', el.dataset.id === sessionId);
  });
}

async function loadSessions() {
  try {
    const response = await fetch('/api/sessions');
    const data = await response.json();

    const listEl = document.getElementById('sessionList');
    if (!listEl) return;

    listEl.innerHTML = '';

    (data.sessions || []).forEach((session) => {
      const item = document.createElement('div');
      item.className = 'session-item';
      item.dataset.id = session.session_id;
      if (session.session_id === currentSessionId) item.classList.add('active');

      const title = document.createElement('span');
      title.className = 'session-title';
      title.textContent = session.title || '新会话';

      const del = document.createElement('button');
      del.className = 'session-delete';
      del.textContent = '✕';
      del.title = '删除会话';
      del.addEventListener('click', async (event) => {
        event.stopPropagation();
        await removeSession(session.session_id);
      });

      item.appendChild(title);
      item.appendChild(del);
      item.addEventListener('click', () => openSession(session.session_id));

      listEl.appendChild(item);
    });
  } catch (error) {
    console.warn('读取会话列表失败：', error);
  }
}

async function createNewSession() {
  try {
    const response = await fetch('/api/sessions', { method: 'POST' });
    const data = await response.json();
    setActiveSession(data.session_id);
  } catch (error) {
    setActiveSession(null);
  }

  messagesEl.innerHTML = '';
  messagesEl.appendChild(welcome);
  welcome.style.display = '';
  input.focus();
  loadSessions();
}

async function openSession(sessionId) {
  try {
    const response = await fetch(`/api/sessions/${sessionId}/messages`);
    const data = await response.json();

    setActiveSession(sessionId);

    messagesEl.innerHTML = '';

    const messages = data.messages || [];

    if (messages.length === 0) {
      messagesEl.appendChild(welcome);
      welcome.style.display = '';
      return;
    }

    welcome.style.display = 'none';

    messages.forEach((message) => {
      const role = message.role === 'assistant' ? 'ai' : message.role;
      addMessage(role, message.content);
    });
  } catch (error) {
    console.error('打开会话失败：', error);
  }
}

async function removeSession(sessionId) {
  try {
    await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
    if (sessionId === currentSessionId) {
      createNewSession();
    } else {
      loadSessions();
    }
  } catch (error) {
    console.error('删除会话失败：', error);
  }
}


/* ============================================================
   发送消息
   ============================================================ */

async function sendMessage(text = input.value.trim()) {
  if (!text || busy) return;

  addMessage('user', text);
  input.value = '';
  input.style.height = 'auto';
  busy = true;
  sendBtn.disabled = true;
  addTyping();

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        session_id: currentSessionId
      })
    });

    const data = await response.json();
    removeTyping();

    if (!response.ok) {
      addErrorCard(data.detail || '服务器异常');
      return;
    }

    if (data.session_id) setActiveSession(data.session_id);

    renderAgentResult(data?.result);
    loadSessions();
  } catch (error) {
    removeTyping();
    addErrorCard('无法连接到 AI Agent，请确认 FastAPI 服务已经启动。');
    console.error(error);
  } finally {
    busy = false;
    sendBtn.disabled = false;
    input.focus();
  }
}


/* ============================================================
   事件绑定
   ============================================================ */

sendBtn.addEventListener('click', () => sendMessage());

input.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
});

input.addEventListener('input', () => {
  input.style.height = 'auto';
  input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
});

// 欢迎区和开发者面板里的快捷问题
document.querySelectorAll('[data-message]').forEach((button) => {
  button.addEventListener('click', () => sendMessage(button.dataset.message));
});

newChatBtn.addEventListener('click', createNewSession);

// 开发者面板：默认隐藏，点左下角按钮才展开
function toggleDevPanel() {
  devPanel.hidden = !devPanel.hidden;
}
devToggle.addEventListener('click', toggleDevPanel);
devClose.addEventListener('click', toggleDevPanel);

// 载入看板娘
document.getElementById('brandAvatar').innerHTML = mascotSvg();
document.getElementById('welcomeMascot').innerHTML = mascotSvg();

// 读取历史会话
(async function initSessions() {
  await loadSessions();
})();

// 同步后端真实模型名称
(async function loadAgentStatus() {
  try {
    const response = await fetch('/health');
    const data = await response.json();
    const modelName = document.getElementById('modelName');
    if (modelName && data.model) {
      modelName.textContent = data.model;
    }
  } catch (error) {
    console.warn('无法读取 Agent 状态：', error);
  }
})();
