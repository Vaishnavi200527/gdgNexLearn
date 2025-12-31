import os
from dotenv import load_dotenv
import requests

load_dotenv()
key = os.getenv('GEMINI_API_KEY')
print('KEY_PRESENT:', bool(key), 'TRUNC:', (key[:6]+'...') if key else None)
try:
    r = requests.get('https://generativelanguage.googleapis.com/v1/models', params={'key': key}, timeout=10)
    print('STATUS:', r.status_code)
    print('BODY:', r.text[:1000])
except Exception as e:
    print('REQUEST_ERROR:', e)
