import re

DIGIT_WORDS = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
}


def normalize_numeric_text(text: str) -> str:
    """
    Converts:
    two zero one five -> 2015
    9, 3, 1, 1 -> 9311
    """

    if not text:
        return text

    value = text.lower().strip()

    # remove commas
    value = value.replace(",", " ")

    tokens = value.split()

    if all(token in DIGIT_WORDS for token in tokens):
        return "".join(DIGIT_WORDS[token] for token in tokens)

    return re.sub(r"[\s,]+", "", text)


def normalize_address(text: str) -> str:

    if not text:
        return text

    mapping = {
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9",
    }

    street_words = [
        "road",
        "street",
        "drive",
        "lane",
        "avenue",
        "highway",
        "circle",
        "court",
        "way",
    ]

    words = text.split()

    if len(words) >= 2:

        if (
            words[0].lower() in mapping
            and words[1].lower() in street_words
        ):
            words[0] = mapping[words[0].lower()]

    return " ".join(words)
