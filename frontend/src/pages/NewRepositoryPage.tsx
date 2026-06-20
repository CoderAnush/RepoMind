import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { repoService } from '../services/endpoints';
import { Sparkles, GitBranch, ArrowLeft, ArrowRight, Terminal, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function NewRepositoryPage() {
  const navigate = useNavigate();
  const [githubUrl, setGithubUrl] = useState('');
  const [branch, setBranch] = useState('main');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedRepoId, setSubmittedRepoId] = useState<string | null>(null);
  const [repoStatus, setRepoStatus] = useState<string>('PENDING');
  const [jobs, setJobs] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'url' | 'select'>('url');
  const [searchQuery, setSearchQuery] = useState('');
  const [githubRepos, setGithubRepos] = useState<any[]>([]);
  const [isFetchingRepos, setIsFetchingRepos] = useState(false);
  
  // Timer ref for polling
  const pollingRef = useRef<any>(null);

  useEffect(() => {
    if (activeTab !== 'select') return;
    
    const githubToken = localStorage.getItem('repomind_github_token');
    if (!githubToken || githubToken.startsWith('mock_')) {
      setGithubRepos([
        { name: 'octocat/Spoon-Knife', desc: 'Lurk in the shadows and fork this project.', url: 'https://github.com/octocat/Spoon-Knife.git', branch: 'main' },
        { name: 'octocat/hello-world', desc: 'My very first repository on GitHub.', url: 'https://github.com/octocat/hello-world.git', branch: 'master' },
        { name: 'octocat/git-consortium', desc: 'A repository to test git federation.', url: 'https://github.com/octocat/git-consortium.git', branch: 'master' },
        { name: 'octocat/boysenberry-app-demo', desc: 'An example Ruby app for testing.', url: 'https://github.com/octocat/boysenberry-app-demo.git', branch: 'master' },
        { name: 'octocat/Spoon-Knife-Backup', desc: 'Backup repository of Spoon-Knife.', url: 'https://github.com/octocat/Spoon-Knife.git', branch: 'main' }
      ]);
      return;
    }
    
    setIsFetchingRepos(true);
    fetch('https://api.github.com/user/repos?per_page=100&sort=updated', {
      headers: {
        'Authorization': `Bearer ${githubToken}`,
        'Accept': 'application/vnd.github.v3+json'
      }
    })
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch repositories');
        return res.json();
      })
      .then(data => {
        if (Array.isArray(data)) {
          const mapped = data.map((r: any) => ({
            name: r.full_name,
            desc: r.description || 'No description provided.',
            url: r.clone_url || r.html_url,
            branch: r.default_branch || 'main'
          }));
          setGithubRepos(mapped);
        }
      })
      .catch(err => {
        console.error(err);
        setGithubRepos([
          { name: 'octocat/Spoon-Knife', desc: 'Lurk in the shadows and fork this project.', url: 'https://github.com/octocat/Spoon-Knife.git', branch: 'main' },
          { name: 'octocat/hello-world', desc: 'My very first repository on GitHub.', url: 'https://github.com/octocat/hello-world.git', branch: 'master' },
          { name: 'octocat/git-consortium', desc: 'A repository to test git federation.', url: 'https://github.com/octocat/git-consortium.git', branch: 'master' },
          { name: 'octocat/boysenberry-app-demo', desc: 'An example Ruby app for testing.', url: 'https://github.com/octocat/boysenberry-app-demo.git', branch: 'master' },
          { name: 'octocat/Spoon-Knife-Backup', desc: 'Backup repository of Spoon-Knife.', url: 'https://github.com/octocat/Spoon-Knife.git', branch: 'main' }
        ]);
      })
      .finally(() => {
        setIsFetchingRepos(false);
      });
  }, [activeTab]);

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  const handleValidation = (url: string) => {
    if (!url.trim()) return 'GitHub URL is required';
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      return 'URL must start with http:// or https://';
    }
    if (!url.includes('github.com')) {
      return 'URL must be a valid github.com repository';
    }
    return null;
  };

  const startPolling = (repoId: string) => {
    if (pollingRef.current) clearInterval(pollingRef.current);

    pollingRef.current = setInterval(async () => {
      try {
        const repo = await repoService.get(repoId);
        setRepoStatus(repo.status);

        // Fetch jobs for granular steps
        try {
          const jobList = await repoService.jobs(repoId);
          setJobs(jobList);
        } catch {
          // Fallback if jobs is empty
        }

        if (repo.status === 'COMPLETE') {
          if (pollingRef.current) clearInterval(pollingRef.current);
          // Auto redirect to workspace overview
          setTimeout(() => {
            navigate(`/repositories/${repoId}`);
          }, 2000);
        } else if (repo.status === 'FAILED') {
          if (pollingRef.current) clearInterval(pollingRef.current);
          setError('Analysis pipeline failed. Please check repository public accessibility.');
          setIsSubmitting(false);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 3000);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const validationError = handleValidation(githubUrl);
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSubmitting(true);
    try {
      const repo = await repoService.submit({
        github_url: githubUrl.trim(),
        branch: branch.trim() || 'main'
      });
      setSubmittedRepoId(repo.id);
      setRepoStatus(repo.status);
      startPolling(repo.id);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to submit repository. Check if server is online.');
      setIsSubmitting(false);
    }
  };

  const handleSubmitDirect = async (url: string, targetBranch: string = 'main') => {
    setError(null);
    setIsSubmitting(true);
    try {
      const repo = await repoService.submit({
        github_url: url,
        branch: targetBranch
      });
      setSubmittedRepoId(repo.id);
      setRepoStatus(repo.status);
      startPolling(repo.id);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to submit repository. Check if server is online.');
      setIsSubmitting(false);
    }
  };

  // Steps tracking
  const currentStep = () => {
    if (repoStatus === 'PENDING') return 0;
    if (repoStatus === 'CLONING') return 1;
    if (repoStatus === 'INDEXING') return 2;
    if (repoStatus === 'COMPLETE') return 3;
    return 0;
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-8 bg-zinc-950 relative flex flex-col justify-center items-center">
      {/* Background glow effects */}
      <div className="absolute top-[20%] left-[20%] w-[40%] h-[40%] rounded-full bg-violet-600/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[20%] right-[10%] w-[35%] h-[35%] rounded-full bg-cyan-600/5 blur-[120px] pointer-events-none" />

      <div className="max-w-xl w-full">
        {/* Back Link */}
        <button
          onClick={() => navigate('/dashboard')}
          className="flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-300 transition-colors mb-6 focus:outline-none"
        >
          <ArrowLeft size={14} /> Back to Dashboard
        </button>

        <AnimatePresence mode="wait">
          {!submittedRepoId ? (
            <motion.div
              key="form-container"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              className="glass-card border-zinc-800/80 p-6 md:p-8 bg-zinc-900/40 relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-violet-500/5 rounded-full blur-2xl pointer-events-none" />
              
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400">
                  <GitBranch size={20} />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-zinc-100">Analyze New Repository</h1>
                  <p className="text-xs text-zinc-500 mt-0.5">Enter details to build diagrams & documents.</p>
                </div>
              </div>

              {error && (
                <div className="flex items-start gap-2.5 p-3.5 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400 mb-6">
                  <AlertCircle size={15} className="shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              {/* Tab Navigation */}
              <div className="flex border-b border-zinc-800/80 mb-6">
                <button
                  type="button"
                  onClick={() => setActiveTab('url')}
                  className={`flex-1 pb-3 text-xs font-bold border-b-2 transition-all flex items-center justify-center gap-2 ${
                    activeTab === 'url' ? 'border-violet-500 text-violet-400' : 'border-transparent text-zinc-500 hover:text-zinc-300'
                  }`}
                >
                  <GitBranch size={14} /> Paste GitHub URL
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('select')}
                  className={`flex-1 pb-3 text-xs font-bold border-b-2 transition-all flex items-center justify-center gap-2 ${
                    activeTab === 'select' ? 'border-violet-500 text-violet-400' : 'border-transparent text-zinc-500 hover:text-zinc-300'
                  }`}
                >
                  <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                  </svg>
                  Select Repository
                </button>
              </div>

              {activeTab === 'url' ? (
                <form onSubmit={handleSubmit} className="space-y-5">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-zinc-400" htmlFor="github-url">
                      GitHub Repository URL
                    </label>
                    <input
                      id="github-url"
                      type="text"
                      required
                      placeholder="https://github.com/username/repository"
                      value={githubUrl}
                      onChange={(e) => setGithubUrl(e.target.value)}
                      className="input-field"
                      disabled={isSubmitting}
                    />
                    <p className="text-[10px] text-zinc-500">Provide public repositories or authorized connection paths.</p>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-zinc-400" htmlFor="branch">
                      Target Git Branch
                    </label>
                    <input
                      id="branch"
                      type="text"
                      required
                      placeholder="main"
                      value={branch}
                      onChange={(e) => setBranch(e.target.value)}
                      className="input-field font-mono"
                      disabled={isSubmitting}
                    />
                    <p className="text-[10px] text-zinc-500">Defaults to main. Ensure the branch exists on remote.</p>
                  </div>

                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="btn-primary w-full py-3 justify-center text-sm font-bold bg-violet-600 hover:bg-violet-500 shadow-md shadow-violet-500/10 flex items-center gap-2 mt-8"
                  >
                    {isSubmitting ? (
                      <>
                        <RefreshCw size={15} className="animate-spin" /> Submitting Workspace...
                      </>
                    ) : (
                      <>
                        Analyze Repository <ArrowRight size={15} />
                      </>
                    )}
                  </button>
                </form>
              ) : (
                <div className="space-y-4">
                  <input
                    type="text"
                    placeholder="Search repositories..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="input-field text-xs py-2 px-3 mb-2"
                  />
                  <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
                    {isFetchingRepos ? (
                      <div className="flex flex-col items-center justify-center py-12 gap-3">
                        <RefreshCw size={24} className="text-violet-400 animate-spin" />
                        <span className="text-xs text-zinc-500 font-medium">Fetching repositories from GitHub...</span>
                      </div>
                    ) : githubRepos.length === 0 ? (
                      <div className="text-center py-12 text-xs text-zinc-500">
                        No repositories found.
                      </div>
                    ) : (
                      githubRepos
                        .filter(r => 
                          r.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          r.desc.toLowerCase().includes(searchQuery.toLowerCase())
                        )
                        .map((repo, idx) => (
                          <div key={idx} className="flex items-center justify-between p-3 rounded-lg border border-zinc-800/80 bg-zinc-950/40 hover:border-zinc-700/80 hover:bg-zinc-900/30 transition-all">
                            <div className="space-y-1 text-left min-w-0 flex-1 pr-3">
                              <div className="text-xs font-bold text-zinc-200 flex items-center gap-1.5 truncate">
                                <svg className="w-3.5 h-3.5 text-zinc-400 shrink-0" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                                  <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                                </svg>
                                <span className="truncate">{repo.name}</span>
                                <span className="text-[9px] px-1 bg-zinc-800 text-zinc-500 font-mono rounded shrink-0">{repo.branch}</span>
                              </div>
                              <div className="text-[10px] text-zinc-500 truncate">{repo.desc}</div>
                            </div>
                            <button
                              type="button"
                              onClick={() => handleSubmitDirect(repo.url, repo.branch || 'main')}
                              className="btn-primary py-1.5 px-3 text-[10px] bg-violet-600 hover:bg-violet-500 font-bold flex items-center gap-1 shrink-0"
                            >
                              Import
                            </button>
                          </div>
                        ))
                    )}
                  </div>
                </div>
              )}
            </motion.div>
          ) : (
            <motion.div
              key="loader-container"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="glass-card border-zinc-800/80 p-6 md:p-8 bg-zinc-900/40 relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/5 rounded-full blur-2xl pointer-events-none" />

              <div className="text-center mb-8">
                <Sparkles size={28} className="text-violet-400 mx-auto animate-pulse mb-3" />
                <h2 className="text-lg font-bold text-zinc-200">Repository Analysis Queue</h2>
                <p className="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">Please wait while RepoMind indexes, generates vector embeddings, and structures diagrams.</p>
              </div>

              {/* Progress Stepper */}
              <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-[1px] before:bg-zinc-800">
                {/* Step 1 */}
                <div className="relative flex gap-4">
                  <div className={`absolute -left-[22px] w-3 h-3 rounded-full border ${
                    currentStep() >= 0 ? 'bg-violet-500 border-violet-500' : 'bg-zinc-950 border-zinc-700'
                  }`} />
                  <div>
                    <h3 className={`text-xs font-bold ${currentStep() >= 0 ? 'text-zinc-200' : 'text-zinc-500'}`}>
                      1. Submitting to pipeline
                    </h3>
                    <p className="text-[10px] text-zinc-500 mt-0.5">Creating workspace tracking session.</p>
                  </div>
                  {currentStep() === 0 && <RefreshCw size={12} className="text-violet-400 animate-spin ml-auto mt-0.5" />}
                  {currentStep() > 0 && <CheckCircle2 size={13} className="text-emerald-400 ml-auto mt-0.5" />}
                </div>

                {/* Step 2 */}
                <div className="relative flex gap-4">
                  <div className={`absolute -left-[22px] w-3 h-3 rounded-full border ${
                    currentStep() >= 1 ? 'bg-violet-500 border-violet-500' : 'bg-zinc-950 border-zinc-700'
                  }`} />
                  <div>
                    <h3 className={`text-xs font-bold ${currentStep() >= 1 ? 'text-zinc-200' : 'text-zinc-500'}`}>
                      2. Cloning Codebase
                    </h3>
                    <p className="text-[10px] text-zinc-500 mt-0.5">Fetching git objects and source tree.</p>
                  </div>
                  {currentStep() === 1 && <RefreshCw size={12} className="text-violet-400 animate-spin ml-auto mt-0.5" />}
                  {currentStep() > 1 && <CheckCircle2 size={13} className="text-emerald-400 ml-auto mt-0.5" />}
                </div>

                {/* Step 3 */}
                <div className="relative flex gap-4">
                  <div className={`absolute -left-[22px] w-3 h-3 rounded-full border ${
                    currentStep() >= 2 ? 'bg-violet-500 border-violet-500' : 'bg-zinc-950 border-zinc-700'
                  }`} />
                  <div>
                    <h3 className={`text-xs font-bold ${currentStep() >= 2 ? 'text-zinc-200' : 'text-zinc-500'}`}>
                      3. Parser AST & Qdrant Indexing
                    </h3>
                    <p className="text-[10px] text-zinc-500 mt-0.5">Analyzing classes, dependencies, and generating embeddings.</p>
                  </div>
                  {currentStep() === 2 && <RefreshCw size={12} className="text-violet-400 animate-spin ml-auto mt-0.5" />}
                  {currentStep() > 2 && <CheckCircle2 size={13} className="text-emerald-400 ml-auto mt-0.5" />}
                </div>

                {/* Step 4 */}
                <div className="relative flex gap-4">
                  <div className={`absolute -left-[22px] w-3 h-3 rounded-full border ${
                    currentStep() >= 3 ? 'bg-violet-500 border-violet-500' : 'bg-zinc-950 border-zinc-700'
                  }`} />
                  <div>
                    <h3 className={`text-xs font-bold ${currentStep() >= 3 ? 'text-zinc-200' : 'text-zinc-500'}`}>
                      4. Completing Generation
                    </h3>
                    <p className="text-[10px] text-zinc-500 mt-0.5">Seeding default documentation references and diagrams.</p>
                  </div>
                  {currentStep() === 3 && <CheckCircle2 size={13} className="text-emerald-400 ml-auto mt-0.5" />}
                </div>
              </div>

              {/* Progress bar */}
              <div className="mt-8">
                <div className="progress-bar">
                  <div
                    className="progress-fill-purple"
                    style={{ width: `${(currentStep() / 3) * 100}%` }}
                  />
                </div>
              </div>

              {/* Jobs detail logs */}
              {jobs.length > 0 && (
                <div className="mt-6 border border-zinc-800/80 bg-zinc-950 rounded-lg p-3">
                  <div className="flex items-center gap-1.5 border-b border-zinc-800/60 pb-1.5 mb-2 font-mono text-[9px] text-zinc-500">
                    <Terminal size={11} /> <span>Pipeline Engine Logs</span>
                  </div>
                  <div className="font-mono text-[10px] text-zinc-400 space-y-1 max-h-32 overflow-y-auto">
                    {jobs.map((job, idx) => (
                      <div key={idx} className="flex justify-between">
                        <span>&gt; Step: {job.step} ({job.status})</span>
                        {job.error_message && <span className="text-red-400 font-sans font-bold">Error: {job.error_message}</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Manual navigation fallback */}
              {repoStatus === 'COMPLETE' && (
                <div className="mt-8 flex justify-center">
                  <button
                    onClick={() => navigate(`/repositories/${submittedRepoId}`)}
                    className="btn-primary py-2 px-4 text-xs font-bold bg-violet-600 hover:bg-violet-500"
                  >
                    Go to Workspace Details <ArrowRight size={14} />
                  </button>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
