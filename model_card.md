# Model Card: Guessing Game AI Coach

## Overview

This document is the responsible-AI reflection for the Guessing Game AI Coach, an extension of the AI110 Module 1 "Game Glitch Investigator" project. It covers how AI tools were used during development, one helpful and one flawed AI suggestion encountered, and the system's known limitations.

## AI Collaboration

**Tools used:** Claude (via chat, for planning and code generation) and Claude Code (in VS Code, for in-editor debugging during the original Module 1 project).

### Helpful AI Suggestion

While wiring the AI coaching feature into `app.py`, the Streamlit app began crashing with `NameError: name 'outcome' is not defined` every time the page reloaded. I described the error and pasted the traceback to my AI assistant. It correctly identified that the AI coach block had been placed outside the `if submit:` block, at module level, meaning it ran on every script rerun even when no guess had been submitted yet, so `outcome` and `guess_int` were undefined. It proposed moving the entire coach block inside the `else` branch of the guess-handling logic, where those variables are actually defined. I verified the fix by re-running `pytest` (all 23 tests passed) and manually testing the app in the browser to confirm the coach message appeared correctly after a guess without crashing on page load.

### Flawed or Misleading AI Suggestion

During the original Module 1 project, I asked Claude Code to move the `check_guess` function out of `app.py` and into `logic_utils.py`. It did not warn me that `logic_utils.py` already contained an empty placeholder version of `check_guess` that simply raised `NotImplementedError`. As a result, my tests began calling the empty placeholder instead of my actual fix, and `pytest` failed even though my logic was correct. I only caught this by reading the actual pytest error message carefully rather than assuming the AI's refactor was complete and correct. I had Claude Code swap in my real function afterward. This reinforced a habit I carried into this final project: after any AI-driven refactor, check the rest of the affected file rather than assuming the change was applied cleanly in isolation.

## System Limitations

- **Small, static knowledge base.** The retrieval system draws from only 5 hardcoded strategy tips matched by simple tags. It cannot generalize to game states or strategies outside what was anticipated in advance.
- **Tag-based retrieval, not semantic search.** Retrieval relies on exact tag matches computed from game state (proximity label, attempts left, repeated guesses). It does not use embeddings or semantic similarity, so it cannot handle nuance beyond the predefined tag conditions.
- **Dependent on an external API.** The core coaching feature requires a working Gemini API key and network access. While the fallback path prevents crashes, the "AI-generated" coaching quality is only available when the API is reachable; otherwise the system silently reverts to static, pre-written text.
- **No user personalization across sessions.** The coach has no memory of a player's past games or skill level; every session starts from the same static knowledge base with no adaptation over time.
- **Deprecated SDK.** The project uses the `google.generativeai` package, which Google has marked as deprecated in favor of `google.genai`. The code functions correctly today but will need migration for long-term maintenance.

## Bias and Ethics Considerations

The coaching messages are generated from a small set of strategy tips written by the developer, so any framing bias in those tips (e.g., always encouraging "narrowing the range" as the correct strategy) is reflected directly in the AI's output. Because the tips are static and reviewed by a single person, there was no external review process to check for unintended tone or framing issues. The system poses minimal ethical risk given its scope (a low-stakes number-guessing game), but the same retrieval-then-generate pattern used here would require more careful bias review if applied to a higher-stakes domain, such as tutoring on academic or health topics.