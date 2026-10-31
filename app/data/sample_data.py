"""Clearly synthetic demo records for the ReguLensAI UI foundation."""

PUBLICATIONS = [
    {"id": "REG-IND-2026-014", "title": "Illustrative AI Governance Circular", "authority": "Reserve Bank of India", "country": "India", "area": "AI governance", "published": "2026-10-20", "effective": "2027-04-01", "status": "Awaiting review", "kind": "Amendment"},
    {"id": "REG-UAE-2026-008", "title": "Illustrative Operational Resilience Guidance", "authority": "Central Bank of the UAE", "country": "UAE", "area": "Operational resilience", "published": "2026-10-17", "effective": "2027-01-01", "status": "Processed", "kind": "New obligation"},
    {"id": "REG-KSA-2026-021", "title": "Illustrative Cybersecurity Controls Update", "authority": "Saudi Central Bank (SAMA)", "country": "Saudi Arabia", "area": "Cybersecurity", "published": "2026-10-14", "effective": "2027-03-01", "status": "New", "kind": "Clarification"},
    {"id": "REG-AFR-2026-003", "title": "Illustrative Digital Lending Directive", "authority": "Selected African regulator (demo)", "country": "Africa", "area": "Digital lending", "published": "2026-10-10", "effective": "2027-02-15", "status": "Relationship unresolved", "kind": "Modified obligation"},
    {"id": "REG-IND-2026-011", "title": "Illustrative Digital Lending Directions", "authority": "Reserve Bank of India", "country": "India", "area": "Lending", "published": "2026-10-04", "effective": "2027-01-01", "status": "Processed", "kind": "New obligation"},
]

CHANGES = [
    {
        "id": "CHG-001",
        "publication": "Illustrative AI Governance Circular",
        "country": "India",
        "classification": "New obligation",
        "priority": "High",
        "previous": "No equivalent clause identified in the selected historical sample.",
        "updated": "Regulated entities should establish documented governance and human oversight for AI-assisted credit decisions.",
        "impact": "Potential impact on model governance, credit decision workflows, validation evidence and human review controls.",
        "actions": ["Inventory AI-assisted credit decision use cases", "Review model governance and approval controls", "Define human oversight and escalation evidence"],
        "source": "Demo clause 4.2 (synthetic sample; not an official RBI publication)",
    },
    {
        "id": "CHG-002",
        "publication": "Illustrative Operational Resilience Guidance",
        "country": "UAE",
        "classification": "Modified obligation",
        "priority": "Medium",
        "previous": "Business continuity testing is described at a high level.",
        "updated": "Testing should include documented recovery objectives and evidence of scenario coverage.",
        "impact": "Potential updates to resilience testing procedures, evidence retention and service-owner attestations.",
        "actions": ["Map critical services to recovery objectives", "Update scenario test plan", "Record evidence and remediation owners"],
        "source": "Demo clause 6.1 (synthetic sample; not an official CBUAE publication)",
    },
]
