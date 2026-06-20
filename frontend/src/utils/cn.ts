import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toString();
}

export function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    const mins = Math.floor(diff / 60_000);
    const hours = Math.floor(diff / 3_600_000);
    const days = Math.floor(diff / 86_400_000);

    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return 'Unknown';
  }
}

export function getStatusColor(status: string): string {
  switch (status?.toUpperCase()) {
    case 'COMPLETE': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    case 'FAILED': return 'text-red-400 bg-red-500/10 border-red-500/20';
    case 'PENDING': return 'text-zinc-400 bg-zinc-800 border-zinc-700';
    default: return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
  }
}

export function getSeverityColor(severity: string): string {
  switch (severity?.toUpperCase()) {
    case 'CRITICAL': return 'text-red-400 bg-red-500/10 border-red-500/20';
    case 'HIGH': return 'text-orange-400 bg-orange-500/10 border-orange-500/20';
    case 'MEDIUM': return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
    case 'LOW': return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
    case 'INFO': return 'text-zinc-400 bg-zinc-800 border-zinc-700';
    default: return 'text-zinc-400 bg-zinc-800 border-zinc-700';
  }
}

export function getScoreColor(score: number): string {
  if (score >= 90) return 'text-emerald-400';
  if (score >= 70) return 'text-amber-400';
  return 'text-red-400';
}

export function getLanguageColor(lang: string): string {
  const colors: Record<string, string> = {
    'Python': '#3572A5',
    'TypeScript': '#2b7489',
    'JavaScript': '#f1e05a',
    'React TypeScript': '#61dafb',
    'Go': '#00ADD8',
    'Rust': '#dea584',
    'Java': '#b07219',
    'C++': '#f34b7d',
    'Ruby': '#701516',
    'CSS': '#563d7c',
    'HTML': '#e34c26',
    'YAML': '#cb171e',
    'SQL': '#e38c00',
    'Shell Script': '#89e051',
    'Markdown': '#083fa1',
  };
  return colors[lang] || '#6e7681';
}

export function extractRepoName(url: string): string {
  try {
    const parts = url.replace(/\.git$/, '').split('/');
    return parts[parts.length - 1] || url;
  } catch {
    return url;
  }
}
