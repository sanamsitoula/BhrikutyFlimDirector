# Chain Clarity — Brand Guidelines

> "We don't sell hype. We build understanding."

---

## 1. Brand Identity

| Field | Value |
|-------|-------|
| **Brand Name** | Chain Clarity |
| **Tagline** | Blockchain, without the noise. |
| **Slug** | `chain_clarity` |
| **Niche** | Blockchain & Cryptocurrency Education |
| **Platforms** | YouTube · TikTok · Instagram |

### Target Audience

Curious learners aged 22–40 who have heard about blockchain and crypto but want to understand it *technically*, not speculatively. They are not looking for trading tips. They want knowledge they can explain to someone else and act on with confidence. They are frustrated by content that is either too hyped or too academic.

---

## 2. Color System

| Role | Name | HEX | Usage |
|------|------|-----|-------|
| Primary | Electric Teal | `#00D4AA` | Headers, CTAs, key stats |
| Secondary | Deep Gold | `#F5A623` | Accents, icons, callouts |
| Neutral | Slate | `#8B9BB4` | Body text, secondary labels |
| Background | Deep Navy | `#0A0E1A` | Card and screen backgrounds |
| Highlight | Electric Violet | `#7B5CF0` | Pull quotes, chapter markers |

**Rules:**
- NEVER use CSS color names (no `teal`, `gold`, `white`, `black`).
- ALWAYS use exact HEX codes from this table.
- Minimum contrast ratio: 4.5:1 WCAG AA on all text.
- `#00D4AA` on `#0A0E1A` = 8.1:1 (passes AAA). Use freely.
- `#F5A623` on `#0A0E1A` = 7.4:1 (passes AAA). Use freely.

---

## 3. Typography

| Role | Font | Weight |
|------|------|--------|
| Heading | Space Grotesk | 700 (Bold) |
| Subheading | Space Grotesk | 500 (Medium) |
| Body | Inter | 400 (Regular) |
| Code / Hashes | JetBrains Mono | 400 |

**Rules:**
- Minimum body text: 48px on-screen (video/card context)
- Minimum header text: 72px on-screen
- Maximum 7 words per line on any visual asset
- Google Fonts CDN links:
  - `https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;500;700&family=Inter:wght@400;500&family=JetBrains+Mono:wght@400&display=swap`

---

## 4. Logo

**Concept:** Two interlocking flat-top hexagons representing blockchain blocks forming a chain link. Left block filled in Electric Teal, right block in Deep Navy with Electric Violet stroke, overlap zone in Deep Gold. The gold diamond at the intersection symbolises the moment of connection — where raw data becomes clarity.

**Usage rules:**
- Always use on Deep Navy (`#0A0E1A`) background, or full white background.
- Never stretch, rotate, or recolor individual elements.
- Minimum display size: 48px height for icon mark, 120px for full wordmark.
- Clear space: equal to the height of the "C" in "Chain" on all sides.

---

## 5. Tone of Voice

### Voice Character
Senior engineer. Patient mentor. Zero hype. Deeply knowledgeable but never arrogant. Every abstract concept gets an analogy from the physical world before technical explanation.

### The Formula
> **Concept first. Analogy second. Mechanism third.**

Example (correct):
> "A blockchain is an append-only ledger. Imagine a shared notebook where everyone has a copy — and adding a page notifies every single person in the room. No one can secretly change a page from three months ago without everyone knowing."

Example (wrong):
> "Blockchain is simply a distributed ledger that's basically a chain of blocks connected through cryptographic hashes."

### Sentence Style
- Short. Declarative. Max 15 words per sentence in scripts.
- No passive voice.
- Lead with the concept. Follow with the analogy.

### Forbidden Words
`moon` · `lambo` · `HODL` · `simply` · `just` · `obviously` · `easy` · `basic` · `pump` · `dump` · `guaranteed` · `rich` · `explosive` · `massive gains`

---

## 6. Content Pillars

1. **How Blockchain Works** — mechanics, nodes, consensus, cryptography
2. **Cryptocurrency Fundamentals** — Bitcoin, Ethereum, wallets, transactions
3. **DeFi & Smart Contracts** — protocols, liquidity, yield, real risks
4. **Security & Self-Custody** — wallets, seed phrases, attack vectors
5. **Real-World Blockchain Applications** — beyond finance: supply chain, identity, L2

---

## 7. Sound Identity

| Property | Value |
|----------|-------|
| Style | Electronic ambient / lo-fi tech |
| BPM Range | 88–112 |
| Mood | Focused · Curious · Empowering · Grounded |
| Forbidden Genres | Trap · Hype EDM · Aggressive dubstep · Party anthems |

**Royalty-free search terms:**
- `lo-fi electronic focused`
- `ambient tech background`
- `minimal electronic study`
- `calm tech beat`
- `intelligent electronic chill`

---

## 8. Animation System

| Property | Value |
|----------|-------|
| Default transition | slide-up |
| Duration | 400ms |
| Text animation | typewriter |
| Easing | ease-out |

**Card animation sequence (must follow this order):**
1. Background fades in (0.2s ease-out)
2. Logo mark slides in from top (0.3s ease-out)
3. Headline types in word-by-word (typewriter, 80ms per word)
4. Supporting text slides up (0.4s ease-out, 0.2s delay)
5. Stat / icon counts up (1s, easeOutCubic)
6. CTA chip bounces in (0.3s spring)

---

## 9. Card Dimensions

| Format | Size |
|--------|------|
| Instagram Post | 1080×1080px |
| Stories / Reels | 1080×1920px |
| YouTube Thumbnail | 1280×720px |
| YouTube End Screen | 1920×1080px |
