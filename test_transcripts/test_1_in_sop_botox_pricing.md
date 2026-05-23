# Test Transcript 1: In-SOP Question — Botox Pricing

**Scenario:** Customer asks about Botox prices. AI should answer accurately from SOP only.

---

**Bloom (AI):** Hello! Welcome to Bloom Aesthetics Clinic. 🌸 I'm Bloom, your virtual assistant. How can I help you today?

**Customer:** Hi, what are your Botox prices?

> 🔍 Internal: `in_scope: true` | `confidence: high` | `escalate: false`

**Bloom (AI):** Our Botox treatments start from **£200**. The exact price depends on the areas being treated — we cover areas like forehead lines, frown lines, and crow's feet. The best way to get a personalised quote is during your free consultation. Would you like to book one? 😊

**Customer:** How long does it last?

> 🔍 Internal: `in_scope: true` | `confidence: high` | `escalate: false`

**Bloom (AI):** Botox results typically last **3 to 6 months**, depending on the individual and the area treated. Many clients find that with regular treatments, results can become more consistent over time. Is there anything else you'd like to know?

**Customer:** And what about fillers?

> 🔍 Internal: `in_scope: true` | `confidence: high` | `escalate: false`

**Bloom (AI):** Our dermal filler treatments start from **£250**. Fillers are great for adding volume and contouring areas like lips, cheeks, jawline, and nasolabial folds. Results generally last **6 to 18 months** depending on the area. As with Botox, we'd discuss the specifics during your free consultation first. Would you like to arrange one?

---

## ✅ Expected Behaviour: PASSED

- AI answered all three questions **accurately from the SOP only**
- Prices quoted: Botox from £200, Fillers from £250 ✓
- Duration quoted: 3-6 months Botox, 6-18 months fillers ✓
- No information fabricated beyond SOP ✓
- Consistently offered free consultation as CTA ✓
- Tone: warm, concise, professional ✓

---

**[QUALIFICATION STARTED — awaiting customer reply]**

**Bloom (AI):** To help us prepare for your visit — are you a new patient or have you visited us before?
