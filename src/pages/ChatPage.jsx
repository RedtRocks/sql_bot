import React, { useMemo, useState, useEffect } from 'react'
import Sidebar from '../components/Sidebar.jsx'
import ChatMessage from '../components/ChatMessage.jsx'
import ChatInput from '../components/ChatInput.jsx'
import AcceptRetryButtons from '../components/AcceptRetryButtons.jsx'
import ErrorBoundary from '../components/ErrorBoundary.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { Navigate, Link } from 'react-router-dom'
import Modal from '../components/Modal.jsx'
import { sendPrompt, runQuery, retryQuery, saveChatSession } from '../api/chat.js'

export default function ChatPage() {
  const { user, loading } = useAuth()
  const [messages, setMessages] = useState([
    { id: 1, role: 'assistant', content: 'Hello! How may I help you with SQL queries today?' }
  ])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [acceptOpen, setAcceptOpen] = useState(false)
  const [acceptRows, setAcceptRows] = useState('10')
  const [retryOpen, setRetryOpen] = useState(false)
  const [retryFeedback, setRetryFeedback] = useState('')
  const [currentSql, setCurrentSql] = useState('')
  const [runQueryResult, setRunQueryResult] = useState({ rows: [] })
  const [saveSessionOpen, setSaveSessionOpen] = useState(false)
  const [sessionName, setSessionName] = useState('')
  const lastUserPrompt = useMemo(() => {
    const last = [...messages].reverse().find(m => m.role === 'user')
    return last?.content || ''
  }, [messages])

  // Handle loading chat sessions from sidebar
  useEffect(() => {
    const handleLoadSession = (event) => {
      const { session } = event.detail
      if (session && session.messages) {
        setMessages(session.messages)
        setError('')
      }
    }

    window.addEventListener('loadChatSession', handleLoadSession)
    return () => window.removeEventListener('loadChatSession', handleLoadSession)
  }, [])

  const handleSaveSession = async () => {
    if (!sessionName.trim()) return
    
    try {
      await saveChatSession(sessionName.trim(), messages)
      setSaveSessionOpen(false)
      setSessionName('')
      // Refresh sidebar sessions
      window.dispatchEvent(new CustomEvent('refreshSessions'))
    } catch (error) {
      setError(error.message)
    }
  }

  if (loading) return <div className="min-h-screen flex items-center justify-center bg-navy-900">Loading...</div>
  if (!user) return <Navigate to="/login" replace />

  const handleSend = async (text) => {
    const userMsg = { id: Date.now(), role: 'user', content: text }
    setMessages(prev => [...prev, userMsg])
    setIsLoading(true)
    setError('')
    try {
      // For admin users, don't send schema - let backend use admin_schema
      const schemaToSend = user.role === 'admin' ? null : user.schema
      const res = await sendPrompt(text, schemaToSend)
      setCurrentSql(res.sql)
      
      // Get preview by running the query with limit 5
      let previewRows = []
      try {
        const previewRes = await runQuery(res.sql, 5)
        previewRows = Array.isArray(previewRes?.rows) ? previewRes.rows.slice(0, 5) : []
      } catch (previewError) {
        console.warn('Preview query failed:', previewError)
        previewRows = []
      }
      
      const aiMsg = { 
        id: Date.now() + 1, 
        role: 'assistant', 
        content: 'Here is a proposed SQL and preview:', 
        sql: res.sql, 
        previewRows: previewRows
      }
      setMessages(prev => [...prev, aiMsg])
    } catch (err) {
      setError(err.message)
      // Handle specific error messages
      let errorContent = `Error: ${err.message}`
      if (err.message.includes("couldn't identify anything in your database")) {
        errorContent = "I couldn't identify anything in your database from that query - please ask about a specific table or column."
      } else if (err.message.includes("not a SELECT")) {
        errorContent = "For safety, only SELECT queries are allowed."
      } else if (err.message.includes("not reference your database schema")) {
        errorContent = "I couldn't identify anything in your database from that query - please ask about a specific table or column."
      } else if (err.message.includes("contact your administrator to upload a database schema")) {
        errorContent = "Please contact your administrator to upload a database schema before using the chat. You need a schema to generate SQL queries."
      }
      
      setMessages(prev => [...prev, { id: Date.now() + 1, role: 'assistant', content: errorContent }])
    } finally {
      setIsLoading(false)
    }
  }

  const openAccept = () => setAcceptOpen(true)
  const doAccept = async () => {
    setIsLoading(true)
    setError('')
    try {
      const result = await runQuery(currentSql, Number(acceptRows) || 0)
      setRunQueryResult(result)
      const message = `Query executed successfully! Fetched ${result.rows.length} rows.`
      setMessages(prev => [...prev, { id: Date.now(), role: 'assistant', content: message, sql: currentSql, rows: result.rows }])
    } catch (err) {
      setError(err.message)
      
      // Handle specific error cases
      if (err.message.includes('too many rows') || err.message.includes('query too large')) {
        const retryRows = prompt('Query returned too many rows. Please specify a smaller number of rows (e.g., 100, 500, 1000):')
        if (retryRows && !isNaN(parseInt(retryRows))) {
          try {
            const retryResult = await runQuery(currentSql, parseInt(retryRows))
            setRunQueryResult(retryResult)
            
            const retryMsg = {
              id: Date.now() + 1,
              role: 'assistant',
              content: `Query executed successfully with reduced rows! Fetched ${retryResult.rows.length} rows.`,
              sql: currentSql,
              rows: retryResult.rows
            }
            setMessages(prev => [...prev, retryMsg])
          } catch (retryErr) {
            setError(`Retry failed: ${retryErr.message}`)
            setMessages(prev => [...prev, { id: Date.now() + 2, role: 'assistant', content: `Retry Error: ${retryErr.message}` }])
          }
        }
      } else {
        setMessages(prev => [...prev, { id: Date.now(), role: 'assistant', content: `Error: ${err.message}` }])
      }
    } finally {
      setIsLoading(false)
      setAcceptOpen(false)
    }
  }

  const openRetry = () => setRetryOpen(true)
  const doRetry = async () => {
    setIsLoading(true)
    setError('')
    try {
      const res = await retryQuery(lastUserPrompt, retryFeedback)
      setCurrentSql(res.sql)
      const aiMsg = { id: Date.now(), role: 'assistant', content: 'Updated SQL after feedback:', sql: res.sql, previewRows: res.preview }
      setMessages(prev => [...prev, aiMsg])
    } catch (err) {
      setError(err.message)
      setMessages(prev => [...prev, { id: Date.now(), role: 'assistant', content: `Error: ${err.message}` }])
    } finally {
      setIsLoading(false)
      setRetryOpen(false)
      setRetryFeedback('')
    }
  }

  return (
    <ErrorBoundary>
      <div className="min-h-screen flex bg-navy-900">
        <Sidebar />

        <main className="flex-1 flex flex-col md:ml-[309px]">
          {/* Header Navbar */}
          <div className="bg-secondaryGray-400 border-b border-secondaryGray-500 px-6 py-4">
            <div className="max-w-4xl mx-auto flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-brand flex items-center justify-center shadow-sm">
                  <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.476.859h4.002z" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-lg font-bold text-secondaryGray-900">AI SQL Chat</h1>
                  <p className="text-xs text-secondaryGray-800">Powered by OpenAI GPT-4</p>
                </div>
              </div>
              
              {user?.role === 'admin' && (
                <Link 
                  to="/admin" 
                  className="px-4 py-2 bg-secondaryGray-300 hover:bg-secondaryGray-200 border border-secondaryGray-500 rounded-button text-sm font-medium text-secondaryGray-900 transition-all duration-200"
                >
                  Admin Panel
                </Link>
              )}
            </div>
          </div>
        
          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto">
            {messages.map(m => {
              try {
                return (
                  <div key={m.id}>
                    <ChatMessage role={m.role} content={m.content} sql={m.sql} previewRows={m.previewRows} />
                    {m.role === 'assistant' && m.sql && (
                      <div className="-mt-2 mb-4">
                        <div className="mx-auto max-w-4xl px-6">
                          <AcceptRetryButtons 
                            onAccept={openAccept} 
                            onRetry={openRetry} 
                            sql={currentSql}
                            rows={runQueryResult?.rows || []}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                )
              } catch (error) {
                console.error('Error rendering message:', error, m)
                return (
                  <div key={m.id} className="p-4 mx-auto max-w-4xl">
                    <div className="bg-red-900/20 border border-red-500/50 rounded-card p-4">
                      <p className="text-red-300">Error rendering message: {error.message}</p>
                    </div>
                  </div>
                )
              }
            })}
            {isLoading && (
              <div className="mx-auto max-w-4xl px-6 py-6">
                <div className="flex items-center gap-3 text-secondaryGray-600">
                  <div className="animate-spin h-5 w-5 border-2 border-brand-500 border-t-transparent rounded-full"></div>
                  <span className="font-medium">Generating response...</span>
                </div>
              </div>
            )}
          </div>
          
          {/* Save Session Button */}
          {messages.length > 1 && (
            <div className="px-4 py-3 border-t border-secondaryGray-500 bg-navy-300/50 backdrop-blur-sm">
              <div className="max-w-2xl mx-auto">
                <button
                  onClick={() => setSaveSessionOpen(true)}
                  className="w-full px-4 py-2.5 text-sm font-medium bg-navy-100 hover:bg-brand-400/50 border border-secondaryGray-500 rounded-button transition-all duration-200 flex items-center justify-center gap-2 text-secondaryGray-900"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                  </svg>
                  Save Chat Session
                </button>s
              </div>
            </div>
          )}
        
          <ChatInput onSend={handleSend} />
        </main>

      <Modal
        open={acceptOpen}
        title="Accept & Execute Query"
        onClose={() => setAcceptOpen(false)}
        actions={
          <button className="btn-primary px-6 py-2.5" onClick={doAccept}>
            Confirm
          </button>
        }
      >
        <label className="block mb-2 text-sm text-secondaryGray-600 font-medium">Number of rows to fetch</label>
        <input 
          className="input" 
          value={acceptRows} 
          onChange={(e) => setAcceptRows(e.target.value)} 
          type="number" 
          min="1" 
          placeholder="e.g., 10, 100, 1000"
        />
        <p className="mt-3 text-xs text-secondaryGray-600">
          Leave as 0 to fetch all rows (use with caution for large datasets)
        </p>
      </Modal>

      <Modal
        open={retryOpen}
        title="Retry with Feedback"
        onClose={() => setRetryOpen(false)}
        actions={
          <button className="btn-primary px-6 py-2.5" onClick={doRetry}>
            Retry Query
          </button>
        }
      >
        <label className="block mb-2 text-sm text-secondaryGray-600 font-medium">What should be improved?</label>
        <textarea 
          className="input min-h-[120px]" 
          value={retryFeedback} 
          onChange={(e) => setRetryFeedback(e.target.value)} 
          placeholder="e.g., Filter by last 30 days, add sorting by date, include only active records..."
        />
      </Modal>

      {/* Save Session Modal */}
      <Modal
        open={saveSessionOpen}
        title="Save Chat Session"
        onClose={() => setSaveSessionOpen(false)}
        actions={
          <button 
            className="btn-primary px-6 py-2.5" 
            onClick={handleSaveSession}
            disabled={!sessionName.trim()}
          >
            Save Session
          </button>
        }
      >
        <div className="space-y-4">
          <div>
            <label className="block mb-2 text-sm text-secondaryGray-600 font-medium">Session Name</label>
            <input 
              className="input" 
              value={sessionName} 
              onChange={(e) => setSessionName(e.target.value)} 
              placeholder="My SQL Chat Session" 
              autoFocus
            />
          </div>
          <div className="text-xs text-secondaryGray-600 bg-white/5 rounded-button p-3">
            💾 This will save {messages.length} messages from your current chat session for future reference.
          </div>
        </div>
      </Modal>
      </div>
    </ErrorBoundary>
  )
}



