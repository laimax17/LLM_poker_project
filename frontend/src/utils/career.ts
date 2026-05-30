// Career progression & persistence (local, single-player) via localStorage.

const STORAGE_KEY = 'cyberholdem_career_v1';

export interface TournamentResult {
  date: number;
  place: number;
  totalPlayers: number;
  won: boolean;
}

export interface CareerStats {
  played: number;
  wins: number;
  podiums: number;       // top-3 finishes (in 4+ player events)
  bestPlace: number | null;
  avgPlace: number | null;
  winRate: number;       // 0..1
}

export interface Achievement {
  id: string;
  label: string;
  desc: string;
  unlocked: boolean;
}

export function getResults(): TournamentResult[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as TournamentResult[]) : [];
  } catch {
    return [];
  }
}

export function addResult(result: TournamentResult): TournamentResult[] {
  const results = getResults();
  results.push(result);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(results));
  } catch {
    /* ignore quota errors */
  }
  return results;
}

export function clearCareer(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* ignore */
  }
}

export function computeStats(results: TournamentResult[]): CareerStats {
  const played = results.length;
  if (played === 0) {
    return { played: 0, wins: 0, podiums: 0, bestPlace: null, avgPlace: null, winRate: 0 };
  }
  const wins = results.filter((r) => r.won).length;
  const podiums = results.filter((r) => r.place <= 3 && r.totalPlayers >= 4).length;
  const bestPlace = Math.min(...results.map((r) => r.place));
  const avgPlace = results.reduce((s, r) => s + r.place, 0) / played;
  return { played, wins, podiums, bestPlace, avgPlace, winRate: wins / played };
}

// Achievement definitions, keyed by id; `test` decides unlock from history.
const ACHIEVEMENTS: { id: string; label: string; desc: string; test: (r: TournamentResult[]) => boolean }[] = [
  { id: 'first_blood', label: '🏆 First Blood', desc: 'Win your first tournament', test: (r) => r.some((x) => x.won) },
  { id: 'hat_trick', label: '🎩 Hat Trick', desc: 'Win 3 tournaments', test: (r) => r.filter((x) => x.won).length >= 3 },
  { id: 'giant_slayer', label: '⚔ Giant Slayer', desc: 'Win a full 6-player table', test: (r) => r.some((x) => x.won && x.totalPlayers >= 6) },
  { id: 'heads_up', label: '🤝 Heads-Up Hero', desc: 'Reach heads-up (top 2)', test: (r) => r.some((x) => x.place <= 2) },
  { id: 'podium', label: '🥉 On the Podium', desc: 'Finish top 3 in a 4+ player event', test: (r) => r.some((x) => x.place <= 3 && x.totalPlayers >= 4) },
  { id: 'grinder', label: '⛏ Grinder', desc: 'Play 10 tournaments', test: (r) => r.length >= 10 },
];

export function getAchievements(results: TournamentResult[]): Achievement[] {
  return ACHIEVEMENTS.map((a) => ({
    id: a.id,
    label: a.label,
    desc: a.desc,
    unlocked: a.test(results),
  }));
}
