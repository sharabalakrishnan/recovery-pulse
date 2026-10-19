"""The check-in questions and how their answers map into belonginglab.

Raw answers are stored under short codes (q1, q2, ...). belonginglab's
``map_variables`` renames them to readable "canonical" names using SCHEMA, and
``compute_belonging_score`` combines them with WEIGHTS.
"""

from __future__ import annotations

# Questions answered on a 1-5 agreement scale. Higher = more connected.
LIKERT = [
    ("q1", "neighbor_support", "If I needed help, a neighbor would help me."),
    ("q2", "community_belonging", "I feel like I belong in this community."),
    ("q3", "trust_local_help", "I trust local groups to help us recover."),
    ("q4", "kept_informed", "I know where to get recovery information."),
]

# Yes/no strains since the disaster. 1 = yes, 0 = no, missing = skipped.
STRESSORS = [
    ("q5", "housing_unstable", "Housing", "My home is still damaged, or I'm not living at home."),
    ("q6", "money_strain", "Money", "Paying bills is harder than before."),
    ("q7", "school_work_disrupted", "School/work", "My school or work has been disrupted."),
    ("q8", "daily_stress", "Daily stress", "Stress or worry is affecting my daily life."),
]

NEEDS = [
    "Home repair help",
    "Help with bills",
    "Someone to talk to",
    "Childcare",
    "Rides",
    "Neighborhood events",
]

SCALE_LABELS = ["Strongly disagree", "Disagree", "Not sure", "Agree", "Strongly agree"]

# canonical name -> raw column, in the form belonginglab.map_variables expects
SCHEMA = {canon: code for code, canon, *_ in LIKERT + STRESSORS}

# Positive weights raise connection; negative weights (strains) lower it.
# Belonging items count most; strains count less because they also reflect
# damage that belonging can't fix.
WEIGHTS = {
    "neighbor_support": 1.0,
    "community_belonging": 1.0,
    "trust_local_help": 0.75,
    "kept_informed": 0.5,
    "housing_unstable": -0.75,
    "money_strain": -0.75,
    "school_work_disrupted": -0.5,
    "daily_stress": -0.75,
}

STRESSOR_FLAGS = [f"strain_{canon}" for _, canon, *_ in STRESSORS]
STRESSOR_LABELS = {f"strain_{canon}": label for _, canon, label, _ in STRESSORS}
