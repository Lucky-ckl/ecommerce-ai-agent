const messagesEl = document.getElementById('messages');
const input = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const welcome = document.getElementById('welcome');
const newChatBtn = document.getElementById('newChatBtn');

let busy = false;
let currentSessionId = null;

function scrollBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function addMessage(role, content) {
  if (welcome) welcome.style.display = 'none';

  const row = document.createElement('div');
  row.className = `message-row ${role}`;

  const avatar = document.createElement('div');
  avatar.className = `avatar ${role === 'ai' ? 'ai' : 'user'}`;
  avatar.textContent = role === 'ai' ? '🤖' : '你';

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = content;

  if (role === 'ai') {
    row.appendChild(avatar);
    row.appendChild(bubble);
  } else {
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

  const avatar = document.createElement('div');
  avatar.className = 'avatar ai';
  avatar.textContent = '🤖';

  const card = document.createElement('div');
  card.className = 'order-card';
  card.innerHTML = `
    <div class="order-card-title">📦 订单信息</div>
    <div class="order-card-row"><span>订单号</span><strong>${escapeHtml(order.order_id)}</strong></div>
    <div class="order-card-row"><span>商品</span><strong>${escapeHtml(order.product_name)}</strong></div>
    <div class="order-card-row"><span>状态</span><strong class="order-status">${escapeHtml(order.status)}</strong></div>
  `;

  row.appendChild(avatar);
  row.appendChild(card);
  messagesEl.appendChild(row);
  scrollBottom();
}

function addConfirmationCard(result) {
  if (welcome) welcome.style.display = 'none';

  const row = document.createElement('div');
  row.className = 'message-row ai';

  const avatar = document.createElement('div');
  avatar.className = 'avatar ai';
  avatar.textContent = '🤖';

  const card = document.createElement('div');
  card.className = 'confirm-card';

  const action = result.action || {};
  const orderId = action.arguments?.order_id;

  card.innerHTML = `
    <div class="confirm-title">⚠️ 需要确认</div>
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

  row.appendChild(avatar);
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
  // 1. 正常回答：agent() 最终返回字符串
  if (typeof result === 'string') {
    addMessage('ai', result);
    return;
  }

  if (!result || typeof result !== 'object') {
    addErrorCard('AI 返回了无法识别的结果。');
    return;
  }

  // 2. 危险 Tool：后端要求下一轮用户回复“确认/取消”
  if (result.status === 'confirmation_required') {
    addConfirmationCard(result);
    return;
  }

  // 3. 用户确认后的执行结果 / 普通 Tool 结果
  if (result.status === 'success') {
    const order = result.data?.order;
    if (order) {
      addOrderCard(order);
      return;
    }

    const cancelledOrderId = result.data?.order_id;
    if (cancelledOrderId !== undefined && result.data?.status) {
      addMessage(
        'ai',
        `订单 ${cancelledOrderId} 已处理，当前状态：${result.data.status}`
      );
      return;
    }

    addMessage('ai', JSON.stringify(result.data ?? {}, null, 2));
    return;
  }

  // 4. 后端业务错误 / 系统错误
  if (result.status === 'error') {
    addErrorCard(result.error?.message || '请求处理失败。');
    return;
  }

  // 5. 用户取消或仍在等待确认
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
  row.innerHTML = `
    <div class="avatar ai">🤖</div>
    <div class="bubble"><span class="typing"><i></i><i></i><i></i></span></div>
  `;
  messagesEl.appendChild(row);
  scrollBottom();
}

function removeTyping() {
  document.getElementById('typingRow')?.remove();
}

// ============================================================
// 会话管理
// 历史会话存在 SQLite 里，新建会话只是换一个 session_id，
// 不会删除旧会话。
// ============================================================

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
      if (session.session_id === currentSessionId) {
        item.classList.add('active');
      }

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
      // 后端存的是 user / assistant，前端用 user / ai
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

    if (data.session_id) {
      setActiveSession(data.session_id);
    }

    // 后端返回：{ result: agent(...), session_id }
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

document.querySelectorAll('[data-message]').forEach((button) => {
  button.addEventListener('click', () => sendMessage(button.dataset.message));
});

// 新建会话：只开一个新会话，不再清空历史
newChatBtn.addEventListener('click', createNewSession);

// 页面加载时读取历史会话列表
(async function initSessions() {
  await loadSessions();
})();

// 页面加载后从后端健康检查接口同步实际模型名称。
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
