# database_map.py

# This is the "knowledge base" for our AI Strategist.
# Database codes based on actual AustLII structure from https://www.austlii.edu.au/databases.html
DATABASE_TOOLS_LIST = [
    {
        "name": "High Court of Australia",
        "description": "Searches High Court of Australia cases (1903-present), Australia's highest court.",
        "code": "au/cases/cth/HCA"
    },
    {
        "name": "Federal Court of Australia", 
        "description": "Searches Federal Court of Australia cases (1977-present).",
        "code": "au/cases/cth/FCA"
    },
    {
        "name": "All Commonwealth Cases",
        "description": "Searches all Commonwealth case law databases (broader search).",
        "code": "au/cases/cth"
    },
    {
        "name": "Commonwealth Consolidated Acts",
        "description": "Searches current Commonwealth legislation including Acts.",
        "code": "au/legis/cth/consol_act"
    },
    {
        "name": "New South Wales Supreme Court",
        "description": "Searches NSW Supreme Court cases (1993-present).",
        "code": "au/cases/nsw/NSWSC"
    },
    {
        "name": "Victorian Supreme Court",
        "description": "Searches Victorian Supreme Court cases (1994-present).",
        "code": "au/cases/vic/VSC"
    }
]