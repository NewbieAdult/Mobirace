# Nguyen Tuan Minh
# 22/07/2023
from fastapi import Form, HTTPException
import requests
import json
import os
from dotenv import load_dotenv
async def verify_recaptcha(token: str):
    try:
        load_dotenv()
        r = requests.post('https://www.google.com/recaptcha/api/siteverify',
                      data = {'secret' : os.getenv("secret_recaptcha"),
                              'response' :token})
        google_response = json.loads(r.text)
        return  google_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))