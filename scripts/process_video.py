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
    print("AI Director is planning granular scenes (2-3 seconds each)...")
    words = script_text.split()
    scenes = []
    # Very small chunks for fast-paced professional editing
    chunk_size = 15 # words per visual
    
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        
        # Default: Search for specific visual context
        scene_type = "image"
        
        # Fallback to character if text is generic or highly intense
        intense_words = ["i", "me", "my", "we", "listen", "look", "behold", "warning", "mystery"]
        if any(word in chunk.lower() for word in intense_words) or len(chunk) < 20:
            scene_type = "character_full"
            
        scenes.append({
            "id": len(scenes) + 1,
            "text": chunk,
            "type": scene_type,
            "duration": 3.0, # Fast pacing: 3 seconds per visual
            "prompt": f"Professional cinematic visual for: {chunk[:100]}, 16:9 widescreen, 4k"
        })
    return scenes

def generate_image(prompt, filename):
    if Path(filename).exists(): return True
    headers = {"Authorization": f"Bearer {IMAGE_API_KEY}", "Content-Type": "application/json"}
    try:
        response = requests.post(IMAGE_API_URL, headers=headers, json={"prompt": prompt}, timeout=60)
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

    input_args = []
    if char_path.exists():
        input_args.extend(["-stream_loop", "-1", "-i", str(char_path)]) # [0:v]
    input_args.extend(["-i", str(audio_path)]) # [1:a]

    filter_complex = []
    v_streams = []
    start_idx = 2
    
    for i, scene in enumerate(scenes):
        if scene["type"] == "image":
            img_path = Path("output_images") / f"scene_{scene['id']}.png"
            if generate_image(scene["prompt"], str(img_path)):
                input_args.extend(["-loop", "1", "-t", "3", "-i", str(img_path)])
                idx = start_idx + len(v_streams)
                filter_complex.append(f"[{idx}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='min(zoom+0.001,1.3)':d=75:s=1920x1080[v{i}img];")
                # Add corner character
                filter_complex.append(f"[0:v]scale=400:-1[char_c{i}];[v{i}img][char_c{i}]overlay=W-w-20:y=H-h-20[v{i}final];")
                v_streams.append(f"[v{i}final]")
            else:
                # Fallback to character if image fails
                scene["type"] = "character_full"

        if scene["type"] == "character_full":
            # Just use character video for 3 seconds
            # We create a virtual "image" stream from character video to keep concat logic simple
            filter_complex.append(f"[0:v]trim=duration=3,scale=1920:1080,setsar=1[v{i}final];")
            v_streams.append(f"[v{i}final]")

    # Final Concat
    filter_complex.append(f"{''.join(v_streams)}concat=n={len(v_streams)}:v=1:a=0[vout]")
    
    cmd = [
        "ffmpeg", "-y", *input_args,
        "-filter_complex", "".join(filter_complex),
        "-map", "[vout]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "final_video.mp4"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Success: Fast-paced professional video generated.")
    except Exception as e:
        print(f"FFmpeg Failed: {e}")

if __name__ == "__main__":
    main()
