const API_BASE = process.env.NODE_ENV === 'production' 
  ? 'https://sql-bot-teal.vercel.app/' 
  : 'http://localhost:8000'

function getAuthHeaders() {
  const token = localStorage.getItem('token')
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  }
}

export async function addUser(username, password, role = 'user', schema = null, admin_schema = null) {
  const response = await fetch(`${API_BASE}/api/admin/add-user`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ username, password, role, schema, admin_schema })
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to add user')
  }
  
  const data = await response.json()
  return { success: true, id: data.id }
}

export async function removeUser(username) {
  const response = await fetch(`${API_BASE}/api/admin/remove-user`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ username })
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to remove user')
  }
  
  return { success: true }
}

export async function getUsers() {
  const response = await fetch(`${API_BASE}/api/admin/users`, {
    method: 'GET',
    headers: getAuthHeaders()
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to get users')
  }
  
  const data = await response.json()
  return data.users
}

export async function updateUser(userId, userData) {
  const response = await fetch(`${API_BASE}/api/admin/users/${userId}`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    body: JSON.stringify(userData)
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to update user')
  }
  
  const data = await response.json()
  return data
}

export async function analyzeColumns() {
  const response = await fetch(`${API_BASE}/api/admin/analyze-columns`, {
    method: 'GET',
    headers: getAuthHeaders()
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to analyze columns')
  }
  
  const data = await response.json()
  return data.analysis
}


