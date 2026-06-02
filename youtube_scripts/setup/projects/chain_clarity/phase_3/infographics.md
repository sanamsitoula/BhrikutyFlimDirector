# Infographic Layout Specs — Phase 3
## Chain Clarity · Agent 6 — Infographic Designer

**Phase 3 card count:** 3 cards
**Script sections covered:** Section 1 (smart contracts), Section 2 (DeFi lending), Section 3 (AMMs/liquidity pools)

---

## CARD 01 — "THE SMART CONTRACT: IF THIS, THEN THAT"

**Export format:** Instagram Post 1080×1080px · YouTube Thumbnail 1280×720px
**Script reference:** Section 1
**Layout type:** IF/THEN logic flow — vertical stack

### Layout Structure

```
┌─────────────────────────────────────────────────────┐
│  [LOGO MARK top-left · 60px]                        │
│                                                     │
│  THE SMART CONTRACT  ← headline (white, 72px)      │
│  IF THIS, THEN THAT  ← sub (violet, 72px)          │
│  ──────────────────────────────────────────────    │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  IF  [gold badge]                           │   │
│  │  Deposit 150 USD of ETH as collateral       │   │
│  └─────────────────────────────────────────────┘   │
│            ↓ [teal arrow]                          │
│  ┌─────────────────────────────────────────────┐   │
│  │  THEN  [teal badge]                         │   │
│  │  Release 100 USD in stablecoin              │   │
│  └─────────────────────────────────────────────┘   │
│            ↓ [teal arrow]                          │
│  ┌─────────────────────────────────────────────┐   │
│  │  IF  [gold badge]                           │   │
│  │  Collateral drops below 120 USD             │   │
│  └─────────────────────────────────────────────┘   │
│            ↓ [violet arrow]                        │
│  ┌─────────────────────────────────────────────┐   │
│  │  THEN  [violet badge]                       │   │
│  │  Auto-liquidate. Loan repaid.               │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ═══════════════════════════════════════════════  │
│  NO HUMAN APPROVES. CODE IS THE BANK.   ← violet  │
│  ═══════════════════════════════════════════════  │
│                                                     │
│  [Chain Clarity wordmark]                          │
└─────────────────────────────────────────────────────┘
```

### Text Content (7 words max per line)

- **Headline:** THE SMART CONTRACT [3 words ✓]
- **Sub-headline:** IF THIS, THEN THAT [4 words ✓]
- **IF badge 1:** IF [1 word ✓]
- **IF row 1 content:** Deposit 150 USD as collateral [5 words ✓]
- **THEN badge 1:** THEN [1 word ✓]
- **THEN row 1 content:** Release 100 USD stablecoin loan [5 words ✓]
- **IF badge 2:** IF [1 word ✓]
- **IF row 2 content:** Collateral drops below 120 USD [5 words ✓]
- **THEN badge 2:** THEN [1 word ✓]
- **THEN row 2 content:** Auto-liquidate. Loan repaid. [3 words ✓]
- **Callout:** NO HUMAN APPROVES. CODE IS THE BANK. [7 words ✓]

### Color Assignments

| Element | Color | HEX |
|---------|-------|-----|
| Background | Deep Navy | #0A0E1A |
| Headline "THE SMART CONTRACT" | White | #FFFFFF |
| "IF THIS, THEN THAT" | Electric Violet | #7B5CF0 |
| IF badges | Deep Gold bg | #F5A623 |
| IF badge text | Deep Navy | #0A0E1A |
| IF row content | White | #FFFFFF |
| IF row border | Deep Gold | #F5A623 |
| THEN badge (first) | Electric Teal bg | #00D4AA |
| THEN badge text | Deep Navy | #0A0E1A |
| THEN row content (first) | White | #FFFFFF |
| THEN row border (first) | Electric Teal | #00D4AA |
| THEN badge (second) | Electric Violet bg | #7B5CF0 |
| THEN row content (second) | White | #FFFFFF |
| THEN row border (second) | Electric Violet | #7B5CF0 |
| Arrows (first) | Electric Teal | #00D4AA |
| Arrows (second) | Electric Violet | #7B5CF0 |
| Callout text | Electric Violet | #7B5CF0 |
| Callout bg | rgba(#7B5CF0, 10%) | — |

### Animation Entry

1. Background fade-in (0.2s)
2. Logo slides from top (0.3s)
3. Headline typewriters in (80ms/word)
4. First IF row slides up from bottom (0.4s)
5. Arrow appears (0.3s), then first THEN row slides up (0.4s, 0.2s stagger)
6. Second IF row slides up (0.4s, 0.15s stagger)
7. Second arrow + THEN row (violet) slides up (0.4s, 0.15s stagger)
8. Callout bounces in (0.3s spring)

---

## CARD 02 — "HOW DEFI LENDING WORKS"

**Export format:** Instagram Post 1080×1080px · Stories 1080×1920px
**Script reference:** Section 2
**Layout type:** Two-column flow with central pool

### Layout Structure

```
┌─────────────────────────────────────────────────────┐
│  [LOGO MARK top-left · 60px]                        │
│                                                     │
│  HOW DEFI              ← headline (white, 80px)    │
│  LENDING WORKS         ← sub (teal, 80px)          │
│  ──────────────────────────────────────────────    │
│                                                     │
│  ┌──────────────┐  ┌────────────┐  ┌────────────┐  │
│  │   LENDER     │  │   POOL     │  │  BORROWER  │  │
│  │  [teal col]  │  │ [center]   │  │ [gold col] │  │
│  │              │  │            │  │            │  │
│  │  Deposits    │→ │  Smart     │→ │  Posts     │  │
│  │  ETH/USDC   │  │  Contract  │  │  150% ETH  │  │
│  │              │  │            │  │  collateral│  │
│  │  Earns:      │← │  Routes    │  │            │  │
│  │  Interest %  │  │  interest  │  │  Gets:     │  │
│  │              │  │            │  │  100 USDC  │  │
│  └──────────────┘  └────────────┘  └────────────┘  │
│                                                     │
│  ════════════════════════════════════════════════  │
│  OVERCOLLATERALIZED: 150%+ REQUIRED  ← gold badge  │
│  ════════════════════════════════════════════════  │
│                                                     │
│  [Chain Clarity wordmark]                          │
└─────────────────────────────────────────────────────┘
```

### Text Content

- **Headline:** HOW DEFI [2 words ✓]
- **Sub-headline:** LENDING WORKS [2 words ✓]
- **Col 1 header:** LENDER [1 word ✓]
- **Col 1 line 1:** Deposits ETH or USDC [4 words ✓]
- **Col 1 line 2:** Earns interest automatically [3 words ✓]
- **Col 2 header:** POOL [1 word ✓]
- **Col 2 label:** Smart Contract [2 words ✓]
- **Col 2 sub:** Routes interest automatically [3 words ✓]
- **Col 3 header:** BORROWER [1 word ✓]
- **Col 3 line 1:** Posts 150% ETH collateral [4 words ✓]
- **Col 3 line 2:** Gets 100 USDC loan [4 words ✓]
- **Callout:** OVERCOLLATERALIZED: 150%+ REQUIRED [3 words ✓]
- **Liquidation note:** Drop below threshold → auto-sell [5 words ✓]

### Color Assignments

| Element | Color | HEX |
|---------|-------|-----|
| Background | Deep Navy | #0A0E1A |
| Headline "HOW DEFI" | White | #FFFFFF |
| "LENDING WORKS" | Electric Teal | #00D4AA |
| LENDER column header | Electric Teal | #00D4AA |
| LENDER column border | Electric Teal | #00D4AA |
| LENDER column fill | rgba(#00D4AA, 6%) | — |
| POOL center label | Slate | #8B9BB4 |
| POOL border | Slate | #8B9BB4 |
| BORROWER column header | Deep Gold | #F5A623 |
| BORROWER column border | Deep Gold | #F5A623 |
| BORROWER column fill | rgba(#F5A623, 6%) | — |
| Arrow left-to-right | Electric Teal | #00D4AA |
| Arrow right-to-left (interest) | Electric Teal | #00D4AA |
| Column content text | White | #FFFFFF |
| Callout text | Deep Gold | #F5A623 |
| Callout bg | rgba(#F5A623, 8%) | — |
| Liquidation note | Electric Violet | #7B5CF0 |

### Animation Entry

1. Background fade-in (0.2s)
2. Logo slides from top (0.3s)
3. Headline typewriters in (80ms/word)
4. LENDER column slides in from left (0.4s, delay 1.1s)
5. POOL center fades up (0.4s, delay 1.3s)
6. BORROWER column slides in from right (0.4s, delay 1.5s)
7. Flow arrows draw left-to-right (0.5s, delay 1.8s)
8. Interest return arrow draws right-to-left (0.4s, delay 2.2s)
9. Callout bounces in (0.3s spring, delay 2.5s)

---

## CARD 03 — "HOW AMMS WORK: x × y = k"

**Export format:** Instagram Post 1080×1080px · YouTube Thumbnail 1280×720px
**Script reference:** Section 3
**Layout type:** Pool balance visualization with formula

### Layout Structure

```
┌─────────────────────────────────────────────────────┐
│  [LOGO MARK top-left · 60px]                        │
│                                                     │
│  HOW AMMS WORK        ← headline (white, 72px)     │
│  NO ORDER BOOK        ← sub (teal, 72px)           │
│  ──────────────────────────────────────────────    │
│                                                     │
│  ┌────────────────────────────────────────────┐    │
│  │  x × y = k                                 │    │
│  │  [72px · JetBrains Mono · gold · centered] │    │
│  │  CONSTANT PRODUCT FORMULA [slate · small]  │    │
│  └────────────────────────────────────────────┘    │
│                                                     │
│  ┌───────────────┐       ┌───────────────────────┐ │
│  │  ETH          │  ⇌   │  USDC                 │ │
│  │  [gold hex]   │       │  [teal hex]           │ │
│  │               │       │                       │ │
│  │  You ADD ETH  │       │  You GET USDC         │ │
│  │  Price ↓      │       │  Price ↑              │ │
│  └───────────────┘       └───────────────────────┘ │
│                                                     │
│  ─────────────────────────────────────────────    │
│  POOL BALANCE ALWAYS PRESERVED  ← slate           │
│                                                     │
│  ═══════════════════════════════════════════════  │
│  NO ONE SETS THE PRICE. THE MATH DOES.  ← teal   │
│  ═══════════════════════════════════════════════  │
│                                                     │
│  [Chain Clarity wordmark]                          │
└─────────────────────────────────────────────────────┘
```

### Text Content

- **Headline:** HOW AMMS WORK [3 words ✓]
- **Sub-headline:** NO ORDER BOOK [3 words ✓]
- **Formula:** x × y = k [JetBrains Mono ✓]
- **Formula label:** CONSTANT PRODUCT FORMULA [3 words ✓]
- **Left panel header:** ETH [1 word ✓]
- **Left panel line 1:** You ADD ETH [3 words ✓]
- **Left panel line 2:** Price decreases [2 words ✓]
- **Exchange symbol:** ⇌ [symbol ✓]
- **Right panel header:** USDC [1 word ✓]
- **Right panel line 1:** You GET USDC [3 words ✓]
- **Right panel line 2:** Price increases [2 words ✓]
- **Mid label:** POOL BALANCE ALWAYS PRESERVED [4 words ✓]
- **Callout:** NO ONE SETS THE PRICE. THE MATH DOES. [7 words ✓]

### Color Assignments

| Element | Color | HEX |
|---------|-------|-----|
| Background | Deep Navy | #0A0E1A |
| Headline "HOW AMMS WORK" | White | #FFFFFF |
| "NO ORDER BOOK" | Electric Teal | #00D4AA |
| Formula "x × y = k" | Deep Gold | #F5A623 |
| "CONSTANT PRODUCT FORMULA" label | Slate | #8B9BB4 |
| Formula card border | Deep Gold | #F5A623 |
| Formula card fill | rgba(#F5A623, 6%) | — |
| ETH panel header | Deep Gold | #F5A623 |
| ETH panel border | Deep Gold | #F5A623 |
| ETH panel fill | rgba(#F5A623, 6%) | — |
| "Price ↓" text | Deep Gold | #F5A623 |
| Exchange symbol ⇌ | Slate | #8B9BB4 |
| USDC panel header | Electric Teal | #00D4AA |
| USDC panel border | Electric Teal | #00D4AA |
| USDC panel fill | rgba(#00D4AA, 6%) | — |
| "Price ↑" text | Electric Teal | #00D4AA |
| Panel content text | White | #FFFFFF |
| "POOL BALANCE ALWAYS PRESERVED" | Slate | #8B9BB4 |
| Callout text | Electric Teal | #00D4AA |
| Callout bg | rgba(#00D4AA, 8%) | — |

### Animation Entry

1. Background fade-in (0.2s)
2. Logo slides from top (0.3s)
3. Headline typewriters in (80ms/word)
4. Formula card slides up (0.5s, delay 1.0s)
5. "x × y = k" counts/types in character-by-character (0.6s, delay 1.5s)
6. ETH panel slides in from left (0.4s, delay 2.0s)
7. Exchange symbol ⇌ fades in (0.3s, delay 2.3s)
8. USDC panel slides in from right (0.4s, delay 2.3s)
9. Price arrows animate (↓ ETH, ↑ USDC) (0.4s stagger, delay 2.7s)
10. Callout bounces in (0.3s spring, delay 3.1s)

---

**Next Step:** `🖼️ INFOGRAPHIC DESIGNER complete → 🎨 /preview 3 (Agent 12)`
