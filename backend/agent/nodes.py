import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

_providers_cache = None
_policies_cache = None
_insurance_cache = None

USE_MOCK = not bool(os.getenv("ANTHROPIC_API_KEY", "").strip().startswith("sk-"))


def _get_providers():
    global _providers_cache
    if _providers_cache is None:
        with open(DATA_DIR / "providers.json") as f:
            _providers_cache = json.load(f)
    return _providers_cache


def _get_policies():
    global _policies_cache
    if _policies_cache is None:
        with open(DATA_DIR / "policies.json") as f:
            _policies_cache = json.load(f)
    return _policies_cache


def _get_insurance():
    global _insurance_cache
    if _insurance_cache is None:
        with open(DATA_DIR / "insurance.json") as f:
            _insurance_cache = json.load(f)
    return _insurance_cache


def _llm():
    from langchain_anthropic import ChatAnthropic
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    return ChatAnthropic(model=model, temperature=0)


def _add_step(state, node: str, label: str, detail: str, status: str = "complete") -> list:
    return state.get("steps", []) + [{
        "node": node,
        "label": label,
        "detail": detail,
        "status": status,
    }]


async def triage_node(state) -> dict:
    from .mock_llm import mock_triage

    if USE_MOCK:
        raw = mock_triage(state["request"])
    else:
        from langchain_core.messages import HumanMessage, SystemMessage
        from .prompts import TRIAGE_PROMPT
        llm = _llm()
        response = await llm.ainvoke([
            SystemMessage(content=TRIAGE_PROMPT.format(request=state["request"])),
            HumanMessage(content="Analyze this patient request now."),
        ])
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"intent": "general", "risk_level": "low", "entities": {}, "reasoning": "Parse error"}

    steps = _add_step(
        state, "triage",
        "Classifying Intent & Risk",
        f"Intent: {parsed['intent'].replace('_', ' ').title()} | Risk: {parsed['risk_level'].upper()} — {parsed.get('reasoning', '')}",
    )

    return {
        "intent": parsed["intent"],
        "risk_level": parsed["risk_level"],
        "entities": parsed.get("entities", {}),
        "steps": steps,
    }


async def emergency_node(state) -> dict:
    policies = _get_policies()
    urgent_care = policies["emergency_protocol"]["urgent_care_locations"][0]

    draft = (
        "⚠️ IMPORTANT — Based on your message, you may be experiencing a medical emergency.\n\n"
        "If you are having chest pain, difficulty breathing, or any life-threatening symptoms, "
        "please CALL 911 immediately or go to your nearest emergency room.\n\n"
        f"Nearest Urgent Care (for non-emergency urgent needs):\n"
        f"• {urgent_care['name']}\n"
        f"  {urgent_care['address']}\n"
        f"  Hours: {urgent_care['hours']}\n"
        f"  Phone: {urgent_care['phone']}\n\n"
        "We cannot schedule appointments for active medical emergencies. "
        "Once you are stable and have received care, our team will be happy to help with follow-up scheduling."
    )

    steps = _add_step(
        state, "emergency",
        "Emergency Protocol Activated",
        "Medical emergency keywords detected. Routing to safety protocol — bypassing scheduling.",
        status="emergency",
    )

    return {
        "draft_response": draft,
        "retrieved_data": {"emergency_triggered": True, "urgent_care": urgent_care},
        "steps": steps,
    }


async def provider_lookup_node(state) -> dict:
    from .mock_llm import mock_provider_response

    entities = state.get("entities", {})
    all_providers = _get_providers()["providers"]

    specialty = entities.get("specialty", "").lower()
    language = entities.get("language", "").lower()
    insurance = entities.get("insurance", "").lower()
    location = entities.get("location", "").lower()

    matches = all_providers
    if specialty:
        matches = [p for p in matches if specialty in p["specialty"].lower()]
    if language:
        matches = [p for p in matches if any(language in lang.lower() for lang in p["languages"])]
    if insurance:
        matches = [p for p in matches if any(insurance in ins.lower() for ins in p["insurance"])]
    if location:
        matches = [p for p in matches if location in p["location"].lower()]

    if not matches and specialty:
        matches = [p for p in all_providers if specialty in p["specialty"].lower()]

    top_matches = matches[:3]

    filter_desc = " | ".join(filter(None, [
        f"Specialty: {specialty.title()}" if specialty else "",
        f"Language: {language.title()}" if language else "",
        f"Insurance: {insurance.title()}" if insurance else "",
        f"Location: {location}" if location else "",
    ])) or "No filters applied"

    steps = _add_step(
        state, "provider_lookup",
        "Searching Provider Directory",
        f"Filters — {filter_desc} → {len(top_matches)} match(es) found",
    )

    if USE_MOCK:
        draft = mock_provider_response(state["request"], top_matches)
    else:
        from langchain_core.messages import HumanMessage, SystemMessage
        from .prompts import PROVIDER_LOOKUP_PROMPT
        llm = _llm()
        response = await llm.ainvoke([
            SystemMessage(content=PROVIDER_LOOKUP_PROMPT.format(
                request=state["request"],
                providers=json.dumps(top_matches, indent=2),
            )),
            HumanMessage(content="Generate the patient response."),
        ])
        draft = response.content

    return {
        "retrieved_data": {"providers": top_matches, "filter": filter_desc},
        "draft_response": draft,
        "steps": steps,
    }


async def appointment_node(state) -> dict:
    from .mock_llm import mock_appointment_response

    policies = _get_policies()
    appt_policy = policies["appointment_policies"]

    steps = _add_step(
        state, "appointment",
        "Retrieving Appointment Policies",
        f"Telehealth: {'Available' if appt_policy['telehealth_available'] else 'N/A'} | "
        f"Cancellation window: 24 hours",
    )

    if USE_MOCK:
        draft = mock_appointment_response(state["request"], appt_policy)
    else:
        from langchain_core.messages import HumanMessage, SystemMessage
        from .prompts import APPOINTMENT_PROMPT
        llm = _llm()
        response = await llm.ainvoke([
            SystemMessage(content=APPOINTMENT_PROMPT.format(
                request=state["request"],
                policies=json.dumps(appt_policy, indent=2),
            )),
            HumanMessage(content="Generate the patient response."),
        ])
        draft = response.content

    return {
        "retrieved_data": {"appointment_policy": appt_policy},
        "draft_response": draft,
        "steps": steps,
    }


async def insurance_node(state) -> dict:
    from .mock_llm import mock_insurance_response

    entities = state.get("entities", {})
    insurance_data = _get_insurance()
    plan_name = entities.get("insurance", "")

    matched_plan = None
    for plan_key, plan_info in insurance_data["plans"].items():
        if plan_name.lower() in plan_key.lower() or plan_key.lower() in plan_name.lower():
            matched_plan = {plan_key: plan_info}
            break

    if not matched_plan:
        matched_plan = {"all_plans": list(insurance_data["plans"].keys())}
        detail = "Insurance not specified — returning full accepted plans list"
    else:
        plan_key = list(matched_plan.keys())[0]
        detail = f"Found plan: {plan_key} — Copay: {matched_plan[plan_key]['copay_primary']}"

    steps = _add_step(state, "insurance", "Checking Insurance Coverage", detail)

    if USE_MOCK:
        draft = mock_insurance_response(state["request"], matched_plan)
    else:
        from langchain_core.messages import HumanMessage, SystemMessage
        from .prompts import INSURANCE_PROMPT
        llm = _llm()
        response = await llm.ainvoke([
            SystemMessage(content=INSURANCE_PROMPT.format(
                request=state["request"],
                insurance_info=json.dumps(matched_plan, indent=2),
            )),
            HumanMessage(content="Generate the patient response."),
        ])
        draft = response.content

    return {
        "retrieved_data": {"insurance": matched_plan},
        "draft_response": draft,
        "steps": steps,
    }


async def prescription_node(state) -> dict:
    policies = _get_policies()
    rx_policy = policies["prescription_policy"]

    steps = _add_step(
        state, "prescription",
        "Retrieving Prescription Policy",
        f"Refill lead time: {rx_policy['refill_lead_time_days']} days | "
        f"Partners: {', '.join(rx_policy['pharmacy_partners'][:3])}",
    )

    draft = (
        f"Thank you for reaching out about your prescription!\n\n"
        f"Here's how to request a refill:\n"
        f"• **Patient Portal:** patientportal.clinicname.com (fastest)\n"
        f"• **Phone:** (816) 555-0000 (allow {rx_policy['refill_lead_time_days']} business days)\n\n"
        f"Please note: {rx_policy['controlled_substance_note']}\n\n"
        f"We work with {', '.join(rx_policy['pharmacy_partners'])} for prescription fulfillment. "
        f"If your medication requires prior authorization, {rx_policy['prior_auth_process']}"
    )

    return {
        "retrieved_data": {"prescription_policy": rx_policy},
        "draft_response": draft,
        "steps": steps,
    }

    
async def synthesize_node(state) -> dict:
    from .mock_llm import mock_general_response, mock_case_summary

    draft = state.get("draft_response", "")
    if not draft:
        if USE_MOCK:
            draft = mock_general_response(state["request"])
        else:
            from langchain_core.messages import HumanMessage, SystemMessage
            from .prompts import SYNTHESIZE_PROMPT
            llm = _llm()
            response = await llm.ainvoke([
                SystemMessage(content=SYNTHESIZE_PROMPT.format(
                    request=state["request"],
                    intent=state.get("intent", "general"),
                    risk_level=state.get("risk_level", "low"),
                )),
                HumanMessage(content="Generate the patient response."),
            ])
            draft = response.content

    # Generate case summary
    if USE_MOCK:
        summary = mock_case_summary(
            state["request"], state.get("intent", "general"),
            state.get("risk_level", "low"), draft,
        )
    else:
        from langchain_core.messages import HumanMessage, SystemMessage
        from .prompts import CASE_SUMMARY_PROMPT
        llm = _llm()
        summary_response = await llm.ainvoke([
            SystemMessage(content=CASE_SUMMARY_PROMPT.format(
                request=state["request"],
                intent=state.get("intent", "general"),
                risk_level=state.get("risk_level", "low"),
                response=draft,
                retrieved_data=json.dumps(state.get("retrieved_data", {})),
            )),
            HumanMessage(content="Generate the case summary JSON."),
        ])
        raw = summary_response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
        try:
            summary = json.loads(raw.strip())
        except json.JSONDecodeError:
            summary = mock_case_summary(
                state["request"], state.get("intent", "general"),
                state.get("risk_level", "low"), draft,
            )

    steps = _add_step(
        state, "synthesize",
        "Drafting Response & Case Summary",
        f"Response drafted ({len(draft)} chars) | Summary generated",
    )

    return {"draft_response": draft, "case_summary": summary, "steps": steps}


async def log_node(state) -> dict:
    from database import log_case

    case_id = await log_case(
        request=state["request"],
        intent=state.get("intent", "general"),
        risk_level=state.get("risk_level", "low"),
        response=state.get("draft_response", ""),
        case_summary=state.get("case_summary", {}),
        steps=state.get("steps", []),
    )

    steps = _add_step(state, "log", "Logging to Audit Trail", f"Case saved: {case_id}")

    return {"case_id": case_id, "steps": steps}
