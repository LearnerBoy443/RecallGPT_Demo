import os
import uuid
import requests
from django.conf import settings
import logging
from PIL import Image
import pytesseract


logger = logging.getLogger(__name__)

def get_keybert_model():
    if not hasattr(settings, 'KW_MODEL'):
        logger.info("Loading KeyBERT Model... This might take a moment.")
        settings.KW_MODEL = load_models("all-MiniLM-L6-v2")
        logger.info("Model loaded successfully.")
    return settings.KW_MODEL

def fix_broken_prompt(prompt: str) -> str:
    """Uses LLM to rewrite a broken/short prompt into a descriptive image prompt."""
    try:
        instruction = f"Rewrite the following vague or broken input into a highly detailed, breathtakingly photorealistic masterpiece image generation prompt. Mandatorily construct it like a professional 8k camera shot. Include keywords: 'award-winning macro photography, ultra-realistic, ray-traced lighting, subsurface scattering, ambient occlusion, Unreal Engine 5 render style reality'. ONLY return the prompt text, no pleasantries, no quotes: {prompt}"
        url = f"https://text.pollinations.ai/{requests.utils.quote(instruction)}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and response.text.strip():
            return response.text.strip()
    except Exception as e:
        print(f"Text restructuring failed: {e}")
    return prompt

def generate_image_pollinations(prompt: str, seed: int) -> str:
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?seed={seed}&width=1024&height=1024&nologo=true&model=flux-realism"
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    filename = f"{uuid.uuid4().hex}.jpg"
    image_dir = os.path.join(settings.BASE_DIR, 'static', 'images')
    os.makedirs(image_dir, exist_ok=True)
    
    filepath = os.path.join(image_dir, filename)
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(1024):
            f.write(chunk)
            
    return filename

def extract_text_from_image(filepath: str) -> str:
    """Uses OCR to extract text from a locally saved image."""
    try:
        img = Image.open(filepath)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return ""
