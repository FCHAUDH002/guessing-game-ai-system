STRATEGY_TIPS = [
    {
        "id": "binary_search",
        "tags": ["early_game", "wide_range"],
        "text": "Splitting the range in half each guess (binary search) narrows things down fastest — if the range is 1-100, start near 50."
    },
    {
        "id": "hot_cold_close",
        "tags": ["very_hot"],
        "text": "When you're this close, small adjustments (±1-3) work better than big jumps."
    },
    {
        "id": "hot_cold_far",
        "tags": ["cold"],
        "text": "A cold result means you're far off — consider jumping toward the middle of the remaining range rather than nudging slightly."
    },
    {
        "id": "low_attempts_left",
        "tags": ["low_attempts_left"],
        "text": "With few attempts left, prioritize narrowing the range over guessing exact numbers."
    },
    {
        "id": "repeat_guess",
        "tags": ["repeated_guess"],
        "text": "You've guessed this number before — try tracking your guess history to avoid repeats."
    },
]

def retrieve_tips(proximity_label, attempts_left, attempt_limit, guess, history):
    tags_present = set()

    if proximity_label == "🔥 Very Hot!":
        tags_present.add("very_hot")
    if proximity_label == "❄️ Cold":
        tags_present.add("cold")
    if attempts_left <= max(1, attempt_limit // 3):
        tags_present.add("low_attempts_left")
    if history.count(guess) > 1:
        tags_present.add("repeated_guess")
    if len(history) <= 1:
        tags_present.add("early_game")
        tags_present.add("wide_range")

    matches = [tip for tip in STRATEGY_TIPS if tags_present & set(tip["tags"])]
    return matches[:2]  # top 2 relevant tips