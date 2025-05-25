import os
from openai import OpenAI
from PyPDF2 import PdfReader
from langdetect import detect
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("OPENAI_API_KEY loaded:", bool(os.getenv("OPENAI_API_KEY")))  # Debug print

# Logging functions
def record_user_details(email, name="Not provided", notes="Not provided"):
    os.makedirs("logs", exist_ok=True)
    with open("logs/emails.txt", "a", encoding="utf-8") as f:
        f.write(f"{email}, {name}, {notes}\n")

def record_unknown_question(question):
    os.makedirs("logs", exist_ok=True)
    with open("logs/unanswered.txt", "a", encoding="utf-8") as f:
        f.write(question + "\n")

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

        # Load Summary
        try:
            with open("me/summary.txt", "r", encoding="utf-8") as f:
                self.summary = f.read()
        except Exception as e:
            print(f"[ERROR] Reading summary: {e}")
            self.summary = "[Summary could not be loaded]"

    def system_prompt(self):
        return f"""You are acting as {self.name}. You are answering professionally as if you're {self.name}.

## Summary:
{self.summary}

## LinkedIn Resume:
{self.linkedin}

Always ask for the user's email if it's not provided yet.
"""

    def chat(self, message, history):
        try:
            lang = detect(message)
        except:
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

            if any(x in reply.lower() for x in ["i don't know", "i'm not sure", "i cannot answer"]):
                record_unknown_question(message)

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