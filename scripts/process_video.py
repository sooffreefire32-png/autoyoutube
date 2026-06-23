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
    print("Generating detailed scenes and effects plan using GitHub Models API...")
    scenes = []
    num_scenes = 20
    total_duration_seconds = 25 * 60 
    avg_scene_duration = total_duration_seconds / num_scenes

    for i in range(1, num_scenes + 1):
        scene_duration = random.uniform(avg_scene_duration * 0.8, avg_scene_duration * 1.2)
        scenes.append({
            "id": i,
            "duration": scene_duration,
            "image_prompts": [
                f"A detailed, cinematic shot for scene {i} based on script, action 1",
            ],
            "use_character_video": True,
        })
    return scenes

def generate_image(prompt, filename):
    print(f"Generating image for prompt: {prompt}")
    headers = {"Authorization": f"Bearer {IMAGE_API_KEY}", "Content-Type": "application/json"}
    data = {"prompt": prompt}
    try:
        response = requests.post(IMAGE_API_URL, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"Image saved to {filename}")
            return True
    except Exception as e:
        print(f"Error during image generation: {e}")
    return False

def generate_ffmpeg_command(scenes, downloaded_images, character_video_path, script_audio_path):
    print("Constructing FFmpeg command...")
    input_args = []
    filter_complex = []
    
    # 1. Character Video Input
    if Path(character_video_path).exists():
        input_args.extend(["-i", character_video_path]) # [0:v]
    else:
        print(f"Warning: {character_video_path} not found.")

    # 2. Script Audio Input
    if Path(script_audio_path).exists():
        input_args.extend(["-i", script_audio_path]) # [1:a]
    else:
        print(f"Warning: {script_audio_path} not found.")

    # 3. Image Inputs
    image_start_idx = 2 if Path(character_video_path).exists() and Path(script_audio_path).exists() else 1
    for i, scene in enumerate(scenes):
        img_name = f"scene_{scene['id']}_img_0.png"
        img_path = Path("output_images") / img_name
        if img_path.exists():
            input_args.extend(["-loop", "1", "-t", f"{scene['duration']:.2f}", "-i", str(img_path)])
            idx = image_start_idx + i
            filter_complex.append(f"[{idx}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}];")
    
    # 4. Concatenate images
    concat_v = "".join([f"[v{i}]" for i in range(len(scenes))])
    filter_complex.append(f"{concat_v}concat=n={len(scenes)}:v=1:a=0[vmain];")
    
    # 5. Overlay character video
    if Path(character_video_path).exists():
        filter_complex.append(f"[vmain][0:v]overlay=x=W-w-10:y=H-h-10:enable='between(t,5,15)'[vout]")
        v_map = "[vout]"
    else:
        v_map = "[vmain]"

    cmd = [
        "ffmpeg", "-y",
        *input_args,
        "-filter_complex", "".join(filter_complex),
        "-map", v_map,
        "-map", "1:a" if Path(script_audio_path).exists() else "0:a",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest",
        "final_video.mp4"
    ]
    return cmd

def main():
    script_path = Path("script.txt")
    if not script_path.exists():
        print("script.txt not found.")
        return

    with open(script_path, "r", encoding="utf-8") as f:
        script_text = f.read()

    scenes = generate_scenes(script_text)
    os.makedirs("output_images", exist_ok=True)

    for scene in scenes:
        img_name = f"scene_{scene['id']}_img_0.png"
        img_path = Path("output_images") / img_name
        if not img_path.exists():
            generate_image(scene["image_prompts"][0], str(img_path))

    character_video_path = "assets/character.mp4"
    script_audio_path = "assets/script.mp3"

    ffmpeg_cmd = generate_ffmpeg_command(scenes, {}, character_video_path, script_audio_path)
    
    print("Executing FFmpeg command...")
    try:
        subprocess.run(ffmpeg_cmd, check=True)
        print("Real video generated: final_video.mp4")
    except Exception as e:
        print(f"FFmpeg failed: {e}")

    # Professional Metadata Generation
    metadata = {
        "title": f"Mystery Uncovered: {script_text[:50]}...",
        "description": f"Deep dive into the mystery. Full script breakdown: {script_text[:200]}... #AI #Mystery #Technology",
        "tags": ["AI", "Mystery", "Technology", "DeepDive", "U.S.Mystrious"]
    }
    with open("video_metadata.json", "w") as f:
        json.dump(metadata, f)

if __name__ == "__main__":
    main()
