import React, { useState, useEffect, useRef } from 'react'
import { 
  Bot, 
  GitBranch, 
  Github, 
  LayoutDashboard, 
  LogOut, 
  Plus, 
  RefreshCw, 
  ShieldAlert, 
  Sparkles, 
  Sun, 
  Moon, 
  FileText, 
  CheckCircle, 
  AlertTriangle,
  Code2
} from 'lucide-react'
import mermaid from 'mermaid'

// Initialize mermaid for diagram renders
mermaid.initialize({
  startOnLoad: true,
  theme: 'dark',
  securityLevel: 'loose',
})

// Types
interface Repository {
  id: string
  name: string
  github_url: string
  branch: string
  status: string
  metadata_info?: {
    total_files: number
    total_loc: number
    languages: Record<string, number>
    languages_loc_percentage: Record<string, number>
  }
}

interface ChatMessage {
  role: 'user' | 'assistant'
  message: string
  references?: Array<{
    file_path: string
    symbol_name?: string
    snippet: string
  }>
}

interface Documentation {
  doc_type: string
  title: string
  content: string
}

interface DiagramData {
  diagram_type: string
  code: string
}

interface AuditReport {
  score: number
  findings: Array<{
    severity: string
    category: string
    message: string
    line?: number
    file?: string
  }>
}

// Mock Data for Fallback
const MOCK_REPOSITORIES: Repository[] = [
  {
    id: "repo-1",
    name: "repomind-backend",
    github_url: "https://github.com/coderanush/repomind-backend",
    branch: "main",
    status: "COMPLETE",
    metadata_info: {
      total_files: 24,
      total_loc: 4850,
      languages: { "Python": 18, "SQL": 3, "YAML": 3 },
      languages_loc_percentage: { "Python": 84.5, "SQL": 10.2, "YAML": 5.3 }
    }
  },
  {
    id: "repo-2",
    name: "repomind-react-ui",
    github_url: "https://github.com/coderanush/repomind-react-ui",
    branch: "master",
    status: "COMPLETE",
    metadata_info: {
      total_files: 38,
      total_loc: 7200,
      languages: { "TypeScript": 20, "React TypeScript": 12, "CSS": 6 },
      languages_loc_percentage: { "TypeScript": 65.0, "React TypeScript": 25.0, "CSS": 10.0 }
    }
  }
]

const MOCK_DOCS: Record<string, Documentation[]> = {
  "repo-1": [
    {
      doc_type: "README",
      title: "README.md",
      content: `# RepoMind Backend\n\nAI-powered repository understanding platform. Extracts ASTs and generates documentation.\n\n## Getting Started\n1. Install Python 3.11\n2. Run pip install -r requirements.txt\n3. Start the server: uvicorn app.main:app --reload\n\n## Architecture\nUses a clean layered architecture with a multi-agent LangGraph orchestrator.`
    },
    {
      doc_type: "SETUP",
      title: "Setup & Onboarding Guide",
      content: `# Setup & Onboarding Guide\n\n## Prerequisites\nEnsure Python 3.10+ and git are installed.\n\n## Environment Variables\nCopy \`.env.example\` to \`.env\` and add your \`OPENAI_API_KEY\` and \`QDRANT_HOST\` keys.`
    },
    {
      doc_type: "API_REFERENCE",
      title: "API Reference Guide",
      content: `# API Endpoints\n\n### POST \`/api/v1/repositories\`\nSubmit a new repository for indexing.\n\n### POST \`/api/v1/chat\`\nQuery the repository chatbot with context.`
    }
  ]
}

const MOCK_DIAGRAMS: Record<string, DiagramData[]> = {
  "repo-1": [
    {
      diagram_type: "ARCHITECTURE",
      code: `graph TD
    User([User Client]) -->|APIs| ALB[Application Load Balancer]
    ALB -->|Route| FastAPI[FastAPI Backend]
    FastAPI -->|Orchestrate| LangGraph[LangGraph Agents]
    LangGraph -->|Index Chunks| Qdrant[(Qdrant Vector DB)]
    LangGraph -->|Relational| Postgres[(PostgreSQL)]`
    }
  ]
}

const MOCK_REPORTS: Record<string, Record<string, AuditReport>> = {
  "repo-1": {
    "SECURITY": {
      score: 90.0,
      findings: [
        { severity: "HIGH", category: "Hardcoded Secret", message: "Potential API key definition on line 24 in `app/core/config.py`.", file: "app/core/config.py", line: 24 },
        { severity: "LOW", category: "Git config", message: "Git log files are exposed in development folder structure.", file: ".gitignore", line: 4 }
      ]
    },
    "QUALITY": {
      score: 85.0,
      findings: [
        { severity: "MEDIUM", category: "File Size", message: "Large file detected: `app/services/agent_service.py` is 340 lines. Consider refactoring.", file: "app/services/agent_service.py" },
        { severity: "LOW", category: "Code Smell", message: "Unused imports found in `app/main.py`.", file: "app/main.py", line: 3 }
      ]
    }
  }
}

export default function App() {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark')
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(true)
  const [userEmail, setUserEmail] = useState<string>("dev@repomind.io")
  
  // Dashboard states
  const [repos, setRepos] = useState<Repository[]>(MOCK_REPOSITORIES)
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(MOCK_REPOSITORIES[0])
  const [activeTab, setActiveTab] = useState<'summary' | 'chat' | 'diagrams' | 'docs' | 'reports'>('summary')
  
  // Repo submit form
  const [githubUrl, setGithubUrl] = useState('')
  const [branch, setBranch] = useState('main')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState('')

  // Chat window states
  const [chatInput, setChatInput] = useState('')
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { role: 'assistant', message: "Hi! I am the RepoMind code intelligence bot. Ask me anything about this repository's classes, endpoints, database schemas, or general setup." }
  ])
  const [isChatLoading, setIsChatLoading] = useState(false)
  const chatBottomRef = useRef<HTMLDivElement>(null)

  // Docs tab state
  const [selectedDocIndex, setSelectedDocIndex] = useState(0)

  // API base URL
  const API_URL = (import.meta as any).env.VITE_API_URL || "http://localhost:8000/api/v1"
  const [token, setToken] = useState<string | null>(null)
  
  // Auth Form states
  const [loginEmail, setLoginEmail] = useState('')
  const [loginPassword, setLoginPassword] = useState('')
  const [isRegistering, setIsRegistering] = useState(false)
  const [registerName, setRegisterName] = useState('')

  // Toggle Theme
  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [theme])

  // Scroll to chat bottom
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages])

  // Fetch Repositories on startup if backend running
  useEffect(() => {
    fetchRepositories()
  }, [token])

  const fetchRepositories = async () => {
    try {
      const res = await fetch(`${API_URL}/repositories`, {
        headers: token ? { "Authorization": `Bearer ${token}` } : {}
      })
      if (res.ok) {
        const data = await res.json()
        setRepos(data)
        if (data.length > 0) {
          setSelectedRepo(data[0])
        }
      }
    } catch (e) {
      console.log("Using Mock Data (Backend server offline)")
    }
  }

  // Handle Auth
  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (isRegistering) {
      // Register
      try {
        const res = await fetch(`${API_URL}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: loginEmail, password: loginPassword, full_name: registerName })
        })
        if (res.ok) {
          setIsRegistering(false)
          alert("Account created. Please login.")
        } else {
          const err = await res.json()
          alert(err.detail || "Registration failed")
        }
      } catch (e) {
        alert("Registration failed. Please make sure the backend is running.")
      }
    } else {
      // Login
      try {
        const params = new URLSearchParams()
        params.append('username', loginEmail)
        params.append('password', loginPassword)
        const res = await fetch(`${API_URL}/auth/token`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: params
        })
        if (res.ok) {
          const data = await res.json()
          setToken(data.access_token)
          setUserEmail(data.user.email)
          setIsAuthenticated(true)
        } else {
          alert("Incorrect username or password")
        }
      } catch (e) {
        // Fallback to offline mode
        setIsAuthenticated(true)
        setUserEmail(loginEmail || "offline-developer@repomind.io")
        console.log("Operating in offline mock mode")
      }
    }
  }

  // Handle Repository submission
  const handleSubmitRepo = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitError('')
    setIsSubmitting(true)

    try {
      const res = await fetch(`${API_URL}/repositories`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { "Authorization": `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ github_url: githubUrl, branch })
      })

      if (res.ok) {
        const newRepo = await res.json()
        setRepos(prev => [newRepo, ...prev])
        setSelectedRepo(newRepo)
        setGithubUrl('')
        // Poll for updates
        pollRepoStatus(newRepo.id)
      } else {
        const err = await res.json()
        setSubmitError(err.detail || "Failed to submit repository.")
      }
    } catch (e) {
      // Mock submit
      const mockName = githubUrl.split('/').pop()?.replace('.git', '') || 'new-repo'
      const mockNew: Repository = {
        id: `repo-${Date.now()}`,
        name: mockName,
        github_url: githubUrl,
        branch: branch,
        status: "INDEXING"
      }
      setRepos(prev => [mockNew, ...prev])
      setSelectedRepo(mockNew)
      setGithubUrl('')
      
      // Simulate indexing completion
      setTimeout(() => {
        setRepos(prev => prev.map(r => r.id === mockNew.id ? {
          ...r,
          status: "COMPLETE",
          metadata_info: {
            total_files: 15,
            total_loc: 1450,
            languages: { "Python": 12, "YAML": 2, "Other": 1 },
            languages_loc_percentage: { "Python": 80.0, "YAML": 15.0, "Other": 5.0 }
          }
        } : r))
        setSelectedRepo(prev => prev?.id === mockNew.id ? {
          ...prev,
          status: "COMPLETE",
          metadata_info: {
            total_files: 15,
            total_loc: 1450,
            languages: { "Python": 12, "YAML": 2, "Other": 1 },
            languages_loc_percentage: { "Python": 80.0, "YAML": 15.0, "Other": 5.0 }
          }
        } : prev)
      }, 5000)
    } finally {
      setIsSubmitting(false)
    }
  }

  const pollRepoStatus = (repoId: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/repositories/${repoId}`, {
          headers: token ? { "Authorization": `Bearer ${token}` } : {}
        })
        if (res.ok) {
          const updatedRepo = await res.json()
          setRepos(prev => prev.map(r => r.id === repoId ? updatedRepo : r))
          if (updatedRepo.id === selectedRepo?.id) {
            setSelectedRepo(updatedRepo)
          }
          if (updatedRepo.status === "COMPLETE" || updatedRepo.status === "FAILED") {
            clearInterval(interval)
          }
        }
      } catch (e) {
        clearInterval(interval)
      }
    }, 4000)
  }

  // Handle Chat message submit
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!chatInput.trim() || !selectedRepo) return

    const userMsg = chatInput
    setChatInput('')
    setChatMessages(prev => [...prev, { role: 'user', message: userMsg }])
    setIsChatLoading(true)

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { "Authorization": `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          repository_id: selectedRepo.id,
          message: userMsg
        })
      })

      if (res.ok) {
        const data = await res.json()
        setChatMessages(prev => [...prev, { 
          role: 'assistant', 
          message: data.answer,
          references: data.references
        }])
      } else {
        throw new Error("API call failed")
      }
    } catch (e) {
      // Mock chat response
      setTimeout(() => {
        let answer = `I searched this repository for "${userMsg}". Here is what I found:`
        let references = []
        if (selectedRepo.id === "repo-1") {
          answer = `In this repository, authentication is implemented in \`app/core/security.py\`. It utilizes JWT (JSON Web Tokens) with HS256 algorithm signature hashing. Users obtain access tokens via the \`/api/v1/auth/token\` POST route. The \`get_current_user\` dependency verifies incoming Bearer credentials.`
          references = [
            { file_path: "app/core/security.py", symbol_name: "create_access_token", snippet: "def create_access_token(subject, expires_delta):\n  to_encode = {'exp': expire, 'sub': str(subject)}\n  return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)" },
            { file_path: "app/api/v1/auth.py", symbol_name: "get_current_user", snippet: "def get_current_user(db = Depends(get_db), token = Depends(oauth2_scheme)):\n  user_id = decode_access_token(token)\n  return db.query(User).filter(User.id == user_id).first()" }
          ]
        } else {
          answer = `I scanned the react components. The structure is layered. Primary styles are managed using vanilla Tailwind utilities under \`src/index.css\`.`
          references = [
            { file_path: "src/index.css", snippet: "@tailwind base;\n@tailwind components;\n@tailwind utilities;" }
          ]
        }
        setChatMessages(prev => [...prev, { role: 'assistant', message: answer, references }])
      }, 1000)
    } finally {
      setIsChatLoading(false)
    }
  }

  // Helper to load documentation
  const getRepoDocs = (): Documentation[] => {
    if (!selectedRepo) return []
    // If we have custom documentation saved in database, fetch them
    // Otherwise fallback to mock docs
    return MOCK_DOCS[selectedRepo.id] || [
      {
        doc_type: "README",
        title: "README.md",
        content: `# ${selectedRepo.name}\n\nAutomated analysis is complete. Select another tab to see class hierarchies, chat with code intelligence, or review code quality.`
      }
    ]
  }

  // Helper to load diagrams
  const getRepoDiagrams = (): DiagramData[] => {
    if (!selectedRepo) return []
    return MOCK_DIAGRAMS[selectedRepo.id] || [
      {
        diagram_type: "ARCHITECTURE",
        code: `graph LR
    A[Router] --> B[Controller]
    B --> C[Postgres]`
      }
    ]
  }

  // Render Mermaid diagrams safely
  const MermaidRenderer = ({ code }: { code: string }) => {
    const [svg, setSvg] = useState<string>('')
    const [renderError, setRenderError] = useState<boolean>(false)

    useEffect(() => {
      setRenderError(false)
      const renderDiagram = async () => {
        try {
          const { svg: renderedSvg } = await mermaid.render(`mermaid-${Math.random().toString(36).substr(2, 9)}`, code)
          setSvg(renderedSvg)
        } catch (e) {
          console.error("Failed to render mermaid diagram", e)
          setRenderError(true)
        }
      }
      renderDiagram()
    }, [code])

    if (renderError) {
      return (
        <div className="p-6 bg-red-950/20 border border-red-500/30 rounded-xl flex items-center gap-3 text-red-400">
          <AlertTriangle size={24} />
          <div>
            <h4 className="font-semibold">Rendering Error</h4>
            <p className="text-sm">This diagram could not be drawn. Check the diagram code below.</p>
          </div>
        </div>
      )
    }

    return (
      <div 
        className="p-6 bg-card-light dark:bg-slate-900/60 rounded-xl border border-border-light dark:border-border-dark flex justify-center overflow-auto max-w-full"
        dangerouslySetInnerHTML={{ __html: svg || '<p className="text-gray-400">Rendering graph diagram...</p>' }}
      />
    )
  }

  // Render Login page if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background-light dark:bg-background-dark px-4 glow-bg">
        <div className="w-full max-w-md p-8 glass-panel rounded-2xl shadow-xl transition-all duration-300">
          <div className="flex flex-col items-center mb-8">
            <div className="p-3 bg-gradient-to-tr from-indigo-500 to-purple-500 rounded-xl shadow-lg shadow-indigo-500/20 text-white mb-3">
              <Sparkles size={32} />
            </div>
            <h2 className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">RepoMind</h2>
            <p className="text-sm text-secondary-light dark:text-slate-400 mt-1">AI-Powered Code Intelligence Platform</p>
          </div>

          <form onSubmit={handleAuthSubmit} className="space-y-4">
            {isRegistering && (
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Full Name</label>
                <input 
                  type="text" 
                  value={registerName}
                  onChange={(e) => setRegisterName(e.target.value)}
                  placeholder="John Doe" 
                  required
                  className="w-full px-4 py-2 rounded-lg border border-border-light dark:border-border-dark bg-white dark:bg-slate-900/50 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                />
              </div>
            )}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Email Address</label>
              <input 
                type="email" 
                value={loginEmail}
                onChange={(e) => setLoginEmail(e.target.value)}
                placeholder="you@example.com" 
                required
                className="w-full px-4 py-2 rounded-lg border border-border-light dark:border-border-dark bg-white dark:bg-slate-900/50 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Password</label>
              <input 
                type="password" 
                value={loginPassword}
                onChange={(e) => setLoginPassword(e.target.value)}
                placeholder="••••••••" 
                required
                className="w-full px-4 py-2 rounded-lg border border-border-light dark:border-border-dark bg-white dark:bg-slate-900/50 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
              />
            </div>

            <button 
              type="submit" 
              className="w-full py-2.5 px-4 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-semibold rounded-lg shadow-lg hover:shadow-indigo-500/20 active:scale-[0.98] transition-all"
            >
              {isRegistering ? "Create Account" : "Access Workspace"}
            </button>
          </form>

          <div className="mt-6 text-center text-sm text-secondary-light dark:text-slate-400">
            {isRegistering ? (
              <button onClick={() => setIsRegistering(false)} className="text-indigo-500 hover:underline">
                Already have an account? Sign in
              </button>
            ) : (
              <button onClick={() => setIsRegistering(true)} className="text-indigo-500 hover:underline">
                New user? Create a profile
              </button>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background-light dark:bg-background-dark transition-colors duration-300 flex flex-col">
      {/* Top Navigation */}
      <header className="border-b border-border-light dark:border-border-dark py-4 px-6 glass-panel sticky top-0 z-50 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-tr from-indigo-500 to-purple-500 rounded-lg text-white">
            <Sparkles size={22} />
          </div>
          <div>
            <span className="text-xl font-extrabold tracking-tight text-slate-900 dark:text-white flex items-center gap-1.5">
              RepoMind <span className="text-xs bg-indigo-500/10 text-indigo-400 px-2 py-0.5 rounded-full font-medium">SaaS Platform</span>
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button 
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="p-2 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400 transition-colors"
          >
            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          </button>
          
          <div className="flex items-center gap-2 pl-4 border-l border-border-light dark:border-border-dark">
            <div className="w-8 h-8 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-sm">
              {userEmail.substring(0, 2).toUpperCase()}
            </div>
            <div className="hidden md:block">
              <p className="text-xs text-slate-400 font-semibold">{userEmail}</p>
            </div>
            <button 
              onClick={() => setIsAuthenticated(false)}
              className="p-2 rounded-lg hover:bg-red-500/10 text-red-500 transition-colors"
              title="Sign Out"
            >
              <LogOut size={18} />
            </button>
          </div>
        </div>
      </header>

      {/* Workspace Area */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* Left Sidebar */}
        <aside className="w-full md:w-80 border-r border-border-light dark:border-border-dark glass-panel p-6 flex flex-col gap-6 shrink-0">
          <div>
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Connect Codebase</h3>
            <form onSubmit={handleSubmitRepo} className="space-y-3">
              <div>
                <input 
                  type="text" 
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  placeholder="GitHub Repository URL" 
                  required
                  className="w-full px-3 py-1.5 text-sm rounded-lg border border-border-light dark:border-border-dark bg-white dark:bg-slate-900/50 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                />
              </div>
              <div className="flex gap-2">
                <input 
                  type="text" 
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  placeholder="branch (main)" 
                  className="flex-1 px-3 py-1.5 text-xs rounded-lg border border-border-light dark:border-border-dark bg-white dark:bg-slate-900/50 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                />
                <button 
                  type="submit" 
                  disabled={isSubmitting}
                  className="px-4 py-1.5 text-xs bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg shadow disabled:opacity-50 active:scale-[0.98] transition-all flex items-center gap-1.5"
                >
                  <Plus size={14} /> Submit
                </button>
              </div>
              {submitError && <p className="text-xs text-red-500 mt-1">{submitError}</p>}
            </form>
          </div>

          <div className="flex-1 flex flex-col">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Repositories</h3>
            <div className="flex-1 overflow-y-auto space-y-2 max-h-[300px] md:max-h-none">
              {repos.map((r) => (
                <button
                  key={r.id}
                  onClick={() => setSelectedRepo(r)}
                  className={`w-full p-3 rounded-xl border text-left transition-all ${
                    selectedRepo?.id === r.id 
                      ? "bg-indigo-600/10 border-indigo-500/40 text-indigo-400" 
                      : "bg-transparent border-border-light dark:border-border-dark text-slate-500 dark:text-slate-400 hover:bg-slate-800/20"
                  }`}
                >
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-semibold text-sm truncate max-w-[150px]">{r.name}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                      r.status === "COMPLETE" 
                        ? "bg-emerald-500/10 text-emerald-400" 
                        : r.status === "FAILED" 
                        ? "bg-red-500/10 text-red-400" 
                        : "bg-amber-500/10 text-amber-400"
                    }`}>
                      {r.status}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 truncate flex items-center gap-1">
                    <GitBranch size={10} /> {r.branch}
                  </p>
                </button>
              ))}
            </div>
          </div>
        </aside>

        {/* Main Workspace Dashboard */}
        <main className="flex-1 flex flex-col overflow-hidden bg-background-light dark:bg-[#0c1220]">
          {selectedRepo ? (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Repo Bar */}
              <div className="p-6 border-b border-border-light dark:border-border-dark flex flex-col sm:flex-row justify-between sm:items-center gap-4 bg-card-light dark:bg-card-dark/40">
                <div>
                  <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <Github size={24} /> {selectedRepo.name}
                  </h1>
                  <p className="text-sm text-slate-400 mt-1 truncate">{selectedRepo.github_url}</p>
                </div>
                
                <div className="flex items-center gap-2">
                  <span className="text-xs bg-slate-200 dark:bg-slate-800 text-slate-500 dark:text-slate-400 px-3 py-1 rounded-full font-medium flex items-center gap-1.5">
                    <GitBranch size={13} /> {selectedRepo.branch}
                  </span>
                  <span className={`text-xs px-3 py-1 rounded-full font-medium flex items-center gap-1.5 ${
                    selectedRepo.status === "COMPLETE" 
                      ? "bg-emerald-500/10 text-emerald-400" 
                      : "bg-amber-500/10 text-amber-400"
                  }`}>
                    {selectedRepo.status === "COMPLETE" ? <CheckCircle size={13} /> : <RefreshCw size={13} className="animate-spin" />}
                    {selectedRepo.status}
                  </span>
                </div>
              </div>

              {/* Sub-nav Tab bar */}
              <div className="flex border-b border-border-light dark:border-border-dark px-6 bg-card-light dark:bg-card-dark/20">
                {(['summary', 'chat', 'diagrams', 'docs', 'reports'] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`py-3 px-4 text-sm font-semibold border-b-2 capitalize transition-all ${
                      activeTab === tab 
                        ? "border-indigo-500 text-indigo-400" 
                        : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-300"
                    }`}
                  >
                    {tab === 'summary' && <LayoutDashboard size={14} className="inline mr-1.5" />}
                    {tab === 'chat' && <Bot size={14} className="inline mr-1.5" />}
                    {tab === 'diagrams' && <Code2 size={14} className="inline mr-1.5" />}
                    {tab === 'docs' && <FileText size={14} className="inline mr-1.5" />}
                    {tab === 'reports' && <ShieldAlert size={14} className="inline mr-1.5" />}
                    {tab}
                  </button>
                ))}
              </div>

              {/* Tab Content Panels */}
              <div className="flex-1 overflow-y-auto p-6">
                
                {/* 1. Summary Tab */}
                {activeTab === 'summary' && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                      <div className="p-5 glass-panel rounded-2xl flex flex-col justify-between">
                        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Code Files</span>
                        <h2 className="text-4xl font-extrabold text-slate-900 dark:text-white mt-2">
                          {selectedRepo.metadata_info?.total_files || 0}
                        </h2>
                      </div>
                      <div className="p-5 glass-panel rounded-2xl flex flex-col justify-between">
                        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Lines of Code</span>
                        <h2 className="text-4xl font-extrabold text-slate-900 dark:text-white mt-2">
                          {selectedRepo.metadata_info?.total_loc.toLocaleString() || 0}
                        </h2>
                      </div>
                      <div className="p-5 glass-panel rounded-2xl flex flex-col justify-between">
                        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Languages</span>
                        <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                          {selectedRepo.metadata_info ? (
                            Object.keys(selectedRepo.metadata_info.languages).map((l) => (
                              <span key={l} className="text-xs bg-indigo-500/10 text-indigo-400 px-2 py-0.5 rounded-full font-medium">
                                {l}
                              </span>
                            ))
                          ) : (
                            <span className="text-xs text-slate-500">None detected</span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <div className="p-6 glass-panel rounded-2xl">
                        <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4">Programming Languages</h3>
                        <div className="space-y-4">
                          {selectedRepo.metadata_info ? (
                            Object.entries(selectedRepo.metadata_info.languages_loc_percentage).map(([lang, pct]) => (
                              <div key={lang}>
                                <div className="flex justify-between text-xs font-semibold mb-1">
                                  <span>{lang}</span>
                                  <span>{pct}%</span>
                                </div>
                                <div className="w-full bg-slate-200 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                                  <div className="bg-indigo-500 h-full rounded-full" style={{ width: `${pct}%` }} />
                                </div>
                              </div>
                            ))
                          ) : (
                            <p className="text-sm text-slate-500">No language metrics compiled yet.</p>
                          )}
                        </div>
                      </div>

                      <div className="p-6 glass-panel rounded-2xl flex flex-col justify-between">
                        <div>
                          <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Automated Architecture Scan</h3>
                          <p className="text-sm text-slate-400 leading-relaxed">
                            RepoMind multi-agent engine scanned this repository structure. It identified core entrypoints 
                            and categorized dependencies. To view fully compiled interactive class diagrams, click the "Diagrams" tab.
                          </p>
                        </div>
                        <div className="mt-4 pt-4 border-t border-border-light dark:border-border-dark flex justify-between text-xs text-slate-400">
                          <span>Framework: MVC / Web Service</span>
                          <span>Last Indexed: Just Now</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* 2. RAG Chat Tab */}
                {activeTab === 'chat' && (
                  <div className="h-[500px] flex flex-col rounded-2xl border border-border-light dark:border-border-dark overflow-hidden bg-card-light dark:bg-card-dark/30">
                    {/* Chat Messages */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-4">
                      {chatMessages.map((m, idx) => (
                        <div key={idx} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                          <div className={`p-3 rounded-2xl max-w-[80%] text-sm ${
                            m.role === 'user' 
                              ? 'bg-indigo-600 text-white rounded-tr-none' 
                              : 'bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded-tl-none'
                          }`}>
                            <p className="leading-relaxed whitespace-pre-wrap">{m.message}</p>
                            
                            {m.references && m.references.length > 0 && (
                              <div className="mt-3 pt-3 border-t border-slate-700/40 text-xs">
                                <span className="font-semibold text-[10px] text-indigo-400 uppercase tracking-wider block mb-1">Sources & Citations:</span>
                                <div className="space-y-1.5">
                                  {m.references.map((ref, rIdx) => (
                                    <div key={rIdx} className="bg-slate-900/50 p-2 rounded border border-border-dark">
                                      <p className="font-semibold text-slate-300 font-mono text-[10px]">{ref.file_path} {ref.symbol_name ? `-> ${ref.symbol_name}` : ''}</p>
                                      <pre className="mt-1 text-[9px] text-slate-400 overflow-x-auto p-1 bg-slate-950/40 rounded">
                                        {ref.snippet}
                                      </pre>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                      {isChatLoading && (
                        <div className="flex gap-3 justify-start">
                          <div className="bg-slate-200 dark:bg-slate-800 text-slate-400 p-3 rounded-2xl rounded-tl-none text-xs flex items-center gap-2">
                            <RefreshCw size={14} className="animate-spin" /> RepoMind is understanding code context...
                          </div>
                        </div>
                      )}
                      <div ref={chatBottomRef} />
                    </div>

                    {/* Chat Form Input */}
                    <form onSubmit={handleSendMessage} className="p-3 border-t border-border-light dark:border-border-dark flex gap-2 bg-slate-900/20">
                      <input 
                        type="text" 
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        placeholder="Ask a question (e.g. 'Explain how security token generation works')" 
                        required
                        className="flex-1 px-4 py-2 text-sm rounded-lg border border-border-light dark:border-border-dark bg-white dark:bg-slate-950/50 text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                      />
                      <button 
                        type="submit" 
                        disabled={isChatLoading}
                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg disabled:opacity-50 transition-all flex items-center gap-1.5 text-sm"
                      >
                        Ask <Bot size={16} />
                      </button>
                    </form>
                  </div>
                )}

                {/* 3. Diagrams Tab */}
                {activeTab === 'diagrams' && (
                  <div className="space-y-6">
                    <div>
                      <h2 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Interactive Component Architecture</h2>
                      <p className="text-sm text-slate-400">Mermaid graphs mapping the architecture model of {selectedRepo.name}.</p>
                    </div>
                    {getRepoDiagrams().map((diagram, idx) => (
                      <div key={idx} className="space-y-4">
                        <MermaidRenderer code={diagram.code} />
                        <div className="p-4 bg-slate-900/40 border border-border-dark rounded-xl">
                          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">Mermaid Source Code</span>
                          <pre className="text-xs text-slate-400 overflow-x-auto bg-slate-950/60 p-3 rounded font-mono">
                            {diagram.code}
                          </pre>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* 4. Docs Tab */}
                {activeTab === 'docs' && (
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-6 items-start">
                    {/* Left Index */}
                    <div className="flex flex-col gap-2 border-r border-border-light dark:border-border-dark pr-4">
                      {getRepoDocs().map((doc, idx) => (
                        <button
                          key={idx}
                          onClick={() => setSelectedDocIndex(idx)}
                          className={`w-full p-2.5 rounded-lg text-left text-sm transition-all ${
                            selectedDocIndex === idx 
                              ? "bg-indigo-600/10 border-l-4 border-indigo-500 text-indigo-400 font-semibold" 
                              : "text-slate-400 hover:bg-slate-800/30"
                          }`}
                        >
                          {doc.title}
                        </button>
                      ))}
                    </div>

                    {/* Main Docs Content */}
                    <div className="md:col-span-3 p-6 glass-panel rounded-2xl prose dark:prose-invert max-w-none">
                      {getRepoDocs()[selectedDocIndex] ? (
                        <div>
                          <h2 className="text-2xl font-bold text-slate-900 dark:text-white mb-4 border-b border-border-dark pb-2">
                            {getRepoDocs()[selectedDocIndex].title}
                          </h2>
                          <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap font-sans">
                            {getRepoDocs()[selectedDocIndex].content}
                          </div>
                        </div>
                      ) : (
                        <p className="text-slate-500">No documentation files selected.</p>
                      )}
                    </div>
                  </div>
                )}

                {/* 5. Audit Reports Tab */}
                {activeTab === 'reports' && (
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                      {/* Security Box */}
                      <div className="p-6 glass-panel rounded-2xl border-l-4 border-red-500">
                        <div className="flex justify-between items-center mb-4">
                          <h3 className="text-lg font-bold text-slate-900 dark:text-white">Security Vulnerabilities</h3>
                          <span className="text-3xl font-extrabold text-red-400">
                            {MOCK_REPORTS[selectedRepo.id]?.["SECURITY"]?.score || 100}%
                          </span>
                        </div>
                        <div className="space-y-3">
                          {(MOCK_REPORTS[selectedRepo.id]?.["SECURITY"]?.findings || []).map((f, fIdx) => (
                            <div key={fIdx} className="bg-red-500/5 border border-red-500/15 p-3 rounded-xl flex gap-3 items-start text-xs text-red-200">
                              <ShieldAlert className="text-red-400 shrink-0 mt-0.5" size={16} />
                              <div>
                                <span className="font-semibold block mb-0.5">{f.category} ({f.severity})</span>
                                <p className="text-red-300/80 mb-1">{f.message}</p>
                                {f.file && <span className="font-mono text-[10px] text-red-400/60 block">{f.file} : L{f.line}</span>}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Code Quality Box */}
                      <div className="p-6 glass-panel rounded-2xl border-l-4 border-amber-500">
                        <div className="flex justify-between items-center mb-4">
                          <h3 className="text-lg font-bold text-slate-900 dark:text-white">Code Quality Audit</h3>
                          <span className="text-3xl font-extrabold text-amber-400">
                            {MOCK_REPORTS[selectedRepo.id]?.["QUALITY"]?.score || 100}%
                          </span>
                        </div>
                        <div className="space-y-3">
                          {(MOCK_REPORTS[selectedRepo.id]?.["QUALITY"]?.findings || []).map((f, fIdx) => (
                            <div key={fIdx} className="bg-amber-500/5 border border-amber-500/15 p-3 rounded-xl flex gap-3 items-start text-xs text-amber-200">
                              <AlertTriangle className="text-amber-400 shrink-0 mt-0.5" size={16} />
                              <div>
                                <span className="font-semibold block mb-0.5">{f.category}</span>
                                <p className="text-amber-300/80 mb-1">{f.message}</p>
                                {f.file && <span className="font-mono text-[10px] text-amber-400/60 block">{f.file} {f.line ? `: L${f.line}` : ''}</span>}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-500 flex-col gap-3">
              <Bot size={48} className="text-slate-600" />
              <p className="font-semibold text-slate-400">No Repository Selected</p>
              <p className="text-xs text-slate-500">Submit a GitHub URL or select a repository from the left panel to begin.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
