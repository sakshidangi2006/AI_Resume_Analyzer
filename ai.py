import os
import json
from google import genai

# SECURITY FIX: Load API key from environment variable, never hardcode it
client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY")
)

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

        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        start = content.find("{")
        end = content.rfind("}")

        if start == -1 or end == -1:
            raise ValueError("No JSON object found in model response")

        return json.loads(content[start:end + 1])

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