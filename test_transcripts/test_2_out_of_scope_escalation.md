# Test Transcript 2: Out-of-Scope Question — Escalation

**Scenario:** Customer asks three questions not in the SOP. AI should acknowledge each gap and escalate after the second unanswered question.

---

**Bloom (AI):** Hello! Welcome to Bloom Aesthetics Clinic. 🌸 I'm Bloom, your virtual assistant. How can I help you today?

**Customer:** Do you offer laser hair removal?

> 🔍 Internal: `in_scope: false` | `confidence: low` | `escalate: false` | `unanswered_count: 1`

**Bloom (AI):** I'm afraid I don't have information about laser hair removal in our current service offering. I'd recommend speaking directly with our team — they'll be happy to give you the most up-to-date answer! You can reach us via WhatsApp or our website.

**Customer:** What about microneedling treatments?

> 🔍 Internal: `in_scope: false` | `confidence: low` | `escalate: false` | `unanswered_count: 2`

**Bloom (AI):** I don't have details on microneedling in our current services either. I want to make sure you get accurate information rather than guessing — I'm going to connect you with a member of our team who can answer these questions properly. 🌸

> ⚠️ **ESCALATION TRIGGERED**  
> **Reason:** Exceeded 2 out-of-scope / unanswered questions (count: 2)

**Bloom (AI):** I want to make sure you get the best support possible. 🌸 I'm connecting you with one of our team members who will be in touch shortly.

📋 **Reason for handoff:** Exceeded 2 out-of-scope questions — customer asked about services not listed in the clinic SOP (laser hair removal, microneedling).

Our team is available Mon–Sat, 9 am–7 pm. You can also reach us directly on WhatsApp.

---

## 📋 Session Summary

# Session Summary — Bloom Aesthetics Clinic

## Customer Intent
Customer was enquiring about cosmetic services — specifically laser hair removal and microneedling — neither of which is listed in the current SOP.

## Key Details Collected
- No personal details provided
- Interested in: laser hair removal, microneedling

## Qualification Summary
Qualification not completed — session escalated before questions were answered.

## SOP Gaps Identified
- **Laser hair removal** — not in SOP; customer asked about it
- **Microneedling** — not in SOP; customer asked about it
- Recommendation: Consider adding a "services we don't offer" section to the SOP, or a referral pathway for enquiries about unlisted services

## Escalation Status
**Escalated: Yes**  
Reason: 2 consecutive out-of-scope questions with no SOP-grounded answer available.

## Recommended Next Action
Human agent should follow up to clarify whether the clinic offers or plans to offer these services, and either answer the customer's query or direct them to an appropriate provider.

## Conversation Quality Notes
AI handled the gaps gracefully — acknowledged limitations without fabricating information. Escalation threshold (2 unanswered questions) functioned correctly. SOP gap log updated for clinic review.

---

## ✅ Expected Behaviour: PASSED

- AI did **not** fabricate answers for out-of-scope questions ✓
- AI acknowledged gaps honestly and politely ✓
- **Escalation triggered at exactly 2 unanswered questions** ✓
- Escalation reason logged to `logs/escalations.jsonl` ✓
- SOP gaps identified in summary ✓
