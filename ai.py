import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# SECURITY FIX: Load API key from environment variable, never hardcode it

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

def analyze_resume(resume_text: str, user_goal: str) -> dict:
    prompt = f"""
You are a senior software engineer and hiring manager.

Evaluate the resume based on the user goal.

User goal: "{user_goal}"

STRICT RULES:
- Extract only relevant skills for this goal
- Remove irrelevant tools
- Identify real gaps
- Generate roadmap only for missing fields
- Make output DIFFERENT based on goal

Return ONLY a raw JSON object with no markdown, no backticks, no preamble:
{{
  "skills": [],
  "missing_skills": [],
  "roadmap": [],
  "interview_questions": []
}}

Resume:
{resume_text}
"""

    try:
        response = genai.GenerativeModel("gemini-2.5-flash").generate_content(
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
            "skills": [],
            "missing_skills": [],
            "roadmap": [],
            "interview_questions": [],
            "error": str(err)
        }