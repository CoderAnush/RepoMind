import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { authService } from '../services/endpoints';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Mail, Lock, User as UserIcon, ArrowRight, CheckCircle2, AlertCircle } from 'lucide-react';

export default function LoginPage() {
  const { login, register, loginWithGitHub, isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Redirect if already authenticated
  const from = (location.state as any)?.from?.pathname || '/dashboard';
  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, authLoading, navigate, from]);

  // Handle GitHub OAuth callback code or auto-trigger from landing page
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const code = params.get('code');
    const github = params.get('github');
    if (code) {
      setLoading(true);
      setError(null);
      loginWithGitHub(code)
        .then(() => {
          navigate(from, { replace: true });
        })
        .catch((err: any) => {
          console.error(err);
          setError(err.response?.data?.detail || err.message || 'GitHub Authentication failed.');
        })
        .finally(() => {
          setLoading(false);
        });
    } else if (github === 'true') {
      setError(null);
      setLoading(true);
      const redirectUri = `${window.location.origin}/login`;
      authService.getGitHubUrl(redirectUri)
        .then((authData) => {
          window.location.href = authData.url;
        })
        .catch((err: any) => {
          console.error(err);
          setError('Failed to initiate GitHub OAuth login.');
          setLoading(false);
        });
    }
  }, [location.search, loginWithGitHub, navigate, from]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isLogin) {
        await login(email, password);
        navigate(from, { replace: true });
      } else {
        if (!fullName.trim()) {
          throw new Error('Please enter your full name');
        }
        await register(email, password, fullName);
        // Automatically login after registration
        await login(email, password);
        navigate(from, { replace: true });
      }
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async () => {
    setError(null);
    setLoading(true);
    try {
      await login('demo@repomind.io', 'demouser123!');
      navigate(from, { replace: true });
    } catch (err: any) {
      console.error(err);
      setError('Failed to log in with demo account.');
    } finally {
      setLoading(false);
    }
  };

  const handleGitHubLogin = async () => {
    setError(null);
    setLoading(true);
    try {
      const redirectUri = `${window.location.origin}/login`;
      const authData = await authService.getGitHubUrl(redirectUri);
      window.location.href = authData.url;
    } catch (err: any) {
      console.error(err);
      setError('Failed to initiate GitHub OAuth login.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 flex overflow-hidden relative">
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 bg-grid-pattern opacity-[0.2] pointer-events-none" />

      {/* Split screen Left Side: Illustration / Brand Info */}
      <div className="hidden lg:flex lg:w-1/2 bg-zinc-950 border-r border-zinc-900 flex-col justify-between p-12 relative overflow-hidden">
        {/* Glow */}
        <div className="absolute top-[20%] left-[-10%] w-[80%] h-[50%] rounded-full bg-violet-600/10 blur-[130px] pointer-events-none" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[50%] rounded-full bg-cyan-600/10 blur-[120px] pointer-events-none" />

        {/* Top Brand Link */}
        <div className="flex items-center gap-2.5 z-10">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
            <Sparkles size={16} className="text-white" />
          </div>
          <div>
            <span className="text-sm font-bold text-zinc-100 tracking-wider">RepoMind</span>
            <div className="text-[10px] text-zinc-500 font-medium leading-tight">AI Intelligence</div>
          </div>
        </div>

        {/* Feature Checklists */}
        <div className="my-auto space-y-8 z-10 max-w-lg">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h1 className="text-4xl font-extrabold tracking-tight text-white mb-4 leading-tight">
              Deep Code Analysis & Visual Insights
            </h1>
            <p className="text-zinc-400 text-sm leading-relaxed">
              Unlock the blueprint of your repositories. RepoMind parses structure, checks security compliance, logs complexity charts, and handles RAG conversation.
            </p>
          </motion.div>

          <div className="space-y-4">
            {[
              'Interactive Class & Dependency diagrams',
              'SaaS Security audit & Code smell scoring',
              'RAG-powered repository AI search & chat',
              'Step-by-step developer onboarding guides'
            ].map((text, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.4, delay: 0.2 + idx * 0.1 }}
                className="flex items-center gap-3 text-sm text-zinc-300"
              >
                <CheckCircle2 size={16} className="text-violet-400 shrink-0" />
                <span>{text}</span>
              </motion.div>
            ))}
          </div>

          {/* Mini Mockup */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="glass-card p-4 border-zinc-800 bg-zinc-900/30 w-full"
          >
            <div className="flex items-center justify-between border-b border-zinc-800/80 pb-2 mb-3">
              <span className="text-[10px] text-zinc-500 font-mono">Qdrant Vector Database</span>
              <span className="badge-purple text-[9px] px-1.5 py-0.5">Connected</span>
            </div>
            <div className="space-y-1.5 font-mono text-[10px] text-zinc-500">
              <div>&gt; Loading file parser AST model...</div>
              <div className="text-cyan-400">&gt; Embeddings generated successfully (788 vectors)</div>
              <div className="text-emerald-400">&gt; Index status: READY</div>
            </div>
          </motion.div>
        </div>

        {/* Footer info */}
        <div className="text-xs text-zinc-600 z-10">
          RepoMind Security Compliance. ES256 and OAuth2 Authorized.
        </div>
      </div>

      {/* Split screen Right Side: Form */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center px-6 sm:px-12 md:px-20 lg:px-24 py-12 relative">
        {/* Mobile Logo */}
        <div className="flex lg:hidden items-center gap-2.5 mb-12 absolute top-6 left-6">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
            <Sparkles size={14} className="text-white" />
          </div>
          <span className="text-xs font-bold text-zinc-200 uppercase tracking-wider">RepoMind</span>
        </div>

        <div className="max-w-md w-full mx-auto space-y-8 relative z-10">
          {/* Header */}
          <div className="text-left">
            <h2 className="text-3xl font-extrabold text-white">
              {isLogin ? 'Sign in to platform' : 'Create your account'}
            </h2>
            <p className="text-zinc-500 text-sm mt-2">
              {isLogin ? "Don't have an account? " : 'Already have an account? '}
              <button
                type="button"
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError(null);
                }}
                className="text-violet-400 hover:text-violet-300 font-semibold focus:outline-none transition-colors"
              >
                {isLogin ? 'Sign up' : 'Sign in'}
              </button>
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <AnimatePresence mode="wait">
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="flex items-start gap-2.5 p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400"
                >
                  <AlertCircle size={15} className="shrink-0 mt-0.5" />
                  <span>{error}</span>
                </motion.div>
              )}
            </AnimatePresence>

            {!isLogin && (
              <div className="space-y-1">
                <label className="text-xs font-semibold text-zinc-400" htmlFor="name">
                  Full Name
                </label>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500">
                    <UserIcon size={16} />
                  </span>
                  <input
                    id="name"
                    type="text"
                    required
                    placeholder="Jane Doe"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="input-field pl-10"
                  />
                </div>
              </div>
            )}

            <div className="space-y-1">
              <label className="text-xs font-semibold text-zinc-400" htmlFor="email">
                Email Address
              </label>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500">
                  <Mail size={16} />
                </span>
                <input
                  id="email"
                  type="email"
                  required
                  placeholder="name@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input-field pl-10"
                />
              </div>
            </div>

            <div className="space-y-1">
              <div className="flex justify-between items-center">
                <label className="text-xs font-semibold text-zinc-400" htmlFor="password">
                  Password
                </label>
              </div>
              <div className="relative">
                <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500">
                  <Lock size={16} />
                </span>
                <input
                  id="password"
                  type="password"
                  required
                  placeholder="Min. 6 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input-field pl-10"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3 justify-center font-bold text-sm bg-violet-600 hover:bg-violet-500 shadow-md flex items-center gap-2 mt-6"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  {isLogin ? 'Sign In' : 'Create Account'}
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </form>

          {/* GitHub Button */}
          <button
            type="button"
            onClick={handleGitHubLogin}
            disabled={loading}
            className="w-full py-3 px-4 border border-zinc-800 hover:border-zinc-700 bg-zinc-900/50 hover:bg-zinc-900 text-zinc-100 rounded-lg font-bold text-sm flex items-center justify-center gap-2.5 transition-all shadow-sm"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
            </svg>
            Continue with GitHub
          </button>

          {/* Divider */}
          <div className="flex items-center gap-3 my-6">
            <div className="h-[1px] bg-zinc-800 flex-1" />
            <span className="text-[10px] text-zinc-500 uppercase tracking-widest font-bold">Or Demo Session</span>
            <div className="h-[1px] bg-zinc-800 flex-1" />
          </div>

          {/* Demo Button */}
          <button
            type="button"
            onClick={handleDemoLogin}
            disabled={loading}
            className="btn-secondary w-full py-3 justify-center font-bold text-sm bg-zinc-900 border border-zinc-800 hover:bg-zinc-800/80 transition-all"
          >
            Explore Demo Environment
          </button>
        </div>
      </div>
    </div>
  );
}
