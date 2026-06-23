import os
import requests
import json
import subprocess
from pathlib import Path

# Load configuration from environment variables
IMAGE_API_URL = os.getenv("IMAGE_API_URL")
IMAGE_API_KEY = os.getenv("IMAGE_API_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")

def generate_scenes(script_text):
    print("Generating scenes using GitHub Models API...")
    # Using GitHub Models API to convert script to scenes and prompts
    # This is a placeholder for the actual API call logic
    headers = {"Authorization": f"Bearer {GH_TOKEN}", "Content-Type": "application/json"}
    # Simplified logic for demonstration
    scenes = []
    for i in range(1, 151):
        scenes.append({
            "id": i,
            "image_prompts": [f"Scene {i} prompt 1", f"Scene {i} prompt 2"],
            "stock_query": "modern city"
        })
    return scenes

def generate_image(prompt, filename):
    headers = {"Authorization": f"Bearer {IMAGE_API_KEY}", "Content-Type": "application/json"}
    data = {"prompt": prompt}
    try:
        response = requests.post(IMAGE_API_URL, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"Error generating image: {e}")
    return False

def main():
    script_path = Path("script.txt")
    if not script_path.exists():
        print("script.txt not found!")
        return

    with open(script_path, "r") as f:
        script_text = f.read()

    scenes = generate_scenes(script_text)
    
    os.makedirs("output_images", exist_ok=True)

    for scene in scenes:
        for idx, p in enumerate(scene['image_prompts']):
            img_name = f"output_images/scene_{scene['id']}_img_{idx}.png"
            if not os.path.exists(img_name):
                generate_image(p, img_name)
        
    print("Processing complete. Images generated.")

if __name__ == "__main__":
    main()
