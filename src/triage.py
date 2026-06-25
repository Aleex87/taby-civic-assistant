from src.schemas import CitizenInquiry, InquiryDomain, InquiryIntent


DOMAIN_KEYWORDS: dict[InquiryDomain, set[str]] = {
    InquiryDomain.BUILDING_AND_PLANNING: {
        "altan",
        "balkong",
        "inglasning",
        "bygglov",
        "garage",
        "attefall",
        "attefallshus",
        "tillbyggnad",
        "ombyggnad",
        "renovering",
        "fasad",
        "fasadändring",
        "riva",
        "rivning",
        "bygga",
        "byggnad",
        "construction",
        "build",
        "extension",
        "renovation",
    },
    InquiryDomain.NEIGHBOUR_AND_PROPERTY: {
        "granne",
        "grannfastighet",
        "tomtgräns",
        "fastighetsgräns",
        "störning",
        "buller",
        "ovårdad",
        "skräpigt",
        "complaint",
        "neighbour",
        "neighbor",
        "boundary",
        "noise",
    },
    InquiryDomain.WASTE_AND_ENVIRONMENT: {
        "avfall",
        "sopor",
        "skräp",
        "återvinning",
        "sophämtning",
        "miljö",
        "kompost",
        "farligt avfall",
        "waste",
        "garbage",
        "rubbish",
        "recycling",
        "environment",
    },
    InquiryDomain.MUNICIPAL_SERVICE: {
        "kontakt",
        "kontakta",
        "handläggare",
        "tjänsteman",
        "kommun",
        "kommunen",
        "ärende",
        "ärendestatus",
        "ansökan",
        "kontaktcenter",
        "contact",
        "officer",
        "municipality",
        "case status",
        "application status",
    },
}


LOCATION_KEYWORDS: set[str] = {
    "adress",
    "gata",
    "gatan",
    "väg",
    "vägen",
    "fastighet",
    "fastighetsbeteckning",
    "tomt",
    "hus",
    "hem",
    "bostad",
    "granne",
    "grannfastighet",
    "address",
    "street",
    "road",
    "property",
    "house",
    "home",
    "neighbour",
    "neighbor",
}
INTENT_KEYWORDS: dict[InquiryIntent, set[str]] = {
    InquiryIntent.GENERAL_INFORMATION: {
        "what are the rules",
        "which rules",
        "information",
        "guidance",
        "regler",
        "vilka regler",
        "information om",
        "hur fungerar",
    },
    InquiryIntent.PERMISSION_QUESTION: {
        "can i",
        "may i",
        "is it allowed",
        "do i need permission",
        "do i need a permit",
        "får jag",
        "kan jag",
        "är det tillåtet",
        "behöver jag bygglov",
        "krävs bygglov",
    },
    InquiryIntent.REPORT_POSSIBLE_VIOLATION: {
        "not allowed",
        "illegal",
        "unauthorised",
        "unauthorized",
        "too close",
        "built without permission",
        "inte tillåtet",
        "olovligt",
        "utan bygglov",
        "för nära",
        "har byggt",
    },
    InquiryIntent.REQUEST_CONTACT: {
        "contact",
        "speak with",
        "talk to",
        "officer",
        "kontakta",
        "prata med",
        "handläggare",
        "tjänsteman",
    },
    InquiryIntent.CASE_STATUS: {
        "case status",
        "application status",
        "status of my case",
        "ärendestatus",
        "status på mitt ärende",
        "min ansökan",
    },
    InquiryIntent.SUBMIT_COMPLAINT: {
        "complaint",
        "report a problem",
        "make a complaint",
        "klagomål",
        "anmäla",
        "göra en anmälan",
        "rapportera ett problem",
    },
}

def classify_inquiry(inquiry: CitizenInquiry) -> CitizenInquiry:
    """Apply lightweight deterministic triage rules to an inquiry."""

    normalized_text = inquiry.original_text.casefold()

    domain_scores = {
        domain: sum(
            keyword in normalized_text
            for keyword in keywords
        )
        for domain, keywords in DOMAIN_KEYWORDS.items()
    }

    best_domain = max(
        domain_scores,
        key=domain_scores.get,
    )

    if domain_scores[best_domain] == 0:
        best_domain = InquiryDomain.UNKNOWN

    intent_scores = {
        intent: sum(
            keyword in normalized_text
            for keyword in keywords
        )
        for intent, keywords in INTENT_KEYWORDS.items()
    }

    best_intent = max(
        intent_scores,
        key=intent_scores.get,
    )

    if intent_scores[best_intent] == 0:
        best_intent = InquiryIntent.UNKNOWN

    requires_location = any(
        keyword in normalized_text
        for keyword in LOCATION_KEYWORDS
    )

    return inquiry.model_copy(
        update={
            "domain": best_domain,
            "intent": best_intent,
            "requires_location": requires_location,
        }
    )