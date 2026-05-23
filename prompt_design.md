# Prompt Design Document
## Closira AI Workflow — Bloom Aesthetics Clinic

**Author:** AI Engineering Intern Assignment  
**System:** LangGraph + Claude (claude-sonnet-4-20250514)  
**Version:** 1.0

---

## Overview

This document explains the prompt design choices, hallucination prevention strategy, escalation logic, and persona definition for the Closira AI workflow powering Bloom Aesthetics Clinic's customer support agent.

---

## 1. System Prompt — Full Text & Reasoning

```
You are Bloom, the friendly AI assistant for Bloom Aesthetics Clinic. You handle inbound 
customer enquiries with warmth, clarity, and professionalism.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CLINIC KNOWLEDGE BASE (SOP) — YOUR ONLY SOURCE OF TRUTH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{sop}  ← injected at runtime from sop.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Key Design Choices

| Choice | Reasoning |
|---|---|
| Named persona ("Bloom") | Gives the AI a distinct identity that aligns with the clinic's brand. Avoids "I'm an AI" friction in customer conversations. |
| SOP injected verbatim as JSON | JSON preserves structure (prices, hours, service details) without information loss. The model can reason over it more reliably than prose paraphrase. |
| Visual separator around SOP block | Visually and semantically marks the SOP as a boundary — the model is less likely to bleed outside it. |
| Tone declared first | The model anchors its persona from the first instruction. Declaring "warm, professional, concise" upfront reduces the chance of cold or verbose responses. |
| Mandatory JSON output contract | All responses are structured — enables programmatic escalation detection, confidence checks, and scope tracking without fragile string parsing. |

---

## 2. Hallucination Prevention

### Strategy: Retrieval Grounding + Explicit Refusal Instruction

Hallucination is the primary safety risk for an SMB AI handling medical aesthetics enquiries. Providing fabricated pricing, unavailable services, or false medical claims could damage trust or cause harm.

**Three-layer approach:**

#### Layer 1 — Inject SOP at every call
```python
system = SYSTEM_PROMPT.format(sop=format_sop_for_prompt(state["sop_data"]))
```
The SOP is injected as the system prompt's context at **every turn**, not once at session start. This ensures the model always has the authoritative source in context, even in long conversations.

#### Layer 2 — Hard grounding instruction
The system prompt includes an explicit rule block:
```
GROUNDING RULES (CRITICAL — NEVER VIOLATE):
1. Answer ONLY from the SOP above.
2. If the answer is partially in the SOP, share what you know and flag the gap.
3. If the answer is NOT in the SOP at all, set "in_scope": false and do not guess.
4. Never speculate on medical outcomes, drug interactions, or individual suitability.
```

The label **"CRITICAL — NEVER VIOLATE"** is intentional — LLMs respond to emphasis in instructions. The word "speculate" is specifically chosen to block the model from hedging its way into unsafe medical territory.

#### Layer 3 — Structured output gate
By requiring JSON with `"in_scope": bool`, we create a forced self-assessment. The model must explicitly classify whether it can ground its answer:
```json
{
  "in_scope": false,
  "answer": "I don't have information about that in our current offering...",
  "escalate": false
}
```
If `in_scope` is false and `unanswered_count >= 2`, the system automatically escalates — preventing the model from being repeatedly asked out-of-scope questions with no human fallback.

**Few-shot examples in the prompt** show the model how to handle both in-scope (Botox pricing) and out-of-scope (laser hair removal) questions, anchoring its behaviour before it sees a real query.

---

## 3. Confidence-Based Escalation

### Detection Method: Structured JSON Flag + Threshold Counter

I chose **explicit structured output** over threshold-based scoring for the primary escalation trigger. Here's why:

| Method | Pros | Cons |
|---|---|---|
| Confidence score (0-1 float) | Granular | Arbitrary thresholds; inconsistent across queries |
| Structured flag + reason | Predictable; auditable; LLM-native | Binary; requires good prompting |
| Sentiment classifier (separate model) | Specialised | Extra latency; extra cost |

**Chosen approach:** The main SOP prompt returns `"escalate": true/false` with `"escalation_reason"`. A secondary `ESCALATION_CHECK_PROMPT` runs as a validation pass when the primary model flags escalation, confirming with sentiment + scope analysis.

```json
{
  "escalate": true,
  "reason": "Customer reported adverse reaction and expressed frustration",
  "sentiment": "distressed",
  "confidence": "high"
}
```

### Escalation Triggers (from system prompt)
1. **Anger / frustration** — any intensity, even mild ("a bit annoyed")
2. **Complaint about past treatment** — any mention of a negative prior experience
3. **Medical question** beyond SOP scope (drug interactions, contraindications)
4. **Price negotiation / discount request**
5. **Refund request**
6. **Explicit human request** ("can I speak to someone?")
7. **Two+ unanswered questions** — tracked via `unanswered_count` in state

### Logging
Every escalation writes a timestamped JSONL record to `logs/escalations.jsonl`:
```json
{
  "timestamp": "2025-05-23T14:32:01Z",
  "reason": "Customer reported adverse reaction",
  "qualification_data": {...},
  "unanswered_count": 0,
  "message_count": 3
}
```
This creates an auditable trail for team review.

---

## 4. Tone & Persona

### Target Persona: "Bloom"

**SMB context:** Bloom Aesthetics Clinic is a small medical aesthetics clinic, not a corporate healthcare provider. Their customers are booking personal, appearance-related treatments. The AI needs to feel like a knowledgeable, welcoming receptionist — not a cold FAQ bot.

**Tone guidelines baked into the system prompt:**
- **Warm and empathetic** — especially important for a clinic where customers may feel vulnerable or anxious
- **Concise** (2-4 sentences default) — customers on WhatsApp don't want paragraphs
- **No jargon** — "forehead lines" not "glabellar complex"
- **Light formatting** — bold key info (prices, hours) but avoid bulleted lists for simple answers
- **No AI self-reference** — never "As an AI, I..." — Bloom is an extension of the clinic team

**Anti-patterns explicitly banned:**
- Making up staff names, addresses, or services
- Speculating on medical suitability
- Using dismissive or cold language
- Excessive caveating (e.g., "I think possibly maybe...")

### Example response demonstrating persona
```
Customer: "How much does Botox cost?"

Bloom: "Our Botox treatments start from £200. The exact price depends on the areas 
being treated, which we'll discuss during your free consultation. Would you like 
to book one? 😊"
```
Warm, factual, action-oriented, closes with an invitation — matches clinic brand.

---

## 5. LangGraph Workflow Design

### Why LangGraph?

LangGraph allows explicit state management with typed nodes and conditional routing. This maps cleanly to the four stages of the workflow:

```
[Entry] → faq_node → [route_after_faq] ─┬→ qualification_node → [wait for input]
                                          ├→ escalation_node → summary_node → END
                                          └→ summary_node → END
```

### State Design
The `ConversationState` TypedDict tracks:
- `messages` — full LangChain message history (annotated with `add_messages` for automatic append)
- `stage` — current node label for routing
- `qualification_data / step / complete` — lead intake progress
- `escalated / reason / logged` — escalation audit trail
- `unanswered_count` — scope tracking across turns
- `sop_data` — injected once at session start, passed through state

### Temperature
`temperature=0.2` — low temperature for factual SOP responses. The model should be consistent and precise, not creative. Slightly above 0 to allow natural language variation in phrasing.

---

## 6. Trade-offs & Known Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| No vector search / semantic retrieval | SOP is injected in full; won't scale to large SOPs | Fine for this demo; production should use Qdrant/RAG |
| No persistent memory across sessions | Each session starts fresh | Add LangGraph checkpointing + Redis for production |
| JSON parsing fallback is lenient | Malformed model output degrades to plain text | Acceptable for demo; add Pydantic validation for production |
| No human-agent handoff integration | Escalation is logged but not routed | Requires CRM/ticketing webhook integration |
| Single-language support | English only | Add language detection + multilingual prompts for real SMB use |

---

## 7. Production Improvements (if extended)

1. **Qdrant vector store** — embed SOP chunks; retrieve relevant sections per query rather than injecting the full SOP
2. **LangGraph checkpointing** — persist conversation state to Redis for session continuity across WhatsApp reconnects
3. **Langfuse observability** — trace every LLM call, log token usage, monitor escalation rates and SOP gap frequency
4. **Webhook escalation** — POST escalation events to a CRM (HubSpot, Pipedrive) or ticket system (Zendesk)
5. **A/B prompt testing** — evaluate multiple system prompt variants against real conversations using LangSmith
