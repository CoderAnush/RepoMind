import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  Sparkles, FileText, GitBranch, ShieldCheck, BarChart2,
  MessageSquare, Layout, ArrowRight,
  Terminal, Network, Shield, Cpu, Lock
} from 'lucide-react';

export default function LandingPage() {

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.15 }
    }
  };

  const itemVariants = {
    hidden: { y: 30, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { type: 'spring' as const, stiffness: 100, damping: 15 }
    }
  };

  const features = [
    {
      icon: FileText,
      title: 'Documentation Generation',
      description: 'Automatically generate comprehensive READMEs, detailed API references, and step-by-step developer onboarding guides from your code.',
      color: 'from-violet-500 to-purple-500',
    },
    {
      icon: GitBranch,
      title: 'Architecture Analysis',
      description: 'Parse package dependencies, directory boundaries, and class relationships to map the entire architecture outline instantly.',
      color: 'from-cyan-500 to-blue-500',
    },
    {
      icon: ShieldCheck,
      title: 'Security Audits',
      description: 'Run deep scans for secrets exposure, dependency vulnerabilities, and code safety flaws with clear severity classifications.',
      color: 'from-emerald-500 to-teal-500',
    },
    {
      icon: BarChart2,
      title: 'Code Quality Reports',
      description: 'Analyze maintainability indices, cyclomatic complexity, code smells, and technical debt hotspots with concrete fixes.',
      color: 'from-amber-500 to-orange-500',
    },
    {
      icon: MessageSquare,
      title: 'AI Repository Chat',
      description: 'Engage in a context-aware conversation with your codebase. Ask about design flows, locate files, and draft code with citations.',
      color: 'from-pink-500 to-rose-500',
    },
    {
      icon: Layout,
      title: 'Diagram Generation',
      description: 'Render interactive system architectures, class relationships, sequence diagrams, and dependency flows powered by Mermaid.',
      color: 'from-indigo-500 to-purple-500',
    },
  ];

  const steps = [
    {
      step: '01',
      title: 'Submit Repository',
      description: 'Provide any public or private GitHub repository URL. Enter the branch name to get started.',
    },
    {
      step: '02',
      title: 'AI Analysis',
      description: 'Our pipeline clones, indexes, and creates semantic embeddings of your entire codebase within Qdrant.',
    },
    {
      step: '03',
      title: 'Generate Intelligence',
      description: 'RepoMind extracts technical documentation, computes complexity scores, audits security, and renders diagrams.',
    },
    {
      step: '04',
      title: 'Ask Questions',
      description: 'Engage in semantic repository chat, explore class flows, zoom diagrams, and copy generated markdown docs.',
    },
  ];

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 selection:bg-violet-500/30 selection:text-violet-200 overflow-x-hidden relative">
      {/* Background Grid Pattern */}
      <div className="absolute inset-0 bg-grid-pattern opacity-[0.4] pointer-events-none" />
      
      {/* Global Glow Gradients */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-violet-600/10 blur-[120px] pointer-events-none" />
      <div className="absolute top-[40%] right-[-10%] w-[50%] h-[50%] rounded-full bg-cyan-600/10 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[20%] w-[60%] h-[50%] rounded-full bg-purple-600/10 blur-[120px] pointer-events-none" />

      {/* Header */}
      <header className="sticky top-0 z-50 glass bg-zinc-950/80 border-b border-zinc-800/60">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
              <Sparkles size={16} className="text-white" />
            </div>
            <div>
              <span className="text-sm font-bold text-zinc-100 tracking-wider">RepoMind</span>
              <div className="text-[10px] text-zinc-500 font-medium leading-tight">AI Intelligence</div>
            </div>
          </Link>
          <div className="flex items-center gap-4">
            <Link to="/login" className="text-sm text-zinc-400 hover:text-zinc-100 transition-colors font-medium">
              Sign In
            </Link>
            <Link to="/login" className="btn-primary py-2 px-4 text-xs font-bold bg-violet-600 hover:bg-violet-500 shadow-md">
              Get Started <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-24 pb-20 px-6 max-w-7xl mx-auto flex flex-col items-center text-center">
        {/* Floating Code Snippets */}
        <motion.div
          animate={{ y: [0, -12, 0] }}
          transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute left-8 top-1/4 hidden lg:flex flex-col gap-2 p-4 glass rounded-xl w-60 text-left border border-zinc-800/80 bg-zinc-950/80 shadow-2xl glow-purple"
        >
          <div className="flex items-center gap-1.5 border-b border-zinc-800/80 pb-2 mb-2">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/80" />
            <div className="w-2.5 h-2.5 rounded-full bg-green-500/80" />
            <span className="text-[10px] text-zinc-500 ml-2 font-mono">analysis_job.py</span>
          </div>
          <code className="text-[11px] font-mono text-zinc-400 leading-normal">
            <span className="text-violet-400">async def</span> <span className="text-cyan-400">analyze_repo</span>(url):<br />
            &nbsp;&nbsp;repo = await clone(url)<br />
            &nbsp;&nbsp;ast = parse_syntax(repo)<br />
            &nbsp;&nbsp;<span className="text-emerald-400"># Embed to Qdrant</span><br />
            &nbsp;&nbsp;await index_vectors(ast)<br />
            &nbsp;&nbsp;return <span className="text-amber-400">"SUCCESS"</span>
          </code>
        </motion.div>

        <motion.div
          animate={{ y: [0, 12, 0] }}
          transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut', delay: 0.5 }}
          className="absolute right-8 top-1/3 hidden lg:flex flex-col gap-2 p-4 glass rounded-xl w-64 text-left border border-zinc-800/80 bg-zinc-950/80 shadow-2xl glow-cyan"
        >
          <div className="flex items-center justify-between border-b border-zinc-800/80 pb-2 mb-2">
            <span className="text-[10px] text-zinc-500 font-mono">Metrics Report</span>
            <div className="badge bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px]">A+ Grade</div>
          </div>
          <div className="space-y-2">
            <div>
              <div className="flex justify-between text-[11px] text-zinc-400 mb-1">
                <span>Security Score</span>
                <span className="text-emerald-400">100%</span>
              </div>
              <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-400 w-full" />
              </div>
            </div>
            <div>
              <div className="flex justify-between text-[11px] text-zinc-400 mb-1">
                <span>Maintainability</span>
                <span className="text-cyan-400">92%</span>
              </div>
              <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
                <div className="h-full bg-cyan-400 w-[92%]" />
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2.5 px-3 py-1.5 rounded-full bg-violet-500/10 border border-violet-500/20 text-xs font-semibold text-violet-400 mb-8"
        >
          <Sparkles size={13} className="animate-pulse" /> Introducing RepoMind v1.0
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="text-5xl md:text-7xl font-extrabold tracking-tight max-w-4xl text-balance mb-8"
        >
          Understand Any <span className="bg-gradient-to-r from-violet-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent">Codebase</span> in Minutes
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="text-zinc-400 text-lg md:text-xl max-w-2xl text-balance leading-relaxed mb-12"
        >
          AI-powered repository intelligence, documentation generation, architecture visualization, and semantic code search.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.45 }}
          className="flex flex-col sm:flex-row items-center gap-4 z-10"
        >
          <Link to="/login" className="btn-primary px-8 py-3.5 text-base font-bold bg-violet-600 hover:bg-violet-500 shadow-xl shadow-violet-500/20 hover:scale-[1.02]">
            Get Started Free <ArrowRight size={18} />
          </Link>
          <Link
            to="/login?github=true"
            className="btn-secondary px-8 py-3.5 text-base font-bold bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 hover:scale-[1.02] flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
            </svg>
            Sign In with GitHub
          </Link>
        </motion.div>
      </section>

      {/* Features Section */}
      <section className="py-24 px-6 max-w-7xl mx-auto border-t border-zinc-900">
        <div className="text-center mb-16">
          <h2 className="text-xs uppercase tracking-widest text-violet-400 font-bold mb-3">Core Capabilities</h2>
          <p className="text-3xl md:text-4xl font-extrabold">Supercharged Repository Intelligence</p>
          <p className="text-zinc-500 text-sm max-w-lg mx-auto mt-3">Everything you need to onboard developers, debug legacy codebases, and maintain top quality.</p>
        </div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-100px' }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {features.map((feat, idx) => {
            const Icon = feat.icon;
            return (
              <motion.div
                key={idx}
                variants={itemVariants}
                className="glass-card p-6 border-zinc-800 hover:border-violet-500/30 hover:bg-zinc-900/50 hover:shadow-glow-purple group transition-all duration-300 relative overflow-hidden"
              >
                {/* Gradient background hover glow */}
                <div className="absolute top-0 right-0 w-32 h-32 bg-violet-500/5 rounded-full blur-2xl group-hover:bg-violet-500/10 transition-colors pointer-events-none" />
                
                <div className="w-12 h-12 rounded-xl bg-zinc-800 flex items-center justify-center mb-5 group-hover:bg-violet-500/10 group-hover:text-violet-400 transition-colors">
                  <Icon size={24} className="text-zinc-300 transition-colors" />
                </div>
                <h3 className="text-lg font-bold mb-3 text-zinc-100 group-hover:text-white transition-colors">{feat.title}</h3>
                <p className="text-zinc-400 text-sm leading-relaxed">{feat.description}</p>
              </motion.div>
            );
          })}
        </motion.div>
      </section>

      {/* How It Works Section */}
      <section className="py-24 px-6 max-w-7xl mx-auto border-t border-zinc-900">
        <div className="text-center mb-20">
          <h2 className="text-xs uppercase tracking-widest text-cyan-400 font-bold mb-3">Workflow</h2>
          <p className="text-3xl md:text-4xl font-extrabold">Analyze and Understand in 4 Steps</p>
        </div>

        {/* Timeline */}
        <div className="relative">
          {/* Vertical connecting line */}
          <div className="absolute left-1/2 transform -translate-x-1/2 top-4 bottom-4 w-[1px] bg-zinc-800/80 hidden md:block" />
          
          <div className="space-y-12 md:space-y-24">
            {steps.map((step, idx) => {
              const isEven = idx % 2 === 0;
              return (
                <div key={idx} className={`flex flex-col md:flex-row items-center justify-between ${isEven ? '' : 'md:flex-row-reverse'}`}>
                  {/* Text side */}
                  <motion.div
                    initial={{ opacity: 0, x: isEven ? -40 : 40 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true, margin: '-100px' }}
                    transition={{ duration: 0.6 }}
                    className="w-full md:w-[45%] text-center md:text-left mb-6 md:mb-0"
                  >
                    <div className="flex items-center gap-3 justify-center md:justify-start mb-3">
                      <span className="text-xs font-mono px-2 py-0.5 bg-zinc-800 text-zinc-400 rounded-md border border-zinc-700">{step.step}</span>
                      <h3 className="text-xl font-bold">{step.title}</h3>
                    </div>
                    <p className="text-zinc-400 text-sm leading-relaxed max-w-md mx-auto md:mx-0">{step.description}</p>
                  </motion.div>

                  {/* Bullet center dot */}
                  <div className="w-10 h-10 rounded-full bg-zinc-900 border border-zinc-800 flex items-center justify-center relative z-10 shrink-0 shadow-lg shadow-zinc-950 hidden md:flex">
                    <div className="w-3.5 h-3.5 rounded-full bg-gradient-to-br from-violet-500 to-cyan-500 animate-pulse" />
                  </div>

                  {/* Graphic/Visual placeholder on other side */}
                  <motion.div
                    initial={{ opacity: 0, x: isEven ? 40 : -40 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true, margin: '-100px' }}
                    transition={{ duration: 0.6 }}
                    className="w-full md:w-[45%] flex justify-center"
                  >
                    <div className="w-full max-w-sm h-32 glass rounded-2xl flex items-center justify-center p-6 border border-zinc-800/80 relative overflow-hidden bg-zinc-900/30">
                      <div className="absolute inset-0 bg-gradient-to-br from-violet-500/5 to-cyan-500/5 opacity-50" />
                      {idx === 0 && (
                        <div className="flex items-center gap-3 w-full bg-zinc-950 p-3 rounded-lg border border-zinc-800 font-mono text-xs text-zinc-400 select-none">
                          <Terminal size={14} className="text-violet-400" />
                          <span>https://github.com/pypa/sampleproject</span>
                          <span className="ml-auto text-[10px] text-zinc-600">main</span>
                        </div>
                      )}
                      {idx === 1 && (
                        <div className="flex flex-col gap-2 items-center text-center">
                          <Cpu size={24} className="text-cyan-400 animate-spin-slow" />
                          <span className="text-xs text-zinc-500 font-semibold uppercase tracking-wider animate-pulse">Running AST Pipeline...</span>
                        </div>
                      )}
                      {idx === 2 && (
                        <div className="flex gap-4">
                          <div className="flex flex-col items-center bg-zinc-950/80 border border-zinc-800/60 p-2.5 rounded-lg w-20">
                            <FileText size={16} className="text-violet-400 mb-1" />
                            <span className="text-[10px] text-zinc-400 font-bold">Docs</span>
                          </div>
                          <div className="flex flex-col items-center bg-zinc-950/80 border border-zinc-800/60 p-2.5 rounded-lg w-20">
                            <Network size={16} className="text-cyan-400 mb-1" />
                            <span className="text-[10px] text-zinc-400 font-bold">Diagrams</span>
                          </div>
                          <div className="flex flex-col items-center bg-zinc-950/80 border border-zinc-800/60 p-2.5 rounded-lg w-20">
                            <Shield size={16} className="text-emerald-400 mb-1" />
                            <span className="text-[10px] text-zinc-400 font-bold">Security</span>
                          </div>
                        </div>
                      )}
                      {idx === 3 && (
                        <div className="w-full flex items-center gap-2 bg-zinc-950 border border-zinc-800 rounded-xl p-3 text-xs text-zinc-300">
                          <MessageSquare size={13} className="text-violet-400 shrink-0" />
                          <span className="truncate italic">"Explain the database schema here..."</span>
                          <span className="text-[10px] bg-violet-500/10 text-violet-400 border border-violet-500/20 px-1.5 py-0.5 rounded font-mono ml-auto">Ask</span>
                        </div>
                      )}
                    </div>
                  </motion.div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Architecture Showcase Section */}
      <section id="showcase" className="py-24 px-6 max-w-7xl mx-auto border-t border-zinc-900">
        <div className="text-center mb-16">
          <h2 className="text-xs uppercase tracking-widest text-emerald-400 font-bold mb-3">Showcase</h2>
          <p className="text-3xl md:text-4xl font-extrabold">Explore High-Fidelity Mockups</p>
          <p className="text-zinc-500 text-sm max-w-lg mx-auto mt-3">Interactive diagram renderers, security findings lists, and code architecture summaries.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Architecture Diagram preview */}
          <div className="glass-card border-zinc-800/80 p-6 flex flex-col h-full bg-zinc-900/40 relative overflow-hidden group">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-violet-500 to-transparent" />
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold text-violet-400 uppercase tracking-wider">Architecture Diagram</span>
              <span className="text-[10px] px-2 py-0.5 bg-violet-500/10 border border-violet-500/20 text-violet-400 rounded-md font-mono">Mermaid Flow</span>
            </div>
            
            {/* Mockup Canvas */}
            <div className="flex-1 rounded-xl bg-zinc-950 border border-zinc-800/80 p-4 font-mono text-[11px] text-zinc-400 h-64 overflow-y-auto mb-4 flex flex-col justify-center items-center">
              <div className="mermaid-wrapper w-full text-center space-y-3">
                <div className="inline-block p-2 rounded border border-zinc-800 bg-zinc-900/60 font-semibold text-zinc-300">FastAPI Router</div>
                <div className="h-6 w-[2px] bg-violet-500/50 mx-auto" />
                <div className="inline-block p-2 rounded border border-zinc-800 bg-zinc-900/60 font-semibold text-zinc-300">RAG Query Handler</div>
                <div className="h-6 w-[2px] bg-cyan-500/50 mx-auto" />
                <div className="inline-block p-2 rounded border border-violet-500/30 bg-violet-500/5 font-semibold text-violet-400">Qdrant Client</div>
              </div>
            </div>
            <p className="text-xs text-zinc-500 leading-normal">
              Dynamically maps modules, routing endpoints, and database interactions into an interactive diagram format.
            </p>
          </div>

          {/* Class Diagram preview */}
          <div className="glass-card border-zinc-800/80 p-6 flex flex-col h-full bg-zinc-900/40 relative overflow-hidden group">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-cyan-500 to-transparent" />
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold text-cyan-400 uppercase tracking-wider">Class Diagram</span>
              <span className="text-[10px] px-2 py-0.5 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 rounded-md font-mono">UML Format</span>
            </div>
            
            {/* Mockup Canvas */}
            <div className="flex-1 rounded-xl bg-zinc-950 border border-zinc-800/80 p-4 font-mono text-[11px] text-zinc-400 h-64 overflow-y-auto mb-4 flex flex-col justify-center">
              <div className="border border-zinc-800 bg-zinc-900/40 rounded p-2.5 mb-2.5">
                <div className="font-bold text-zinc-300 border-b border-zinc-800 pb-1 mb-1.5">class VectorDBService</div>
                <div className="text-[10px] text-zinc-500 space-y-0.5">
                  <div>+qdrant_client: QdrantClient</div>
                  <div>+collection_name: str</div>
                  <div className="border-t border-zinc-850 pt-1 mt-1 text-cyan-400">+get_collection_names()</div>
                  <div className="text-cyan-400">+upsert_embeddings()</div>
                </div>
              </div>
              <div className="border border-zinc-800 bg-zinc-900/40 rounded p-2.5">
                <div className="font-bold text-zinc-300 border-b border-zinc-800 pb-1 mb-1.5">class RAGService</div>
                <div className="text-[10px] text-zinc-500 space-y-0.5">
                  <div>+vector_db: VectorDBService</div>
                  <div className="border-t border-zinc-850 pt-1 mt-1 text-cyan-400">+query_repository()</div>
                </div>
              </div>
            </div>
            <p className="text-xs text-zinc-500 leading-normal">
              Extracts classes, inheritances, field properties, and public method signatures automatically from code structure.
            </p>
          </div>

          {/* Security Report preview */}
          <div className="glass-card border-zinc-800/80 p-6 flex flex-col h-full bg-zinc-900/40 relative overflow-hidden group">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-emerald-500 to-transparent" />
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Security Report</span>
              <span className="text-[10px] px-2 py-0.5 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-md font-mono">Audit Engine</span>
            </div>
            
            {/* Mockup Canvas */}
            <div className="flex-1 rounded-xl bg-zinc-950 border border-zinc-800/80 p-4 h-64 overflow-y-auto mb-4 space-y-2">
              <div className="flex items-center justify-between border-b border-zinc-900 pb-2">
                <span className="text-xs font-bold text-zinc-300">Security Score</span>
                <span className="text-xs font-mono font-bold text-emerald-400">95 / 100</span>
              </div>
              
              <div className="flex items-start gap-2 bg-red-500/5 border border-red-500/20 p-2 rounded-lg text-[10px]">
                <Lock size={12} className="text-red-400 shrink-0 mt-0.5" />
                <div>
                  <div className="font-bold text-zinc-200">Hardcoded Secrets Exposure</div>
                  <div className="text-zinc-500">Found connection string in app/core/config.py:L14</div>
                </div>
              </div>

              <div className="flex items-start gap-2 bg-yellow-500/5 border border-yellow-500/20 p-2 rounded-lg text-[10px]">
                <ShieldCheck size={12} className="text-yellow-400 shrink-0 mt-0.5" />
                <div>
                  <div className="font-bold text-zinc-200">Unencrypted Token Payload</div>
                  <div className="text-zinc-500">Verify algorithm constraints in auth.py:L22</div>
                </div>
              </div>
            </div>
            <p className="text-xs text-zinc-500 leading-normal">
              Continuously monitors code files for database credentials, token validation issues, and bad configuration practices.
            </p>
          </div>
        </div>
      </section>

      {/* CTA Footer Wrapper */}
      <section className="py-20 px-6 max-w-4xl mx-auto text-center border-t border-zinc-900">
        <h2 className="text-3xl font-extrabold mb-5">Ready to index your codebase?</h2>
        <p className="text-zinc-400 mb-8 max-w-lg mx-auto">Get full documentation, diagrams, security audits, and semantic code search on any GitHub repo.</p>
        <Link to="/login" className="btn-primary px-8 py-3.5 bg-violet-600 hover:bg-violet-500 shadow-lg">
          Get Started For Free <ArrowRight size={16} />
        </Link>
      </section>

      {/* Footer */}
      <footer className="bg-zinc-950 border-t border-zinc-900 py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
              <Sparkles size={12} className="text-white" />
            </div>
            <span className="text-xs font-bold text-zinc-300">RepoMind © 2026. All rights reserved.</span>
          </div>
          <div className="flex gap-6 text-xs text-zinc-500">
            <a href="#" className="hover:text-zinc-300 transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-zinc-300 transition-colors">Terms of Service</a>
            <a href="#" className="hover:text-zinc-300 transition-colors">Security docs</a>
            <a href="#" className="hover:text-zinc-300 transition-colors">Contact Support</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
