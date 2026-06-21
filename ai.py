import ast
import os
import re
import json
from google import genai
from dotenv import load_dotenv

load_dotenv("api.env")

# SECURITY FIX: Load API key from environment variable, never hardcode it
client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY")
)


def _extract_json_text(content: str) -> str:
    if content.startswith("```"):
        parts = content.split("```")
        if len(parts) >= 2:
            content = parts[1]
            if content.lstrip().startswith("json"):
                content = content[4:]

    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model response")

    json_text = content[start:end + 1].strip()
    json_text = re.sub(r",\s*([}\]])", r"\1", json_text)
    return json_text


def _parse_json_text(json_text: str) -> dict:
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as err:
        try:
            return ast.literal_eval(json_text)
        except Exception:
            raise ValueError(
                f"Failed to parse JSON response: {err.msg} "
                f"(line {err.lineno} column {err.colno} char {err.pos})"
            ) from err


def analyze_resume(resume_text: str, user_goal: str, job_description: str = "") -> dict:
    jd_section = f"""
Job Description (for keyword matching):
{job_description}
""" if job_description.strip() else "No job description provided — skip keyword_matches and keyword_gaps."

    prompt = f"""
You are a senior software engineer, ATS expert, and hiring manager.

Evaluate the resume for the given user goal and return a comprehensive analysis.

User goal: "{user_goal}"

{jd_section}

SCORING RULES:
- resume_score (0–100): Overall quality based on formatting, clarity, impact, and relevance to goal
- ats_score (0–100): How well the resume would pass Applicant Tracking Systems (clean formatting, keywords, no tables/columns/images)

KEYWORD RULES (only if job description is provided):
- keyword_matches: important keywords/phrases from the JD that ARE present in the resume
- keyword_gaps: important keywords/phrases from the JD that are MISSING from the resume

ANALYSIS RULES:
- skills: relevant skills the candidate already has for the goal
- missing_skills: important skills needed for the goal that are absent
- strengths: 3–5 specific things the resume does well
- weaknesses: 3–5 specific things that weaken the resume
- improvement_suggestions: concrete, actionable fixes to improve the resume
- roadmap: step-by-step learning path only for the missing skills
- interview_questions: likely interview questions for this role based on their background

Return ONLY a raw JSON object — no markdown, no backticks, no preamble:
{{
  "resume_score": 0,
  "ats_score": 0,
  "skills": [],
  "missing_skills": [],
  "strengths": [],
  "weaknesses": [],
  "improvement_suggestions": [],
  "keyword_matches": [],
  "keyword_gaps": [],
  "roadmap": [],
  "interview_questions": []
}}

Resume:
{resume_text}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        content = response.text.strip()
        json_text = _extract_json_text(content)
        return _parse_json_text(json_text)

    except Exception as err:
        return {
            "resume_score": 0,
            "ats_score": 0,
            "skills": [],
            "missing_skills": [],
            "strengths": [],
            "weaknesses": [],
            "improvement_suggestions": [],
            "keyword_matches": [],
            "keyword_gaps": [],
            "roadmap": [],
            "interview_questions": [],
            "error": str(err)
        }