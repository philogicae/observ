from json import loads
from os import getenv

from addict import Dict
from dotenv import load_dotenv
from groq import Groq
from regex import compile

from bot import Log

load_dotenv()


def extract_json(string):
    pattern = compile(r"\{(?:[^{}]|(?R))*\}")
    matches = pattern.findall(string)
    if matches:
        return matches[0]


class LLM:
    def __init__(self):
        self.api = Groq(api_key=getenv("GROQ_API_KEY"))

    def call(self, system_prompt, user_prompt):
        content, retry = None, 0
        while not content and retry < 3:
            try:
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
                content = chat_completion.choices[0].message.content
            except Exception as e:
                Log.error("LLM Error: " + str(e))
        return content

    def call_for_json(self, system_prompt, user_prompt):
        formatted, retry = None, 0
        while not formatted and retry < 3:
            content = self.call(system_prompt, user_prompt)
            try:
                formatted = Dict(loads(extract_json(content)))
            except Exception as e:
                Log.error(
                    "JSON Error: "
                    + content
                    + "\nExtracted: "
                    + str(extract_json(content))
                )
            retry += 1
        return formatted
