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
    
    if prompts_path.exists():
        with open(prompts_path, "r", encoding="utf-8") as f:
            prompts = [line.strip() for line in f.readlines() if line.strip()]
    elif script_path.exists():
        with open(script_path, "r", encoding="utf-8") as f:
            script_text = f.read()
        prompts = [f"Cinematic mystery scene: {script_text[:100]}"] * 50
    else:
        return
    
    total_duration = get_audio_duration(str(audio_path))
    scene_duration = total_duration / len(prompts)
    os.makedirs("output_images", exist_ok=True)

    for i, prompt in enumerate(prompts):
        img_path = Path("output_images") / f"prompt_scene_{i+1}.png"
        generate_image(prompt, str(img_path))

    # To avoid "Expressions with frame variables are not valid in init eval_mode" error,
    # we use a more robust way to handle scaling and overlay.
    
    filter_complex = []
    input_args = []
    
    if char_path.exists():
        input_args.extend(["-stream_loop", "-1", "-i", str(char_path)]) # [0:v]
    input_args.extend(["-i", str(audio_path)]) # [1:a]

    image_streams = []
    start_idx = 2
    for i in range(len(prompts)):
        img_path = Path("output_images") / f"prompt_scene_{i+1}.png"
        if img_path.exists():
            input_args.extend(["-loop", "1", "-t", str(scene_duration), "-i", str(img_path)])
            idx = start_idx + i
            # Basic Ken Burns without dynamic scale in filter_complex to avoid errors
            filter_complex.append(f"[{idx}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='min(zoom+0.001,1.3)':d=125:s=1920x1080[v{i}];")
            image_streams.append(f"[v{i}]")

    # Concat images
    filter_complex.append(f"{''.join(image_streams)}concat=n={len(image_streams)}:v=1:a=0[vmain];")
    
    # Character Animation: Full screen (0-5s), then shrink to corner
    if char_path.exists():
        # Using a safer approach for dynamic scaling
        filter_complex.append(
            f"[0:v]scale=1920:1080[char_full];"
            f"[0:v]scale=450:-1[char_small];"
            f"[vmain][char_full]overlay=x=0:y=0:enable='between(t,0,5)'[vtemp];"
            f"[vtemp][char_small]overlay=x=W-w-30:y=H-h-30:enable='gt(t,5)'[vfinal];"
        )
        v_map = "[vfinal]"
    else:
        v_map = "[vmain]"

    cmd = [
        "ffmpeg", "-y", *input_args,
        "-filter_complex", "".join(filter_complex),
        "-map", v_map, "-map", "1:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "final_video.mp4"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Success: Professional video generated.")
    except Exception as e:
        print(f"FFmpeg Failed: {e}")

    # Metadata
    metadata = {
        "title": "THE MYSTERY UNFOLDS: (U.S. MYSTRIOUS)",
        "description": "Professional cinematic experience. #Mystery #USMystrious",
        "tags": ["Mystery", "U.S. Mystrious"]
    }
    with open("video_metadata.json", "w") as f: json.dump(metadata, f)

if __name__ == "__main__":
    main()
