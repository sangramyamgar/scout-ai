import { useState, useEffect } from 'react'
import LoginPage from './components/LoginPage'
import ChatPage from './components/ChatPage'

// Demo users with professional names and emails
const DEMO_USERS = {
  'sarah.mitchell@scout.ai': { password: 'finance2024', role: 'finance', name: 'Sarah Mitchell', department: 'Finance', apiUser: 'Sam', apiPass: 'financepass' },
  'james.chen@scout.ai': { password: 'marketing2024', role: 'marketing', name: 'James Chen', department: 'Marketing', apiUser: 'Bruce', apiPass: 'securepass' },
  'priya.sharma@scout.ai': { password: 'hr2024', role: 'hr', name: 'Priya Sharma', department: 'Human Resources', apiUser: 'Natasha', apiPass: 'hrpass123' },
  'alex.torres@scout.ai': { password: 'eng2024', role: 'engineering', name: 'Alex Torres', department: 'Engineering', apiUser: 'Tony', apiPass: 'password123' },
  'michael.ross@scout.ai': { password: 'exec2024', role: 'c_level', name: 'Michael Ross', department: 'Executive', apiUser: 'Nick', apiPass: 'director123' },
  'emma.wilson@scout.ai': { password: 'employee2024', role: 'employee', name: 'Emma Wilson', department: 'General Staff', apiUser: 'Happy', apiPass: 'employee123' },
}

function App() {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check for saved session
    const savedUser = localStorage.getItem('scout_user')
    if (savedUser) {
      try {
        setUser(JSON.parse(savedUser))
      } catch (e) {
        localStorage.removeItem('scout_user')
      }
    }
    setIsLoading(false)
  }, [])

  const handleLogin = (email, password) => {
    const userData = DEMO_USERS[email.toLowerCase()]
    if (userData && userData.password === password) {
      const userSession = {
        email,
        name: userData.name,
        role: userData.role,
        department: userData.department,
        apiUser: userData.apiUser,
        apiPass: userData.apiPass,
      }
      setUser(userSession)
      localStorage.setItem('scout_user', JSON.stringify(userSession))
      return { success: true }
    }
    return { success: false, error: 'Invalid email or password' }
  }

  const handleLogout = () => {
    setUser(null)
    localStorage.removeItem('scout_user')
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 border-3 border-scout-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-slate-600 font-medium">Loading Scout...</span>
        </div>
      </div>
    )
  }

  return user ? (
    <ChatPage user={user} onLogout={handleLogout} />
  ) : (
    <LoginPage onLogin={handleLogin} demoUsers={DEMO_USERS} />
  )
}

export default App
