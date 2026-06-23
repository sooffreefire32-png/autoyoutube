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

def generate_scenes(script_text, total_duration):
    # Split script into meaningful chunks based on scene duration
    scene_duration = 5.0
    num_scenes = int(total_duration / scene_duration)
    words = script_text.split()
    words_per_scene = max(1, len(words) // num_scenes)
    
    scenes = []
    for i in range(num_scenes):
        start_idx = i * words_per_scene
        end_idx = (i + 1) * words_per_scene
        scene_script = " ".join(words[start_idx:end_idx])
        
        scenes.append({
            "id": i + 1,
            "duration": scene_duration,
            "prompts": [
                f"Cinematic 16:9 widescreen, mystery atmosphere, scene showing: {scene_script[:150]}",
                f"Dramatic 16:9 ultra-wide, mystery action detail: {scene_script[:150]}"
            ]
        })
    return scenes

def generate_image(prompt, filename):
    if Path(filename).exists(): return True
    headers = {"Authorization": f"Bearer {IMAGE_API_KEY}", "Content-Type": "application/json"}
    # Forcing 16:9 and High Quality in the prompt
    full_prompt = f"{prompt}, 16:9 aspect ratio, cinematic widescreen, 4k, ultra-detailed, professional documentary style"
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
    
    total_duration = get_audio_duration(str(audio_path))
    scenes = generate_scenes(script_text, total_duration)
    os.makedirs("output_images", exist_ok=True)

    # Smart Image Generation (Mapping script to scenes)
    for scene in scenes:
        for idx in range(2):
            img_path = Path("output_images") / f"scene_{scene['id']}_img_{idx}.png"
            generate_image(scene["prompts"][idx], str(img_path))

    # Constructing Professional FFmpeg Filter Chain
    filter_complex = []
    input_args = []
    
    if char_path.exists():
        input_args.extend(["-stream_loop", "-1", "-i", str(char_path)]) # [0:v]
    
    input_args.extend(["-i", str(audio_path)]) # [1:a]

    image_streams = []
    start_idx = 2
    for i, scene in enumerate(scenes):
        img1 = Path("output_images") / f"scene_{scene['id']}_img_0.png"
        img2 = Path("output_images") / f"scene_{scene['id']}_img_1.png"
        
        if img1.exists() and img2.exists():
            input_args.extend(["-loop", "1", "-t", "2.5", "-i", str(img1)])
            input_args.extend(["-loop", "1", "-t", "2.5", "-i", str(img2)])
            
            idx1 = start_idx + (i * 2)
            idx2 = start_idx + (i * 2) + 1
            
            # Forced 16:9 Scaling + Ken Burns
            filter_complex.append(f"[{idx1}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='min(zoom+0.001,1.3)':d=75:s=1920x1080[v{i}a];")
            filter_complex.append(f"[{idx2}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='min(zoom+0.001,1.3)':d=75:s=1920x1080[v{i}b];")
            image_streams.extend([f"[v{i}a]", f"[v{i}b]"])

    # Concatenate and Overlay
    filter_complex.append(f"{''.join(image_streams)}concat=n={len(image_streams)}:v=1:a=0[vmain];")
    filter_complex.append(f"[0:v]scale=450:-1[char];[vmain][char]overlay=W-w-30:H-h-30[vfinal];")
    
    cmd = [
        "ffmpeg", "-y", *input_args,
        "-filter_complex", "".join(filter_complex),
        "-map", "[vfinal]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "final_video.mp4"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Success: Professional 16:9 Script-Synced video generated.")
    except Exception as e:
        print(f"FFmpeg Failed: {e}")

    # Metadata
    metadata = {
        "title": f"MYSTERY UNVEILED: {script_text[:40].upper()}... (U.S. MYSTRIOUS)",
        "description": f"{script_text[:400]}... \n\n#Mystery #Documentary #USMystrious",
        "tags": ["Mystery", "U.S. Mystrious", "Documentary", "The Truth"]
    }
    with open("video_metadata.json", "w") as f: json.dump(metadata, f)

if __name__ == "__main__":
    main()
