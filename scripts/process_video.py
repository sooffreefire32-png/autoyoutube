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
    full_prompt = f"{prompt}, 16:9 aspect ratio, 4k, cinematic, high quality"
    try:
        response = requests.post(IMAGE_API_URL, headers=headers, json={"prompt": full_prompt}, timeout=60)
        if response.status_code == 200:
            with open(filename, "wb") as f: f.write(response.content)
            return True
    except: return False
    return False

def main():
    prompts_path = Path("prompts.txt")
    script_path = Path("script.txt")
    audio_path = Path("assets/script.mp3")
    char_path = Path("assets/character.mp4")
    
    # Use prompts.txt if exists, otherwise fallback to script.txt
    if prompts_path.exists():
        with open(prompts_path, "r", encoding="utf-8") as f:
            prompts = [line.strip() for line in f.readlines() if line.strip()]
        print(f"Loaded {len(prompts)} prompts from prompts.txt")
    elif script_path.exists():
        with open(script_path, "r", encoding="utf-8") as f:
            script_text = f.read()
        # Simple split for fallback
        prompts = [f"Cinematic mystery scene: {script_text[:100]}"] * 20
    else:
        print("No prompts.txt or script.txt found.")
        return
    
    total_duration = get_audio_duration(str(audio_path))
    scene_duration = total_duration / len(prompts)
    os.makedirs("output_images", exist_ok=True)

    # Generate images from user prompts
    for i, prompt in enumerate(prompts):
        img_path = Path("output_images") / f"prompt_scene_{i+1}.png"
        generate_image(prompt, str(img_path))

    filter_complex = []
    input_args = []
    
    # 1. Character Video [0:v]
    if char_path.exists():
        input_args.extend(["-stream_loop", "-1", "-i", str(char_path)])
    
    # 2. Audio [1:a]
    input_args.extend(["-i", str(audio_path)])

    # 3. Image Inputs
    image_streams = []
    start_idx = 2
    for i in range(len(prompts)):
        img_path = Path("output_images") / f"prompt_scene_{i+1}.png"
        if img_path.exists():
            input_args.extend(["-loop", "1", "-t", str(scene_duration), "-i", str(img_path)])
            idx = start_idx + i
            # Cinematic Zoom/Pan
            filter_complex.append(f"[{idx}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='min(zoom+0.001,1.3)':d={int(scene_duration*25)}:s=1920x1080[v{i}];")
            image_streams.append(f"[v{i}]")

    # Concatenate images
    filter_complex.append(f"{''.join(image_streams)}concat=n={len(image_streams)}:v=1:a=0[vmain];")
    
    # Keyframe Animation for Character Video
    if char_path.exists():
        filter_complex.append(
            f"[0:v]scale='if(lt(t,5),1920,if(lt(t,7),1920-(t-5)*(1920-450)/2,450))':-1[char];"
            f"[vmain][char]overlay='if(lt(t,5),0,if(lt(t,7),(t-5)*(W-w-30)/2,W-w-30))':'if(lt(t,5),0,if(lt(t,7),(t-5)*(H-h-30)/2,H-h-30))'[vfinal];"
        )
        v_map = "[vfinal]"
    else:
        v_map = "[vmain]"

    cmd = [
        "ffmpeg", "-y", *input_args,
        "-filter_complex", "".join(filter_complex),
        "-map", v_map, "-map", "1:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "final_video.mp4"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Success: Prompt-based professional video generated.")
    except Exception as e:
        print(f"FFmpeg Failed: {e}")

    # Metadata
    metadata = {
        "title": "EXCLUSIVE MYSTERY REVEALED (U.S. MYSTRIOUS)",
        "description": "Custom prompt-driven cinematic experience. #Mystery #Documentary #USMystrious",
        "tags": ["Mystery", "U.S. Mystrious", "Documentary"]
    }
    with open("video_metadata.json", "w") as f: json.dump(metadata, f)

if __name__ == "__main__":
    main()
