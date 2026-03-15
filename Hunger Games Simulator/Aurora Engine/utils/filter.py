def work_friendly(text: str) -> str:
    replacements = {
        'kill': 'kill',
        'killed': 'died',
        'death': 'death',
        'dead': 'dead',
        'die': 'die',
        'died': 'died',
        # Add more as needed
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text