// Get current year and timestamps for start/end of year
const year = new Date().getFullYear();
const start = new Date(`${year}-01-01T00:00:00Z`).getTime();
const end = new Date(`${year}-12-31T23:59:59Z`).getTime();

// Calculate progress percentage clamped between 0 and 1
const progress = Math.min(Math.max((Date.now() - start) / (end - start), 0), 1);

// Braille unicode characters for high-res progress bar (8 dots per char)
const brailleChars = ['⠀','⠂','⠆','⠇','⠧','⠷','⠿','⡿','⡿','⣟','⣯','⣷','⣿'];
function generateBrailleProgressBar(length = 16) {
  const totalDots = length * 8;
  const filledDots = Math.floor(progress * totalDots);
  let bar = '';
  for (let i = 0; i < length; i++) {
    const dotsInChar = Math.min(8, Math.max(0, filledDots - i * 8));
    bar += brailleChars[dotsInChar] || '⠀';
  }
  return bar;
}

// Minimal clock format, 24h
function getHackerTime() {
  return new Date().toISOString().replace('T',' ').replace('Z','').slice(0, 19);
}

// Randomized status line for more dynamic feel
const messages = [
  'Injecting code',
  'Bypassing firewall',
  'Decompiling year',
  'Loading module',
  'Syncing UTC',
  'Compiling vector',
  'Deploying bar'
];
const currentMessage = messages[Math.floor((Date.now() / 2000) % messages.length)];

// Compact single-line hacker box
const markdown = `\
\`\`\`
[ ☣️ Year Progress | ${getHackerTime()} ]
[ ${generateBrailleProgressBar()} ] ${ (progress * 100).toFixed(2) }%
<${currentMessage}...>
\`\`\`

[![GitHub](https://img.shields.io/badge/GitHub-151515?style=for-the-badge&logo=github&logoColor=white)](https://github.com/mdsarfarazalam840)
*⚡ CI monitored; status auto-updates.*
`;

console.log(markdown);
