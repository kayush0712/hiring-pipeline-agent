# 🤖 Agentic Hiring Pipeline

An AI-powered, end-to-end hiring automation system that reads candidate emails, extracts and evaluates resumes, scores them using LLMs, stores results in a database, and automatically notifies recruiters — all without human intervention.

---

## 🧠 How It Works

```
Candidate sends email with resume (PDF)
        ↓
Pipeline reads inbox via IMAP
        ↓
PDF is downloaded & parsed (PyMuPDF)
        ↓
Resume is uploaded to Cloudinary
        ↓
Text is scored by LLaMA 3.3 (via Groq)
        ↓
Scores + metadata saved to MongoDB
        ↓
If score > 6/9 → Notify recruiter + Send ACK to candidate
```

---

## ✨ Features

- **Email Ingestion** — Connects to Gmail via IMAP and reads the latest email with a PDF attachment
- **PDF Parsing** — Extracts raw text from resumes using PyMuPDF (`fitz`)
- **AI Scoring** — Scores candidates across 3 dimensions using LLaMA 3.3 70B via Groq API
- **Cloud Storage** — Uploads resumes to Cloudinary for persistent access
- **Database** — Stores all candidate data and scores in MongoDB
- **Auto-Notifications** — Sends acknowledgement emails to candidates and alerts recruiters for high-quality applicants
- **REST API** — Flask-based endpoints for manual triggers and integrations

---

## 📊 Scoring Rubric

Candidates are evaluated out of **9 points** across three categories:

| Category | Max Score | Description |
|---|---|---|
| **AI Projects** | 3 | Quality and depth of AI/ML projects |
| **Proof** | 3 | GitHub repos, deployed demos, live links |
| **Application Answers** | 3 | Clarity and depth of written responses |

> Candidates scoring **> 6/9** are flagged as high-quality and trigger recruiter notifications automatically.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- MongoDB instance (local or Atlas)
- Groq API key
- Cloudinary account
- Gmail account with IMAP enabled and an App Password

### Installation

```bash
git clone https://github.com/your-username/hiring-pipeline-agent.git
cd hiring-pipeline-agent

pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the root directory:

```env
GROQ_API_KEY=your_groq_api_key

CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret

MONGO_URI=mongodb+srv://your_connection_string

EMAIL_USER=your_gmail@gmail.com
EMAIL_PASS=your_gmail_app_password

RECRUITER_EMAIL=recruiter@yourcompany.com
```

> ⚠️ **Gmail Setup**: Enable IMAP in Gmail settings and generate an [App Password](https://support.google.com/accounts/answer/185833) — do not use your regular Gmail password.

### Run the Server

```bash
python app.py
```

The server starts on `http://localhost:7000`

---

## 📡 API Endpoints

### `GET /`
Health check.

**Response:**
```
Hiring Pipeline Running
```

---

### `GET /read-email`
Reads the latest email from the inbox, processes the attached resume, scores it, and stores results.

**Response:**
```json
{
  "message": "Email processed successfully",
  "resume_url": "https://res.cloudinary.com/...",
  "ai_scores": {
    "name": "John Doe",
    "ai_projects_score": 2,
    "proof_score": 3,
    "answer_score": 2,
    "total": 7,
    "summary": "Strong candidate with deployed AI projects..."
  }
}
```

---

### `POST /upload-resume`
Manually upload a resume PDF for scoring.

**Request:** `multipart/form-data` with field `file` (PDF)

**Response:**
```json
{
  "message": "Resume uploaded successfully",
  "ai_scores": { ... },
  "url": "https://res.cloudinary.com/..."
}
```

---

### `POST /candidate`
Manually insert a candidate record into MongoDB.

**Request Body:**
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com"
}
```

---

## 🗂️ Project Structure

```
hiring-pipeline-agent/
├── app.py              # Main Flask app & all logic
├── .env                # Environment variables (gitignored)
├── requirements.txt    # Python dependencies
└── README.md
```

---

## 📦 Dependencies

```
flask
python-dotenv
pymongo
groq
PyMuPDF
cloudinary
requests
```

Install all at once:
```bash
pip install flask python-dotenv pymongo groq PyMuPDF cloudinary requests
```

---

## 🔒 Security Notes

- Never commit your `.env` file — add it to `.gitignore`
- Use Gmail App Passwords, not your account password
- Restrict your MongoDB URI to specific IPs in Atlas if deploying to production
- Consider adding authentication to your Flask endpoints before deploying publicly

---

## 🛣️ Roadmap / Potential Improvements

- [ ] Poll inbox on a schedule (e.g., using `APScheduler` or a cron job) instead of manual trigger
- [ ] Process multiple emails in a single run (currently handles only the latest)
- [ ] Add a frontend dashboard to view and filter candidates
- [ ] Support resume formats beyond PDF (DOCX, etc.)
- [ ] Add webhook support for real-time triggers
- [ ] Implement role-specific scoring prompts

---

## 🏢 About

Built  an AI startup automating intelligent workflows.

This pipeline was designed to eliminate manual resume screening by combining LLM-based reasoning with email automation, cloud storage, and a database — a fully agentic loop from inbox to recruiter alert.
