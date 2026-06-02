# How Blockchain Works — No Bank Required
## Phase 1 · Long-Form Script · Chain Clarity
**Format:** YouTube · Target duration: 12 min · Pillar: How Blockchain Works

---

## HOOK (0:00–0:12)

[TITLE CARD: "THE BANK FAILED. THE BLOCKCHAIN DIDN'T."]
[B-ROLL: FTX collapse headlines → cut to Bitcoin network nodes visualization]

SPOKEN:
"In 2022, a crypto exchange called FTX collapsed in 72 hours.
Eight billion dollars in customer funds — gone.
No warning. No recourse. No refunds.
That same week, the Bitcoin blockchain processed over 200,000 transactions.
Zero errors. Zero downtime.
Same industry. Completely different result.
Today, we are going to understand exactly why."

ON-SCREEN TEXT:
- "FTX: $8B lost in 72 hours" [#F5A623 · bold]
- "Bitcoin network: 0 errors that week" [#00D4AA · bold]

---

## SECTION 1 — THE TRUST PROBLEM (0:12–2:30)

[TITLE CARD: "01 · THE TRUST PROBLEM"]
[B-ROLL: Bank counters, wire transfer screens, handshakes]

SPOKEN:
"Every financial system has the same design flaw.
It requires you to trust someone else.
When you send money, you trust your bank.
You trust their systems. Their employees. Their decisions.
You trust that they won't fail, freeze your account, or disappear overnight.

For most of history, that was the only option.
No trusted middleman — no transaction.

Computer scientists called this the Byzantine Generals Problem.
Here's the analogy that makes it click.

Imagine four generals surrounding an enemy city.
They must agree on a plan: attack at dawn, or retreat.
They can only communicate by messenger.
But one general is a traitor.
The traitor sends different messages to different generals.
How do you reach agreement — when you can't trust the messenger?

This problem stumped researchers for decades.
Then in 2008, an anonymous developer named Satoshi Nakamoto published a 9-page paper.
The title: 'Bitcoin: A Peer-to-Peer Electronic Cash System.'
The solution: a chain of blocks."

ON-SCREEN TEXT:
- "Byzantine Generals Problem" [#00D4AA · heading]
- "How do you agree with no trusted center?" [#8B9BB4]
- "Satoshi Nakamoto · 2008" [#F5A623 · JetBrains Mono]

---

## SECTION 2 — WHAT IS A BLOCK? (2:30–5:00)

[TITLE CARD: "02 · WHAT IS A BLOCK?"]
[INFOGRAPHIC CUE: card_01 — block anatomy diagram]

SPOKEN:
"Start with the building block.
A block is a container of data.

Think of it like one page in a shared ledger.
Each page records a batch of transactions.
On Bitcoin, each block holds roughly 2,000 to 3,000 transactions.
Once the page fills up — it's sealed.
No changes. A new page begins.

But a blockchain page has three parts a normal ledger doesn't.

First: the data.
Who sent what to whom, and how much.
Every transaction in this block, recorded and verified.

Second: the timestamp.
The exact moment this block was created and sealed.
Precise, permanent, and cannot be altered.

Third: the hash.
This is the most critical part of the entire system.
We need to understand hashes properly.
Everything else depends on this."

ON-SCREEN TEXT:
- "A block = one sealed ledger page" [#00D4AA]
- "DATA" [#F5A623 · large]
- "TIMESTAMP" [#F5A623 · large]
- "HASH" [#F5A623 · large · emphasised last]
- "~2,000–3,000 transactions per block" [#8B9BB4 · small stat]

---

## SECTION 3 — WHAT IS A HASH? (5:00–7:15)

[TITLE CARD: "03 · THE HASH: A DIGITAL FINGERPRINT"]
[INFOGRAPHIC CUE: card_02 — hash input/output demo]

SPOKEN:
"A hash is a fingerprint for data.

You feed any input into a hash function.
It produces a fixed-length string of characters.
Always the same length. Always looks random.

Here is the SHA-256 hash of the word 'Hello':
185f8db32921bd46d35cc96953e114e6c68af82b84a8a22f3...

Here is the hash of 'Hello!' — one character different:
334d016f755cd6dc58c53a86e183882f8ec14f52fb05345...

Completely different output. From a single character change.

This is the key property of a hash.
You cannot predict the output without running the function.
You cannot reverse-engineer the input from the output.
Change one byte of the input — the entire output changes.

Every block gets a hash.
It is the fingerprint of everything inside:
the transactions, the timestamp, and one more thing we'll cover next.

Now here is the chain part."

ON-SCREEN TEXT:
- "SHA-256('Hello') →" [#8B9BB4]
- "185f8db32921bd46d..." [#F5A623 · JetBrains Mono]
- "SHA-256('Hello!') →" [#8B9BB4]
- "334d016f755cd6dc..." [#00D4AA · JetBrains Mono]
- "1 character change = 100% different fingerprint" [#7B5CF0 · emphasis]

---

## SECTION 4 — THE CHAIN (7:15–9:00)

[TITLE CARD: "04 · THE CHAIN"]
[INFOGRAPHIC CUE: card_03 — linked blocks diagram]

SPOKEN:
"Every block contains the hash of the block before it.
That is the entire chain structure. Let that sink in.

Block 101 contains the hash of block 100.
Block 100 contains the hash of block 99.
All the way back to block zero — called the Genesis Block.

Here's the analogy.
Think of a document audit trail.
At the top of every new page, you write a short summary of the previous page.
If anyone secretly changes a past page — your summary no longer matches the page.
The tampering is visible to anyone who checks.

Now watch what happens when someone tries to alter the blockchain.

Suppose an attacker wants to change a transaction from six months ago.
They alter block 500.
The moment they change block 500's data — its hash changes.
Block 501 stored the old hash of block 500. Now block 501 is invalid.
To fix block 501, they must recalculate it.
But recalculating block 501 changes its hash.
Now block 502 is invalid. And block 503. All the way to the present.

In a chain with hundreds of thousands of blocks — this is computationally enormous.
The past is locked. This property is called immutability."

ON-SCREEN TEXT:
- "Block N+1 stores the hash of Block N" [#00D4AA]
- Chain diagram: [BLOCK 99] → [BLOCK 100] → [BLOCK 101]
- "prev_hash" arrows [#7B5CF0 · small label]
- "Alter one block → entire chain breaks" [#F5A623 · emphasis]

---

## SECTION 5 — THE NETWORK (9:00–11:00)

[TITLE CARD: "05 · THE NETWORK"]
[INFOGRAPHIC CUE: card_04 — decentralized node diagram]

SPOKEN:
"Now the final layer.
Who holds this chain?

In a blockchain network, thousands of computers — called nodes — each hold a complete, identical copy.
No central server. No headquarters. No single point of failure.

When a new block is proposed, every node validates it independently.
They check: are all transactions valid?
Does the hash match the block's contents?
Does it correctly reference the previous block's hash?
Only if the majority agrees — the block is added to every copy.

Think of it as a town meeting without a mayor.
A new rule is proposed. Everyone votes independently.
No single person controls the outcome.
No one person can add a rule without majority agreement.
This is called consensus.

Bitcoin uses a mechanism called Proof of Work.
Miners — specialised nodes — compete to solve a computational puzzle.
The first to solve it earns the right to add the next block.
This puzzle requires real energy. That energy cost is what makes attacking the network expensive.

To rewrite Bitcoin's history, an attacker would need more computational power than all honest miners combined.
Today, that would cost billions of dollars per hour.
That is why Bitcoin's ledger has never been successfully altered."

ON-SCREEN TEXT:
- "~15,000+ full nodes worldwide" [#00D4AA · counter animation]
- "No headquarters. No off switch." [#8B9BB4]
- "Consensus = agreement without authority" [#7B5CF0]
- "Proof of Work: energy makes attacks expensive" [#F5A623]

---

## CTA (11:00–12:00)

[TITLE CARD: "WHAT YOU NOW KNOW"]
[B-ROLL: Chain Clarity end screen with logo animation]

SPOKEN:
"Here is what you now understand.

A block is a sealed ledger page — data, timestamp, and hash.
A hash is a digital fingerprint. One byte changed — the fingerprint changes entirely.
Each block stores the previous block's hash. That is the chain.
Thousands of nodes each hold the full chain.
Altering any past block breaks the chain forward — and every node knows immediately.

This is why Bitcoin's ledger is 14 years old and has never been rewritten.
Not because it's protected by a company.
Because the math makes it practically impossible.

In the next video, we go deeper.
Bitcoin versus Ethereum.
What the 21-million-coin limit actually means.
And why Ethereum introduced programmability that Bitcoin was never designed for.

Subscribe now. Hit the bell. Phase 2 drops in [X] days."

ON-SCREEN TEXT:
- "A block: DATA · TIMESTAMP · HASH" [#00D4AA]
- "Hash = fingerprint. Change = entirely new hash." [#8B9BB4]
- "Chain = each block stores prev block's hash" [#00D4AA]
- "Subscribe for Phase 2 →" [CTA chip · bounce in · #F5A623 bg · #0A0E1A text]

---

**Next Step:** `✍️ SCRIPT WRITER → 🛡️ BRAND COMPLIANCE CHECK → /voice 1`
