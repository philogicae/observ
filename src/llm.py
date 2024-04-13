from os import getenv
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=getenv("GROQ_API_KEY"))

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Explain the importance of fast language models",
        }
    ],
    model="mixtral-8x7b-32768",
)

print(chat_completion.choices[0].message.content)
