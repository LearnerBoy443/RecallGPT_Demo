import requests

def fix_broken_prompt(prompt: str) -> str:
    try:
        url = f"https://text.pollinations.ai/{prompt}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except:
        pass
    return prompt

def generate_image_pollinations(prompt: str):
    try:
        url = f"https://image.pollinations.ai/prompt/{prompt}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return url
    except:
        pass
    return None
