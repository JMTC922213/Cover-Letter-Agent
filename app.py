"""app.py — Streamlit UI for the cover letter agent.

Build this Saturday evening. Run:  streamlit run app.py
"""
import streamlit as st

from agent import analyze_skill_gap, generate_cover_letter
from eval import judge

# Load the CV once at startup.
with open("my_cv.txt", encoding="utf-8") as f:
    cv_text = f.read()

st.title("Cover Letter Agent")
st.caption("Paste a job description — get a tailored cover letter and a skill-gap analysis.")

job_description = st.text_area("Job description", height=300)

if st.button("Generate", type="primary"):
    if not job_description.strip():
        st.warning("Paste a job description first.")
    else:
        # TODO (polish): switch to streaming via
        #   client.models.generate_content_stream() + st.write_stream()
        #   for a more responsive feel.

        # 1. Generate the cover letter.
        with st.spinner("Writing cover letter..."):
            cover_letter = generate_cover_letter(job_description, cv_text)
        st.subheader("Cover letter")
        st.write(cover_letter)

        # 2. Score it with the LLM judge (the eval suite, applied live).
        st.subheader("Letter quality (LLM-as-judge)")
        try:
            with st.spinner("Scoring the letter..."):
                scores = judge(cover_letter, job_description, cv_text)
            cols = st.columns(len(scores))
            for col, (dim, score) in zip(cols, scores.items()):
                col.metric(dim.capitalize(), f"{score}/5")
            total = sum(scores.values())
            st.write(f"**Total: {total}/25**")
            st.caption("Each dimension scored 1-5 by an independent LLM judge (gemini-2.5-flash).")
        except Exception as e:
            st.warning(f"Couldn't score the letter: {e}")

        # 3. Identify gaps in the candidate's CV vs the JD.
        with st.spinner("Analyzing skill gaps..."):
            gaps = analyze_skill_gap(job_description, cv_text)
        st.subheader("Skill gap")
        st.write(gaps)
