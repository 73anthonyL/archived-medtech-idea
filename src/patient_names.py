"""
Strata — deterministic synthetic patient name generator.

Maps each subject_id to a stable fictional name using a seeded hash so the
same patient always gets the same name across sessions without storing any
real PHI.  Names are clearly fictional and span multiple cultural backgrounds;
first names are drawn from the gender-appropriate pool so they align with the
patient's recorded sex (M/F from the MIMIC admissions table).
"""

import hashlib

# Male first names spanning multiple cultural backgrounds
_FIRST_NAMES_M = [
    # English / American
    "Aaron", "Arthur", "Benjamin", "Blake", "Charles", "Daniel",
    "Edward", "Eric", "Frank", "George", "Harold", "Henry",
    "James", "John", "Kevin", "Lawrence", "Louis", "Lucas",
    "Mark", "Martin", "Matthew", "Michael", "Nathan", "Paul",
    "Peter", "Richard", "Robert", "Russell", "Scott", "Steven",
    "Thomas", "Timothy", "Victor", "Walter", "William",
    # Hispanic / Latino
    "Alejandro", "Andres", "Carlos", "Diego", "Eduardo", "Emilio",
    "Felipe", "Javier", "Jorge", "Jose", "Luis", "Manuel",
    "Miguel", "Rafael", "Rodrigo",
    # East Asian (Chinese / Japanese / Korean)
    "Bo", "Chen-Wei", "Daiki", "Haruto", "Hiroshi", "Jae-Won",
    "Kenji", "Min-Jun", "Ryu", "Seung", "Takeshi", "Wei",
    # South Asian (Indian / Sri Lankan)
    "Aditya", "Arjun", "Dev", "Kiran", "Nikhil", "Rahul",
    "Rajan", "Rohan", "Suresh", "Vikram",
    # African / West African
    "Amara", "Chidi", "Emeka", "Kofi", "Kwame", "Obinna",
    "Seun", "Taiwo", "Thabo", "Tobi",
    # Middle Eastern / North African
    "Hassan", "Khalid", "Nasser", "Omar", "Tariq", "Yusuf",
    # Eastern European / Russian
    "Alexei", "Andrei", "Dmitri", "Ivan", "Nikolai", "Sergei",
    # French / Italian / Portuguese
    "Antoine", "Etienne", "Gabriel", "Luca", "Marco", "Philippe",
    # Scandinavian
    "Bjorn", "Erik", "Lars", "Magnus",
]

# Female first names spanning multiple cultural backgrounds
_FIRST_NAMES_F = [
    # English / American
    "Alice", "Amelia", "Angela", "Barbara", "Beth", "Catherine",
    "Christine", "Diana", "Donna", "Dorothy", "Elizabeth", "Emily",
    "Eva", "Frances", "Gloria", "Grace", "Hannah", "Helen",
    "Irene", "Janet", "Jasmine", "Jennifer", "Joyce", "Karen",
    "Katherine", "Laura", "Lillian", "Linda", "Lisa", "Margaret",
    "Maria", "Martha", "Mary", "Michelle", "Monica", "Nancy",
    "Nicole", "Olivia", "Patricia", "Pauline", "Rachel", "Rebecca",
    "Rita", "Rosa", "Sandra", "Sarah", "Sharon", "Sophia",
    "Susan", "Teresa", "Valeria", "Virginia", "Wendy",
    # Hispanic / Latina
    "Alejandra", "Carmen", "Catalina", "Esperanza", "Isabella",
    "Lucia", "Marisol", "Valentina", "Ximena",
    # East Asian (Chinese / Japanese / Korean)
    "Hana", "Ji-Yeon", "Ling", "Mei", "Soo-Jin", "Yuki", "Zhen",
    # South Asian (Indian / Sri Lankan)
    "Anjali", "Deepa", "Kavitha", "Meera", "Nisha", "Priya",
    "Riya", "Sunita",
    # African / West African
    "Adaeze", "Ama", "Chiamaka", "Chisom", "Fatima", "Ngozi", "Zara",
    # Middle Eastern / North African
    "Aisha", "Layla", "Leila", "Nadia", "Rania", "Yasmin",
    # Eastern European / Russian
    "Anastasia", "Irina", "Katya", "Natasha", "Olga", "Vera",
    # French / Italian / Portuguese
    "Camille", "Elise", "Isabelle", "Sofia",
    # Scandinavian
    "Astrid", "Freya", "Ingrid", "Sigrid",
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
    "Okafor", "Osei",
    "Parker", "Patel", "Perez", "Phillips", "Price",
    "Reed", "Rivera", "Roberts", "Robinson", "Rodriguez", "Rogers", "Ross",
    "Sanders", "Scott", "Silva", "Singh", "Smith", "Stewart",
    "Taylor", "Thomas", "Thompson", "Torres", "Turner",
    "Walker", "Ward", "Watson", "White", "Williams", "Wilson", "Wood",
    "Yamamoto", "Young",
    "Zhang",
]


def _stable_indices(subject_id: int, gender: str) -> tuple[int, int]:
    """Return (first_idx, last_idx) derived deterministically from subject_id and gender."""
    digest = hashlib.md5(str(subject_id).encode()).digest()
    pool = _FIRST_NAMES_M if gender.upper() == "M" else _FIRST_NAMES_F
    first_idx = int.from_bytes(digest[:4], "big") % len(pool)
    last_idx  = int.from_bytes(digest[4:8], "big") % len(_LAST_NAMES)
    return first_idx, last_idx


def get_display_name(subject_id: int, gender: str = "M") -> str:
    """Return 'Firstname Lastname' for a given subject_id and gender, always the same."""
    pool = _FIRST_NAMES_M if gender.upper() == "M" else _FIRST_NAMES_F
    f, l = _stable_indices(int(subject_id), gender)
    return f"{pool[f]} {_LAST_NAMES[l]}"


def add_display_names(df) -> None:
    """Add a 'display_name' column in-place; uses 'gender' column when present."""
    if "gender" in df.columns:
        df["display_name"] = df.apply(
            lambda row: get_display_name(int(row["subject_id"]), row["gender"]),
            axis=1,
        )
    else:
        df["display_name"] = df["subject_id"].apply(get_display_name)
