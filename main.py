import datetime
import hashlib
import pandas as pd
from core.config import logger, CV_PDF_PATH, CSV_EXPORT_PATH, GOOGLE_SHEET_ID
from data.dataset import get_training_data
from ml.classifier import JobEmailClassifier
from services.gmail_service import GmailService
from services.gemini_service import GeminiService
from services.sheets_service import SheetsService
from services.cv_parser import extract_cv_text
from domain.matching_engine import compute_match_score, score_to_stars

def main():
    logger.info("=== Starting SmartHire AI Pipeline ===")

    # 1. Train or load ML model
    classifier = JobEmailClassifier()
    if not classifier.load_model():
        logger.info("Training new model...")
        df = get_training_data()
        classifier.train(df)
        classifier.save_model()

    # 2. Authenticate external services
    gmail = GmailService()
    gemini = GeminiService()
    sheets = SheetsService(GOOGLE_SHEET_ID)

    # 3. Search Gmail — only UNREAD emails from the last 7 days
    logger.info("Searching Gmail for unread job emails (last 7 days)...")
    KEYWORDS = (
        "Flutter OR Dart OR Kotlin OR Android OR \"React Native\" OR \"App Developer\" "
        "OR \"Mobile Developer\" OR \"Mobile Application\" OR \"Android Developer\" "
        "OR \"iOS Developer\" OR \"Cross-platform\""
    )
    JOB_SITES = (
        "from:linkedin.com OR from:glassdoor.com OR from:bdjobs.com OR from:indeed.com "
        "OR from:jobgether.com OR from:remotehunter.co OR from:nextjobz.com OR from:ai2cyber.com"
    )
    queries = [
        # Unread job keyword emails from last 7 days
        f"is:unread newer_than:7d ({KEYWORDS})",
        # Unread from known job sites in last 7 days
        f"is:unread newer_than:7d ({JOB_SITES}) ({KEYWORDS})",
    ]

    message_refs = []
    for q in queries:
        refs = gmail.search_emails(q, max_results=20)
        message_refs.extend(refs)

    # Deduplicate by email ID, keep newest first
    message_refs = list({ref["id"]: ref for ref in message_refs}.values())
    logger.info(f"Found {len(message_refs)} unique unread job emails.")

    # 4. Fetch and classify
    classified_jobs = []
    for ref in message_refs:
        detail = gmail.get_email_details(ref["id"])
        combined_text = detail["subject"] + " " + detail["body"]
        result = classifier.classify(combined_text)
        
        if result["is_relevant"]:
            detail["confidence"] = result["relevant_probability"]
            classified_jobs.append(detail)
            
    logger.info(f"Filtered down to {len(classified_jobs)} relevant emails via ML.")

    if not classified_jobs:
        logger.info("No relevant jobs found. Exiting.")
        return

    # 5. Extract structured job info via Gemini
    extracted_jobs = []
    for i, job in enumerate(classified_jobs):
        logger.info(f"[{i+1}/{len(classified_jobs)}] Extracting: {job['subject'][:50]}")
        job_info = gemini.extract_job_info(job["subject"], job["body"])
        job_info["email_subject"] = job["subject"]
        job_info["email_from"] = job["from"]
        job_info["email_date"] = job["date"]
        job_info["confidence_score"] = job["confidence"]
        extracted_jobs.append(job_info)

    # 6. Extract and parse CV
    logger.info("Processing CV...")
    cv_text = extract_cv_text(CV_PDF_PATH)
    if cv_text:
        cv_profile = gemini.analyze_cv(cv_text)
        logger.info(f"CV Profile extracted for: {cv_profile.get('name', 'Unknown')}")
    else:
        logger.warning("CV extraction failed or empty. Using fallback profile.")
        cv_profile = {
            "name": "Candidate", "skills": ["Flutter", "Dart", "Firebase", "REST API", "Git"],
            "experience_years": 1, "location": "Dhaka, Bangladesh",
            "frameworks": ["Flutter", "GetX", "Provider"], "languages": ["Dart", "Python"],
            "summary": "Sample profile — please provide cv.pdf"
        }

    # 7. Match and score
    logger.info("Running matching engine...")
    final_results = []
    for job_info in extracted_jobs:
        semantic_score = gemini.semantic_similarity_score(
            cv_profile.get("summary", ""),
            job_info.get("email_summary", "")
        )
        scores = compute_match_score(cv_profile, job_info, semantic_score)
        stars = score_to_stars(scores["total_score"])
        recommendation = gemini.generate_recommendation(cv_profile, job_info, scores)

        # Build dedup key
        raw_url = job_info.get("Apply Link") or ""
        job_title = job_info.get("Job Title") or ""
        dedup_key_str = raw_url if raw_url else job_title
        if not dedup_key_str:
            dedup_key_str = job_info.get("email_from", "") + job_info.get("email_date", "")
        dedup_key = hashlib.md5(dedup_key_str.encode("utf-8")).hexdigest()

        # Extract dates
        email_date_str = job_info.get("email_date", "")
        now = datetime.datetime.now()
        
        final_results.append({
            "Application Date": "",
            "Application Time": "",
            "Job Found Date": now.strftime("%Y-%m-%d"),
            "Job Found Time": now.strftime("%H:%M"),
            "Job Title": job_info.get("Job Title", "Unknown"),
            "Company": job_info.get("Company", "Unknown"),
            "Recruiter Name": job_info.get("Recruiter Name", ""),
            "Recruiter Email": job_info.get("Recruiter Email", ""),
            "Recruiter Phone": job_info.get("Recruiter Phone", ""),
            "Location": job_info.get("Location", "Unknown"),
            "Work Type": job_info.get("Work Type", ""),
            "Salary": job_info.get("Salary", ""),
            "Experience": job_info.get("Experience", ""),
            "Requirements": job_info.get("Requirements", ""),
            "Technologies": job_info.get("Technologies", ""),
            "Apply Link": raw_url,
            "Source": "Gmail",
            "Job Email": job_info.get("email_from", ""),
            "Job Email Subject": job_info.get("email_subject", "No Subject"),
            "Status": "New",
            "Notes": recommendation,
            "Job Summary": job_info.get("Job Summary", ""),
            "Match Score": scores["total_score"],
            "Dedup Key": dedup_key
        })

    if final_results:
        final_df = pd.DataFrame(final_results).sort_values("Match Score", ascending=False).reset_index(drop=True)
    else:
        # Create empty dataframe with proper columns if no results
        columns = [
            "Application Date", "Application Time", "Job Found Date", "Job Found Time",
            "Job Title", "Company", "Recruiter Name", "Recruiter Email", "Recruiter Phone",
            "Location", "Work Type", "Salary", "Experience", "Requirements", "Technologies",
            "Apply Link", "Source", "Job Email", "Job Email Subject", "Status", "Notes",
            "Job Summary", "Match Score", "Dedup Key"
        ]
        final_df = pd.DataFrame(columns=columns)

    # 8. Export and output
    logger.info("\n=== FINAL RANKED JOBS ===")
    print(final_df[["Job Title", "Company", "Match Score"]].to_string())

    final_df.to_csv(CSV_EXPORT_PATH, index=False)
    logger.info(f"Results exported to {CSV_EXPORT_PATH}")

    sheets.export(final_df)

    logger.info("=== Pipeline Complete ===")

if __name__ == "__main__":
    main()
