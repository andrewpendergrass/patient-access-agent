from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    triage_node, emergency_node, provider_lookup_node,
    appointment_node, insurance_node, prescription_node,
    synthesize_node, log_node
)


def _route_after_triage(state: AgentState) -> str:
    if state.get("risk_level") == "emergency":
        return "emergency"
    intent = state.get("intent", "general")
    routing = {
        "provider_lookup": "provider_lookup",
        "appointment": "appointment",
        "insurance": "insurance",
        "prescription": "prescription",
    }
    return routing.get(intent, "synthesize")


def build_graph():
    g = StateGraph(AgentState)

    g.add_node("triage", triage_node)
    g.add_node("emergency", emergency_node)
    g.add_node("provider_lookup", provider_lookup_node)
    g.add_node("appointment", appointment_node)
    g.add_node("insurance", insurance_node)
    g.add_node("prescription", prescription_node)
    g.add_node("synthesize", synthesize_node)
    g.add_node("log", log_node)

    g.set_entry_point("triage")

    g.add_conditional_edges("triage", _route_after_triage, {
        "emergency": "emergency",
        "provider_lookup": "provider_lookup",
        "appointment": "appointment",
        "insurance": "insurance",
        "prescription": "prescription",
        "synthesize": "synthesize",
    })

    g.add_edge("emergency", "synthesize")
    g.add_edge("provider_lookup", "synthesize")
    g.add_edge("appointment", "synthesize")
    g.add_edge("insurance", "synthesize")
    g.add_edge("prescription", "synthesize")
    g.add_edge("synthesize", "log")
    g.add_edge("log", END)

    return g.compile()


agent_graph = build_graph()
