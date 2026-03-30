import { useState, useRef, useEffect } from 'react'
import { 
  Send, LogOut, User, Shield, Database, MessageSquare, 
  ChevronDown, ChevronUp, FileText, Sparkles, Moon, Sun,
  Compass, Building2, BarChart3, Users, Briefcase, BookOpen, Info
} from 'lucide-react'

// Sample questions per role - matched to actual document content
const SAMPLE_QUESTIONS = {
  finance: [
    "What was the revenue growth in 2024 and what drove it?",
    "What are the key financial ratios and how do they compare to industry benchmarks?",
    "What is the breakdown of vendor service expenses?",
    "What are the cash flow trends and recommendations for improvement?",
    "What risks should finance focus on and how can they be mitigated?",
  ],
  marketing: [
    "What is our total marketing budget and how is it allocated across channels?",
    "What is our social media performance across different platforms?",
    "What were the results of our Google Ads campaigns?",
    "What is our customer acquisition cost by channel and which is most efficient?",
    "What were our top performing content pieces in 2024?",
  ],
  hr: [
    "What is the current headcount breakdown by department?",
    "What are the salary bands for different job levels?",
    "What percentage of employees received outstanding performance ratings?",
    "What is the company attendance rate and leave utilization pattern?",
    "What training programs were conducted in 2024 and what was the investment?",
  ],
  engineering: [
    "What is the high-level system architecture of the platform?",
    "What microservices are part of the backend and what do they do?",
    "What databases are used and for what purposes?",
    "What is the CI/CD pipeline and deployment process?",
    "What security and compliance frameworks are implemented?",
  ],
  c_level: [
    "What is the overall company revenue and employee count?",
    "What is our market position compared to competitors?",
    "What are the key performance metrics across all departments?",
    "What is the employee retention rate and engagement score?",
    "What are the main business risks and how are they being addressed?",
  ],
  employee: [
    "What are the company's core values and mission?",
    "What are the upcoming company events?",
    "What office locations does the company have?",
    "Who are the members of the executive team?",
    "What products and services does the company offer?",
  ],
}

// Format source document names
const formatSourceName = (source) => {
  if (!source) return 'Unknown Document'
  const name = source.replace(/\.[^/.]+$/, '')
    .replace(/_/g, ' ')
    .replace(/-/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
  return name
}

// Get department label
const formatDepartment = (dept) => {
  const labels = {
    engineering: 'Engineering',
    finance: 'Finance',
    hr: 'Human Resources',
    marketing: 'Marketing',
    general: 'Company Information'
  }
  return labels[dept] || dept
}

// Get department icon
const getDepartmentIcon = (dept) => {
  const icons = {
    engineering: BarChart3,
    finance: Briefcase,
    hr: Users,
    marketing: BarChart3,
    general: Building2
  }
  return icons[dept] || FileText
}

// Clean markdown artifacts from source text
const cleanSourceText = (text) => {
  if (!text) return ''
  return text
    .replace(/^#{1,6}\s*/gm, '')
    .replace(/\*\*/g, '')
    .replace(/\*/g, '')
    .replace(/`{1,3}/g, '')
    .replace(/^\s*[-*+]\s*/gm, '• ')
    .replace(/^\|.*\|$/gm, '')
    .replace(/^\s*[-:]+\s*$/gm, '')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/^---+$/gm, '')
    .trim()
}

// Citation component with hover tooltip
const Citation = ({ index, source, darkMode }) => {
  const [showTooltip, setShowTooltip] = useState(false)
  const DeptIcon = getDepartmentIcon(source?.department)
  
  return (
    <span className="relative inline-block">
      <button
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onClick={() => setShowTooltip(!showTooltip)}
        className={`inline-flex items-center justify-center w-5 h-5 text-xs font-medium rounded-full mx-0.5 cursor-pointer transition-all
          ${darkMode 
            ? 'bg-scout-600/30 text-scout-400 hover:bg-scout-600/50' 
            : 'bg-scout-100 text-scout-700 hover:bg-scout-200'}`}
      >
        {index}
      </button>
      
      {showTooltip && source && (
        <div className={`absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 p-3 rounded-lg shadow-xl border animate-fade-in-up
          ${darkMode 
            ? 'bg-slate-800 border-slate-700 text-slate-200' 
            : 'bg-white border-slate-200 text-slate-700'}`}>
          <div className="flex items-center gap-2 mb-2">
            <div className={`w-6 h-6 rounded flex items-center justify-center
              ${darkMode ? 'bg-slate-700' : 'bg-slate-100'}`}>
              <DeptIcon className={`w-3.5 h-3.5 ${darkMode ? 'text-scout-400' : 'text-scout-600'}`} />
            </div>
            <div>
              <p className={`text-sm font-medium ${darkMode ? 'text-slate-200' : 'text-slate-800'}`}>
                {formatSourceName(source.filename)}
              </p>
              <p className={`text-xs ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
                {formatDepartment(source.department)}
              </p>
            </div>
          </div>
          <p className={`text-xs leading-relaxed ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>
            {cleanSourceText(source.chunk || source.content)}
          </p>
          <div className={`absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-full w-0 h-0 
            border-l-8 border-r-8 border-t-8 border-transparent
            ${darkMode ? 'border-t-slate-800' : 'border-t-white'}`} />
        </div>
      )}
    </span>
  )
}

// Parse response and add inline citations
const ResponseWithCitations = ({ text, sources, darkMode }) => {
  if (!text) return null
  
  // Add citation markers at the end of key sentences
  const addCitations = (text, sources) => {
    if (!sources || sources.length === 0) return text
    
    // Split into paragraphs
    const paragraphs = text.split('\n\n')
    
    // For each paragraph, add a relevant citation at the end
    return paragraphs.map((para, idx) => {
      const sourceIdx = Math.min(idx, sources.length - 1)
      // Only add citation if paragraph has substance
      if (para.trim().length > 50) {
        return `${para.trim()} [cite:${sourceIdx + 1}]`
      }
      return para
    }).join('\n\n')
  }
  
  const citedText = addCitations(text, sources)
  
  // Parse and render with citations
  const parts = citedText.split(/(\[cite:\d+\])/)
  
  return (
    <span>
      {parts.map((part, idx) => {
        const match = part.match(/\[cite:(\d+)\]/)
        if (match) {
          const citationIdx = parseInt(match[1])
          const source = sources[citationIdx - 1]
          return <Citation key={idx} index={citationIdx} source={source} darkMode={darkMode} />
        }
        // Render text with basic formatting
        return <span key={idx} dangerouslySetInnerHTML={{ 
          __html: part
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br/>')
        }} />
      })}
    </span>
  )
}

export default function ChatPage({ user, onLogout }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [expandedSources, setExpandedSources] = useState({})
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('scout_darkMode')
    return saved ? JSON.parse(saved) : false
  })
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    localStorage.setItem('scout_darkMode', JSON.stringify(darkMode))
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSampleQuestion = (question) => {
    setInput(question)
    inputRef.current?.focus()
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      
      // Create abort controller with 60s timeout (Lambda cold starts can take ~30s)
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 60000)
      
      const response = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Basic ' + btoa(`${user.apiUser}:${user.apiPass}`)
        },
        body: JSON.stringify({ message: input }),
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)

      const data = await response.json()
      
      if (data.error || data.metadata?.error) {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: data.response || data.error || 'An error occurred',
          isError: true 
        }])
      } else {
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: data.response,
          sources: data.sources || []
        }])
      }
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage = error.name === 'AbortError' 
        ? 'Request timed out. The server may be starting up - please try again.'
        : `Unable to connect: ${error.message}. Please try again.`
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: errorMessage,
        isError: true 
      }])
    }

    setIsLoading(false)
  }

  const toggleSources = (messageIndex) => {
    setExpandedSources(prev => ({
      ...prev,
      [messageIndex]: !prev[messageIndex]
    }))
  }

  const sampleQuestions = SAMPLE_QUESTIONS[user.role] || SAMPLE_QUESTIONS.employee
  
  // Get random suggestions for the input area (different from what was asked)
  const getRandomSuggestions = () => {
    const asked = messages.filter(m => m.role === 'user').map(m => m.content)
    const available = sampleQuestions.filter(q => !asked.includes(q))
    return available.slice(0, 3)
  }

  return (
    <div className={`min-h-screen flex flex-col ${darkMode ? 'dark bg-slate-900' : 'bg-slate-50'}`}>
      {/* Header */}
      <header className={`sticky top-0 z-50 border-b backdrop-blur-lg
        ${darkMode 
          ? 'bg-slate-900/95 border-slate-800' 
          : 'bg-white/95 border-slate-200'}`}>
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-scout-500 to-scout-700 rounded-xl flex items-center justify-center shadow-lg shadow-scout-500/20">
              <Compass className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className={`font-bold text-lg ${darkMode ? 'text-white' : 'text-slate-900'}`}>Scout</h1>
              <p className={`text-xs ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>Enterprise Knowledge Assistant</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Dark mode toggle */}
            <button
              onClick={() => setDarkMode(!darkMode)}
              className={`p-2 rounded-lg transition-colors
                ${darkMode 
                  ? 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-300' 
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
            >
              {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>

            {/* User menu */}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className={`flex items-center gap-2 px-3 py-2 rounded-xl transition-colors
                  ${darkMode 
                    ? 'bg-slate-800 hover:bg-slate-700' 
                    : 'bg-slate-100 hover:bg-slate-200'}`}
              >
                <div className="w-8 h-8 bg-gradient-to-br from-scout-100 to-scout-200 rounded-full flex items-center justify-center">
                  <span className="text-scout-700 font-medium text-sm">
                    {user.name.split(' ').map(n => n[0]).join('')}
                  </span>
                </div>
                <span className={`font-medium text-sm hidden sm:inline ${darkMode ? 'text-slate-300' : 'text-slate-700'}`}>
                  {user.name}
                </span>
                <ChevronDown className={`w-4 h-4 ${darkMode ? 'text-slate-400' : 'text-slate-400'}`} />
              </button>

              {showUserMenu && (
                <div className={`absolute right-0 mt-2 w-72 rounded-xl shadow-xl border overflow-hidden z-50
                  ${darkMode 
                    ? 'bg-slate-800 border-slate-700 shadow-slate-900/50' 
                    : 'bg-white border-slate-200'}`}>
                  <div className={`p-4 border-b ${darkMode ? 'border-slate-700' : 'border-slate-100'}`}>
                    <p className={`font-semibold ${darkMode ? 'text-white' : 'text-slate-900'}`}>{user.name}</p>
                    <p className={`text-sm ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>{user.department}</p>
                  </div>
                  
                  <div className={`p-3 space-y-2 border-b ${darkMode ? 'border-slate-700' : 'border-slate-100'}`}>
                    <div className={`flex items-center gap-3 px-2 py-1.5 rounded-lg ${darkMode ? 'bg-slate-700/50' : 'bg-slate-50'}`}>
                      <Shield className={`w-4 h-4 ${darkMode ? 'text-slate-400' : 'text-slate-400'}`} />
                      <div>
                        <p className={`text-xs ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>Role</p>
                        <p className={`text-sm font-medium capitalize ${darkMode ? 'text-slate-200' : 'text-slate-700'}`}>
                          {user.role.replace('_', ' ')}
                        </p>
                      </div>
                    </div>
                    <div className={`flex items-center gap-3 px-2 py-1.5 rounded-lg ${darkMode ? 'bg-slate-700/50' : 'bg-slate-50'}`}>
                      <Database className={`w-4 h-4 ${darkMode ? 'text-slate-400' : 'text-slate-400'}`} />
                      <div>
                        <p className={`text-xs ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>Data Access</p>
                        <p className={`text-sm font-medium ${darkMode ? 'text-slate-200' : 'text-slate-700'}`}>
                          {user.access.map(a => a.charAt(0).toUpperCase() + a.slice(1)).join(', ')}
                        </p>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={onLogout}
                    className={`w-full flex items-center gap-2 px-4 py-3 text-sm text-red-500 hover:bg-red-50 
                      dark:hover:bg-red-900/20 transition-colors`}
                  >
                    <LogOut className="w-4 h-4" />
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="flex-1 max-w-4xl w-full mx-auto px-4 py-6">
        {messages.length === 0 ? (
          /* Welcome Screen */
          <div className="h-full flex flex-col items-center justify-center py-8">
            <div className="w-20 h-20 bg-gradient-to-br from-scout-500 to-scout-700 rounded-2xl flex items-center justify-center mb-6 shadow-xl shadow-scout-500/25">
              <Sparkles className="w-10 h-10 text-white" />
            </div>
            <h2 className={`text-2xl font-bold mb-2 ${darkMode ? 'text-white' : 'text-slate-900'}`}>
              Welcome, {user.name.split(' ')[0]}!
            </h2>
            <p className={`text-center max-w-md mb-8 ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
              I'm Scout, your enterprise knowledge assistant. Ask me anything about 
              {user.access.length > 1 
                ? ` ${user.access.slice(0, -1).join(', ')} and ${user.access.slice(-1)}` 
                : ` ${user.access[0]}`} data.
            </p>

            <div className="w-full max-w-2xl">
              <p className={`text-sm font-medium mb-3 flex items-center gap-2 ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>
                <BookOpen className="w-4 h-4" />
                Try asking
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {sampleQuestions.map((question, i) => (
                  <button
                    key={i}
                    onClick={() => handleSampleQuestion(question)}
                    className={`text-left px-4 py-3 rounded-xl text-sm transition-all group
                      ${darkMode 
                        ? 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 hover:border-scout-600' 
                        : 'bg-white hover:bg-scout-50 text-slate-600 border border-slate-200 hover:border-scout-300'}`}
                  >
                    <span className={`group-hover:text-scout-600 ${darkMode ? 'group-hover:text-scout-400' : ''}`}>
                      {question}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Messages */
          <div className="space-y-6 pb-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in-up`}
              >
                <div className={`max-w-[85%] ${message.role === 'user' ? 'order-2' : ''}`}>
                  {message.role === 'assistant' && (
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-6 h-6 bg-gradient-to-br from-scout-500 to-scout-700 rounded-lg flex items-center justify-center">
                        <Compass className="w-4 h-4 text-white" />
                      </div>
                      <span className={`text-sm font-medium ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>Scout</span>
                    </div>
                  )}
                  
                  <div className={`rounded-2xl px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-gradient-to-r from-scout-500 to-scout-600 text-white'
                      : message.isError
                        ? darkMode 
                          ? 'bg-red-900/30 border border-red-800 text-red-300'
                          : 'bg-red-50 border border-red-100 text-red-700'
                        : darkMode
                          ? 'bg-slate-800 border border-slate-700 text-slate-200'
                          : 'bg-white border border-slate-200 text-slate-700'
                  }`}>
                    {message.role === 'assistant' && message.sources && message.sources.length > 0 ? (
                      <ResponseWithCitations 
                        text={message.content} 
                        sources={message.sources} 
                        darkMode={darkMode}
                      />
                    ) : (
                      <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                    )}
                  </div>

                  {/* Sources */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-2">
                      <button
                        onClick={() => toggleSources(index)}
                        className={`flex items-center gap-2 text-sm transition-colors
                          ${darkMode 
                            ? 'text-slate-400 hover:text-scout-400' 
                            : 'text-slate-500 hover:text-scout-600'}`}
                      >
                        <FileText className="w-4 h-4" />
                        <span>View {message.sources.length} source{message.sources.length > 1 ? 's' : ''}</span>
                        {expandedSources[index] ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                      
                      {expandedSources[index] && (
                        <div className={`mt-3 space-y-2 pl-2 border-l-2 
                          ${darkMode ? 'border-slate-700' : 'border-slate-200'}`}>
                          {message.sources.map((source, sIdx) => {
                            const DeptIcon = getDepartmentIcon(source.department)
                            return (
                              <div 
                                key={sIdx}
                                className={`p-3 rounded-xl
                                  ${darkMode 
                                    ? 'bg-slate-800/50 border border-slate-700' 
                                    : 'bg-slate-50 border border-slate-100'}`}
                              >
                                <div className="flex items-start justify-between gap-2 mb-2">
                                  <div className="flex items-center gap-2">
                                    <div className={`w-6 h-6 rounded-lg flex items-center justify-center
                                      ${darkMode ? 'bg-slate-700' : 'bg-white border border-slate-200'}`}>
                                      <DeptIcon className={`w-3.5 h-3.5 ${darkMode ? 'text-scout-400' : 'text-scout-600'}`} />
                                    </div>
                                    <div>
                                      <p className={`text-sm font-medium ${darkMode ? 'text-slate-200' : 'text-slate-700'}`}>
                                        {formatSourceName(source.filename)}
                                      </p>
                                      <p className={`text-xs ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
                                        {formatDepartment(source.department)}
                                      </p>
                                    </div>
                                  </div>
                                  <span className={`text-xs px-2 py-0.5 rounded-full
                                    ${darkMode 
                                      ? 'bg-scout-900/50 text-scout-400' 
                                      : 'bg-scout-100 text-scout-700'}`}>
                                    #{sIdx + 1}
                                  </span>
                                </div>
                                <p className={`text-sm leading-relaxed
                                  ${darkMode ? 'text-slate-400' : 'text-slate-600'}`}>
                                  {cleanSourceText(source.chunk || source.content)}
                                </p>
                              </div>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start animate-fade-in-up">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-6 h-6 bg-gradient-to-br from-scout-500 to-scout-700 rounded-lg flex items-center justify-center">
                      <Compass className="w-4 h-4 text-white" />
                    </div>
                    <span className={`text-sm font-medium ${darkMode ? 'text-slate-400' : 'text-slate-500'}`}>Scout</span>
                  </div>
                  <div className={`rounded-2xl px-4 py-3 inline-flex items-center gap-1
                    ${darkMode 
                      ? 'bg-slate-800 border border-slate-700' 
                      : 'bg-white border border-slate-200'}`}>
                    <div className={`w-2 h-2 rounded-full typing-dot ${darkMode ? 'bg-slate-400' : 'bg-slate-400'}`}></div>
                    <div className={`w-2 h-2 rounded-full typing-dot ${darkMode ? 'bg-slate-400' : 'bg-slate-400'}`}></div>
                    <div className={`w-2 h-2 rounded-full typing-dot ${darkMode ? 'bg-slate-400' : 'bg-slate-400'}`}></div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </main>

      {/* Input Area */}
      <div className={`sticky bottom-0 border-t backdrop-blur-lg
        ${darkMode 
          ? 'bg-slate-900/95 border-slate-800' 
          : 'bg-white/95 border-slate-200'}`}>
        <div className="max-w-4xl mx-auto px-4 py-4">
          {/* Suggestions above input when there are messages */}
          {messages.length > 0 && getRandomSuggestions().length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              <span className={`text-xs ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
                Suggestions:
              </span>
              {getRandomSuggestions().map((q, i) => (
                <button
                  key={i}
                  onClick={() => handleSampleQuestion(q)}
                  className={`text-xs px-3 py-1 rounded-full transition-colors truncate max-w-[250px]
                    ${darkMode 
                      ? 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-scout-400 border border-slate-700' 
                      : 'bg-slate-100 text-slate-600 hover:bg-scout-50 hover:text-scout-700 border border-slate-200'}`}
                >
                  {q}
                </button>
              ))}
            </div>
          )}
          
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask me anything..."
              disabled={isLoading}
              className={`flex-1 px-4 py-3 rounded-xl border transition-all
                ${darkMode 
                  ? 'bg-slate-800 border-slate-700 text-white placeholder:text-slate-500 focus:bg-slate-700 focus:border-scout-500 focus:ring-2 focus:ring-scout-500/20' 
                  : 'bg-slate-50 border-slate-200 placeholder:text-slate-400 focus:bg-white focus:border-scout-500 focus:ring-2 focus:ring-scout-500/20'
                }
                disabled:opacity-50 disabled:cursor-not-allowed`}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="px-5 py-3 bg-gradient-to-r from-scout-500 to-scout-600 text-white rounded-xl
                       hover:from-scout-600 hover:to-scout-700 
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-all shadow-lg shadow-scout-500/25 hover:shadow-xl hover:shadow-scout-500/30"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
          <p className={`text-xs text-center mt-3 ${darkMode ? 'text-slate-500' : 'text-slate-400'}`}>
            Scout only has access to data you're authorized to view based on your role.
          </p>
        </div>
      </div>
    </div>
  )
}
