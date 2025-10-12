const API_BASE = process.env.NODE_ENV === 'production' 
  ? 'https://sql-bot-teal.vercel.app' 
  : 'http://localhost:8000'

function getAuthHeaders() {
  const token = localStorage.getItem('token')
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  }
}

export async function sendPrompt(prompt, schema = null) {
  const response = await fetch(`${API_BASE}/api/generate-sql`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ prompt, schema })
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to generate SQL')
  }
  
  const data = await response.json()
  return { sql: data.sql, explain: data.explain }
}

export async function runQuery(sql, limit = null) {
  const response = await fetch(`${API_BASE}/api/run-query`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ sql, limit })
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to run query')
  }
  
  const data = await response.json()
  return { success: true, message: `Fetched ${data.rows.length} rows successfully`, rows: data.rows }
}

export async function retryQuery(prompt, feedback) {
  return sendPrompt(prompt, feedback)
}

export async function getChatHistory() {
  const response = await fetch(`${API_BASE}/api/chat-history`, {
    method: 'GET',
    headers: getAuthHeaders()
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to get chat history')
  }
  
  const data = await response.json()
  return data.messages
}

export async function saveChatSession(sessionName, messages) {
  const response = await fetch(`${API_BASE}/api/save-session`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      session_name: sessionName,
      messages: messages
    })
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to save chat session')
  }
  
  const data = await response.json()
  return data.session_id
}

export async function getChatSessions() {
  const response = await fetch(`${API_BASE}/api/chat-sessions`, {
    method: 'GET',
    headers: getAuthHeaders()
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to get chat sessions')
  }
  
  const data = await response.json()
  return data.sessions
}

export async function getChatSession(sessionId) {
  const response = await fetch(`${API_BASE}/api/chat-session/${sessionId}`, {
    method: 'GET',
    headers: getAuthHeaders()
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to get chat session')
  }
  
  const data = await response.json()
  return data.session
}

export async function deleteChatSession(sessionId) {
  const response = await fetch(`${API_BASE}/api/chat-session/${sessionId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to delete chat session')
  }
  
  const data = await response.json()
  return data
}


