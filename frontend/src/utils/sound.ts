/**
 * Programmatic sound effects via Web Audio API.
 * No external audio files required — all sounds are synthesized inline.
 *
 * Usage:
 *   import { playChipClink, playCardDeal, ... } from './sound';
 *   setSoundEnabled(false); // mute all
 */

let _ctx: AudioContext | null = null;
let _enabled = true;

export function setSoundEnabled(v: boolean): void {
  _enabled = v;
}

export function isSoundEnabled(): boolean {
  return _enabled;
}

/** Lazily initialise AudioContext (requires a prior user gesture in most browsers). */
function getCtx(): AudioContext | null {
  if (!_enabled) return null;
  try {
    if (!_ctx) _ctx = new AudioContext();
    // Resume if it was suspended (autoplay policy)
    if (_ctx.state === 'suspended') _ctx.resume();
    return _ctx;
  } catch {
    return null;
  }
}

/** Play a simple oscillator tone with exponential gain decay. */
function osc(
  freq: number,
  type: OscillatorType,
  duration: number,
  gain = 0.3,
  delayMs = 0,
): void {
  const c = getCtx();
  if (!c) return;
  try {
    const startTime = c.currentTime + delayMs / 1000;
    const o = c.createOscillator();
    const g = c.createGain();
    o.type = type;
    o.frequency.value = freq;
    g.gain.setValueAtTime(gain, startTime);
    g.gain.exponentialRampToValueAtTime(0.0001, startTime + duration);
    o.connect(g);
    g.connect(c.destination);
    o.start(startTime);
    o.stop(startTime + duration);
  } catch { /* swallow – never break the game for audio */ }
}

/** Short white-noise burst (card swish / deal sound). */
function noiseBurst(duration: number, gain = 0.12, delayMs = 0): void {
  const c = getCtx();
  if (!c) return;
  try {
    const startTime = c.currentTime + delayMs / 1000;
    const sampleRate = c.sampleRate;
    const frameCount = Math.ceil(sampleRate * duration);
    const buf = c.createBuffer(1, frameCount, sampleRate);
    const data = buf.getChannelData(0);
    for (let i = 0; i < frameCount; i++) data[i] = Math.random() * 2 - 1;

    const src = c.createBufferSource();
    const g = c.createGain();
    src.buffer = buf;
    g.gain.setValueAtTime(gain, startTime);
    g.gain.exponentialRampToValueAtTime(0.0001, startTime + duration);
    src.connect(g);
    g.connect(c.destination);
    src.start(startTime);
  } catch { /* swallow */ }
}

// ─── Public sound effects ──────────────────────────────────────────────────

/**
 * Chip clink — metallic double-ping.
 * Used when pot increases or when placing a bet/call.
 */
export function playChipClink(): void {
  osc(1200, 'sine', 0.12, 0.25);
  osc(900,  'sine', 0.09, 0.15, 40);
}

/**
 * Card deal — paper swish + soft low thud.
 * Used when community cards are revealed or a new hand starts.
 */
export function playCardDeal(): void {
  noiseBurst(0.055, 0.13);
  osc(280, 'triangle', 0.07, 0.12, 20);
}

/**
 * Your turn — ascending two-note chime (E5 → A5).
 * Used when `current_player_idx` switches to the human.
 */
export function playYourTurn(): void {
  osc(659, 'sine', 0.2, 0.22);
  osc(880, 'sine', 0.25, 0.28, 190);
}

/**
 * Win fanfare — ascending major-triad arpeggio (C5 → E5 → G5).
 * Used when the human player wins the hand.
 */
export function playWin(): void {
  osc(523, 'sine', 0.32, 0.30);
  osc(659, 'sine', 0.32, 0.30, 160);
  osc(784, 'sine', 0.38, 0.34, 320);
}

/**
 * Fold thud — low sawtooth decay.
 * Used when the human player folds.
 */
export function playFold(): void {
  osc(150, 'sawtooth', 0.18, 0.22);
  osc(100, 'triangle', 0.12, 0.15, 30);
}
