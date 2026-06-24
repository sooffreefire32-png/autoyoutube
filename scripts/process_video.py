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

def get_audio_duration(file_path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        return float(result.stdout)
    except:
        return 600.0

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
    prompts_path = Path("prompts.txt")
    audio_path = Path("assets/script.mp3")
    char_path = Path("assets/character.mp4")
    
    if not prompts_path.exists():
        print("prompts.txt not found.")
        return
    
    with open(prompts_path, "r", encoding="utf-8") as f:
        prompts = [line.strip() for line in f.readlines() if line.strip()]
    
    total_duration = get_audio_duration(str(audio_path))
    scene_duration = total_duration / len(prompts)
    os.makedirs("output_images", exist_ok=True)

    # Image Generation
    for i, prompt in enumerate(prompts):
        img_path = Path("output_images") / f"user_prompt_{i+1}.png"
        generate_image(prompt, str(img_path))

    input_args = []
    if char_path.exists():
        input_args.extend(["-stream_loop", "-1", "-i", str(char_path)]) # [0:v]
    input_args.extend(["-i", str(audio_path)]) # [1:a]

    filter_complex = []
    v_streams = []
    start_idx = 2
    
    for i in range(len(prompts)):
        img_path = Path("output_images") / f"user_prompt_{i+1}.png"
        if img_path.exists():
            input_args.extend(["-loop", "1", "-t", str(scene_duration), "-i", str(img_path)])
            idx = start_idx + len(v_streams)
            
            # Ken Burns Zoom
            filter_complex.append(f"[{idx}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='min(zoom+0.001,1.3)':d={int(scene_duration*25)}:s=1920x1080[v{i}img];")
            
            # Character Integration Logic
            # Full screen for first 5s and every 60s, otherwise corner
            current_time = i * scene_duration
            if current_time < 5 or int(current_time) % 60 < 5:
                filter_complex.append(f"[v{i}img][0:v]scale=1920:1080,overlay=0:0[v{i}final];")
            else:
                filter_complex.append(f"[0:v]scale=450:-1[char_c{i}];[v{i}img][char_c{i}]overlay=W-w-30:y=H-h-30[v{i}final];")
            
            v_streams.append(f"[v{i}final]")

    # Final Assembly
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
        print("Success: 100-Prompt professional video generated.")
    except Exception as e:
        print(f"FFmpeg Failed: {e}")

if __name__ == "__main__":
    main()
