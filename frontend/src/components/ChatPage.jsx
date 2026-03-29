import { useState, useRef, useEffect } from 'react'
import { 
  Compass, Send, LogOut, User, Shield, Database, BarChart3, 
  FileText, ChevronDown, ChevronRight, Sparkles, AlertCircle,
  Building2, MessageSquare, RefreshCw, Copy, Check, ExternalLink
} from 'lucide-react'

// Sample questions by role
const SAMPLE_QUESTIONS = {
  finance: [
    "What was our gross margin in Q4 2024?",
    "Show me the quarterly revenue breakdown",
    "What are our key financial ratios?",
    "Summarize marketing expenses for 2024"
  ],
  marketing: [
    "What were the Q3 campaign results?",
    "Show me customer acquisition metrics",
    "What's our social media performance?",
    "Summarize the marketing strategy for 2024"
  ],
  hr: [
    "What are the employee attendance trends?",
    "Show me performance review statistics",
    "What are our payroll expenses?",
    "List employees by department"
  ],
  engineering: [
    "Explain our technical architecture",
    "What are the development guidelines?",
    "Show me the deployment process",
    "What security protocols do we follow?"
  ],
  c_level: [
    "Give me an executive summary of Q4",
    "What are the key risks and mitigations?",
    "Compare department performance",
    "What's our overall financial health?"
  ],
  employee: [
    "What's the company leave policy?",
    "When is the next company event?",
    "What are the office guidelines?",
    "How do I submit expense reports?"
  ]
}

const ROLE_INFO = {
  finance: { icon: BarChart3, color: 'emerald', access: ['Finance Reports', 'General Info'] },
  marketing: { icon: Sparkles, color: 'purple', access: ['Marketing Data', 'General Info'] },
  hr: { icon: User, color: 'amber', access: ['HR Records', 'General Info'] },
  engineering: { icon: Database, color: 'blue', access: ['Tech Docs', 'General Info'] },
  c_level: { icon: Building2, color: 'rose', access: ['All Departments'] },
  employee: { icon: User, color: 'slate', access: ['General Info'] },
}

// API Configuration
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function ChatPage({ user, onLogout }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showSidebar, setShowSidebar] = useState(true)
  const [usage, setUsage] = useState({ requests_today: 0, max_requests_per_day: 100 })
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const roleInfo = ROLE_INFO[user.role] || ROLE_INFO.employee
  const sampleQuestions = SAMPLE_QUESTIONS[user.role] || SAMPLE_QUESTIONS.employee

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    fetchUsage()
  }, [])

  const fetchUsage = async () => {
    try {
      const credentials = btoa(`${user.apiUser}:${user.apiPass}`)
      const res = await fetch(`${API_BASE}/usage`, {
        headers: { 'Authorization': `Basic ${credentials}` }
      })
      if (res.ok) {
        setUsage(await res.json())
      }
    } catch (e) {
      console.error('Failed to fetch usage:', e)
    }
  }

  const sendMessage = async (text) => {
    if (!text.trim() || isLoading) return

    const userMessage = { role: 'user', content: text, timestamp: new Date() }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const credentials = btoa(`${user.apiUser}:${user.apiPass}`)
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Basic ${credentials}`
        },
        body: JSON.stringify({ message: text })
      })

      const data = await res.json()
      
      const assistantMessage = {
        role: 'assistant',
        content: data.response || 'Sorry, I encountered an error.',
        sources: data.sources || [],
        metadata: data.metadata || {},
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, assistantMessage])
      fetchUsage()
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I could not connect to the server. Please try again.',
        error: true,
        timestamp: new Date()
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    sendMessage(input)
  }

  const handleSampleQuestion = (question) => {
    sendMessage(question)
  }

  return (
    <div className="h-screen flex bg-slate-50">
      {/* Sidebar */}
      <aside className={`${showSidebar ? 'w-72' : 'w-0'} transition-all duration-300 overflow-hidden bg-white border-r border-slate-200 flex flex-col`}>
        <div className="p-5 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-scout-500 to-scout-700 rounded-xl flex items-center justify-center">
              <Compass className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold gradient-text">Scout</h1>
              <p className="text-xs text-slate-400">Knowledge Assistant</p>
            </div>
          </div>
        </div>

        {/* User Info */}
        <div className="p-5 border-b border-slate-100">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-gradient-to-br from-scout-100 to-scout-200 rounded-full flex items-center justify-center">
              <span className="text-scout-700 font-semibold text-sm">
                {user.name.split(' ').map(n => n[0]).join('')}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-medium text-slate-800 truncate">{user.name}</p>
              <p className="text-xs text-slate-400 truncate">{user.email}</p>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm">
              <roleInfo.icon className={`w-4 h-4 text-${roleInfo.color}-500`} />
              <span className="text-slate-600">{user.department}</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <Shield className="w-4 h-4 text-scout-500" />
              <span className="text-slate-600">
                {roleInfo.access.join(', ')}
              </span>
            </div>
          </div>
        </div>

        {/* Usage Stats */}
        <div className="p-5 border-b border-slate-100">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Today's Usage
          </h3>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-600">Queries</span>
              <span className="font-medium text-slate-800">
                {usage.requests_today} / {usage.max_requests_per_day}
              </span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2">
              <div 
                className="bg-gradient-to-r from-scout-400 to-scout-600 h-2 rounded-full transition-all"
                style={{ width: `${(usage.requests_today / usage.max_requests_per_day) * 100}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="p-5 flex-1">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Try asking
          </h3>
          <div className="space-y-2">
            {sampleQuestions.map((q, i) => (
              <button
                key={i}
                onClick={() => handleSampleQuestion(q)}
                className="w-full text-left px-3 py-2.5 text-sm text-slate-600 bg-slate-50 
                         rounded-lg hover:bg-scout-50 hover:text-scout-700 transition-colors
                         border border-transparent hover:border-scout-200"
              >
                <MessageSquare className="w-3.5 h-3.5 inline mr-2 opacity-50" />
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Logout */}
        <div className="p-5 border-t border-slate-100">
          <button
            onClick={onLogout}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm
                     text-slate-600 bg-slate-50 rounded-lg hover:bg-red-50 hover:text-red-600
                     transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6">
          <button
            onClick={() => setShowSidebar(!showSidebar)}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <ChevronRight className={`w-5 h-5 text-slate-400 transition-transform ${showSidebar ? 'rotate-180' : ''}`} />
          </button>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
              Connected
            </div>
            <button
              onClick={() => setMessages([])}
              className="p-2 hover:bg-slate-100 rounded-lg transition-colors text-slate-400 hover:text-slate-600"
              title="Clear chat"
            >
              <RefreshCw className="w-5 h-5" />
            </button>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6">
          {messages.length === 0 ? (
            <WelcomeScreen 
              user={user} 
              sampleQuestions={sampleQuestions}
              onQuestionClick={handleSampleQuestion}
            />
          ) : (
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.map((msg, i) => (
                <MessageBubble key={i} message={msg} />
              ))}
              {isLoading && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input */}
        <div className="p-6 bg-white border-t border-slate-200">
          <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
            <div className="relative">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask Scout anything about your company data..."
                disabled={isLoading}
                className="w-full px-5 py-4 pr-14 rounded-2xl border border-slate-200 bg-slate-50
                         focus:bg-white focus:border-scout-500 focus:ring-2 focus:ring-scout-500/20
                         disabled:opacity-50 transition-all text-slate-800 placeholder:text-slate-400"
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-2.5
                         bg-gradient-to-r from-scout-500 to-scout-600 text-white rounded-xl
                         hover:from-scout-600 hover:to-scout-700 disabled:opacity-30 
                         disabled:cursor-not-allowed transition-all"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
            <p className="text-xs text-slate-400 mt-2 text-center">
              Scout can make mistakes. Verify important information from source documents.
            </p>
          </form>
        </div>
      </main>
    </div>
  )
}

function WelcomeScreen({ user, sampleQuestions, onQuestionClick }) {
  return (
    <div className="h-full flex items-center justify-center">
      <div className="text-center max-w-2xl">
        <div className="w-20 h-20 bg-gradient-to-br from-scout-500 to-scout-700 rounded-2xl 
                      flex items-center justify-center mx-auto mb-6 shadow-lg shadow-scout-500/25">
          <Compass className="w-10 h-10 text-white" />
        </div>
        <h2 className="text-3xl font-bold text-slate-800 mb-3">
          Hello, {user.name.split(' ')[0]}!
        </h2>
        <p className="text-slate-500 text-lg mb-8">
          I'm Scout, your AI knowledge assistant. Ask me anything about company data 
          you have access to.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-left">
          {sampleQuestions.map((q, i) => (
            <button
              key={i}
              onClick={() => onQuestionClick(q)}
              className="p-4 bg-white rounded-xl border border-slate-200 hover:border-scout-300 
                       hover:shadow-md hover:shadow-scout-100 transition-all text-left group"
            >
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-scout-100 rounded-lg flex items-center justify-center 
                              group-hover:bg-scout-200 transition-colors">
                  <MessageSquare className="w-4 h-4 text-scout-600" />
                </div>
                <span className="text-slate-600 group-hover:text-slate-800 text-sm flex-1">
                  {q}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

function MessageBubble({ message }) {
  const [showSources, setShowSources] = useState(false)
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'user'

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in-up`}>
      <div className={`max-w-[85%] ${isUser ? 'order-2' : ''}`}>
        {/* Avatar and Name */}
        <div className={`flex items-center gap-2 mb-1 ${isUser ? 'justify-end' : ''}`}>
          {!isUser && (
            <div className="w-6 h-6 bg-gradient-to-br from-scout-500 to-scout-700 rounded-lg 
                          flex items-center justify-center">
              <Compass className="w-3.5 h-3.5 text-white" />
            </div>
          )}
          <span className="text-xs font-medium text-slate-500">
            {isUser ? 'You' : 'Scout'}
          </span>
          <span className="text-xs text-slate-400">
            {message.timestamp?.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>

        {/* Message Content */}
        <div className={`rounded-2xl px-5 py-4 ${
          isUser 
            ? 'bg-gradient-to-r from-scout-500 to-scout-600 text-white' 
            : message.error 
              ? 'bg-red-50 border border-red-100 text-red-700'
              : 'bg-white border border-slate-200 text-slate-700'
        }`}>
          <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
          
          {/* Sources */}
          {!isUser && message.sources?.length > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-100">
              <button
                onClick={() => setShowSources(!showSources)}
                className="flex items-center gap-2 text-sm text-scout-600 hover:text-scout-700"
              >
                <FileText className="w-4 h-4" />
                {message.sources.length} source{message.sources.length > 1 ? 's' : ''}
                <ChevronDown className={`w-4 h-4 transition-transform ${showSources ? 'rotate-180' : ''}`} />
              </button>
              
              {showSources && (
                <div className="mt-3 space-y-3">
                  {message.sources.map((source, i) => (
                    <SourceCard key={i} source={source} index={i + 1} />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Metadata */}
          {!isUser && message.metadata?.model_used && (
            <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs text-slate-400">
                Model: {message.metadata.model_used}
              </span>
              <button
                onClick={handleCopy}
                className="text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1"
              >
                {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function SourceCard({ source, index }) {
  const [expanded, setExpanded] = useState(false)
  
  return (
    <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 bg-scout-100 rounded-lg flex items-center justify-center text-scout-600 text-xs font-semibold">
            {index}
          </div>
          <div>
            <p className="text-sm font-medium text-slate-700">{source.filename}</p>
            <p className="text-xs text-slate-400 capitalize">{source.department} Department</p>
          </div>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-scout-600 hover:text-scout-700 whitespace-nowrap"
        >
          {expanded ? 'Show less' : 'Show more'}
        </button>
      </div>
      
      {expanded && source.chunk && (
        <div className="mt-3 pt-3 border-t border-slate-200">
          <p className="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap">
            {source.chunk}
          </p>
        </div>
      )}
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex justify-start animate-fade-in-up">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <div className="w-6 h-6 bg-gradient-to-br from-scout-500 to-scout-700 rounded-lg 
                        flex items-center justify-center">
            <Compass className="w-3.5 h-3.5 text-white" />
          </div>
          <span className="text-xs font-medium text-slate-500">Scout</span>
        </div>
        <div className="bg-white border border-slate-200 rounded-2xl px-5 py-4">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-scout-400 rounded-full typing-dot"></div>
            <div className="w-2 h-2 bg-scout-400 rounded-full typing-dot"></div>
            <div className="w-2 h-2 bg-scout-400 rounded-full typing-dot"></div>
          </div>
        </div>
      </div>
    </div>
  )
}
