"""
Scripted mock responses for demo/testing without a real API key.
Matches on keywords in the patient request and returns realistic JSON / text.
"""
import json


def mock_triage(request: str) -> str:
    text = request.lower()

    # Emergency detection
    emergency_keywords = [
        "chest tightness", "chest pain", "can't breathe", "difficulty breathing",
        "stroke", "unconscious", "self-harm", "suicidal", "heart attack",
    ]
    if any(kw in text for kw in emergency_keywords):
        return json.dumps({
            "intent": "appointment",
            "risk_level": "emergency",
            "entities": {
                "specialty": "cardiology" if "cardiology" in text else "",
                "medical_concern": "chest tightness / possible cardiac event",
            },
            "reasoning": "Patient reports chest tightness — potential cardiac emergency. Immediate escalation required.",
        })

    # Provider lookup
    if any(kw in text for kw in ["find", "looking for", "provider", "doctor", "pediatrician", "cardiologist", "specialist"]):
        specialty = ""
        if "pediatr" in text: specialty = "Pediatrics"
        elif "cardio" in text: specialty = "Cardiology"
        elif "family" in text: specialty = "Family Medicine"

        language = "Spanish" if "spanish" in text else ""
        insurance = ""
        for ins in ["aetna", "blue cross", "unitedheath", "cigna", "humana", "medicare", "medicaid"]:
            if ins in text:
                insurance = ins.title()
                break

        location = ""
        if "lee" in text and "summit" in text: location = "Lee's Summit, MO"
        elif "overland park" in text: location = "Overland Park, KS"
        elif "kansas city" in text: location = "Kansas City, MO"

        return json.dumps({
            "intent": "provider_lookup",
            "risk_level": "low",
            "entities": {
                "specialty": specialty,
                "language": language,
                "insurance": insurance,
                "location": location,
            },
            "reasoning": f"Patient is requesting a provider search with filters: {specialty}, {language}, {insurance}, {location}.",
        })

    # Appointment
    if any(kw in text for kw in ["appointment", "schedule", "reschedule", "cancel", "book"]):
        return json.dumps({
            "intent": "appointment",
            "risk_level": "low",
            "entities": {
                "specialty": "cardiology" if "cardiology" in text else "",
                "date_preference": "next Tuesday" if "tuesday" in text else "",
            },
            "reasoning": "Patient is requesting appointment management (rescheduling/cancellation).",
        })

    # Insurance
    if any(kw in text for kw in ["insurance", "copay", "coverage", "accept", "deductible", "prior auth"]):
        insurance = ""
        for ins in ["aetna", "blue cross", "united", "cigna", "humana", "medicare", "medicaid"]:
            if ins in text:
                insurance = ins.title()
                break
        return json.dumps({
            "intent": "insurance",
            "risk_level": "low",
            "entities": {"insurance": insurance},
            "reasoning": "Patient is asking about insurance coverage and accepted plans.",
        })

    # Prescription
    if any(kw in text for kw in ["prescription", "refill", "medication", "drug", "pharmacy"]):
        return json.dumps({
            "intent": "prescription",
            "risk_level": "low",
            "entities": {},
            "reasoning": "Patient is asking about prescription or medication refill.",
        })

    return json.dumps({
        "intent": "general",
        "risk_level": "low",
        "entities": {},
        "reasoning": "General patient inquiry — no specific intent or risk detected.",
    })


def mock_provider_response(request: str, providers: list) -> str:
    if not providers:
        return (
            "Thank you for reaching out! Unfortunately, we were unable to find an exact match "
            "in our current provider directory based on your preferences. "
            "Please call us at (816) 555-0000 and our team will help you find the right provider."
        )
    lines = ["Thank you for reaching out to our patient access team!\n\nBased on your request, here are the providers we found for you:\n"]
    for p in providers:
        avail = p.get("next_available", "N/A") or "Currently not accepting new patients"
        lines.append(
            f"**{p['name']}** - {p['specialty']}\n"
            f"  Location: {p['address']}\n"
            f"  Languages: {', '.join(p['languages'])}\n"
            f"  Insurance: {', '.join(p['insurance'][:3])}{'...' if len(p['insurance']) > 3 else ''}\n"
            f"  Next Available: {avail} | Accepting New Patients: {'Yes' if p.get('accepting_new_patients') else 'No'}\n"
            f"  Phone: {p['phone']}\n"
        )
    lines.append(
        "\nTo schedule with any of these providers, please call the clinic at **(816) 555-0000** "
        "or log in to your **Patient Portal** at patientportal.clinicname.com."
    )
    return "\n".join(lines)


def mock_appointment_response(request: str, policy: dict) -> str:
    text = request.lower()
    if "reschedule" in text:
        return (
            "Thank you for contacting us about rescheduling your appointment!\n\n"
            f"You can reschedule at no charge as long as it's done more than 24 hours in advance. "
            f"Here's how:\n"
            f"• **Online:** Log in to your Patient Portal at patientportal.clinicname.com\n"
            f"• **By Phone:** Call us at (816) 555-0000\n\n"
            f"Please note: {policy.get('cancellation_policy', 'Cancellations within 24 hours may incur a fee.')}\n\n"
            f"Telehealth is also available for follow-up visits if that's more convenient for you!"
        )
    if "cancel" in text:
        return (
            f"Thank you for letting us know! To cancel your appointment:\n"
            f"• **Online:** Patient Portal at patientportal.clinicname.com\n"
            f"• **Phone:** (816) 555-0000\n\n"
            f"Please note: {policy.get('cancellation_policy', 'Cancellations within 24 hours may incur a fee.')}"
        )
    return (
        f"Thank you for reaching out about your appointment. "
        f"Please contact us at (816) 555-0000 or visit patientportal.clinicname.com to schedule. "
        f"New patients typically have appointments available within {policy.get('new_patient_lead_time_days', 14)} days."
    )


def mock_insurance_response(request: str, insurance_info: dict) -> str:
    plans = list(insurance_info.keys())
    if "all_plans" in insurance_info:
        plan_list = ", ".join(insurance_info["all_plans"])
        return (
            f"We accept the following insurance plans:\n{plan_list}\n\n"
            "Please call us at (816) 555-0000 or visit patientportal.clinicname.com "
            "to verify your specific coverage before your appointment."
        )
    plan_name = plans[0]
    info = insurance_info[plan_name]
    return (
        f"Great news — we accept **{plan_name}**!\n\n"
        f"Here are the key details for your plan:\n"
        f"• Primary Care Copay: {info.get('copay_primary', 'Verify with insurer')}\n"
        f"• Specialist Copay: {info.get('copay_specialist', 'Verify with insurer')}\n"
        f"• Annual Deductible: {info.get('deductible_individual', 'Verify with insurer')}\n"
        f"• Prior Authorization Required For: {', '.join(info.get('prior_auth_required_for', []))}\n\n"
        f"For exact coverage details, please contact {plan_name} Member Services at "
        f"**{info.get('member_services', 'the number on your card')}** "
        f"or visit {info.get('portal', 'your insurer website')}."
    )


def mock_general_response(request: str) -> str:
    return (
        "Thank you for reaching out to our patient access team! "
        "We're happy to help with your request.\n\n"
        "For personalized assistance, please:\n"
        "• Call us at **(816) 555-0000** (Mon–Fri 8am–5pm)\n"
        "• Message us through the **Patient Portal** at patientportal.clinicname.com\n\n"
        "A member of our team will follow up with you within one business day."
    )


def mock_case_summary(request: str, intent: str, risk_level: str, response: str) -> dict:
    escalated = risk_level == "emergency"
    tag_map = {
        "appointment": ["scheduling", "appointment-management"],
        "provider_lookup": ["provider-search", "directory-lookup"],
        "insurance": ["insurance", "billing"],
        "prescription": ["prescription", "medication"],
        "general": ["general-inquiry"],
    }
    return {
        "chief_request": request[:120],
        "intent_category": intent,
        "risk_assessment": risk_level,
        "action_taken": "Emergency protocol activated" if escalated else f"Retrieved {intent.replace('_', ' ')} information and drafted patient response",
        "resolution": "Safety guidance provided — patient directed to 911/urgent care" if escalated else "Patient response drafted and delivered",
        "follow_up_required": escalated or risk_level in ("high", "medium"),
        "escalated": escalated,
        "tags": tag_map.get(intent, ["general"]) + (["escalated", "emergency"] if escalated else []),
    }
