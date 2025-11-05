import React, { useState, useEffect } from 'react'
import Sidebar from '../components/Sidebar.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { Navigate } from 'react-router-dom'
import { addUser, removeUser, analyzeColumns, getUsers, updateUser } from '../api/admin.js'
import { getChatHistory } from '../api/chat.js'
import Modal from '../components/Modal.jsx'

export default function AdminDashboard() {
  const { user, loading } = useAuth()
  const [users, setUsers] = useState([])
  const [columnAnalysis, setColumnAnalysis] = useState(null)
  const [allChatHistory, setAllChatHistory] = useState([])
  const [addUserOpen, setAddUserOpen] = useState(false)
  const [removeUserOpen, setRemoveUserOpen] = useState(false)
  const [showAnalysis, setShowAnalysis] = useState(false)
  const [showChatHistory, setShowChatHistory] = useState(false)
  const [newUser, setNewUser] = useState({ username: '', password: '', role: 'user', schema: '', admin_schema: '' })
  const [editUser, setEditUser] = useState(null)
  const [removeUsername, setRemoveUsername] = useState('')
  const [error, setError] = useState('')
  const [loadingState, setLoadingState] = useState(false)

  if (loading) return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  if (!user) return <Navigate to="/login" replace />
  if (user.role !== 'admin') return <Navigate to="/" replace />

  const handleAnalyze = async () => {
    await loadColumnAnalysis()
    setShowAnalysis(true)
  }

  const handleAddUser = async () => {
    setLoadingState(true)
    setError('')
    try {
      // Validate required fields
      if (!newUser.schema || newUser.schema.trim() === '') {
        setError('Schema is required for user creation')
        setLoadingState(false)
        return
      }
      
      await addUser(newUser.username, newUser.password, newUser.role, newUser.schema, newUser.admin_schema || null)
      setAddUserOpen(false)
      setNewUser({ username: '', password: '', role: 'user', schema: '', admin_schema: '' })
      
      // Refresh the users list
      await loadUsers()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingState(false)
    }
  }

  const handleRemoveUser = async () => {
    setLoadingState(true)
    setError('')
    try {
      await removeUser(removeUsername)
      setRemoveUserOpen(false)
      setRemoveUsername('')
      loadUsers() // Refresh users list
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingState(false)
    }
  }

  const handleEditUser = async () => {
    setLoadingState(true)
    setError('')
    try {
      if (!editUser) return
      
      // Update user via API
      await updateUser(editUser.id, {
        username: editUser.username,
        password: editUser.password,
        role: editUser.role,
        schema: editUser.schema,
        admin_schema: editUser.admin_schema
      })
      
      setEditUser(null)
      await loadUsers() // Refresh users list
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingState(false)
    }
  }

  const loadUsers = async () => {
    try {
      const usersList = await getUsers()
      setUsers(usersList)
    } catch (err) {
      console.error('Failed to load users:', err)
    }
  }

  const loadColumnAnalysis = async () => {
    setLoadingState(true)
    try {
      const analysis = await analyzeColumns()
      setColumnAnalysis(analysis)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingState(false)
    }
  }

  const loadAllChatHistory = async () => {
    try {
      const history = await getChatHistory()
      setAllChatHistory(history)
    } catch (err) {
      console.error('Failed to load chat history:', err)
    }
  }

  useEffect(() => {
    loadUsers()
    loadAllChatHistory()
    
    // Auto-refresh users list every 30 seconds
    const interval = setInterval(() => {
      loadUsers()
    }, 30000)
    
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen flex bg-navy-900">
      <Sidebar />
      <main className="flex-1 flex flex-col md:ml-[309px]">
        {/* Header */}
        <div className="bg-secondaryGray-400 border-b border-secondaryGray-600 px-6 py-4">
          <div className="max-w-7xl mx-auto flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-brand flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-secondaryGray-900">Admin Dashboard</h1>
                <p className="text-sm text-secondaryGray-800">Manage users and database analytics</p>
              </div>
            </div>
            <button 
              onClick={() => setShowChatHistory(!showChatHistory)}
              className={`px-5 py-2.5 rounded-button font-semibold text-sm transition-all flex items-center gap-2 ${
                showChatHistory 
                  ? 'bg-gradient-brand text-white shadow-lg' 
                  : 'bg-secondaryGray-300 text-secondaryGray-900 hover:bg-secondaryGray-500'
              }`}
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z" />
                <path d="M15 7v2a4 4 0 01-4 4H9.828l-1.766 1.767c.28.149.599.233.938.233h2l3 3v-3h2a2 2 0 002-2V9a2 2 0 00-2-2h-1z" />
              </svg>
              {showChatHistory ? 'Hide Chat History' : 'Show Chat History'}
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="max-w-7xl mx-auto mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-card text-sm flex items-center gap-3">
              <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span>{error}</span>
              <button onClick={() => setError('')} className="ml-auto text-red-700 hover:text-red-900">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          )}

          {showChatHistory ? (
            /* Chat History Display */
            <div className="max-w-5xl mx-auto space-y-4">
              {allChatHistory.length === 0 ? (
                <div className="bg-secondaryGray-100 rounded-card shadow-card p-12 text-center">
                  <div className="w-16 h-16 rounded-full bg-secondaryGray-300 mx-auto mb-4 flex items-center justify-center">
                    <svg className="w-8 h-8 text-secondaryGray-800" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                    </svg>
                  </div>
                  <p className="text-lg font-semibold text-secondaryGray-900 mb-1">No chat history available</p>
                  <p className="text-sm text-secondaryGray-800">Users haven't started any conversations yet</p>
                </div>
              ) : (
                allChatHistory.map((msg, index) => (
                  <div key={index} className={`bg-secondaryGray-100 rounded-card shadow-card p-5 ${
                    msg.role === 'user' ? 'ml-8' : 'mr-8'
                  }`}>
                    <div className="flex gap-4">
                      {msg.role === 'user' ? (
                        <div className="w-10 h-10 rounded-full bg-brand-500/20 flex items-center justify-center text-brand-500 font-bold flex-shrink-0">
                          U
                        </div>
                      ) : (
                        <div className="w-10 h-10 rounded-xl bg-gradient-brand flex items-center justify-center flex-shrink-0">
                          <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z" />
                            <path d="M15 7v2a4 4 0 01-4 4H9.828l-1.766 1.767c.28.149.599.233.938.233h2l3 3v-3h2a2 2 0 002-2V9a2 2 0 00-2-2h-1z" />
                          </svg>
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-semibold text-secondaryGray-900">{msg.username}</span>
                          <span className="text-xs text-secondaryGray-700">•</span>
                          <span className="text-xs text-secondaryGray-700">{new Date(msg.created_at).toLocaleString()}</span>
                        </div>
                        <div className="text-sm text-secondaryGray-900 whitespace-pre-wrap leading-relaxed">{msg.content}</div>
                        {msg.sql_generated && (
                          <div className="mt-3 bg-secondaryGray-200 rounded-button p-3 border border-secondaryGray-600">
                            <div className="text-xs font-semibold text-secondaryGray-800 mb-2 flex items-center gap-1">
                              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                              </svg>
                              Generated SQL
                            </div>
                            <code className="text-xs text-secondaryGray-900 font-mono block overflow-x-auto">{msg.sql_generated}</code>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : (
            /* Admin Controls */
            <div className="max-w-7xl mx-auto space-y-6">
              {/* User Management */}
              <div className="bg-secondaryGray-100 rounded-card shadow-card p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-brand flex items-center justify-center">
                      <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-secondaryGray-900">User Management</h3>
                      <p className="text-sm text-secondaryGray-800">{users.length} total users</p>
                    </div>
                  </div>
                  <button 
                    className="btn-primary flex items-center gap-2" 
                    onClick={() => setAddUserOpen(true)}
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" />
                    </svg>
                    Add User
                  </button>
                </div>
                
                {/* Users Grid */}
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 max-h-[600px] overflow-y-auto pr-2">
                  {users.map((u) => (
                    <div key={u.id} className="bg-secondaryGray-200 rounded-button p-4 border border-secondaryGray-600 hover:border-brand-500 transition-colors">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-xl bg-gradient-brand flex items-center justify-center text-white font-bold text-lg">
                            {u.username.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <div className="font-semibold text-secondaryGray-900">{u.username}</div>
                            <div className={`text-xs font-medium px-2 py-0.5 rounded-full inline-block ${
                              u.role === 'admin' 
                                ? 'bg-brand-500/20 text-brand-500' 
                                : 'bg-secondaryGray-600 text-secondaryGray-900'
                            }`}>
                              {u.role}
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      <div className="space-y-2 mb-4">
                        <div className="flex items-center gap-2 text-xs">
                          <svg className="w-4 h-4 text-secondaryGray-700" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M4 4a2 2 0 012-2h8a2 2 0 012 2v12a1 1 0 110 2h-3a1 1 0 01-1-1v-2a1 1 0 00-1-1H9a1 1 0 00-1 1v2a1 1 0 01-1 1H4a1 1 0 110-2V4zm3 1h2v2H7V5zm2 4H7v2h2V9zm2-4h2v2h-2V5zm2 4h-2v2h2V9z" clipRule="evenodd" />
                          </svg>
                          <span className="text-secondaryGray-800">
                            {u.schema ? 'Has schema' : 'No schema'}
                          </span>
                        </div>
                        {u.admin_schema && (
                          <div className="flex items-center gap-2 text-xs">
                            <svg className="w-4 h-4 text-brand-500" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                            <span className="text-brand-500 font-medium">Admin schema ({u.admin_schema.length} chars)</span>
                          </div>
                        )}
                        <div className="flex items-center gap-2 text-xs text-secondaryGray-700">
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                          </svg>
                          <span>{new Date(u.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      
                      <div className="flex gap-2">
                        <button
                          onClick={() => setEditUser(u)}
                          className="flex-1 px-3 py-2 rounded-button bg-gradient-brand text-white text-sm font-semibold hover:shadow-lg transition-all flex items-center justify-center gap-1"
                        >
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                          </svg>
                          Edit
                        </button>
                        <button
                          onClick={() => {
                            setRemoveUsername(u.username)
                            setRemoveUserOpen(true)
                          }}
                          className="px-3 py-2 rounded-button bg-red-100 text-red-600 hover:bg-red-200 text-sm font-semibold transition-colors flex items-center justify-center"
                        >
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Database Analysis */}
              <div className="bg-secondaryGray-100 rounded-card shadow-card p-6">
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-teal flex items-center justify-center">
                      <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M3 12v3c0 1.657 3.134 3 7 3s7-1.343 7-3v-3c0 1.657-3.134 3-7 3s-7-1.343-7-3z" />
                        <path d="M3 7v3c0 1.657 3.134 3 7 3s7-1.343 7-3V7c0 1.657-3.134 3-7 3S3 8.657 3 7z" />
                        <path d="M17 5c0 1.657-3.134 3-7 3S3 6.657 3 5s3.134-3 7-3 7 1.343 7 3z" />
                      </svg>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-secondaryGray-900">Database Analysis</h3>
                      <p className="text-sm text-secondaryGray-800">Analyze column and table usage</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setShowAnalysis(!showAnalysis)}
                    className="px-4 py-2 rounded-button bg-secondaryGray-300 text-secondaryGray-900 hover:bg-secondaryGray-500 text-sm font-semibold transition-colors flex items-center gap-2"
                  >
                    <svg className={`w-4 h-4 transition-transform ${showAnalysis ? 'rotate-180' : ''}`} fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                    {showAnalysis ? 'Hide' : 'Show'} Analysis
                  </button>
                </div>
                
                {showAnalysis && (
                  <div className="space-y-4">
                    <button 
                      className="btn-primary w-full md:w-auto flex items-center gap-2" 
                      onClick={handleAnalyze}
                      disabled={loadingState}
                    >
                      <svg className={`w-4 h-4 ${loadingState ? 'animate-spin' : ''}`} fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
                      </svg>
                      {loadingState ? 'Analyzing...' : 'Analyze Database Usage'}
                    </button>
                    
                    {columnAnalysis && (
                      <div className="space-y-4">
                        {columnAnalysis.useless_columns && columnAnalysis.useless_columns.length > 0 && (
                          <div className="bg-secondaryGray-200 rounded-button p-4 border border-secondaryGray-600">
                            <div className="flex items-center gap-2 mb-3">
                              <div className="w-8 h-8 rounded-lg bg-red-100 flex items-center justify-center">
                                <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                </svg>
                              </div>
                              <h5 className="text-sm font-bold text-secondaryGray-900">Useless Columns ({columnAnalysis.useless_columns.length})</h5>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {columnAnalysis.useless_columns.map((column, i) => (
                                <span key={i} className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium">
                                  {column}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {columnAnalysis.useless_tables && columnAnalysis.useless_tables.length > 0 && (
                          <div className="bg-secondaryGray-200 rounded-button p-4 border border-secondaryGray-600">
                            <div className="flex items-center gap-2 mb-3">
                              <div className="w-8 h-8 rounded-lg bg-red-100 flex items-center justify-center">
                                <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                                </svg>
                              </div>
                              <h5 className="text-sm font-bold text-secondaryGray-900">Useless Tables ({columnAnalysis.useless_tables.length})</h5>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {columnAnalysis.useless_tables.map((table, i) => (
                                <span key={i} className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium">
                                  {table}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {columnAnalysis.useful_tables && columnAnalysis.useful_tables.length > 0 && (
                          <div className="bg-secondaryGray-200 rounded-button p-4 border border-secondaryGray-600">
                            <div className="flex items-center gap-2 mb-3">
                              <div className="w-8 h-8 rounded-lg bg-green-100 flex items-center justify-center">
                                <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                </svg>
                              </div>
                              <h5 className="text-sm font-bold text-secondaryGray-900">Useful Tables ({columnAnalysis.useful_tables.length})</h5>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {columnAnalysis.useful_tables.map((table, i) => (
                                <span key={i} className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                                  {table}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {columnAnalysis.summary && (
                          <div className="bg-secondaryGray-200 rounded-button p-4 border border-secondaryGray-600">
                            <h5 className="text-sm font-bold text-secondaryGray-900 mb-2 flex items-center gap-2">
                              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                              </svg>
                              Summary
                            </h5>
                            <div className="text-sm text-secondaryGray-900 whitespace-pre-wrap leading-relaxed">
                              {columnAnalysis.summary}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>

      <Modal
        open={addUserOpen}
        title="Add New User"
        onClose={() => setAddUserOpen(false)}
        actions={
          <div className="flex gap-3">
            <button 
              className="px-4 py-2 rounded-button bg-secondaryGray-300 text-secondaryGray-900 hover:bg-secondaryGray-500 font-semibold transition-colors" 
              onClick={() => setAddUserOpen(false)}
            >
              Cancel
            </button>
            <button 
              className="btn-primary flex items-center gap-2" 
              onClick={handleAddUser}
              disabled={loadingState || !newUser.schema || newUser.schema.trim() === ''}
            >
              {loadingState ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  Adding...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 5a1 1 0 011 1v3h3a1 1 0 110 2h-3v3a1 1 0 11-2 0v-3H6a1 1 0 110-2h3V6a1 1 0 011-1z" clipRule="evenodd" />
                  </svg>
                  Add User
                </>
              )}
            </button>
          </div>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-secondaryGray-900 mb-2">Username</label>
            <input 
              className="input" 
              value={newUser.username} 
              onChange={(e) => setNewUser({...newUser, username: e.target.value})}
              placeholder="jane.doe"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-secondaryGray-900 mb-2">Password</label>
            <input 
              className="input" 
              type="password" 
              value={newUser.password} 
              onChange={(e) => setNewUser({...newUser, password: e.target.value})}
              placeholder="••••••••"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-secondaryGray-900 mb-2">Role</label>
            <select 
              className="input" 
              value={newUser.role} 
              onChange={(e) => setNewUser({...newUser, role: e.target.value})}
            >
              <option value="user">User</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-semibold text-secondaryGray-900 mb-2">
              Schema <span className="text-brand-500">*</span>
            </label>
            <textarea 
              className="input min-h-[100px] font-mono text-sm" 
              value={newUser.schema} 
              onChange={(e) => setNewUser({...newUser, schema: e.target.value})}
              placeholder="CREATE TABLE users (&#10;  id SERIAL PRIMARY KEY,&#10;  name VARCHAR(100)&#10;);"
              required
            />
            <p className="text-xs text-secondaryGray-800 mt-2 flex items-center gap-1">
              <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
              Schema is required - paste the DDL for the tables this user can query
            </p>
          </div>
          {newUser.role === 'admin' && (
            <div>
              <label className="block text-sm font-semibold text-secondaryGray-900 mb-2">Admin Schema (optional)</label>
              <textarea 
                className="input min-h-[100px] font-mono text-sm" 
                value={newUser.admin_schema} 
                onChange={(e) => setNewUser({...newUser, admin_schema: e.target.value})}
                placeholder="Full company database schema for admin access"
              />
              <p className="text-xs text-secondaryGray-800 mt-2">Optional extended schema for admin privileges</p>
            </div>
          )}
        </div>
      </Modal>

      <Modal
        open={removeUserOpen}
        title="Remove User"
        onClose={() => setRemoveUserOpen(false)}
        actions={
          <div className="flex gap-3">
            <button 
              className="px-4 py-2 rounded-button bg-secondaryGray-300 text-secondaryGray-900 hover:bg-secondaryGray-500 font-semibold transition-colors" 
              onClick={() => setRemoveUserOpen(false)}
            >
              Cancel
            </button>
            <button 
              className="px-4 py-2 rounded-button bg-red-600 hover:bg-red-700 text-white font-semibold transition-colors flex items-center gap-2" 
              onClick={handleRemoveUser}
              disabled={loadingState}
            >
              {loadingState ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  Removing...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  Remove User
                </>
              )}
            </button>
          </div>
        }
      >
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-button text-sm mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
          <div>
            <p className="font-semibold">Warning: This action cannot be undone</p>
            <p className="text-xs mt-1">All user data and chat history will be permanently deleted</p>
          </div>
        </div>
        <div>
          <label className="block text-sm font-semibold text-secondaryGray-900 mb-2">Username to remove</label>
          <input 
            className="input" 
            value={removeUsername} 
            onChange={(e) => setRemoveUsername(e.target.value)}
            placeholder="jane.doe"
          />
        </div>
      </Modal>

      {/* Edit User Modal */}
      <Modal
        open={editUser !== null}
        title="Edit User"
        onClose={() => setEditUser(null)}
        actions={
          <div className="flex gap-3">
            <button 
              className="px-4 py-2 rounded-button bg-secondaryGray-300 text-secondaryGray-900 hover:bg-secondaryGray-500 font-semibold transition-colors" 
              onClick={() => setEditUser(null)}
            >
              Cancel
            </button>
            <button 
              className="btn-primary flex items-center gap-2" 
              onClick={handleEditUser}
              disabled={loadingState}
            >
              {loadingState ? (
                <>
                  <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  Saving...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Save Changes
                </>
              )}
            </button>
          </div>
        }
      >
        {editUser && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-secondaryGray-900 mb-2">Username</label>
              <input 
                className="input" 
                value={editUser.username} 
                onChange={(e) => setEditUser({...editUser, username: e.target.value})}
                placeholder="jane.doe"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-secondaryGray-900 mb-2">Password (leave blank to keep current)</label>
              <input 
                className="input" 
                type="password" 
                value={editUser.password || ''} 
                onChange={(e) => setEditUser({...editUser, password: e.target.value})}
                placeholder="••••••••"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-secondaryGray-900 mb-2">Role</label>
              <select 
                className="input" 
                value={editUser.role} 
                onChange={(e) => setEditUser({...editUser, role: e.target.value})}
              >
                <option value="user">User</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-secondaryGray-900 mb-2">Schema</label>
              <textarea 
                className="input min-h-[120px] font-mono text-sm" 
                value={editUser.schema || ''} 
                onChange={(e) => setEditUser({...editUser, schema: e.target.value})}
                placeholder="CREATE TABLE users (...)"
              />
            </div>
            {editUser.role === 'admin' && (
              <div>
                <label className="block text-sm font-semibold text-secondaryGray-900 mb-2">Admin Schema</label>
                <textarea 
                  className="input min-h-[120px] font-mono text-sm" 
                  value={editUser.admin_schema || ''} 
                  onChange={(e) => setEditUser({...editUser, admin_schema: e.target.value})}
                  placeholder="Complete database schema for admin access"
                />
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}


