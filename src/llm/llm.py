from os import getenv
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


class LLM:
    def __init__(self):
        self.api = Groq(api_key=getenv("GROQ_API_KEY"))

    def call(self, system_prompt, user_prompt):
        chat_completion = self.api.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )
        return chat_completion.choices[0].message.content