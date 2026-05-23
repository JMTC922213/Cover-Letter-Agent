"""eval.py — LLM-as-judge eval suite (Sunday morning, the differentiator).

Scores cover letters on 4 dimensions, each 1-5 -> 20-point scale:
specificity, authenticity, relevance, structure.

Run:  python eval.py
"""
import json
import os

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

MODEL = "gemini-2.5-flash"
DIMENSIONS = ["specificity", "groundedness", "authenticity", "relevance", "structure"]


def judge(cover_letter: str, job_description: str, cv_text: str) -> dict:
    """Score one cover letter against its JD and the candidate's CV.

    The CV is passed as ground truth so the judge can detect hallucinated
    facts (claims about the candidate not actually present in the CV) —
    a failure mode the judge cannot catch without it.

    Returns a dict like:
      {"specificity": 4, "groundedness": 2, "authenticity": 5,
       "relevance": 3, "structure": 4}
    Each score is an integer 1-5.
    """
    prompt = f"""You are a strict, experienced hiring manager evaluating a cover letter against (a) the job it is meant to respond to and (b) the candidate's actual CV, which is the source of truth for what the candidate has done.

Score the letter on FIVE dimensions, each 1-5 (integers only).
Use the full range. Most cover letters score 2 or 3 on most dimensions; a 5 is rare and means "outstanding". Do not default everything to 4.

DIMENSIONS:

1. SPECIFICITY — Does the letter cite concrete details (named companies, real projects, actual metrics), or is it generic and could-apply-anywhere?
   1 = entirely generic; 3 = some concrete details mixed with filler; 5 = every paragraph cites something specific

2. GROUNDEDNESS — Are the specific claims about the candidate actually supported by the CV? Hallucinated employers, invented metrics, or fabricated projects score very low here, even if they sound impressive. Compare every specific claim in the letter against the CV.
   1 = many claims contradict or are absent from the CV (clear hallucination); 3 = mixed — some grounded, some unsupported; 5 = every specific claim is verifiable in the CV

3. AUTHENTICITY — Does the letter sound like a real candidate in their own voice, or like an LLM template? Penalize clichés ("passionate self-starter", "I am thrilled to apply", "perfect alignment").
   1 = obvious AI/template tone; 3 = readable but full of clichés; 5 = sounds like a distinct human voice

4. RELEVANCE — Does the letter address THIS specific job's requirements, or could it apply to any similar role?
   1 = ignores the JD; 3 = mentions the role superficially; 5 = directly addresses multiple specific JD requirements with evidence

5. STRUCTURE — Is the letter well-organized (clear opening, focused body, strong close, appropriate length around 250-350 words)? Free of formatting issues (markdown leaks, missing greeting/sign-off)?
   1 = formless or formatting broken; 3 = competent but flat; 5 = tightly structured, no formatting issues

JOB DESCRIPTION:
{job_description}

CANDIDATE CV (ground truth):
---
{cv_text}
---

COVER LETTER TO SCORE:
---
{cover_letter}
---

Output a JSON object with exactly five integer keys: specificity, groundedness, authenticity, relevance, structure. No other keys, no commentary."""

    response = client.models.generate_content(
        model=MODEL,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
        contents=prompt,
    )
    return json.loads(response.text)


def score_set(examples: list, label: str) -> float:
    """Score every example in a set; print per-example totals; return the average."""
    totals = []
    for i, ex in enumerate(examples, start=1):
        scores = judge(ex["cover_letter"], ex["job_description"], ex["cv_text"])
        total = sum(scores.values())
        totals.append(total)
        print(f"  {label} #{i}: {scores}  total={total}/25")
    return sum(totals) / len(totals) if totals else 0.0


def main():
    """Score the good and bad sets; confirm a 9+ point gap on 25."""
    with open("evals/good_examples.json", encoding="utf-8") as f:
        good = json.load(f)
    with open("evals/bad_examples.json", encoding="utf-8") as f:
        bad = json.load(f)
    with open("my_cv.txt", encoding="utf-8") as f:
        cv_text = f.read()

    # All examples are judged against the current CV as ground truth.
    # Letters with claims not matching the CV will score low on
    # GROUNDEDNESS — by design.
    for ex in good + bad:
        ex["cv_text"] = cv_text

    print(f"Loaded {len(good)} good and {len(bad)} bad examples.\n")

    print("Scoring GOOD set:")
    good_avg = score_set(good, "good")
    print()
    print("Scoring BAD set:")
    bad_avg = score_set(bad, "bad")
    print()

    gap = good_avg - bad_avg
    verdict = "PASS" if gap >= 9 else "FAIL"
    print(f"Good average: {good_avg:.1f}/25")
    print(f"Bad average:  {bad_avg:.1f}/25")
    print(f"Gap:          {gap:.1f}  ->  {verdict} (need >= 9 for the eval suite to be meaningful)")


if __name__ == "__main__":
    main()
