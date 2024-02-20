# -*- coding: utf-8 -*-
from plugins.AbstractPlugin import *
import os
import openai

class ChatGptPlugin(AbstractPlugin):

    def __init__(self, pMainClass, pPluginID):
        super().__init__(pMainClass, pPluginID)

    def search(self, params):
        pSearchStr = params[0]
        self.logger.info("chatgpt: ask: " + pSearchStr)
        result = ""

        openai.api_key = os.getenv("CHAT_GPT_API_KEY")
        model_engine = os.getenv("CHAT_GPT_ENGINE")
        prompt = pSearchStr
        max_tokens = 1024

        # Generate a response
        completion = openai.Completion.create(
            engine=model_engine,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.5,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        # Print the response
        result = completion.choices[0].text
        return self.trimString(result)

    
    def trimString(self, pStr):
        tmp = """<<RESULT>>"""
        tmp = tmp.replace("<<RESULT>>", pStr)
        return tmp
