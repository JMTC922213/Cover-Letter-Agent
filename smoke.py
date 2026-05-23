"""smoke.py — quick sanity check for generate_cover_letter.

Run:  python smoke.py
Reads my_cv.txt, uses a hardcoded sample JD, prints the letter.
Swap the JD below for a real one you'd actually apply to.
"""
from agent import analyze_skill_gap, generate_cover_letter

with open("my_cv.txt", encoding="utf-8") as f:
    cv_text = f.read()

sample_jd = """Software Engineer — Anthropic, San Francisco

We're hiring a software engineer to help build Claude Code, our
terminal-based AI coding assistant.

You'll:
- Design and ship features in TypeScript and Python
- Work directly with model researchers to shape model capabilities
- Iterate fast on real user feedback

We're looking for:
- 3+ years building production software
- Strong opinions about developer tools and UX
- Comfort working with LLMs at the API layer
- Bonus: experience with terminal applications, Node.js, or React
"""

print("=" * 60)
print("COVER LETTER")
print("=" * 60)
print(generate_cover_letter(sample_jd, cv_text))

print()
print("=" * 60)
print("SKILL GAPS")
print("=" * 60)
print(analyze_skill_gap(sample_jd, cv_text))
