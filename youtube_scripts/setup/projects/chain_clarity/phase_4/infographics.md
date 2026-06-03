# Infographics Brief — Phase 4
## Chain Clarity · Security & Self-Custody
**Card count: 3 · Dimensions: 1080×1080px (Instagram Post)**

---

## CARD 01 — HOT WALLET VS COLD WALLET

**Concept:** A direct comparison diagram that shows the architecture difference between hot and cold wallets.

**Layout:** Two-column split. Left = Hot Wallet (subtle warm treatment), Right = Cold Wallet (teal/violet treatment).

| Layer | Left Column — Hot | Right Column — Cold |
|-------|------------------|---------------------|
| Icon | Laptop with wifi signal (stroke: #F5A623) | Hardware device / vault (stroke: #00D4AA) |
| Label | "HOT WALLET" | "COLD WALLET" |
| Sublabel | "Internet-connected" | "Always offline" |
| Row 1 | MetaMask / Phantom / Trust Wallet | Ledger / Trezor / Coldcard |
| Row 2 | ✓ Convenient for daily use | ✓ Secure for long-term holds |
| Row 3 | ✗ Exposed to online threats | ✗ Less convenient |
| Best for | Small active amounts | Significant holdings |

**Color rules:**
- Background: #0A0E1A
- Hot column accent: #F5A623 (gold — caution/attention, not danger)
- Cold column accent: #00D4AA (teal — secure, recommended)
- Divider: vertical line #8B9BB4 at 30% opacity
- Body text: #8B9BB4

**Animation sequence:**
1. Background fades in (0.2s)
2. Logo slides from top (0.3s, delay 0.3s)
3. Headline words type in (0.15s per word, start 0.6s)
4. Left column slides in from left (0.4s, delay 1.4s)
5. Right column slides in from right (0.4s, delay 1.6s)
6. Stat bar bounces in: "10% hot · 90% cold — suggested split" (delay 2.2s)

**Stat:** "10% hot · 90% cold — suggested allocation"
**CTA strip:** "Where do your holdings live right now?"

---

## CARD 02 — THE SEED PHRASE GUIDE

**Concept:** A clear visual reference showing what a seed phrase is and the critical do/don't rules.

**Layout:** Header section (what it is), middle section (NEVER do this — 4 items), bottom section (ALWAYS do this — 2 items).

**Header:**
- Headline: "THE SEED PHRASE"
- Subhead: "12 or 24 words. Everything."
- Visual: Pill badges showing "WORD 1" through "WORD 12" in a 4×3 grid. JetBrains Mono font, Navy background, Teal border.

**NEVER section (red-tinted — semantic exception #EF4444 border, not fill):**
- ✗ Phone photo
- ✗ Notes app or cloud doc
- ✗ Email to yourself
- ✗ Screenshots

**ALWAYS section:**
- ✓ Metal backup (Cryptosteel / stamped plate)
- ✓ Two copies, separate locations

**Color rules:**
- Background: #0A0E1A
- Headline: #00D4AA
- NEVER items: #EF4444 border/icon only (semantic exception — documented)
- ALWAYS items: #00D4AA
- Pill grid: #7B5CF0 border, #0A0E1A fill, #8B9BB4 text

**Animation sequence:**
1. Background fades in (0.2s)
2. Logo slides from top (0.3s, delay 0.3s)
3. Headline types in word by word (delay 0.6s)
4. Word grid populates left-to-right, row by row (0.08s per pill, start 1.2s)
5. NEVER items slide in from left in sequence (0.3s each, start 2.0s)
6. ALWAYS items bounce in (0.3s, start 2.8s)

**Stat:** "One exposed seed phrase = total fund loss"
**CTA strip:** "Is your seed phrase on paper right now?"

---

## CARD 03 — 5 ATTACK VECTORS

**Concept:** A numbered list of the five attack methods, each with a clear one-line rule at the bottom.

**Layout:** Headline, 5 rows (number + attack name + rule), compact and scannable.

| # | Attack | Rule |
|---|--------|------|
| ① | Phishing Links | Never type seed phrase into a website |
| ② | Fake Extensions | Official source only — check the URL |
| ③ | SIM Swap | Use authenticator app, not SMS |
| ④ | Fake Support | No legitimate protocol asks for seed phrase |
| ⑤ | Clipboard Hijack | Verify first 4 and last 4 address chars |

**Color rules:**
- Background: #0A0E1A
- Numbers: #F5A623 (gold)
- Attack names: #FFFFFF
- Rule text: #8B9BB4
- Divider lines between rows: #8B9BB4 at 20% opacity
- Row hover/highlight: #00D4AA at 8% opacity background

**Animation sequence:**
1. Background fades in (0.2s)
2. Logo slides from top (0.3s, delay 0.3s)
3. Headline "5 ATTACK VECTORS" types in (delay 0.6s)
4. Rows 1–5 slide up in sequence (0.25s each, 0.2s stagger, start 1.2s)
5. Final stat bounces in: "Most attacks rely on one mistake" (delay 2.5s)

**Stat:** "Most attacks are prevented by one habit: verify before you click."
**CTA strip:** "Share this with someone who is new to crypto."

---

## LOTTIE EXPORT NOTES

All 3 cards export to:
- `card_01_hot_cold.mp4` — 6 seconds @ 30fps
- `card_02_seed_phrase.mp4` — 7 seconds @ 30fps
- `card_03_attack_vectors.mp4` — 8 seconds @ 30fps

PNG stills for Instagram carousel:
- `card_01_still.png` — Frame at animation completion
- `card_02_still.png`
- `card_03_still.png`

For After Effects / CapCut / DaVinci Resolve:
- Import HTML as image sequence OR use Lottie plugin
- All animations use CSS keyframes matching standard easing (ease-out)
- No third-party animation libraries — pure CSS + minimal JS counter
