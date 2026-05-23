"""
Closira AI Workflow — workflow.py
LangGraph-powered multi-stage customer support agent for Bloom Aesthetics Clinic.

Stages:
  1. FAQ Answering    — grounded in SOP JSON only
  2. Lead Qualification — structured 3-question intake
  3. Escalation Detection — sentiment + scope + confidence checks
  4. Conversation Summary — structured handoff/close document
"""

import json
import os
from typing import Annotated, Literal, Optional

# Load .env if present (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from prompts import (
    SYSTEM_PROMPT,
    QUALIFICATION_PROMPT,
    ESCALATION_CHECK_PROMPT,
    SUMMARY_PROMPT,
)

# ─────────────────────────────────────────────────────────────────────────────
# State Definition
# ─────────────────────────────────────────────────────────────────────────────

class ConversationState(TypedDict):
    # Full message history
    messages: Annotated[list, add_messages]

    # Current workflow stage
    stage: Literal["faq", "qualification", "escalation", "summary", "end"]

    # Lead qualification data
    qualification_data: dict          # collected answers
    qualification_step: int           # which question we're on (0-based)
    qualification_complete: bool

    # Escalation
    escalated: bool
    escalation_reason: Optional[str]
    escalation_logged: bool

    # Summary
    session_summary: Optional[str]

    # Internal tracking
    unanswered_count: int             # out-of-scope questions in session
    sop_data: dict                    # loaded once, passed through state


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

SOP_PATH = os.path.join(os.path.dirname(__file__), "data", "sop.json")

def load_sop() -> dict:
    with open(SOP_PATH, "r") as f:
        return json.load(f)


def get_llm() -> ChatOpenAI:
    """
    Returns a ChatOpenAI instance pointed at OpenRouter.
    OpenRouter is OpenAI-API-compatible, so langchain-openai works out of the box.
    Set OPENROUTER_API_KEY and optionally OPENROUTER_MODEL in your .env file.
    Default model: anthropic/claude-sonnet-4-5 (change freely in .env)
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENROUTER_API_KEY is not set. "
            "Add it to your .env file: OPENROUTER_API_KEY=sk-or-..."
        )
    model = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5")
    return ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        max_tokens=1000,
        temperature=0.2,          # low temp for factual SOP answers
        default_headers={
            # Optional but recommended by OpenRouter for analytics
            "HTTP-Referer": "https://github.com/closira-assignment",
            "X-Title": "Closira AI Workflow",
        },
    )


def format_sop_for_prompt(sop: dict) -> str:
    """Serialise the SOP to a clean string block for injection into prompts."""
    return json.dumps(sop, indent=2)


def detect_booking_intent(text: str) -> bool:
    """Detect if the customer wants to book / has clear treatment intent."""
    text = text.lower()
    booking_keywords = [
        "book", "booking", "appointment", "consultation",
        "schedule", "visit", "interested", "sign me up",
    ]
    return any(k in text for k in booking_keywords)


# ─────────────────────────────────────────────────────────────────────────────
# Node 1 — FAQ / SOP Answering
# ─────────────────────────────────────────────────────────────────────────────

def faq_node(state: ConversationState) -> ConversationState:
    """
    Answers customer questions strictly from the SOP.
    Returns a structured JSON response with:
      - answer
      - confidence (high / medium / low)
      - escalate (bool)
      - escalation_reason (str | null)
      - in_scope (bool)

    Routing after this node:
      - escalation  → if escalate flag is set
      - qualification → if customer is mid-qualification (qualification_step > 0)
                        OR if booking intent detected and qualification not started yet
      - END (wait for next user message) → default: continue the conversation
    """
    llm = get_llm()
    sop_text = format_sop_for_prompt(state["sop_data"])

    system = SYSTEM_PROMPT.format(sop=sop_text)

    # Build messages for the LLM (system + full history)
    lc_messages = [SystemMessage(content=system)] + state["messages"]

    response = llm.invoke(lc_messages)
    raw = response.content.strip()

    # Parse structured JSON response
    try:
        # Model may wrap JSON in ```json blocks — strip them
        clean = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean)
    except json.JSONDecodeError:
        # Fallback: treat entire response as plain answer with unknown confidence
        parsed = {
            "answer": raw,
            "confidence": "medium",
            "escalate": False,
            "escalation_reason": None,
            "in_scope": True,
        }

    answer_text = parsed.get("answer", raw)
    escalate = parsed.get("escalate", False)
    escalation_reason = parsed.get("escalation_reason")
    in_scope = parsed.get("in_scope", True)

    # Track out-of-scope count
    unanswered = state.get("unanswered_count", 0)
    if not in_scope:
        unanswered += 1

    # Auto-escalate after 2 unanswered / out-of-scope questions
    if unanswered >= 2 and not escalate:
        escalate = True
        escalation_reason = f"Exceeded 2 out-of-scope questions (count: {unanswered})"

    # ── Determine next stage ──────────────────────────────────────────────────
    # Priority: escalation > qualification (if in-progress or booking intent) > wait for user
    if escalate:
        next_stage = "escalation"
    elif state.get("qualification_step", 0) > 0 and not state.get("qualification_complete", False):
        # Qualification is already in-progress; route back so the next question is asked
        next_stage = "qualification"
    else:
        # Detect booking/treatment intent in the latest human message
        last_human = next(
            (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
            None,
        )
        booking_intent = detect_booking_intent(last_human.content) if last_human else False

        if booking_intent:
            next_stage = "qualification"
        else:
            # Normal FAQ answer — stay in FAQ mode and wait for the next user message
            next_stage = "faq"

    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=answer_text)],
        "stage": next_stage,
        "escalated": escalate,
        "escalation_reason": escalation_reason,
        "unanswered_count": unanswered,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Node 2 — Lead Qualification
# ─────────────────────────────────────────────────────────────────────────────

QUALIFICATION_QUESTIONS = [
    "To help us prepare for your visit — are you a new patient or have you visited us before?",
    "Which treatment are you most interested in? (e.g., Botox, Fillers, or a general Consultation)",
    "Is there a particular concern or area you'd like to address, or are you still exploring options?",
]


def qualification_node(state: ConversationState) -> ConversationState:
    """
    Asks up to 3 qualification questions, one per turn.
    Stores answers in qualification_data and marks complete when done.

    Flow:
      - On first entry (step=0): ask question 1, increment step to 1, wait for user.
      - On re-entry (step>0): store previous answer, ask next question, wait for user.
      - When all questions answered: mark complete and route to summary.
    """
    step = state.get("qualification_step", 0)
    qual_data = dict(state.get("qualification_data", {}))

    # If we're re-entering after the user replied to a question, store that answer
    if step > 0 and state["messages"]:
        last_human = next(
            (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
            None,
        )
        if last_human:
            question_key = f"q{step}"
            qual_data[question_key] = {
                "question": QUALIFICATION_QUESTIONS[step - 1],
                "answer": last_human.content,
            }

    if step >= len(QUALIFICATION_QUESTIONS):
        # All questions asked and answers stored → mark complete
        return {
            **state,
            "qualification_data": qual_data,
            "qualification_step": step,
            "qualification_complete": True,
            "stage": "summary",
        }

    # Ask the next question
    question = QUALIFICATION_QUESTIONS[step]
    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=question)],
        "qualification_data": qual_data,
        "qualification_step": step + 1,
        "qualification_complete": False,
        "stage": "faq",   # after user answers, the next user message re-enters faq_node first
    }


# ─────────────────────────────────────────────────────────────────────────────
# Node 3 — Escalation Detection
# ─────────────────────────────────────────────────────────────────────────────

def escalation_node(state: ConversationState) -> ConversationState:
    """
    Logs escalation event, notifies the customer, and terminates the AI session.
    Also proactively checks the latest message for sentiment triggers.
    """
    llm = get_llm()

    # Use the LLM to double-check latest message for sentiment/scope
    last_human = next(
        (m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)),
        None,
    )

    detected_reason = state.get("escalation_reason", "Unspecified")

    if last_human:
        check_prompt = ESCALATION_CHECK_PROMPT.format(
            message=last_human.content,
            sop=format_sop_for_prompt(state["sop_data"]),
        )
        check_response = llm.invoke([SystemMessage(content=check_prompt)])
        try:
            clean = check_response.content.strip().replace("```json", "").replace("```", "").strip()
            check_data = json.loads(clean)
            if check_data.get("escalate") and check_data.get("reason"):
                detected_reason = check_data["reason"]
        except Exception:
            pass

    # Log escalation
    log_escalation(state, detected_reason)

    handoff_message = (
        "I want to make sure you get the best support possible. 🌸 "
        "I'm connecting you with one of our team members who will be in touch shortly. "
        f"\n\n📋 **Reason for handoff:** {detected_reason}\n\n"
        "Our team is available Mon–Sat, 9 am–7 pm. "
        "You can also reach us directly on WhatsApp."
    )

    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=handoff_message)],
        "escalated": True,
        "escalation_reason": detected_reason,
        "escalation_logged": True,
        "stage": "summary",
    }


def log_escalation(state: ConversationState, reason: str):
    """Persist escalation to a log file."""
    os.makedirs("logs", exist_ok=True)
    import datetime
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "reason": reason,
        "qualification_data": state.get("qualification_data", {}),
        "unanswered_count": state.get("unanswered_count", 0),
        "message_count": len(state.get("messages", [])),
    }
    log_path = os.path.join("logs", "escalations.jsonl")
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"\n  [ESCALATION LOGGED] → {log_path}")
    print(f"  Reason: {reason}\n")


# ─────────────────────────────────────────────────────────────────────────────
# Node 4 — Conversation Summary
# ─────────────────────────────────────────────────────────────────────────────

def summary_node(state: ConversationState) -> ConversationState:
    """
    Generates a structured session summary for the human agent or internal records.
    """
    llm = get_llm()

    # Compile conversation transcript
    transcript = "\n".join(
        f"{'Customer' if isinstance(m, HumanMessage) else 'Agent'}: {m.content}"
        for m in state["messages"]
    )

    summary_prompt = SUMMARY_PROMPT.format(
        transcript=transcript,
        qualification_data=json.dumps(state.get("qualification_data", {}), indent=2),
        escalated=state.get("escalated", False),
        escalation_reason=state.get("escalation_reason", "N/A"),
        sop=format_sop_for_prompt(state["sop_data"]),
    )

    response = llm.invoke([SystemMessage(content=summary_prompt)])
    summary_text = response.content.strip()

    # Save summary to file
    os.makedirs("logs", exist_ok=True)
    import datetime
    summary_path = os.path.join("logs", f"summary_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md")
    with open(summary_path, "w") as f:
        f.write(summary_text)

    print(f"\n  [SUMMARY SAVED] → {summary_path}\n")

    return {
        **state,
        "session_summary": summary_text,
        "stage": "end",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Router functions
# ─────────────────────────────────────────────────────────────────────────────

def route_after_faq(state: ConversationState) -> str:
    """
    After faq_node runs, decide which node to visit next (within the same graph step).
    - escalation  → if faq set escalated flag
    - qualification → if faq detected booking intent or qualification is in-progress
    - END          → normal FAQ answer; pause and wait for the next user message
    """
    if state.get("escalated"):
        return "escalation"
    if state["stage"] == "qualification":
        return "qualification"
    # stage == "faq" means: answer was given, wait for next user turn
    return END


def route_after_qualification(state: ConversationState) -> str:
    if state.get("qualification_complete"):
        return "summary"
    return END  # question asked; wait for user's answer


def route_after_escalation(state: ConversationState) -> str:
    return "summary"


def route_after_summary(state: ConversationState) -> str:
    return END


# ─────────────────────────────────────────────────────────────────────────────
# Build the LangGraph
# ─────────────────────────────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(ConversationState)

    graph.add_node("faq", faq_node)
    graph.add_node("qualification", qualification_node)
    graph.add_node("escalation", escalation_node)
    graph.add_node("summary", summary_node)

    graph.set_entry_point("faq")

    graph.add_conditional_edges(
        "faq",
        route_after_faq,
        {
            "escalation": "escalation",
            "qualification": "qualification",
            END: END,
        },
    )

    graph.add_conditional_edges(
        "qualification",
        route_after_qualification,
        {
            "summary": "summary",
            END: END,
        },
    )

    graph.add_conditional_edges(
        "escalation",
        route_after_escalation,
        {"summary": "summary"},
    )

    graph.add_conditional_edges(
        "summary",
        route_after_summary,
        {END: END},
    )

    return graph.compile()
