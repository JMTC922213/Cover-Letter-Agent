"""agent.py — core cover letter logic.

Build this Saturday afternoon (generate_cover_letter) and
Sunday afternoon (analyze_skill_gap). See cover-letter-agent-weekend-plan.md.
"""
import os

from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

MODEL = "gemini-2.5-flash"


def generate_cover_letter(job_description: str, cv_text: str) -> str:
    """Return a tailored cover letter for this job description and CV.

    V3 prompt — adds greeting/sign-off structure; grounds the opening
    hook in JD-quoted specifics to push specificity without inviting
    company-fact hallucination.
    """
    prompt = f"""You are an expert cover letter writer. Write a cover letter for the job below, tailored to the candidate's CV.

JOB DESCRIPTION:
{job_description}

CANDIDATE CV:
{cv_text}

REQUIREMENTS:

Structure:
- Begin with "Dear [Company] Hiring Team," using the company name from the JD if identifiable; otherwise "Dear Hiring Team,". On its own line, followed by a blank line.
- Then 3-4 body paragraphs (the hook + experience + close).
- End with "Sincerely," on its own line, then the candidate's name (use the name from the CV).

Opening (the first body sentence, after the greeting):
- Must quote or closely paraphrase a SPECIFIC phrase or detail from the job description. Do not reference company facts (blog posts, features, news) that are not in the JD or CV. If you cannot find a specific JD detail to ground on, anchor on a verbatim CV experience instead.
- Examples of the pattern:
    "Your JD's emphasis on 'iterating fast on real user feedback' matches the rhythm I built at..."
    "The line in your posting about [exact JD phrase] caught my attention because..."
- The first body sentence must NOT start with: "I am writing", "I'm writing", "I would like to", "I'd like to", "I am excited", "I'm thrilled", "I am applying", "Developing", "Building" (when used as a generic abstract observation) — or any variant. No generic application openers about the candidate's feelings.

Body:
- Cite 2-3 concrete experiences from the CV that match the JD's requirements. Use the CV's actual numbers and names.
- Do not invent achievements, metrics, or experience levels not present in the CV.
- Match the candidate's voice. If the CV says "light exposure," do not call it "deep expertise."

Length: Under 300 words (excluding greeting and sign-off).

Format — output plain text only. Forbidden characters and constructs:
- **bold** or __bold__
- *italic* or _italic_
- `backticks` of any kind (inline or fenced code blocks)
- # headers
- - or * bullet points
- [links](url) and tables
- Do not include preamble like "Here is your cover letter:" or trailing assistant notes.

BEFORE OUTPUTTING — re-read your draft and check:
1. Does it begin "Dear [Company] Hiring Team," on its own line?
2. Does the first body sentence quote or closely paraphrase a specific phrase from the JD?
3. Is every fact in the body present in the CV?
4. Are there ANY forbidden formatting characters? (Strip them.)
5. Does it end with "Sincerely," and the candidate's name from the CV?

Output only the final cover letter."""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )
    return response.text


def analyze_skill_gap(job_description: str, cv_text: str) -> str:
    """Return a list of JD requirements the CV does not clearly cover.

    V2 prompt — adds explicit gap categories so soft/role-fit gaps
    surface; enforces a 3-bullet minimum with anti-padding escape hatch.
    """
    prompt = f"""You are a frank hiring analyst. Identify the gaps between this job description and the candidate's CV — skills, experiences, or qualifications the JD requires that the CV does NOT clearly demonstrate.

JOB DESCRIPTION:
{job_description}

CANDIDATE CV:
{cv_text}

REQUIREMENTS:

Output: a markdown bulleted list, MINIMUM 3 bullets, maximum 8.

Look for gaps in THREE categories — survey each one before writing:

1. MISSING SKILLS — JD requires X; CV does not mention X at all.
   Example: "Specific terminal UI frameworks (e.g., Ink, Blessed) — CV mentions CLI tools generally but not these libraries."

2. DEPTH GAPS — CV mentions X but at a lower level than the JD requires.
   Quote the CV's own qualifier verbatim.
   Example: "Production experience with Anthropic APIs — CV calls it 'light exposure'."

3. SOFT / ROLE-FIT GAPS — JD asks for opinions, perspectives, collaboration
   patterns, or qualitative traits the CV doesn't demonstrate.
   Example: "Direct collaboration with model researchers — CV shows engineering team work only."

Each bullet must:
- Quote or closely paraphrase a SPECIFIC requirement from the JD (do not invent requirements not in the JD).
- Be one line. No hedging language like "could benefit from" or "would be helpful to learn" — name the gap directly.
- Do not list skills the CV already clearly covers at the level the JD requires.

ANTI-PADDING RULE: If after honest analysis of all 3 categories there are genuinely fewer than 3 gaps, output what you have honestly — do not invent weak gaps to hit the count. But: actually survey all 3 categories first. Most JD/CV pairs have at least one gap in each.

If there are no significant gaps anywhere, output exactly: "No significant gaps identified."

BEFORE OUTPUTTING — re-read your draft and check:
1. Did you survey all THREE gap categories (missing, depth, soft/role-fit)?
2. Is every bullet a real JD requirement (not invented)?
3. Did any bullet name something the CV already covers at the required level? (Strip those.)
4. Any hedging language anywhere? ("could benefit from" / "would help to learn" / "may want to")
5. If fewer than 3 bullets — did you genuinely find nothing in one of the categories, or did you skip it?

Output the list only — no preamble like "Here are the gaps:", no closing summary."""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
    )
    return response.text
