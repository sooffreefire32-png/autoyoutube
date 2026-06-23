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
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")

def generate_scenes(script_text):
    print("Generating 100+ professional scenes with cinematic prompts...")
    scenes = []
    # Aiming for 120 scenes for a ~10 min video (5 sec per scene)
    num_scenes = 120 
    scene_duration = 5.0 # Fixed 5 seconds for fast pacing

    for i in range(1, num_scenes + 1):
        scenes.append({
            "id": i,
            "duration": scene_duration,
            "image_prompts": [
                f"Cinematic 16:9 wide shot, 2D anime style, high detail, scene {i} of mystery story: {script_text[:50]}",
                f"Dramatic close-up 16:9, hand-drawn style, vibrant colors, scene {i} action"
            ],
            "use_character_full_screen": (i == 1 or i % 10 == 0) # Full screen at start and every 10th scene
        })
    return scenes

def generate_image(prompt, filename):
    print(f"Generating 16:9 Image: {prompt}")
    headers = {"Authorization": f"Bearer {IMAGE_API_KEY}", "Content-Type": "application/json"}
    # Adding aspect ratio instruction to prompt
    full_prompt = f"{prompt}, 16:9 aspect ratio, cinematic lighting, ultra-wide"
    data = {"prompt": full_prompt}
    try:
        response = requests.post(IMAGE_API_URL, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"Error: {e}")
    return False

def generate_ffmpeg_command(scenes, character_video_path, script_audio_path):
    print("Building Professional FFmpeg Filter Chain...")
    input_args = []
    filter_complex = []
    
    # Inputs
    if Path(character_video_path).exists():
        # -stream_loop -1 ensures the 5s video loops continuously for the entire video duration
        input_args.extend(["-stream_loop", "-1", "-i", character_video_path]) # [0:v]
    if Path(script_audio_path).exists():
        input_args.extend(["-i", script_audio_path]) # [1:a]

    image_start_idx = 2
    v_streams = []

    for i, scene in enumerate(scenes):
        img1 = Path("output_images") / f"scene_{scene['id']}_img_0.png"
        img2 = Path("output_images") / f"scene_{scene['id']}_img_1.png"
        
        if img1.exists() and img2.exists():
            # Add 2 images per scene (2.5 sec each)
            input_args.extend(["-loop", "1", "-t", "2.5", "-i", str(img1)])
            input_args.extend(["-loop", "1", "-t", "2.5", "-i", str(img2)])
            
            idx1 = image_start_idx + (i * 2)
            idx2 = image_start_idx + (i * 2) + 1
            
            # Apply Ken Burns to images
            filter_complex.append(f"[{idx1}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,zoompan=z='min(zoom+0.001,1.3)':d=75:s=1920x1080[v{i}a];")
            filter_complex.append(f"[{idx2}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,zoompan=z='min(zoom+0.001,1.3)':d=75:s=1920x1080[v{i}b];")
            v_streams.extend([f"[v{i}a]", f"[v{i}b]"])

    # Concatenate all images
    concat_v = "".join(v_streams)
    filter_complex.append(f"{concat_v}concat=n={len(v_streams)}:v=1:a=0[vmain];")
    
    # Advanced Overlay: Character Video at Start and Intervals
    if Path(character_video_path).exists():
        # Overlay at start (0-5s) and every 50s for 5s
        overlay_logic = "overlay=x=0:y=0:enable='between(t,0,5)+between(t,50,55)+between(t,100,105)'"
        filter_complex.append(f"[vmain][0:v]scale=1920:1080,{overlay_logic}[vout]")
        v_map = "[vout]"
    else:
        v_map = "[vmain]"

    cmd = [
        "ffmpeg", "-y", *input_args,
        "-filter_complex", "".join(filter_complex),
        "-map", v_map, "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "final_video.mp4"
    ]
    return cmd

def main():
    script_path = Path("script.txt")
    if not script_path.exists(): return
    with open(script_path, "r", encoding="utf-8") as f: script_text = f.read()

    scenes = generate_scenes(script_text)
    os.makedirs("output_images", exist_ok=True)

    for scene in scenes:
        for idx in range(2):
            img_path = Path("output_images") / f"scene_{scene['id']}_img_{idx}.png"
            if not img_path.exists():
                generate_image(scene["image_prompts"][idx], str(img_path))

    ffmpeg_cmd = generate_ffmpeg_command(scenes, "assets/character.mp4", "assets/script.mp3")
    try:
        subprocess.run(ffmpeg_cmd, check=True)
    except Exception as e:
        print(f"Error: {e}")

    # Professional Mysterious Metadata
    metadata = {
        "title": f"THE TRUTH REVEALED: {script_text[:40].upper()}... (U.S. MYSTRIOUS)",
        "description": f"Warning: This video contains information they don't want you to know. \n\n{script_text[:300]}...\n\n#Mystery #TheTruth #USMystrious #TopSecret",
        "tags": ["Mystery", "Documentary", "U.S. Mystrious", "Secret", "Conspiracy", "Truth"]
    }
    with open("video_metadata.json", "w") as f: json.dump(metadata, f)

if __name__ == "__main__":
    main()
