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
        return 600.0 # Default to 10 mins if check fails

def generate_scenes(script_text, total_duration):
    print(f"Generating professional scenes for {total_duration}s duration...")
    # Each scene is 5 seconds, 2 images per scene (2.5s each)
    scene_duration = 5.0
    num_scenes = int(total_duration / scene_duration)
    scenes = []
    
    for i in range(1, num_scenes + 1):
        scenes.append({
            "id": i,
            "duration": scene_duration,
            "prompts": [
                f"Cinematic 16:9, mystery atmosphere, scene {i}: {script_text[:60]}",
                f"Dramatic 16:9, close-up detail, mystery action {i}"
            ]
        })
    return scenes

def generate_image(prompt, filename):
    if Path(filename).exists(): return True
    headers = {"Authorization": f"Bearer {IMAGE_API_KEY}", "Content-Type": "application/json"}
    full_prompt = f"{prompt}, 16:9 aspect ratio, high quality, cinematic lighting"
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

    # Image generation (Resume-able)
    for scene in scenes:
        for idx in range(2):
            img_path = Path("output_images") / f"scene_{scene['id']}_img_{idx}.png"
            generate_image(scene["prompts"][idx], str(img_path))

    # Constructing Professional FFmpeg Filter Chain
    # This chain includes: Ken Burns, Looping Character, and Captions
    filter_complex = []
    input_args = []
    
    # 1. Looping Character Input [0:v]
    if char_path.exists():
        input_args.extend(["-stream_loop", "-1", "-i", str(char_path)])
    
    # 2. Audio Input [1:a]
    input_args.extend(["-i", str(audio_path)])

    # 3. Image Inputs and Filters
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
            
            # Ken Burns Zoom Effect
            filter_complex.append(f"[{idx1}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,zoompan=z='min(zoom+0.001,1.3)':d=75:s=1920x1080[v{i}a];")
            filter_complex.append(f"[{idx2}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,zoompan=z='min(zoom+0.001,1.3)':d=75:s=1920x1080[v{i}b];")
            image_streams.extend([f"[v{i}a]", f"[v{i}b]"])

    # Concatenate images
    filter_complex.append(f"{''.join(image_streams)}concat=n={len(image_streams)}:v=1:a=0[vmain];")
    
    # Overlay Looping Character [0:v] on [vmain]
    # Character will be placed at bottom-right, scaled to 400px width
    filter_complex.append(f"[0:v]scale=400:-1[char];[vmain][char]overlay=W-w-20:H-h-20[vfinal];")
    
    # Add Captions (Simple Drawtext - Needs to be broken down by scene timing)
    # For now, let's focus on the main visual and character sync
    
    cmd = [
        "ffmpeg", "-y", *input_args,
        "-filter_complex", "".join(filter_complex),
        "-map", "[vfinal]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "24",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", "final_video.mp4"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Success: Professional video generated.")
    except Exception as e:
        print(f"FFmpeg Failed: {e}")

    # Metadata
    metadata = {
        "title": f"UNSOLVED MYSTERY: {script_text[:40].upper()}... (U.S. MYSTRIOUS)",
        "description": f"The truth is out there. \n\n{script_text[:300]}...\n\n#Mystery #Documentary #USMystrious",
        "tags": ["Mystery", "U.S. Mystrious", "Documentary"]
    }
    with open("video_metadata.json", "w") as f: json.dump(metadata, f)

if __name__ == "__main__":
    main()
