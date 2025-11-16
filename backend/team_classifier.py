"""
Team classification utility to identify Sundew contractors vs US employees.
"""
import re
from typing import Literal

# Common Indian names patterns (for Sundew identification)
INDIAN_NAME_PATTERNS = [
    r'\b(kumar|singh|sharma|gupta|das|dey|mondal|jana|khan|bhattacharya|bhattacharyya|'
    r'rakshit|sarkar|haldar|kundu|bagdi|ball|paul|ghosh|padhi|bari|ojha|adarsh|anup|'
    r'banerjee|maity|pradhan|darboe|sobchuk|ricci|berg|moreno)\b',
    r'^(amit|ratul|sayon|swarup|arpan|somnath|sujan|ashok|soumyajit|aush|riju|abinash|'
    r'dipak|nasirul|sandeep|souvik|raysa|arup|manas|vikram|soudip|mamata|pritam|shahrukh)$'
]

# Common US/Western name patterns
US_NAME_PATTERNS = [
    r'\b(wright|goyco|sanchez|stern|beckerman|smith|johnson|williams|brown|jones|'
    r'miller|davis|garcia|rodriguez|wilson|martinez|anderson|taylor|thomas|moore)\b',
    r'^(corey|xavier|kevin|remy|david|michael|john|james|robert|william|richard|'
    r'joseph|thomas|charles|christopher|daniel|matthew|anthony|donald|mark)\b'
]


def classify_team(name: str) -> Literal["sundew", "us", "unknown"]:
    """
    Classify a user as Sundew contractor, US employee, or unknown based on name patterns.
    
    Args:
        name: User's display name
        
    Returns:
        "sundew" for contractors, "us" for US employees, "unknown" for unclear
    """
    if not name:
        return "unknown"
    
    name_lower = name.lower().strip()
    
    # Check for Indian name patterns (Sundew contractors)
    for pattern in INDIAN_NAME_PATTERNS:
        if re.search(pattern, name_lower, re.IGNORECASE):
            return "sundew"
    
    # Check for US/Western name patterns
    for pattern in US_NAME_PATTERNS:
        if re.search(pattern, name_lower, re.IGNORECASE):
            return "us"
    
    # Default to unknown if no match
    return "unknown"


def get_team_label(team: str) -> str:
    """Get human-readable team label."""
    labels = {
        "sundew": "Sundew (Contractors)",
        "us": "US Team (Internal)",
        "unknown": "Unknown Team"
    }
    return labels.get(team, "Unknown")
