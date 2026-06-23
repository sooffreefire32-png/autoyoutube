import os
import requests
import json
import subprocess
from pathlib import Path
import random

# Load configuration from environment variables
IMAGE_API_URL = os.getenv("IMAGE_API_URL")
IMAGE_API_KEY = os.getenv("IMAGE_API_KEY")
GH_TOKEN = os.getenv("GH_TOKEN")

def generate_scenes(script_text):
    print("Generating optimized scenes...")
    scenes = []
    # Reduce scenes slightly for memory stability on GitHub Actions
    num_scenes = 80 
    for i in range(1, num_scenes + 1):
        scenes.append({
            "id": i,
            "image_prompts": [
                f"Cinematic 16:9, 2D anime style, mystery scene {i}: {script_text[:40]}",
                f"Dramatic 16:9, hand-drawn detail, scene {i} action"
            ]
        })
    return scenes

def generate_image(prompt, filename):
    if Path(filename).exists():
        return True # Auto-resume: skip if already exists
    
    headers = {"Authorization": f"Bearer {IMAGE_API_KEY}", "Content-Type": "application/json"}
    full_prompt = f"{prompt}, 16:9 aspect ratio, cinematic lighting"
    try:
        response = requests.post(IMAGE_API_URL, headers=headers, json={"prompt": full_prompt}, timeout=60)
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"Saved: {filename}")
            return True
    except Exception as e:
        print(f"Error: {e}")
    return False

def main():
    script_path = Path("script.txt")
    if not script_path.exists(): return
    with open(script_path, "r", encoding="utf-8") as f: script_text = f.read()

    scenes = generate_scenes(script_text)
    os.makedirs("output_images", exist_ok=True)

    # Image generation with resume capability
    for scene in scenes:
        for idx in range(2):
            img_path = Path("output_images") / f"scene_{scene['id']}_img_{idx}.png"
            generate_image(scene["image_prompts"][idx], str(img_path))

    # Memory Efficient Video Assembly
    print("Assembling video in chunks for memory efficiency...")
    input_txt = "inputs.txt"
    with open(input_txt, "w") as f:
        for scene in scenes:
            for idx in range(2):
                img_path = Path("output_images") / f"scene_{scene['id']}_img_{idx}.png"
                if img_path.exists():
                    f.write(f"file '{img_path.absolute()}'\nduration 2.5\n")
    
    # Final assembly using concat demuxer (much lighter on memory)
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", input_txt,
        "-i", "assets/script.mp3",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "25",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "final_video.mp4"
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True)
        print("Success: final_video.mp4 generated.")
    except Exception as e:
        print(f"Failed: {e}")

    # Metadata
    metadata = {
        "title": f"MYSTERY: {script_text[:40].upper()}...",
        "description": f"{script_text[:300]}... #Mystery #USMystrious",
        "tags": ["Mystery", "U.S. Mystrious"]
    }
    with open("video_metadata.json", "w") as f: json.dump(metadata, f)

if __name__ == "__main__":
    main()
