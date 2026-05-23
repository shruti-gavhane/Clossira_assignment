"""
main.py — CLI runner for the Closira / Bloom Aesthetics AI workflow.

Usage:
    python main.py               # interactive mode
    python main.py --test <n>    # run automated test scenario 1-5
    python main.py --test all    # run all test scenarios
"""

import sys
import os
import json
import argparse
from langchain_core.messages import HumanMessage

# ─── ensure project root is on path ───────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from workflow import build_graph, load_sop, ConversationState

# Rich for pretty CLI output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.rule import Rule
    USE_RICH = True
except ImportError:
    USE_RICH = False

console = Console() if USE_RICH else None


# ─────────────────────────────────────────────────────────────────────────────
# Pretty print helpers
# ─────────────────────────────────────────────────────────────────────────────

def print_header():
    if USE_RICH:
        console.print(Rule("[bold pink]🌸 Bloom Aesthetics Clinic — AI Support Agent[/bold pink]"))
        console.print("[dim]Powered by Closira · LangGraph + Claude[/dim]\n")
    else:
        print("\n" + "="*60)
        print("  🌸  Bloom Aesthetics Clinic — AI Support Agent")
        print("  Powered by Closira · LangGraph + Claude")
        print("="*60 + "\n")


def print_agent(text: str):
    if USE_RICH:
        console.print(Panel(text, title="[bold green]Bloom (AI)[/bold green]", border_style="green", padding=(0,1)))
    else:
        print(f"\n[Bloom AI]: {text}\n")


def print_customer(text: str):
    if USE_RICH:
        console.print(f"[bold cyan]You:[/bold cyan] {text}")
    else:
        print(f"[Customer]: {text}")


def print_summary(text: str):
    if USE_RICH:
        console.print(Rule("[bold yellow]📋 Session Summary[/bold yellow]"))
        console.print(text)
        console.print(Rule())
    else:
        print("\n" + "="*60)
        print("SESSION SUMMARY")
        print("="*60)
        print(text)
        print("="*60 + "\n")


def print_stage(stage: str):
    stage_labels = {
        "faq": "💬 FAQ Mode",
        "qualification": "📝 Lead Qualification",
        "escalation": "🚨 Escalation",
        "summary": "📋 Generating Summary",
        "end": "✅ Session Complete",
    }
    label = stage_labels.get(stage, stage)
    if USE_RICH:
        console.print(f"[dim]  Stage: {label}[/dim]")
    else:
        print(f"  [Stage: {label}]")


# ─────────────────────────────────────────────────────────────────────────────
# Initial state factory
# ─────────────────────────────────────────────────────────────────────────────

def make_initial_state(sop: dict) -> ConversationState:
    return {
        "messages": [],
        "stage": "faq",
        "qualification_data": {},
        "qualification_step": 0,
        "qualification_complete": False,
        "escalated": False,
        "escalation_reason": None,
        "escalation_logged": False,
        "session_summary": None,
        "unanswered_count": 0,
        "sop_data": sop,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Run a single turn through the graph
# ─────────────────────────────────────────────────────────────────────────────

def run_turn(graph, state: ConversationState, user_input: str) -> ConversationState:
    """Add user message to state and invoke the graph for one turn."""
    new_messages = state["messages"] + [HumanMessage(content=user_input)]
    updated_state = {**state, "messages": new_messages}
    result = graph.invoke(updated_state)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Get last AI response from state
# ─────────────────────────────────────────────────────────────────────────────

def get_last_ai_message(state: ConversationState) -> str:
    from langchain_core.messages import AIMessage
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage):
            return msg.content
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Interactive Mode
# ─────────────────────────────────────────────────────────────────────────────

def run_interactive():
    print_header()
    sop = load_sop()
    graph = build_graph()
    state = make_initial_state(sop)

    if USE_RICH:
        console.print("[dim]Type 'quit' or 'exit' to end session. Type 'summary' to generate summary now.[/dim]\n")
    else:
        print("Type 'quit' or 'exit' to end. Type 'summary' to generate summary.\n")

    # Opening greeting
    greeting = (
        "Hello! Welcome to Bloom Aesthetics Clinic. 🌸 I'm Bloom, your virtual assistant. "
        "I'm here to help with any questions about our treatments, booking, or anything else you'd like to know. "
        "How can I help you today?"
    )
    print_agent(greeting)

    while True:
        try:
            if USE_RICH:
                user_input = console.input("[bold cyan]You:[/bold cyan] ").strip()
            else:
                user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            break

        if user_input.lower() == "summary":
            # Force summary generation
            state = {**state, "qualification_complete": True, "stage": "summary"}
            from workflow import summary_node
            state = summary_node(state)
            print_summary(state.get("session_summary", "No summary available."))
            break

        state = run_turn(graph, state, user_input)
        print_stage(state.get("stage", ""))

        ai_response = get_last_ai_message(state)
        if ai_response:
            print_agent(ai_response)

        # End conditions
        if state.get("stage") == "end":
            print_summary(state.get("session_summary", ""))
            break

        if state.get("escalated") and state.get("escalation_logged"):
            if USE_RICH:
                console.print("[bold red]  ⚠ Session handed off to human agent. Ending AI session.[/bold red]\n")
            else:
                print("\n  ⚠ Session handed off to human agent. Ending AI session.\n")
            print_summary(state.get("session_summary", ""))
            break

    if USE_RICH:
        console.print(Rule("[dim]Session ended[/dim]"))
    else:
        print("\n--- Session ended ---")


# ─────────────────────────────────────────────────────────────────────────────
# Automated Test Scenarios
# ─────────────────────────────────────────────────────────────────────────────

TEST_SCENARIOS = {
    1: {
        "name": "In-SOP Question — Botox Pricing",
        "description": "Customer asks about Botox prices. AI should answer accurately from SOP.",
        "turns": [
            "Hi, what are your Botox prices?",
            "How long does it last?",
            "And what about fillers?",
        ],
        "end_after": 3,
    },
    2: {
        "name": "Out-of-Scope Question — Escalation",
        "description": "Customer asks something not in the SOP. AI should acknowledge gap and escalate after 2.",
        "turns": [
            "Do you offer laser hair removal?",
            "What about microneedling treatments?",
            "Can you do chemical peels?",
        ],
        "end_after": 3,
    },
    3: {
        "name": "Escalation Trigger — Angry Sentiment",
        "description": "Customer expresses frustration. AI should detect and hand off.",
        "turns": [
            "I had a Botox treatment last month and my face looks terrible now. I'm extremely unhappy.",
        ],
        "end_after": 1,
    },
    4: {
        "name": "Lead Qualification",
        "description": "Full 3-question qualification flow.",
        "turns": [
            "I'd like to find out more about your services.",
            "I'm a new patient.",       # answer to q1
            "I'm interested in Botox for my forehead.",  # answer to q2
            "I have some deep forehead lines I'd like to address.",  # answer to q3
        ],
        "end_after": 4,
    },
    5: {
        "name": "Conversation Summary",
        "description": "Full conversation leading to a clean structured summary.",
        "turns": [
            "What services do you offer?",
            "How do I book a consultation?",
            "I'm a new patient and interested in fillers.",
            "summary",  # trigger summary
        ],
        "end_after": 4,
    },
}


def run_test(scenario_id: int, save_transcript: bool = True):
    scenario = TEST_SCENARIOS[scenario_id]
    sop = load_sop()
    graph = build_graph()
    state = make_initial_state(sop)

    if USE_RICH:
        console.print(Rule(f"[bold blue]Test {scenario_id}: {scenario['name']}[/bold blue]"))
        console.print(f"[dim]{scenario['description']}[/dim]\n")
    else:
        print(f"\n{'='*60}")
        print(f"Test {scenario_id}: {scenario['name']}")
        print(f"{scenario['description']}")
        print('='*60)

    transcript_lines = [
        f"# Test Transcript {scenario_id}: {scenario['name']}",
        f"\n**Scenario:** {scenario['description']}\n",
        "---\n",
    ]

    greeting = (
        "Hello! Welcome to Bloom Aesthetics Clinic. 🌸 I'm Bloom, your virtual assistant. "
        "How can I help you today?"
    )
    print_agent(greeting)
    transcript_lines.append(f"**Bloom (AI):** {greeting}\n")

    for turn_idx, user_msg in enumerate(scenario["turns"]):
        if user_msg == "summary":
            state = {**state, "qualification_complete": True, "stage": "summary"}
            from workflow import summary_node
            state = summary_node(state)
            print_summary(state.get("session_summary", ""))
            transcript_lines.append(f"\n---\n\n**[SUMMARY GENERATED]**\n\n{state.get('session_summary', '')}\n")
            break

        print_customer(user_msg)
        transcript_lines.append(f"**Customer:** {user_msg}\n")

        state = run_turn(graph, state, user_msg)
        ai_response = get_last_ai_message(state)

        print_stage(state.get("stage", ""))
        if ai_response:
            print_agent(ai_response)
            transcript_lines.append(f"**Bloom (AI):** {ai_response}\n")

        if state.get("escalated"):
            transcript_lines.append(
                f"\n> ⚠️ **ESCALATION TRIGGERED**\n> Reason: {state.get('escalation_reason', 'N/A')}\n"
            )

        if state.get("stage") == "end":
            print_summary(state.get("session_summary", ""))
            transcript_lines.append(f"\n---\n\n**[SUMMARY]**\n\n{state.get('session_summary', '')}\n")
            break

        if state.get("escalated") and state.get("escalation_logged"):
            from workflow import summary_node
            state = summary_node(state)
            print_summary(state.get("session_summary", ""))
            transcript_lines.append(f"\n---\n\n**[SUMMARY]**\n\n{state.get('session_summary', '')}\n")
            break

    # Save transcript
    if save_transcript:
        os.makedirs("test_transcripts", exist_ok=True)
        filename = f"test_transcripts/test_{scenario_id}_{scenario['name'].lower().replace(' ', '_').replace('—','').replace('__','_')[:40]}.md"
        with open(filename, "w") as f:
            f.write("\n".join(transcript_lines))
        if USE_RICH:
            console.print(f"[dim]  📄 Transcript saved: {filename}[/dim]\n")
        else:
            print(f"\n  Transcript saved: {filename}\n")

    return state


# ─────────────────────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Closira AI Workflow — Bloom Aesthetics Clinic"
    )
    parser.add_argument(
        "--test",
        nargs="?",
        const="all",
        help="Run test scenario(s). Pass a number 1-5 or 'all'.",
    )
    args = parser.parse_args()

    if args.test:
        if args.test == "all":
            for scenario_id in TEST_SCENARIOS:
                run_test(scenario_id)
        else:
            try:
                scenario_id = int(args.test)
                if scenario_id not in TEST_SCENARIOS:
                    print(f"Unknown scenario: {scenario_id}. Choose 1-{len(TEST_SCENARIOS)}.")
                    sys.exit(1)
                run_test(scenario_id)
            except ValueError:
                print(f"Invalid test argument: {args.test}. Use a number 1-5 or 'all'.")
                sys.exit(1)
    else:
        run_interactive()


if __name__ == "__main__":
    main()
