/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg:               'var(--bg)',
        surface:          'var(--surface)',
        surface2:         'var(--surface2)',
        'felt-c':         'var(--felt-c)',
        'felt-e':         'var(--felt-e)',
        gold:             'var(--gold)',
        'gold-l':         'var(--gold-l)',
        'gold-d':         'var(--gold-d)',
        brown:            'var(--brown)',
        red:              'var(--red)',
        black:            'var(--black)',
        'green-ok':       'var(--green-ok)',
        'yellow-hot':     'var(--yellow-hot)',
        'red-bad':        'var(--red-bad)',
        'card-bg':        'var(--card-bg)',
        'card-border':    'var(--card-border)',
        'card-back-bg':   'var(--card-back-bg)',
        'card-back-border':'var(--card-back-border)',
      },
      fontFamily: {
        rank:  ['Georgia', "'Times New Roman'", 'serif'],
        ui:    ["'Silkscreen'", 'monospace'],
        ai:    ["'VT323'", 'monospace'],
        label: ["'Press Start 2P'", 'monospace'],
      },
      animation: {
        'gold-pulse': 'gold-pulse 0.8s steps(1) infinite',
        'blink':      'blink 1s steps(1) infinite',
        'status-dot': 'status-dot-pulse 1.2s steps(1) infinite',
      },
    },
  },
  plugins: [],
}
