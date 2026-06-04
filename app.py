from flask import Flask, request, jsonify
from dotenv import load_dotenv
from pymongo import MongoClient
from groq import Groq
import fitz
import requests
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
import json
import imaplib
import email
from email.header import decode_header
import smtplib
from email.mime.text import MIMEText


app = Flask(__name__)
load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


mongo_client = MongoClient(os.getenv("MONGO_URI"))
db = mongo_client["hiring_db"]
candidate_collection = db["candidates"]

print(os.getenv("CLOUDINARY_API_KEY"))


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def score_resume(text):

    prompt = f"""
You are a hiring assistant for Company, an AI startup.

Your task is to evaluate candidates realistically and critically.

Evaluate the candidate on these 3 categories:

1. AI Projects Score (0-3)
- 0 = No real AI projects
- 1 = Basic/tutorial projects only
- 2 = Good practical AI projects
- 3 = Strong real-world AI systems or production-level work

2. Proof Score (0-3)
- 0 = No GitHub/demo/links
- 1 = Weak or incomplete proof
- 2 = Good GitHub/demo/projects
- 3 = Strong proof with deployed demos, repositories, or real usage

3. Application Answer Score (0-3)
- 0 = Did not answer application questions
- 1 = Weak/generic answers
- 2 = Good thoughtful answers
- 3 = Exceptional clarity and reasoning

Candidate Resume/Application:
-----------------------------
{text}
-----------------------------

Reply ONLY in valid JSON.

Format:
{{
  "name": "candidate name",
  "ai_projects_score": 0,
  "proof_score": 0,
  "answer_score": 0,
  "total": 0,
  "summary": "short recruiter-style evaluation"
}}
"""

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="llama-3.3-70b-versatile",
    )

    content = chat_completion.choices[0].message.content

    print(content)

    content = content.strip()

    content = content.replace("```json", "")
    content = content.replace("```", "")

    parsed_json = json.loads(content)

    return parsed_json


def upload_to_cloudinary(file_path):

    result = cloudinary.uploader.upload(
        file_path,
        resource_type="raw",
        type="upload"
    )

    return result["secure_url"]

def read_emails():

    mail = imaplib.IMAP4_SSL("imap.gmail.com")

    mail.login(
        os.getenv("EMAIL_USER"),
        os.getenv("EMAIL_PASS")
    )

    mail.select("inbox")

    status, messages = mail.search(None, "ALL")

    email_ids = messages[0].split()

    latest_email_id = email_ids[-1]

    status, msg_data = mail.fetch(latest_email_id, "(RFC822)")

    raw_email = msg_data[0][1]

    msg = email.message_from_bytes(raw_email)

    subject = msg["subject"]

    print("Subject:", subject)

    from email.utils import parseaddr

    from_email = parseaddr(msg["from"])[1]

    print("From:", from_email)

    for part in msg.walk():

        if part.get_content_disposition() == "attachment":

            filename = part.get_filename()

            if filename.endswith(".pdf"):

                os.makedirs("upload", exist_ok=True)

                filepath = os.path.join("upload", filename)

                with open(filepath, "wb") as f:
                    f.write(part.get_payload(decode=True))

                print("Resume downloaded:", filepath)
                secure_url = upload_to_cloudinary(filepath)

                print("Cloudinary URL:", secure_url)

                extracted_text = extract_text_from_pdf(filepath)

                ai_scores = score_resume(extracted_text)
                print(ai_scores)

                candidate_data = {

                    "candidate_email": from_email,

                    "resume_url": secure_url,

                    "ai_scores": ai_scores,

                    "resume_text": extracted_text

                }

                candidate_collection.insert_one(candidate_data)

                if ai_scores["total"] > 6:

                    send_recruiter_email(
                                from_email,
                                ai_scores,
                                secure_url
                            )
                    send_ack_email(from_email)

                    print("High quality candidate detected")

                return {
                        "message": "Email processed successfully",
                        "resume_url": secure_url,
                        "ai_scores": ai_scores
                    }
  
def send_ack_email(to_email):

    subject = "Application Received - Company"

    body = """
Hi,

Thank you for applying to Company.

We have successfully received your application and our team is reviewing it.

We’ll reach out if your profile matches our requirements.

Best,
Company Hiring Team
"""

    msg = MIMEText(body)

    msg["Subject"] = subject
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = to_email

    server = smtplib.SMTP("smtp.gmail.com", 587)

    server.starttls()

    server.login(
        os.getenv("EMAIL_USER"),
        os.getenv("EMAIL_PASS")
    )

    server.send_message(msg)

    server.quit()

    print("Acknowledgement email sent")

def send_recruiter_email(candidate_email, ai_scores, resume_url):

    subject = "New High Quality Candidate - Company"

    body = f"""
New candidate detected by Company Hiring Agent.

Candidate Email:
{candidate_email}

Total Score:
{ai_scores["total"]}/9

AI Projects Score:
{ai_scores["ai_projects_score"]}

Proof Score:
{ai_scores["proof_score"]}

Answer Score:
{ai_scores["answer_score"]}

Summary:
{ai_scores["summary"]}

Resume URL:
{resume_url}
"""

    msg = MIMEText(body)

    msg["Subject"] = subject
    msg["From"] = os.getenv("EMAIL_USER")
    msg["To"] = os.getenv("RECRUITER_EMAIL")

    server = smtplib.SMTP("smtp.gmail.com", 587)

    server.starttls()

    server.login(
        os.getenv("EMAIL_USER"),
        os.getenv("EMAIL_PASS")
    )

    server.send_message(msg)

    server.quit()

    print("Recruiter email sent")

@app.route("/")
def home():
    return "Hiring Pipeline Running"

@app.route("/candidate", methods=["POST"])
def candidate():

    data = request.json


    result = candidate_collection.insert_one(data)

    data["_id"] = str(result.inserted_id)
    return jsonify({
        "message": "Candidate created successfully",
        "data": data,
    })



@app.route("/upload-resume", methods=["POST"])
def upload_resume():
   file = request.files["file"]

   upload_path = os.path.join("upload", file.filename)
   os.makedirs("upload", exist_ok=True)

   file.save(upload_path)
   extracted_text = extract_text_from_pdf(upload_path)
   ai_scores = score_resume(extracted_text)

   secure_url = upload_to_cloudinary(upload_path)

   print(secure_url)

   return jsonify({
    "message": "Resume uploaded successfully",
    "ai_scores": ai_scores,
    "url" : secure_url

   })


@app.route("/read-email")
def read_email():

    result = read_emails()

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, port=7000)
