# Cover Letter Agent

A Streamlit app that drafts a tailored cover letter, identifies skill gaps between a CV and a job description, and scores the generated letter using an independent LLM judge — all in a single click.

Built as a weekend project to practice **prompt engineering**, **LLM-as-judge evaluation**, and **iterative quality measurement** against a real free-tier LLM API (Gemini).

> _Drop a screenshot here once you've taken one — add `![screenshot](docs/screenshot.png)` and the image at that path._

---

## What it does

- **Generates** a cover letter from a candidate's CV and a pasted job description
- **Identifies** the gaps between the CV and the JD's stated requirements (missing skills, depth gaps, soft / role-fit gaps)
- **Scores** the generated letter live, on 5 dimensions (Specificity, Groundedness, Authenticity, Relevance, Structure), using an independent LLM-as-judge with structured JSON output

The whole flow runs in ~10–15 seconds and stays within Gemini's free tier.

---

## Getting started

```bash
git clone <your-repo-url>
cd cover-letter-agent

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and paste a free Gemini key from https://aistudio.google.com/apikey

# my_cv.txt ships with a fake demo CV (Alex Chen). The app reads from it
# at startup. To generate real letters for yourself, swap the contents
# LOCALLY only — don't commit your real CV.

streamlit run app.py        # the app
python smoke.py             # CLI smoke test (one JD, prints letter + gaps)
python eval.py              # run the LLM-as-judge eval suite
```

---

## How it works

```
┌────────────────────────────────────────────────────────────────┐
│  app.py (Streamlit UI)                                         │
│  ──────────────────                                            │
│  user pastes JD  ─┬──>  generate_cover_letter()  ──>  letter  │
│                   │                                            │
│                   ├──>  judge(letter, jd, cv)    ──>  scores  │
│                   │                                            │
│                   └──>  analyze_skill_gap()      ──>  gaps    │
└────────────────────────────────────────────────────────────────┘

eval.py (separate, developer-side)
  - loads evals/good_examples.json and evals/bad_examples.json
  - scores each with judge()
  - prints per-example breakdown, averages, and a PASS/FAIL verdict
    based on whether the good–bad gap is large enough to be meaningful
```

Three core LLM calls, each with intentional prompt design:

| Function | Lives in | Output type | Key prompt design choice |
|---|---|---|---|
| `generate_cover_letter` | `agent.py` | Plain prose | Hook grounded in JD-quoted phrases; concrete formatting bans (no `**bold**`, no `` ` `` etc.); self-check rules at the bottom |
| `analyze_skill_gap` | `agent.py` | Markdown bulleted list | Three explicit gap categories (missing / depth / soft–role-fit); anti-padding clause prevents inventing weak gaps to hit a count; anti-sycophancy framing |
| `judge` | `eval.py` | Structured JSON | `response_mime_type="application/json"` as an SDK-level *contract* (not a prompt request); scale anchors prevent inflated scoring |

---

## The iteration story (the interesting part)

This is what the project is really about. Three components each went through several prompt iterations driven by observed failures.

### Cover letter: v1 → v3

| Version | Output | Failure |
|---|---|---|
| **v1** | "At InnovateTech Solutions, I led the development… **25% improvement**…" | Massive hallucination — fabricated companies, invented metrics, markdown bold leaks |
| **v2** | "I'm writing to express my strong interest in the Software Engineer position…" | Generic opener (the model dodged "no I am writing" by rephrasing to "I'm writing"); backticks leaked around code-like tokens |
| **v3** | "The line in your job description emphasizing 'iterating fast on real user feedback' immediately resonated…" | None of the v1/v2 issues; opening quotes the JD verbatim |

The biggest lesson came between v1 and v2 — when `my_cv.txt` was an empty placeholder, the model invented an entire fictional candidate to satisfy the "write a compelling letter" goal. **Strengthening "do not invent" in the prompt couldn't have helped — a prompt cannot conjure information that isn't in the input.** Once a real CV was added, hallucination disappeared without changing the prompt.

The v2→v3 jump applied real prompt-engineering tactics:
- **Positive instructions beat negative ones.** "Don't open with X" gets dodged by rephrasing. "Open with a JD-quoted phrase" tells the model what TO do.
- **Concrete enumeration beats vague rules.** "No markdown" lost to backticks. `` "no **bold**, *italic*, `backticks`, # headers..." `` worked.
- **Rules at the end beat rules at the start.** The model attends more to recent context.

### Skill gap: v1 → v2

v1 found only 2 gaps when the prompt asked for 3–8. The missing one was the soft / role-fit category ("Strong opinions about developer tools and UX") — the model wasn't surveying that kind of gap.

v2 added three explicit gap categories (MISSING / DEPTH / SOFT-ROLE-FIT) with examples for each, plus an anti-padding rule preventing the model from inventing weak gaps to hit the minimum count. Result: 3 honest bullets including the previously-missed soft gap.

### Eval suite: v1 → v2

v1's judge took only `(cover_letter, job_description)` — no CV. Result:

| | good avg | bad avg | gap |
|---|---|---|---|
| v1 | 19.0 / 20 | 11.5 / 20 | **7.5** (barely passing) |

The bad set was dragged down by a synthetic template (6/20). The actually-hallucinated v1 cover letter scored **17/20** — almost as high as the good examples. Why? Because the judge had no ground truth: from its perspective, fabricated company names *looked* specific and credible.

v2 added `cv_text` to the judge's input and a new GROUNDEDNESS dimension explicitly comparing letter claims against CV. Result:

| | good avg | bad avg | gap |
|---|---|---|---|
| v2 | 24.0 / 25 | 9.0 / 25 | **15.0** (passes with margin) |

**The non-obvious finding:** giving the judge ground truth didn't just enable a new dimension — it sharpened *four out of five* existing ones. The hallucinated bad example's Specificity score collapsed from 5 → 1, because hollow specifics aren't actually specific if the judge can see they're fabricated. The same cascaded into Authenticity (3→1) and Relevance (5→3).

---

## What I learned about prompt engineering

1. **Prompt vs data.** When you see a failure, first ask: is this a prompt problem or a data problem? Hallucination from sparse input is a data problem; no amount of prompt cleverness fixes it.
2. **Sycophancy is the default.** Any evaluative task (judging, gap analysis, scoring) needs explicit anti-sycophancy structure — frank role-priming, scale anchors, banned hedge phrases. Otherwise the model softens criticism and inflates scores to be agreeable.
3. **Negative instructions get dodged.** "Don't say X" leaves a vacuum; the model picks the next closest thing. Positive instructions with examples ("open by quoting a JD phrase like 'iterating fast on user feedback'") work much better.
4. **Format = consumer.** Cover letter → human reader → plain text. Gap analysis → Streamlit `st.write()` → markdown bullets. Judge output → `json.loads()` → SDK-level JSON contract (`response_mime_type`), not a prompt request.
5. **An LLM judge can only detect failures visible in its input.** Hallucination requires ground truth. Without the CV, the judge cannot in principle distinguish "specific" from "specifically fabricated."

---

## Limitations and what I'd do next

This is a deliberately small project. Things I'd improve if I kept going:

- **More eval examples.** Currently 2 of each. A noisy gap. I'd hand-author ~10 in each set with varied failure modes.
- **Streaming output.** Currently the user waits 30–60s for the full response. `client.models.generate_content_stream()` + `st.write_stream()` would feel ~10× more responsive.
- **Retry + backoff for 503s.** The SDK does basic retries but Gemini's free tier saturates daily; a smarter exponential backoff + user-facing "try again in N seconds" would harden the app.
- **Judge biases.** LLM-as-judge has known biases (prefers its own model family's writing style). I'd compare scores across multiple judge models (Gemini + Claude + GPT) and average.
- **Authenticity ceiling.** Even v3 letters cap at 4/5 on Authenticity — a known limit of LLM-generated writing. Hard to push past without human-in-the-loop edits.
- **Structured outputs everywhere.** `analyze_skill_gap` could return JSON with category labels, enabling per-category counts and dashboards in the UI.

---

## Tech stack

- **Python 3.14** with a single `requirements.txt`
- **Google Gemini** (`gemini-2.5-flash`) via the `google-genai` SDK
- **Streamlit** for the UI
- **python-dotenv** for env loading

No vector DB, no embeddings, no fine-tuning. Just a CV in plain text and three well-designed prompts.

---

## File structure

```
.
├── README.md
├── agent.py                          # generate_cover_letter, analyze_skill_gap
├── eval.py                           # judge, score_set, main
├── app.py                            # Streamlit UI
├── smoke.py                          # CLI smoke test
├── my_cv.txt                         # candidate CV (plain text; demo CV included)
├── evals/
│   ├── good_examples.json            # good-quality reference letters
│   └── bad_examples.json             # known-bad reference letters
├── .env.example                      # env var template
├── .gitignore
└── requirements.txt
```

---

## License

MIT. Use it however you like.
