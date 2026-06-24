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

def ai_director_plan(script_text):
    print("AI Director (GH Models) is analyzing the script for intense moments...")
    # Using GitHub Models to decide scene types
    # Since we can't call the actual GH API here easily without setup, 
    # we simulate the logic: Detect keywords like "mystery", "shocking", "truth", "chapter"
    
    words = script_text.split()
    scenes = []
    chunk_size = 30 # words per scene
    
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        scene_type = "image"
        effect = "zoom"
        
        # AI Logic Simulation: Intense words trigger full screen character
        intense_words = ["mystery", "secret", "shocking", "unbelievable", "truth", "chapter", "warning"]
        if any(word in chunk.lower() for word in intense_words):
            scene_type = "character_full"
            effect = "shake"
        
        scenes.append({
            "id": len(scenes) + 1,
            "text": chunk,
            "type": scene_type,
            "effect": effect,
            "prompt": f"Cinematic mystery scene, 16:9, realistic documentary style: {chunk[:100]}"
        })
    return scenes

def generate_image(prompt, filename):
    if Path(filename).exists(): return True
    headers = {"Authorization": f"Bearer {IMAGE_API_KEY}", "Content-Type": "application/json"}
    full_prompt = f"{prompt}, 16:9 aspect ratio, 4k, cinematic"
    try:
        response = requests.post(IMAGE_API_URL, headers=headers, json={"prompt": full_prompt}, timeout=60)
        if response.status_code == 200:
            with open(filename, "wb") as f: f.write(response.content)
            return True
    except: return False
    return False

def main():
    script_path = Path("script.txt")
    audio_path = Path("assets/script.mp3")
    char_path = Path("assets/character.mp4")
    
    if not script_path.exists(): return
    with open(script_path, "r", encoding="utf-8") as f: script_text = f.read()
    
    scenes = ai_director_plan(script_text)
    os.makedirs("output_images", exist_ok=True)

    # 1. Inputs
    input_args = []
    if char_path.exists():
        input_args.extend(["-stream_loop", "-1", "-i", str(char_path)]) # [0:v]
    input_args.extend(["-i", str(audio_path)]) # [1:a]

    # 2. Scene Processing
    filter_complex = []
    v_streams = []
    start_idx = 2
    
    for i, scene in enumerate(scenes):
        img_path = Path("output_images") / f"scene_{scene['id']}.png"
        generate_image(scene["prompt"], str(img_path))
        
        if img_path.exists():
            input_args.extend(["-loop", "1", "-t", "5", "-i", str(img_path)])
            idx = start_idx + i
            
            # Apply AI-decided effect
            if scene["effect"] == "shake":
                effect_str = "zoompan=z='min(zoom+0.001,1.3)':d=125:x='if(eq(mod(n,2),0),10,-10)':y='if(eq(mod(n,2),0),10,-10)':s=1920x1080"
            else:
                effect_str = "zoompan=z='min(zoom+0.001,1.3)':d=125:s=1920x1080"
            
            filter_complex.append(f"[{idx}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,{effect_str}[v{i}];")
            
            # AI Director: Decide if Character should be Full Screen or Corner
            if scene["type"] == "character_full":
                filter_complex.append(f"[v{i}][0:v]scale=1920:1080,overlay=0:0[v{i}final];")
            else:
                filter_complex.append(f"[0:v]scale=450:-1[char_s{i}];[v{i}][char_s{i}]overlay=W-w-30:y=H-h-30[v{i}final];")
            
            v_streams.append(f"[v{i}final]")

    # 3. Final Assembly
    filter_complex.append(f"{''.join(v_streams)}concat=n={len(v_streams)}:v=1:a=0[vout]")
    
    cmd = [
        "ffmpeg", "-y", *input_args,
        "-filter_complex", "".join(filter_complex),
        "-map", "[vout]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "25",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "final_video.mp4"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Success: AI-Directed professional video generated.")
    except Exception as e:
        print(f"FFmpeg Failed: {e}")

    # Metadata
    metadata = {
        "title": "AI DIRECTED MYSTERY: (U.S. MYSTRIOUS)",
        "description": "Edited by AI Director. #Mystery #USMystrious",
        "tags": ["Mystery", "U.S. Mystrious"]
    }
    with open("video_metadata.json", "w") as f: json.dump(metadata, f)

if __name__ == "__main__":
    main()
