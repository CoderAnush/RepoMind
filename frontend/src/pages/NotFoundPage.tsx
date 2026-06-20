import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, HelpCircle, ArrowLeft } from 'lucide-react';

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col justify-between items-center relative overflow-hidden p-6 font-sans select-none">
      {/* Background Gradients */}
      <div className="absolute top-[20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-violet-600/10 blur-[130px] pointer-events-none" />
      <div className="absolute bottom-[20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-cyan-600/10 blur-[130px] pointer-events-none" />
      <div className="absolute inset-0 bg-grid-pattern opacity-[0.2] pointer-events-none" />

      {/* Top Header */}
      <div className="w-full max-w-7xl mx-auto flex items-center justify-between z-10 pt-4">
        <button onClick={() => navigate('/')} className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
            <Sparkles size={16} className="text-white" />
          </div>
          <div>
            <span className="text-sm font-bold text-zinc-100 tracking-wider">RepoMind</span>
            <div className="text-[10px] text-zinc-500 font-medium leading-tight">AI Intelligence</div>
          </div>
        </button>
      </div>

      {/* Main Content Card */}
      <div className="my-auto z-10 max-w-md w-full text-center space-y-6 px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="glass-card border-zinc-800 bg-zinc-900/30 p-8 flex flex-col items-center gap-4 relative overflow-hidden"
        >
          {/* Subtle Glow */}
          <div className="absolute top-0 right-0 w-24 h-24 bg-violet-500/5 rounded-full blur-xl pointer-events-none" />
          
          <div className="w-16 h-16 rounded-2xl bg-zinc-850 border border-zinc-800 flex items-center justify-center text-zinc-400 mb-2">
            <HelpCircle size={32} className="text-violet-400" />
          </div>

          <h1 className="text-5xl font-mono font-extrabold tracking-tight bg-gradient-to-b from-white to-zinc-400 bg-clip-text text-transparent">
            404
          </h1>
          
          <h2 className="text-lg font-bold text-zinc-200">
            Page Not Found
          </h2>

          <p className="text-zinc-500 text-xs leading-relaxed max-w-xs">
            The page you are looking for doesn't exist or has been moved. Check the URL or return to dashboard.
          </p>

          <button
            onClick={() => navigate('/dashboard')}
            className="btn-primary w-full py-2.5 justify-center font-bold text-xs bg-violet-600 hover:bg-violet-500 shadow-md flex items-center gap-1.5 mt-4"
          >
            <ArrowLeft size={14} /> Go to Dashboard
          </button>
        </motion.div>
      </div>

      {/* Footer Info */}
      <div className="text-[10px] text-zinc-600 z-10 pb-4">
        RepoMind Security & Reliability. All connections TLS-encrypted.
      </div>
    </div>
  );
}
