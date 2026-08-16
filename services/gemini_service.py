import re
import time
import json
from google import genai
from core.config import GEMINI_API_KEY, logger


class GeminiService:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set.")
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = "gemini-3.5-flash"
        self._quota_exhausted = False  # set True when daily limit hit

    def _generate(self, prompt: str, max_retries: int = 5) -> str:
        """Call Gemini with automatic retry on rate-limit (429) errors."""
        if self._quota_exhausted:
            raise RuntimeError("Daily Gemini quota already exhausted. Skipping.")

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                return response.text.strip()
            except Exception as e:
                err_str = str(e)
                is_rate_limit = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str
                is_daily_quota = "PerDay" in err_str or "per_day" in err_str.lower()

                if is_daily_quota:
                    self._quota_exhausted = True
                    logger.error(
                        "🚫 Daily Gemini quota exhausted (limit: 20/day on free tier).\n"
                        "   Quota resets at midnight UTC (6:00 AM Bangladesh time).\n"
                        "   Skipping all remaining Gemini calls for this run."
                    )
                    raise  # bubble up so callers log one clean error

                if is_rate_limit:
                    # Read the exact retry delay from error if present
                    wait = 65
                    match = re.search(r"retryDelay.*?['\"](\d+)s['\"]", err_str)
                    if match:
                        wait = int(match.group(1)) + 5
                    logger.warning(
                        f"Rate limit hit (attempt {attempt+1}/{max_retries}). "
                        f"Waiting {wait}s before retry..."
                    )
                    time.sleep(wait)
                else:
                    raise  # Non-rate-limit error, don't retry

        raise RuntimeError(f"Gemini failed after {max_retries} retries due to rate limits.")

    def extract_job_info(self, email_subject: str, email_body: str) -> dict:
        prompt = f"""
You are a job information extractor. Extract structured data from the job email below.
Return ONLY valid JSON — no markdown, no explanation, no extra text.

Fields to extract:
- Job Title: string (or null)
- Company: string (or null)
- Recruiter Name: string (or null)
- Recruiter Email: string (or null)
- Recruiter Phone: string (or null)
- Location: string (or null)
- Work Type: string (Remote/On-site/Hybrid or null)
- Salary: string (or null)
- Experience: string (or null)
- Requirements: string (short summary of key requirements or null)
- Technologies: string (comma separated list of tech stack e.g. "Flutter, React, Firebase" or null)
- Apply Link: string (direct URL or null)
- Job Summary: string (one-sentence summary of the job)
- skills: list of strings (for matching purposes, list all skills)

Email Subject: {email_subject}

Email Body:
{email_body[:3000]}

Return ONLY the JSON object.
"""
        try:
            raw = self._generate(prompt)
            if raw.startswith("```"):
                raw = re.sub(r"```[a-z]*\n?", "", raw).strip().rstrip("```").strip()
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Gemini job extraction error: {e}")
            return {
                "Job Title": None, "Company": None, "Recruiter Name": None, "Recruiter Email": None,
                "Recruiter Phone": None, "Location": None, "Work Type": None, "Salary": None,
                "Experience": None, "Requirements": None, "Technologies": None, "Apply Link": None,
                "Job Summary": "Could not parse job info.", "skills": []
            }


    def analyze_cv(self, cv_text: str) -> dict:
        prompt = f"""
You are a professional CV analyser. Extract the candidate's profile from the CV below.
Return ONLY valid JSON — no markdown, no explanation.

Fields to extract:
- name: string
- email: string or null
- phone: string or null
- location: string or null
- skills: list of strings (all technical and soft skills)
- experience_years: number (total years of professional experience, 0 if fresher)
- education: string (highest qualification)
- job_titles_held: list of strings (previous/current job titles)
- languages: list of strings (programming languages known)
- frameworks: list of strings (frameworks/tools known)
- summary: string (2-sentence profile summary)

CV Text:
{cv_text[:4000]}

Return ONLY the JSON object.
"""
        try:
            raw = self._generate(prompt)
            if raw.startswith("```"):
                raw = re.sub(r"```[a-z]*\n?", "", raw).strip().rstrip("```").strip()
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Gemini CV error: {e}")
            return {
                "name": "Unknown", "email": None, "phone": None, "location": None,
                "skills": [], "experience_years": 0, "education": None, "job_titles_held": [],
                "languages": [], "frameworks": [], "summary": "Could not parse CV."
            }

    def semantic_similarity_score(self, cv_summary: str, job_summary: str) -> float:
        prompt = f"""
You are a recruitment expert. Rate how well the candidate's profile matches the job description.

Candidate Profile:
{cv_summary}

Job Description:
{job_summary}

Return ONLY a decimal number between 0.0 and 1.0 representing the match quality.
0.0 = completely unrelated, 1.0 = perfect match.
Return ONLY the number, nothing else.
"""
        try:
            raw = self._generate(prompt)
            return max(0.0, min(1.0, float(raw.strip())))
        except Exception:
            return 0.5

    def generate_recommendation(self, cv_profile: dict, job_info: dict, scores: dict) -> str:
        prompt = f"""
You are a smart career advisor. Write a 2-3 sentence personalised recommendation
explaining whether this candidate is a good fit and what they should focus on.

Candidate Skills: {', '.join(cv_profile.get('skills', [])[:10])}
Candidate Experience: {cv_profile.get('experience_years', 0)} years
Candidate Location: {cv_profile.get('location', 'Unknown')}

Job Title: {job_info.get('job_title', 'Unknown')}
Job Company: {job_info.get('company', 'Unknown')}
Job Required Skills: {', '.join(job_info.get('skills', [])[:10])}
Job Location: {job_info.get('location', 'Unknown')}

Match Scores: Skill={scores['skill_score']}/100, Experience={scores['experience_score']}/100,
Location={scores['location_score']}/100, Semantic={scores['semantic_score']}/100,
Overall={scores['total_score']}/100

Write a helpful, honest, and encouraging recommendation.
"""
        try:
            return self._generate(prompt)
        except Exception as e:
            return f"Could not generate recommendation: {e}"
