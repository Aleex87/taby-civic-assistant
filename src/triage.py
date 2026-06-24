from src.schemas import CitizenInquiry, InquiryDomain


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

    requires_location = any(
        keyword in normalized_text
        for keyword in LOCATION_KEYWORDS
    )

    return inquiry.model_copy(
        update={
            "domain": best_domain,
            "requires_location": requires_location,
        }
    )