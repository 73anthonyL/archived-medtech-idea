"""
Strata — deterministic synthetic patient name generator.

Maps each subject_id to a stable fictional name using a seeded hash so the
same patient always gets the same name across sessions without storing any
real PHI.  Names are clearly Western-style fiction, not derived from real data.
"""

import hashlib

_FIRST_NAMES = [
    "Aaron", "Alice", "Amelia", "Andre", "Angela", "Arthur",
    "Barbara", "Benjamin", "Beth", "Blake",
    "Carlos", "Carmen", "Catherine", "Charles", "Christine",
    "Daniel", "Diana", "Diego", "Donna", "Dorothy",
    "Elena", "Elizabeth", "Emily", "Eric", "Eva",
    "Frances", "Frank", "Frederic",
    "Gabriel", "George", "Gloria", "Grace",
    "Hannah", "Harold", "Helen", "Henry",
    "Irene", "Ivan",
    "James", "Janet", "Jasmine", "Jennifer", "John", "Jordan", "Joyce",
    "Karen", "Katherine", "Kevin",
    "Laura", "Lawrence", "Lillian", "Linda", "Lisa", "Louis", "Lucas",
    "Margaret", "Maria", "Mark", "Martha", "Martin", "Mary", "Matthew",
    "Michael", "Michelle", "Monica",
    "Nancy", "Nathan", "Nicole",
    "Olivia", "Omar",
    "Patricia", "Paul", "Pauline", "Peter",
    "Rachel", "Rebecca", "Richard", "Rita", "Robert", "Rosa", "Russell",
    "Sandra", "Sarah", "Scott", "Sharon", "Sophia", "Steven", "Susan",
    "Teresa", "Thomas", "Timothy",
    "Valeria", "Victor", "Virginia",
    "Walter", "Wendy", "William",
]

_LAST_NAMES = [
    "Adams", "Allen", "Anderson", "Andrews",
    "Baker", "Barnes", "Bell", "Bennett", "Brooks", "Brown",
    "Campbell", "Carter", "Chen", "Clark", "Collins", "Cooper",
    "Davis", "Dixon",
    "Edwards", "Evans",
    "Fisher", "Flores", "Foster",
    "Garcia", "Gonzalez", "Gray", "Green", "Griffin",
    "Hall", "Harris", "Henderson", "Hill", "Howard",
    "Jackson", "Jenkins", "Johnson", "Jones",
    "Kim", "King",
    "Lee", "Lewis", "Lin", "Lopez",
    "Martin", "Martinez", "Mitchell", "Moore", "Morgan",
    "Nelson", "Nguyen",
    "Parker", "Patel", "Perez", "Phillips", "Price",
    "Reed", "Rivera", "Roberts", "Robinson", "Rodriguez", "Rogers", "Ross",
    "Sanders", "Scott", "Silva", "Smith", "Stewart",
    "Taylor", "Thomas", "Thompson", "Torres", "Turner",
    "Walker", "Ward", "Watson", "White", "Williams", "Wilson", "Wood",
    "Young",
]


def _stable_indices(subject_id: int) -> tuple[int, int]:
    """Return (first_idx, last_idx) derived deterministically from subject_id."""
    digest = hashlib.md5(str(subject_id).encode()).digest()
    first_idx = int.from_bytes(digest[:4], "big") % len(_FIRST_NAMES)
    last_idx  = int.from_bytes(digest[4:8], "big") % len(_LAST_NAMES)
    return first_idx, last_idx


def get_display_name(subject_id: int) -> str:
    """Return 'Firstname Lastname' for a given subject_id, always the same."""
    f, l = _stable_indices(int(subject_id))
    return f"{_FIRST_NAMES[f]} {_LAST_NAMES[l]}"


def add_display_names(df) -> None:
    """Add a 'display_name' column in-place to a DataFrame with a 'subject_id' column."""
    df["display_name"] = df["subject_id"].apply(get_display_name)
