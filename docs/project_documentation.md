# SmartHire AI Pipeline - Project Documentation

## 1. What is the Project About?
**SmartHire AI** is an intelligent, automated recruitment pipeline. Its core goal is to connect to a user's Gmail account, search for newly received emails that are potential job alerts or job postings, filter out irrelevant emails, extract structured job information from the relevant ones, analyze the user's CV, score how well the user matches the job, and finally export this data into a formatted Google Sheet and a local CSV.

## 2. Why this Project?
Job hunting is tedious. Professionals often receive dozens of job alerts daily from LinkedIn, Glassdoor, and recruiters. Manually reading each email, determining if the role is a good fit, and tracking applications in a spreadsheet is incredibly time-consuming. 
This project automates the entire top-of-funnel job search process:
* **Saves Time:** Automatically reads and categorizes emails.
* **Smart Filtering:** Uses Machine Learning to discard newsletters and spam, keeping only genuine job posts.
* **AI Evaluation:** AI automatically compares your CV to the job description and tells you if it's worth applying for.
* **Organized Tracking:** Outputs everything directly to Google Sheets for easy tracking.

## 3. Technologies Used
* **Python (3.10+)**: The core programming language.
* **Google APIs (Gmail API & Google Sheets API)**: For reading incoming emails and writing output data.
* **Google Gemini AI API (`google-genai`)**: For advanced text extraction and semantic candidate-job matching.
* **Scikit-Learn (TF-IDF & Naive Bayes)**: For the initial fast, local Machine Learning classification.
* **Pandas**: For data manipulation and CSV export.
* **PyMuPDF (`pymupdf`)**: To read and extract text from the user's CV PDF.

## 4. Which Models I Used & Why? (And Alternatives)

### Model 1: Local Machine Learning (`Multinomial Naive Bayes` + `TF-IDF`)
* **What it does:** Scans the subject line and email body to classify it as a "Job Post" (1) or "Not a Job Post" (0).
* **Why use it:** AI APIs (like Gemini) cost money or have strict rate limits (like Gemini's 20 requests/day free tier). It is highly inefficient to send 100 spam emails to Gemini just to find out they aren't jobs. Naive Bayes is extremely fast, runs locally, costs nothing, and acts as a "bouncer" to filter out junk before using the expensive AI.
* **Alternatives:** `Support Vector Machines (SVM)`, `Random Forest`, or `HuggingFace Transformers (BERT)`. We used Naive Bayes because it requires very little training data to work well on text classification and uses almost zero memory.

### Model 2: Large Language Model (`Gemini 3.5 Flash`)
* **What it does:** Extracts structured JSON data (Salary, Location, Tech Stack, etc.) from the raw email text and semantically compares the CV to the Job Description.
* **Why use it:** Traditional coding (Regex or string matching) is terrible at understanding human language context (e.g., figuring out if a salary is monthly, yearly, or hourly). Gemini excels at extracting structured JSON from messy email threads.
* **Alternatives:** `OpenAI GPT-4o-mini`, `Anthropic Claude 3 Haiku`, or local LLMs like `Llama 3 8B`. Gemini was chosen because it has a generous free tier for developers.

## 5. File Structure & Explanation of Every File

* **`main.py`**: The main entry point of the application. It orchestrates everything: trains the ML model, fetches emails, runs the extraction, computes scores, and triggers the Google Sheets export.
* **`core/config.py`**: Holds all the environment variables, API keys, file paths, and logger configurations. Centralizes settings.
* **`data/dataset.py`**: Contains the hardcoded training data (examples of job emails vs spam emails) used to train the Naive Bayes classifier.
* **`domain/matching_engine.py`**: Contains the logic and mathematical weights for scoring a job match. It calculates scores based on Skills (40%), Experience (30%), Location (10%), and Semantic AI Match (20%).
* **`domain/text_cleaner.py`**: A utility to clean HTML tags and weird formatting out of email bodies before ML processing.
* **`ml/classifier.py`**: The actual Scikit-Learn Machine Learning pipeline. It vectorizes text and trains the Naive Bayes model. It also saves/loads the model to a `.pkl` file so it doesn't have to retrain every time.
* **`services/cv_parser.py`**: Uses PyMuPDF to open `cv.pdf` and extract all the text so the AI can read it.
* **`services/gemini_service.py`**: Connects to Google's Gemini API. It contains the exact prompts used to ask the AI to extract Job JSON data and CV JSON data. It also includes retry-logic if the API rate limit is hit.
* **`services/gmail_service.py`**: Handles Google OAuth login for Gmail and uses the Gmail API to search for `is:unread` emails from the last 7 days.
* **`services/sheets_service.py`**: Handles Google OAuth login for Google Sheets and appends the Pandas DataFrame to the target spreadsheet.

## 6. What Happens If You Change Something? (Impact Analysis)
* **Updating `data/dataset.py`**: If you add new examples of emails to this file, the `ml/classifier.py` will retrain the model on the next run. This will make your spam filter smarter.
* **Updating `domain/matching_engine.py`**: If you change the weights (e.g., make Skills worth 80% instead of 40%), the final "Match Score" out of 100 will drastically change for all jobs.
* **Updating `services/gemini_service.py`**: If you add a new field to the prompt (e.g., "Extract Visa Sponsorship"), the AI will start returning that data. However, you must also update `main.py` to map that new JSON key into the Pandas DataFrame, or it will be ignored.

---

## 7. Code Walkthrough (Cell-by-Cell Explanation)
*(This section explains the conceptual flow of the code as if it were a Jupyter Notebook)*

### ============================================
### CELL 1: INITIALIZATION & ML TRAINING
### ============================================
```python
classifier = JobEmailClassifier()
if not classifier.load_model():
    df = get_training_data()
    classifier.train(df)
    classifier.save_model()
```
**Explanation:** 
When the script starts, it checks if `job_email_classifier.pkl` exists. If it doesn't, it loads the hardcoded dataset from `dataset.py`, trains the TF-IDF Vectorizer and Naive Bayes model, and saves it to disk. 
**Why:** Training takes a few seconds. Saving it to a `.pkl` file means future runs happen instantly.

### ============================================
### CELL 2: FETCHING EMAILS VIA GMAIL API
### ============================================
```python
gmail = GmailService()
emails = gmail.get_unread_job_emails(days=7, max_results=50)
```
**Explanation:** 
Logs into your Gmail using OAuth tokens. It uses a specific query (`newer_than:7d is:unread`) to fetch up to 50 recent unread emails. 
**Why:** We only want fresh jobs, and we don't want to process the same emails twice (hence `is:unread`).

### ============================================
### CELL 3: ML SPAM FILTERING
### ============================================
```python
relevant_emails = []
for em in emails:
    text = clean_text(em["subject"] + " " + em["snippet"])
    if classifier.predict(text) == 1:
        relevant_emails.append(em)
```
**Explanation:** 
The script takes the subject and snippet of every email and feeds it to the local Naive Bayes model. If the model outputs `1` (Job), it keeps it. If `0` (Spam/Newsletter), it ignores it.
**Why:** This protects your Gemini API quota. You don't want to waste your 20 daily free requests on LinkedIn marketing spam.

### ============================================
### CELL 4: AI EXTRACTION (GEMINI)
### ============================================
```python
for em in relevant_emails:
    job_info = gemini.extract_job_info(em["subject"], em["body"])
    extracted_jobs.append(job_info)
```
**Explanation:** 
Sends the full raw text of the relevant emails to Google Gemini. The prompt explicitly forces Gemini to return a structured JSON object containing things like `Job Title`, `Company`, `Salary`, and `Requirements`.
**Why:** This turns unstructured, messy human text into a clean database row.

### ============================================
### CELL 5: CV ANALYSIS
### ============================================
```python
cv_text = extract_cv_text("cv.pdf")
cv_profile = gemini.analyze_cv(cv_text)
```
**Explanation:** 
Reads your PDF resume using PyMuPDF, grabs all the text, and asks Gemini to turn your resume into a structured JSON profile (listing your exact skills, years of experience, and role).
**Why:** To score the jobs, the system needs to know who *you* are in a structured format.

### ============================================
### CELL 6: MATCHING ENGINE & SCORING
### ============================================
```python
for job in extracted_jobs:
    semantic_score = gemini.semantic_similarity_score(cv_summary, job_summary)
    scores = compute_match_score(cv_profile, job, semantic_score)
```
**Explanation:** 
Compares your CV JSON against the Job JSON. It calculates mathematical overlaps (e.g., if you have 4 out of 5 required skills, you get an 80% skill score). It also asks Gemini to evaluate the "semantic" fit (how well your vibes match the job description).
**Why:** This allows the final Google Sheet to be sorted from "Best Match" to "Worst Match", so you know exactly which jobs to apply for first.

### ============================================
### CELL 7: GOOGLE SHEETS EXPORT
### ============================================
```python
final_df = pd.DataFrame(final_results)
final_df.to_csv("Job_result.csv", index=False)
sheets = SheetsService(GOOGLE_SHEET_ID)
sheets.export(final_df)
```
**Explanation:** 
Converts the list of dictionaries into a Pandas DataFrame. It then exports it locally to a CSV, connects to the Google Sheets API, and appends the DataFrame as new rows at the bottom of your spreadsheet.
**Why:** This gives you a beautiful, permanent UI (Google Sheets) to track your applications, write notes, and manage your job hunt.
