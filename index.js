// Current year and timestamps for start and end of year
const year = new Date().getFullYear();
const start = new Date(`${year}-01-01T00:00:00Z`).getTime();
const end = new Date(`${year}-12-31T23:59:59Z`).getTime();

// Calculate progress percentage clamped between 0 and 1
const progress = Math.min(Math.max((Date.now() - start) / (end - start), 0), 1);

// Braille unicode characters for high-res progress bar (8 dots per char)
const brailleChars = ['⠀','⠂','⠆','⠇','⠧','⠷','⠿','⡿','⡿','⣟','⣯','⣷','⣿'];

// Generate high resolution morphing progress bar using braille chars
function generateBrailleProgressBar(length = 24) {
  const totalDots = length * 8;
  const filledDots = Math.floor(progress * totalDots);
  let bar = '';

  for (let i = 0; i < length; i++) {
    const dotsInChar = Math.min(8, Math.max(0, filledDots - i * 8));
    bar += brailleChars[dotsInChar] || '⠀';
  }
  return bar;
}

// Real-time clock in hacker style, 24h format with milliseconds for "live" effect
function getHackerTime() {
  const date = new Date();
  return date.toISOString().replace('T',' ').replace('Z','') + ` ⏳`;
}

// Hacker jargon phrases cycling for engagement
const messages = [
  'Injecting code...',
  'Bypassing firewall...',
  'Decompiling year...',
  'Loading temporal module...',
  'Calibrating timeline...',
  'Syncing with UTC...',
  'Compiling progress vector...',
  'Deploying status bar...',
];

const currentMessage = messages[Math.floor((Date.now() / 2000) % messages.length)];

const markdown = `\
 ┌─[ ☣️ Anonymous Year Progress Tracker ☣️ ]─────────────┐
 │                                                           │
 │ ${getHackerTime()}                              │
 │                                                           │
 │ Progress: [${generateBrailleProgressBar()}] ${(progress * 100).toFixed(4)}%                  │
 │                                                           │
 │ Status: ${currentMessage.padEnd(48)}│
 └───────────────────────────────────────────────────────────┘

---

### Connect with the system:

[![GitHub](https://img.shields.io/badge/GitHub-151515?style=for-the-badge&logo=github&logoColor=white)](https://github.com/mdsarfarazalam840)

---

*⚡ Updated live by your CI sentinel, silently monitoring the chronostream.*`;

// Output the stylized hacker markdown
console.log(markdown);
