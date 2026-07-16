# ai-agents.md — Responsibilities & Interaction Rules for Each AI/Plugin Role

**Scope note**: "AI agents" here means the **AI-calling roles inside the Bhrikuty pipeline itself** (script generation, compliance-adjacent text, future research/highlight-detection) — not external chat assistants. This document defines what each role is responsible for and how they hand off to one another, so that adding a new AI-driven capability means adding a new role in this table, not a new ad hoc prompt call somewhere in `server.py`.

## Current AI orchestration pattern (as it exists)

- **No agent framework.** No planning loop, no memory store, no tool-use/function-calling abstraction, no evaluation loop exists today. Every "AI step" is a single prompt-in-markdown-out call — this is a deliberate, reasonable fit for the product's actual need (deterministic content generation, not autonomous decision-making), not an accidental gap.
- **Provider fallback chain**: Claude (Sonnet) → Gemini (Flash) → Qwen3/DashScope (OpenAI-compatible endpoint), each script independently implementing its own `try: import anthropic ... except: try: import google.genai ...`. This duplication is a known defect (`architecture.md` CP1/CP10) — new roles must consume the shared `ai/providers.py` `LLMProvider` interface once it exists, not add another copy.
- **"ChatGPT" is advertised in the README's fallback chain but has no corresponding OpenAI API call anywhere in the code** (confirmed, tracked as E11). Do not assume OpenAI/Codex support exists until `ai/providers.py` has a real implementation for it.
- **Compliance checking is rule-based, not LLM-based** (`compliance_checker.py`, 17 fixed rules) — a deliberate choice for determinism and cost. Do not convert this to an LLM-judged check without a documented reason; the two approaches serve different guarantees (deterministic rule-check vs. LLM judgment).

## AI roles — current and planned

| Role | Responsibility | Input → Output | Status |
|---|---|---|---|
| **Script Generator** | Writes narration script, short-form cut, subtitles, voiceover/music briefs, infographic specs, `content_spec.json` | `topic + outline` → `script.md` + friends | **Implemented** (`generate_phase.py`) |
| **Text Content Generator** | Writes blog/Twitter/LinkedIn/GitHub text from the same phase's script | `script.md` → platform text files | **Implemented**, but gated by the CP10/E10 bug — must be fixed to check "any provider," not `ANTHROPIC_API_KEY` specifically |
| **Compliance Checker** | Runs 17 fixed brand-consistency rules | generated content + `brand_profile.json` → compliance report | **Implemented, rule-based** — not an AI agent, listed here to make the boundary explicit |
| **Self-Evaluator** (`ai/eval.py`) | Bounded self-check loop (generate → eval → retry, <3 loops) validating output actually matches spec (duration, subtitle sync, word count, and eventually visual checks) | generated artifact + spec → pass/fail + retry signal | **Planned, not built** — required before any Phase 1B/1C work per CP6 |
| **Research Provider** (`deep_research.py` pattern) | Turns a rough idea into a sourced topic + outline + citations, feeding the existing `--topic`/`--outline` inputs | rough idea → sourced brief | **Planned, optional, additive** — manual entry remains the default path |
| **Footage Editor** | Transcript-first analysis of raw/uploaded clips: silence/filler detection, retake selection, cut points | raw clips + transcript → EDL (edit decision list) | **Planned** (Phase 1B) |
| **Highlight Detector** | Scores segments of an existing long-form video for virality/hook strength (heuristic pass + LLM re-rank) | transcript + footage → ranked clip candidates | **Planned, genuinely new capability** (Phase 1C, CP11) — no existing code to wrap |
| **AI Director** (`ai/director.py`) | Plans scene order, pacing, and per-section visual treatment from a finished script — a new prompt, not a new AI capability | script → storyboard | **Planned, Phase 7** — the one module in the Phase 7 vision with no existing mapping anywhere |

## Interaction rules

1. **Every role that calls an LLM goes through the shared `LLMProvider` interface** (`ai/providers.py`) once it exists — a role must never hardcode which specific provider it uses or gate its own execution on a specific provider's env var being set.
2. **Roles hand off via typed artifacts on disk** (script.md, content_spec.json, transcript, EDL) — consistent with the filesystem-is-truth architecture (`architecture.md` §2). A role does not call another role's function directly in-process until `core/` genuinely supports that (Stage 2+ of `roadmap.md`); today's subprocess-per-tool model is the reality to design within.
3. **The Self-Evaluator wraps every generation role**, it does not replace any of them. Adding self-evaluation to a role is additive — the underlying generation call is unchanged.
4. **A role is not "done" until it has a name in this table, a plugin-interface mapping in `architecture.md` §3 (if applicable), and a test.** Do not add a new AI-driven behavior as an inline prompt call buried in `server.py` or a one-off script — give it a role here first.
5. **Cost-sensitive roles** (Footage Editor, Highlight Detector's LLM re-rank pass, any B-roll/voice-cloning provider) must run through the same free→cheap→paid escalation policy defined once, applied uniformly (`requirements.md` NFR-2) — not a bespoke retry/cost policy per role.
