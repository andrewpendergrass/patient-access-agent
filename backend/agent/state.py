from typing import TypedDict, Optional


class AgentState(TypedDict):
    request: str
    intent: str            # appointment | provider_lookup | insurance | prescription | general
    risk_level: str        # low | medium | high | emergency
    entities: dict         # extracted: specialty, language, insurance, location, date, etc.
    retrieved_data: dict   # results from mock data lookups
    steps: list            # trace of agent steps for UI streaming
    draft_response: str
    case_summary: dict
    case_id: str
