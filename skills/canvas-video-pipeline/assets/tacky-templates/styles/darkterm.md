# Style 06 — Dark Terminal 深夜終端 (command-narrative terminal) ★ LOCKED v1.0 · 2026-07-04

The card IS a terminal session. GitHub-dark palette, JetBrains Mono + Noto Sans TC 900,
tmux status bar with live clock（深夜模式）. The story is told as COMMANDS: what you
`cat`, what you `rm`, what `echo` reveals. For 深夜剪片 creators, dev/AI/productivity
content, anyone whose audience lives in dark mode.

**NOT VHS.** VHS is analog（tape hiss, glitch, camcorder OSD）; this is digital（crisp
borders, syntax colors, phosphor glow）. Zero grain, zero shake, zero easing curves —
everything moves in monospace ticks. The terminal never floats.

## Card types — route by pasted content
| Context contains… | Build | Template |
|---|---|---|
| a rejected belief + a payoff line | 文字卡 command narrative | `templates/darkterm.html` |
| numbers, percentages, comparisons | 監控卡 htop monitor | `templates/darkterm_top.html` |
| progress, done-vs-doing, checklist, 成長對比 | 狀態卡 git status | `templates/darkterm_status.html` |

## The emphasis vocabulary (unique — never borrow)
- 文字卡 `{cmd,out}` — command types after ❯, spinner ticks, output prints BIG;
  `<hot>` word = amber. `{cmd,rm:true}` = **the strike**: the previous output gets
  backspace-DELETED character by character, ends as dim `deleted ✕`. `{cmd,out,key:true}`
  = **the payoff**: glowing phosphor-green output, `<sel>` word gets the selection
  block, `[✓]` pulses once.
- 監控卡 — segmented block bars（█░）fill in DISCRETE TICKS + % counters. ONE row
  `hl:true`: fills LAST, glowing green, locks with its `note`（[✓] …）. Real numbers
  only — never invent data.
- 狀態卡 — `git status` of a life: green `+ 新增:` done items vs amber `~ 修改中:`
  wip items. ONE done item `key:true`（glow + `<sel>` block + [✓]）lands last in its
  section. The done/wip contrast IS the story.
- comment（all cards）= final `#` line, types itself, cursor blinks forever.

## Directing rules
- Syntax colors are grammar: commands cyan, flags purple, prompt/payoff green,
  warnings amber, deletion red. Don't repaint them per card.
- Timing is mechanical: typeChar ~0.05s, bars tick ~0.05s/seg. If it needs to
  "breathe" or float → wrong style（Pastel）. If it needs impacts → Pop.
- Copy register: 自嘲、清醒、深夜的誠實. Commands are half the joke —
  `rm -f 這個建議`、`htop --sort 佔用心力`、`git status` on your life.
- SFX language: mechanical keyboard clatter per typed char, backspace 咔咔（rm）,
  soft blips for prints, ONE low bass swell + clean confirm chime for the key moment,
  case-fan room tone under everything.
- O outro = brightness flash → cut to black（power off）. R / S as always.

## Palette
bg #0c1016 · panel #10151d · frame #2b3340 · text #c9d1d9 · dim #8b949e ·
green #7ee787 · cyan #79c0ff · amber #ffa657 · red #ff7b72 · purple #d2a8ff ·
selection #153b26. Fonts: JetBrains Mono（chrome/commands）· Noto Sans TC 900（outputs）.
