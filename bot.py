import os
import traceback
from openai import OpenAI
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langdetect import detect

# Load environment variables
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise EnvironmentError("OPENAI_API_KEY is not set in the environment.")

# ✅ Initialize OpenAI client (no `api_key=` needed, uses env var)
client = OpenAI()

print("[INFO] OPENAI_API_KEY loaded:", bool(api_key))  # Optional debug print

# Logging user interactions
def record_user_details(email, name="Not provided", notes="Not provided"):
    os.makedirs("logs", exist_ok=True)
    with open("logs/emails.txt", "a", encoding="utf-8") as f:
        f.write(f"{email}, {name}, {notes}\n")

def record_unknown_question(question):
    os.makedirs("logs", exist_ok=True)
    with open("logs/unanswered.txt", "a", encoding="utf-8") as f:
        f.write(question + "\n")

# Main class for the assistant logic
class Me:
    def __init__(self):
        self.client = client
        self.name = "Alaa Allam"
        self.user_email = None

        # Load LinkedIn resume
        try:
            reader = PdfReader("me/linkedin.pdf")
            self.linkedin = "".join([p.extract_text() for p in reader.pages if p.extract_text()])
        except Exception as e:
            print(f"[ERROR] Reading CV: {e}")
            self.linkedin = "[LinkedIn resume could not be loaded]"

        # Load personal summary
        try:
            with open("me/summary.txt", "r", encoding="utf-8") as f:
                self.summary = f.read()
        except Exception as e:
            print(f"[ERROR] Reading summary: {e}")
            self.summary = "[Summary could not be loaded]"

    # Prompt for the assistant’s persona
    def system_prompt(self):
        return f"""You are acting as {self.name}, a data scientist and AI expert in retail and e-commerce. Answer professionally and helpfully.

## Summary:
{self.summary}

## LinkedIn Resume:
{self.linkedin}

Always ask for the user's email if it's not provided yet.
"""

    # Main chat function
    def chat(self, message, history):
        try:
            lang = detect(message)
        except Exception:
            lang = "en"

        messages = [{"role": "system", "content": self.system_prompt()}]
        for user_msg, bot_msg in history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": bot_msg})
        messages.append({"role": "user", "content": message})

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7
            )
            reply = response.choices[0].message.content

            # Log unanswered queries
            if any(phrase in reply.lower() for phrase in ["i don't know", "i'm not sure", "i cannot answer"]):
                record_unknown_question(message)

            # Capture user email
            if not self.user_email and "@" not in message:
                reply += "\n\n---\nCould you please share your email so I can follow up if needed?"
            elif "@" in message and "." in message:
                self.user_email = message
                record_user_details(self.user_email)

        except Exception as e:
            print(f"[ERROR] OpenAI API failed: {e}")
            traceback.print_exc()
            reply = "Sorry, something went wrong while generating a response."

        history.append([message, reply])
        return history
    