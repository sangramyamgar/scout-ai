import { useState } from 'react'
import { Eye, EyeOff, Compass, Shield, Zap, Users, ChevronDown } from 'lucide-react'

export default function LoginPage({ onLogin, demoUsers }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showDemoAccounts, setShowDemoAccounts] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    
    // Simulate network delay
    await new Promise(r => setTimeout(r, 500))
    
    const result = onLogin(email, password)
    if (!result.success) {
      setError(result.error)
    }
    setIsLoading(false)
  }

  const handleDemoLogin = (demoEmail) => {
    const userData = demoUsers[demoEmail]
    setEmail(demoEmail)
    setPassword(userData.password)
    setShowDemoAccounts(false)
  }

  const features = [
    { icon: Shield, title: 'Role-Based Access', desc: 'Secure, department-specific data access' },
    { icon: Zap, title: 'AI-Powered', desc: 'Intelligent answers with source citations' },
    { icon: Users, title: 'Multi-Department', desc: 'Finance, HR, Marketing, Engineering & more' },
  ]

  return (
    <div className="min-h-screen flex">
      {/* Left Panel - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-scout-600 via-scout-700 to-scout-900 p-12 flex-col justify-between relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-20 w-72 h-72 bg-white rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-white rounded-full blur-3xl"></div>
        </div>
        
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center backdrop-blur">
              <Compass className="w-7 h-7 text-white" />
            </div>
            <span className="text-3xl font-bold text-white">Scout</span>
          </div>
          <p className="text-scout-200 text-lg mt-1">Enterprise Knowledge Assistant</p>
        </div>

        <div className="relative z-10 space-y-8">
          <h1 className="text-4xl font-bold text-white leading-tight">
            Your intelligent guide to<br />company knowledge
          </h1>
          <p className="text-scout-200 text-lg max-w-md">
            Access department-specific insights, financial reports, HR data, and more — 
            all through natural conversation with AI-powered accuracy.
          </p>
          
          <div className="space-y-4 pt-4">
            {features.map((feature, i) => (
              <div key={i} className="flex items-center gap-4">
                <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center">
                  <feature.icon className="w-5 h-5 text-scout-200" />
                </div>
                <div>
                  <h3 className="text-white font-medium">{feature.title}</h3>
                  <p className="text-scout-300 text-sm">{feature.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="relative z-10">
          <p className="text-scout-300 text-sm">
            Powered by AWS + Agentic AI • Built with LangChain & LangGraph
          </p>
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <div className="w-12 h-12 bg-gradient-to-br from-scout-500 to-scout-700 rounded-xl flex items-center justify-center">
              <Compass className="w-7 h-7 text-white" />
            </div>
            <span className="text-3xl font-bold gradient-text">Scout</span>
          </div>

          <div className="bg-white rounded-2xl shadow-xl shadow-slate-200/50 p-8">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-slate-900">Welcome back</h2>
              <p className="text-slate-500 mt-2">Sign in to access your knowledge base</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Email address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@scout.ai"
                  className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 
                           focus:bg-white focus:border-scout-500 focus:ring-2 focus:ring-scout-500/20
                           transition-all duration-200 placeholder:text-slate-400"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 
                             focus:bg-white focus:border-scout-500 focus:ring-2 focus:ring-scout-500/20
                             transition-all duration-200 placeholder:text-slate-400 pr-12"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              {error && (
                <div className="bg-red-50 text-red-600 text-sm px-4 py-3 rounded-xl border border-red-100">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 px-4 bg-gradient-to-r from-scout-500 to-scout-600 
                         text-white font-medium rounded-xl shadow-lg shadow-scout-500/25
                         hover:from-scout-600 hover:to-scout-700 hover:shadow-xl hover:shadow-scout-500/30
                         focus:ring-2 focus:ring-scout-500 focus:ring-offset-2
                         disabled:opacity-50 disabled:cursor-not-allowed
                         transition-all duration-200"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    Signing in...
                  </span>
                ) : (
                  'Sign in'
                )}
              </button>
            </form>

            {/* Demo Accounts Dropdown */}
            <div className="mt-6 pt-6 border-t border-slate-100">
              <button
                onClick={() => setShowDemoAccounts(!showDemoAccounts)}
                className="w-full flex items-center justify-between px-4 py-3 text-sm text-slate-600 
                         bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors"
              >
                <span className="flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  Demo accounts available
                </span>
                <ChevronDown className={`w-4 h-4 transition-transform ${showDemoAccounts ? 'rotate-180' : ''}`} />
              </button>
              
              {showDemoAccounts && (
                <div className="mt-3 space-y-2 animate-fade-in-up">
                  {Object.entries(demoUsers).map(([demoEmail, userData]) => (
                    <button
                      key={demoEmail}
                      onClick={() => handleDemoLogin(demoEmail)}
                      className="w-full flex items-center justify-between px-4 py-3 text-sm
                               bg-white border border-slate-200 rounded-xl
                               hover:border-scout-300 hover:bg-scout-50 transition-all group"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-gradient-to-br from-scout-100 to-scout-200 
                                      rounded-full flex items-center justify-center">
                          <span className="text-scout-700 font-medium text-xs">
                            {userData.name.split(' ').map(n => n[0]).join('')}
                          </span>
                        </div>
                        <div className="text-left">
                          <p className="font-medium text-slate-700 group-hover:text-scout-700">{userData.name}</p>
                          <p className="text-xs text-slate-400">{userData.department}</p>
                        </div>
                      </div>
                      <span className="text-xs px-2 py-1 bg-slate-100 text-slate-500 rounded-full
                                     group-hover:bg-scout-100 group-hover:text-scout-600">
                        {userData.role === 'c_level' ? 'Executive' : userData.role}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          <p className="text-center text-sm text-slate-400 mt-6">
            This is a demo application. Use the demo accounts above to explore.
          </p>
        </div>
      </div>
    </div>
  )
}
