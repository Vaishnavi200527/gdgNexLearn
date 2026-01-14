import google.generativeai as genai
import os

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
models = genai.list_models()
available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
print("Available models:", available_models)
