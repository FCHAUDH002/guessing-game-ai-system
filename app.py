import html
import random
import streamlit as st

from logic_utils import check_guess, get_proximity_hint
from ai_coach import retrieve_tips, generate_ai_coach_message

def get_range_for_difficulty(difficulty: str):
    if difficulty == "Easy":
        return 1, 20
    if difficulty == "Normal":
        return 1, 100
    if difficulty == "Hard":
        return 1, 50
    return 1, 100


def parse_guess(raw: str):
    if raw is None:
        return False, None, "Enter a guess."

    if raw == "":
        return False, None, "Enter a guess."

    try:
        if "." in raw:
            value = int(float(raw))
        else:
            value = int(raw)
    except Exception:
        return False, None, "That is not a number."

    return True, value, None

STARTING_SCORE = 100

# Points lost per wrong guess, based on how close the guess was.
# A "cold" guess costs more than a "very hot" one.
PROXIMITY_PENALTY = {
    "🔥 Very Hot!": 5,
    "🌡️ Warm": 10,
    "❄️ Cold": 15,
}

def update_score(current_score: int, outcome: str, proximity: str):
    # Correct guess: no penalty, keep whatever score is left.
    if outcome == "Win":
        return current_score

    penalty = PROXIMITY_PENALTY.get(proximity, 15)
    new_score = current_score - penalty
    if new_score < 0:
        new_score = 0
    return new_score

st.set_page_config(page_title="Mystery Number Quest", page_icon="🎯", layout="centered")

st.markdown(
    """
    <style>
    /* ===== Candy Light theme (blue) ===== */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 20% 0%, #f0f7ff 0%, #e6f0ff 55%, #d9e8ff 100%);
        color: #1e3a5f;
    }
    [data-testid="stHeader"] {
        background: transparent;
    }
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid rgba(37, 99, 235, 0.18);
    }
    [data-testid="stSidebar"] * {
        color: #2b4a6b;
    }
    /* Trim the empty space above the title + center the game in a card */
    [data-testid="stAppViewContainer"] .block-container {
        padding-top: 1.5rem;
        max-width: 720px;
        margin: 0 auto;
    }
    /* Bigger, focused guess input */
    div[data-testid="stTextInput"] input {
        font-size: 1.25rem;
        font-weight: 600;
        text-align: center;
        padding: 0.6rem;
    }
    /* Guess-history chips */
    .guess-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin: 0.4rem 0 0.2rem 0;
    }
    .guess-chip {
        background: #ffffff;
        border: 1px solid rgba(37, 99, 235, 0.3);
        color: #2563eb;
        font-weight: 700;
        border-radius: 999px;
        padding: 0.15rem 0.7rem;
        font-size: 0.85rem;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.12);
    }
    .guess-chip.bad {
        border-color: rgba(220, 38, 38, 0.35);
        color: #dc2626;
    }
    /* Soft candy hero banner */
    .game-hero {
        text-align: center;
        padding: 1.1rem 1rem;
        border-radius: 16px;
        background: linear-gradient(135deg, #2575fc 0%, #38bdf8 100%);
        box-shadow: 0 8px 22px rgba(37, 117, 252, 0.28);
        margin-bottom: 1rem;
    }
    .game-hero h1 {
        color: #ffffff;
        font-size: 1.7rem;
        margin: 0;
        letter-spacing: 1px;
        text-shadow: 0 2px 6px rgba(20, 60, 130, 0.35);
    }
    .game-hero p {
        color: #eaf3ff;
        font-size: 0.9rem;
        margin: 0.3rem 0 0 0;
    }
    /* Smaller pastel stat metric cards */
    div[data-testid="stMetric"] {
        padding: 0.4rem 0.2rem;
        background: #ffffff;
        border: 1px solid rgba(37, 99, 235, 0.22);
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 3px 10px rgba(37, 99, 235, 0.10);
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.1rem;
        color: #2563eb;
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 0.8rem;
        color: #5b6b88;
    }
    /* Section headings + body text */
    h2, h3, .stMarkdown p {
        color: #1e3a5f !important;
    }
    /* Chunky, soft pastel buttons */
    div.stButton > button {
        border-radius: 12px;
        font-weight: 700;
        padding: 0.55rem 1rem;
        color: #ffffff;
        background: linear-gradient(135deg, #2575fc 0%, #38bdf8 100%);
        border: none;
        box-shadow: 0 4px 12px rgba(37, 117, 252, 0.35);
        transition: transform 0.05s ease-in-out, box-shadow 0.15s ease-in-out;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(56, 189, 248, 0.5);
    }
    /* Pastel progress bar fill */
    div[data-testid="stProgress"] div[role="progressbar"] > div {
        background: linear-gradient(90deg, #2575fc, #38bdf8);
    }
    </style>
    <div class="game-hero">
        <h1>🎯 Mystery Number Quest</h1>
        <p>Crack the secret number before your guesses run out!</p>
    </div>
    """,
    unsafe_allow_html=True,
)

stats_placeholder = st.empty()

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox(
    "Difficulty",
    ["Easy", "Normal", "Hard"],
    index=1,
)

attempt_limit_map = {
    "Easy": 6,
    "Normal": 8,
    "Hard": 5,
}
attempt_limit = attempt_limit_map[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")

# Reset the game whenever the difficulty changes so the secret stays in range
if st.session_state.get("difficulty") != difficulty:
    st.session_state.difficulty = difficulty
    st.session_state.secret = random.randint(low, high)
    st.session_state.attempts = 0
    st.session_state.score = STARTING_SCORE
    st.session_state.status = "playing"
    st.session_state.history = []

if "secret" not in st.session_state:
    st.session_state.secret = random.randint(low, high)

if "attempts" not in st.session_state:
    st.session_state.attempts = 0

if "score" not in st.session_state:
    st.session_state.score = STARTING_SCORE

if "status" not in st.session_state:
    st.session_state.status = "playing"

if "history" not in st.session_state:
    st.session_state.history = []

st.subheader("🕹️ Make your guess")

st.info(f"I'm thinking of a number between **{low}** and **{high}**. Can you find it?")

with st.sidebar.expander("Developer Debug Info"):
    st.write("Secret:", st.session_state.secret)
    st.write("Attempts:", st.session_state.attempts)
    st.write("Score:", st.session_state.score)
    st.write("Difficulty:", difficulty)
    st.write("History:", st.session_state.history)

raw_guess = st.text_input(
    "Your guess",
    placeholder="Type here…",
    label_visibility="collapsed",
    key=f"guess_input_{difficulty}",
)

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

# FIX: New Game now resets score, status, and history too, fixed with Claude Code and verified with new tests
# FIX: New Game now draws the secret from the current difficulty's range (was hardcoded 1-100)
if new_game:
    st.session_state.attempts = 0
    st.session_state.secret = random.randint(low, high)
    st.session_state.score = STARTING_SCORE
    st.session_state.status = "playing"
    st.session_state.history = []
    st.success("New game started.")
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

if submit:
    st.session_state.attempts += 1

    ok, guess_int, err = parse_guess(raw_guess)

    if not ok:
        st.session_state.history.append(raw_guess)
        st.error(err)
    elif guess_int < low or guess_int > high:
        # Out-of-range guesses don't count against the player
        st.session_state.attempts -= 1
        st.error(f"Your guess must be between {low} and {high}. Try again!")
    else:
        st.session_state.history.append(guess_int)

        if st.session_state.attempts % 2 == 0:
            secret = str(st.session_state.secret)
        else:
            secret = st.session_state.secret

        outcome, message = check_guess(guess_int, secret)
        proximity = get_proximity_hint(guess_int, st.session_state.secret)
        penalty = PROXIMITY_PENALTY.get(proximity, 15)

        if show_hint:
            if outcome == "Win":
                st.warning(message)
            else:
                st.warning(f"{proximity} — {message}  (−{penalty} pts)")
        elif outcome != "Win":
            st.info(
                f"Guess **{guess_int}** registered (−{penalty} pts). "
                f"Turn on “Show hint” for clues!"
            )

        st.session_state.score = update_score(
            current_score=st.session_state.score,
            outcome=outcome,
            proximity=proximity,
        )

        # --- AI Coach block moved here, inside the else, using local outcome/guess_int ---
        if outcome != "Win":
            tips = retrieve_tips(
                proximity, attempt_limit - st.session_state.attempts,
                attempt_limit, guess_int, st.session_state.history
            )
            coach_message = generate_ai_coach_message(
                outcome, proximity, tips, attempt_limit - st.session_state.attempts
            )
            st.write(f"💡 **Hint:** {coach_message}")

        if outcome == "Win":
            st.balloons()
            st.session_state.status = "won"
            guesses_used = st.session_state.attempts
            plural = "guess" if guesses_used == 1 else "guesses"
            st.success(
                f"🏆 You cracked it! The number was **{st.session_state.secret}** "
                f"in {guesses_used} {plural}. Final score: **{st.session_state.score}** ⭐"
            )
        else:
            if st.session_state.attempts >= attempt_limit:
                st.session_state.status = "lost"
                st.error(
                    f"💥 Out of guesses! The number was **{st.session_state.secret}**. "
                    f"Score: **{st.session_state.score}** — better luck next round!"
                )

with stats_placeholder.container():
    attempts_left = attempt_limit - st.session_state.attempts

    stat1, stat2, stat3 = st.columns(3)
    stat1.metric("⭐ Score", st.session_state.score)
    stat2.metric("❤️ Guesses Left", max(attempts_left, 0))
    stat3.metric("🎚️ Difficulty", difficulty)

    # Progress bar showing how many attempts are used up
    used_ratio = min(st.session_state.attempts / attempt_limit, 1.0)
    st.progress(used_ratio, text=f"Attempts used: {st.session_state.attempts} / {attempt_limit}")

# --- Guess history strip (shown to the player, reflects the latest guess) ---
if st.session_state.history:
    chips = []
    for g in st.session_state.history:
        # Non-numeric entries are stored as raw strings — flag them as invalid
        css_class = "guess-chip" if isinstance(g, int) else "guess-chip bad"
        chips.append(f'<span class="{css_class}">{html.escape(str(g))}</span>')
    st.markdown("**Your guesses so far:**")
    st.markdown(f'<div class="guess-chips">{"".join(chips)}</div>', unsafe_allow_html=True)