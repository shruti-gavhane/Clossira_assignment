# Test Transcript 4: Lead Qualification — Full 3-Question Intake

**Scenario:** Customer expresses interest in services. AI runs through the complete 3-question qualification flow and produces a qualification summary.

---

**Bloom (AI):** Hello! Welcome to Bloom Aesthetics Clinic. 🌸 I'm Bloom, your virtual assistant. How can I help you today?

**Customer:** I'd like to find out more about your services.

> 🔍 Internal: `in_scope: true` | `confidence: high` | `escalate: false`

**Bloom (AI):** Of course! We offer a range of aesthetic treatments at Bloom, including **Botox** (from £200), **Dermal Fillers** (from £250), and **free initial consultations** for all new patients. All treatments are carried out by our qualified practitioners with over 10 years of combined experience.

To help us better understand how we can help you, I'd love to ask a few quick questions. 😊

---

**[QUALIFICATION — Question 1 of 3]**

**Bloom (AI):** To help us prepare for your visit — are you a new patient or have you visited us before?

**Customer:** I'm a new patient, haven't been before.

> 📝 Qualification Q1 recorded: `"patient_type": "New patient"`

---

**[QUALIFICATION — Question 2 of 3]**

**Bloom (AI):** Great, welcome! Which treatment are you most interested in? (e.g., Botox, Fillers, or a general Consultation)

**Customer:** I'm interested in Botox for my forehead, I have some lines I'd like to address.

> 📝 Qualification Q2 recorded: `"treatment_interest": "Botox — forehead lines"`

---

**[QUALIFICATION — Question 3 of 3]**

**Bloom (AI):** That's one of our most popular treatments! Is there a particular concern or area you'd like to focus on, or are you still exploring your options?

**Customer:** I have some deep forehead lines and frown lines between my eyebrows. I'd like to soften them before a big event in 3 months.

> 📝 Qualification Q3 recorded: `"primary_concern": "Deep forehead lines and frown lines (glabella). Event-driven timeline: 3 months."`

---

**[QUALIFICATION COMPLETE]**

**Bloom (AI):** That's really helpful, thank you! Botox is a great option for exactly those areas — results typically appear within 2 weeks and last 3–6 months, so timing-wise you're in great shape for your event. 🎉

The next step would be a **free consultation** (about 20–30 minutes) where one of our practitioners can assess your needs and create a personalised treatment plan. You can book via WhatsApp or our website — would you like guidance on how to book?

---

## 📋 Qualification Summary

```json
{
  "q1": {
    "question": "Are you a new patient or have you visited us before?",
    "answer": "New patient — first visit"
  },
  "q2": {
    "question": "Which treatment are you most interested in?",
    "answer": "Botox for forehead"
  },
  "q3": {
    "question": "Is there a particular concern or area you'd like to address?",
    "answer": "Deep forehead lines and frown lines before an event in 3 months"
  }
}
```

---

## 📋 Session Summary

# Session Summary — Bloom Aesthetics Clinic

## Customer Intent
New patient enquiring about Botox treatment for forehead lines and glabellar frown lines. Has a specific event-driven timeline (3 months).

## Key Details Collected
- **Patient type:** New patient (first visit)
- **Treatment interest:** Botox
- **Target areas:** Forehead lines, frown lines (glabella)
- **Motivation:** Wants to look refreshed for a specific event in approximately 3 months
- **Timeline:** 3 months — well within recommended treatment window (results in 2 weeks, lasting 3–6 months)

## Qualification Summary
All 3 qualification questions completed. Customer is a strong lead — clear treatment preference, specific concern, and actionable timeline.

## SOP Gaps Identified
None — all questions were answerable from the SOP. The mention of frown lines and forehead areas is covered under Botox treatment areas in the SOP.

## Escalation Status
**Escalated: No**

## Recommended Next Action
Book a **free consultation** for this new patient. Suggest the practitioner discuss:
1. Assessment of forehead and glabellar area
2. Expected Botox dosage and pricing
3. Pre-treatment advice (avoid alcohol 24h before, no makeup on the day)
4. Confirm timing relative to their event (2-week onset + buffer recommended)

## Conversation Quality Notes
Smooth, natural qualification flow. Customer was engaged and forthcoming. AI correctly used SOP information to reinforce the value proposition (timing aligns well with their event). Strong lead — recommend prioritising booking confirmation.

---

## ✅ Expected Behaviour: PASSED

- All 3 qualification questions asked in sequence ✓
- Customer answers collected and stored in structured `qualification_data` ✓
- AI used answers to provide relevant, SOP-grounded follow-up ✓
- Qualification summary generated with all key details ✓
- Session summary includes recommended next action ✓
- No escalation triggered (clean, positive interaction) ✓
