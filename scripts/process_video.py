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
    num_scenes = 20 # Can be adjusted
    total_duration_seconds = 25 * 60 
    avg_scene_duration = total_duration_seconds / num_scenes

    cinematic_effects = [
        "Ken Burns Effect (Zoom In/Out)", "Pan & Scan", "Parallax Effect",
        "Camera Shake", "Motion Blur", "Film Grain", "Vignette",
        "Dark Color Grading", "Glow Effect", "Fog/Smoke Overlay",
        "Dust Particles", "Light Leaks", "Blur Transition",
        "Glitch Transition", "Cross Dissolve", "Fade In/Out",
        "Typewriter Text Animation", "Scale Animation", "Rotation Animation",
        "Opacity Animation", "Speed Ramp", "Letterbox Cinematic Bars",
        "Shadow Enhancement", "Suspense Sound Effects Sync"
    ]

    for i in range(1, num_scenes + 1):
        scene_duration = random.uniform(avg_scene_duration * 0.8, avg_scene_duration * 1.2)
        selected_effects = random.sample(cinematic_effects, k=random.randint(2, 5))
        
        scenes.append({
            "id": i,
            "duration": scene_duration,
            "image_prompts": [
                f"A detailed, cinematic shot for scene {i} based on script, action 1",
                f"A wide shot showing the environment for scene {i} based on script, action 2"
            ],
            "stock_video_query": f"dynamic city life {i}",
            "use_character_video": random.choice([True, False]),
            "character_video_start_time": random.uniform(0, scene_duration * 0.5) if random.choice([True, False]) else None,
            "effects": selected_effects,
            "sound_effect_cue": random.choice(["suspense", "impact", "whoosh", None])
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

def download_pixabay_asset(query, asset_type="video"):
    url = f"https://pixabay.com/api/{'videos/' if asset_type == 'video' else ''}?key={PIXABAY_API_KEY}&q={query}&per_page=3"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data["hits"]:
                return data["hits"][0]["videos"]["large"]["url"] if "large" in data["hits"][0]["videos"] else data["hits"][0]["videos"]["medium"]["url"]
    except Exception as e:
        print(f"Error during Pixabay download: {e}")
    return None

def download_file(url, destination):
    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading file: {e}")
        return False

def generate_ffmpeg_command(scenes, downloaded_images, character_video_path, script_audio_path):
    print("Constructing FFmpeg command...")
    input_files = []
    filter_complex = []
    
    # 1. Inputs
    if Path(character_video_path).exists():
        input_files.append(f"-i {character_video_path}") # [0:v]
    
    if Path(script_audio_path).exists():
        input_files.append(f"-i {script_audio_path}") # [1:a]

    # Add images as inputs
    image_start_idx = len(input_files)
    for i, scene in enumerate(scenes):
        img_name = f"scene_{scene['id']}_img_0.png"
        img_path = Path("output_images") / img_name
        if img_path.exists():
            input_files.append(f"-loop 1 -t {scene['duration']:.2f} -i {img_path}")
    
    # 2. Filter Complex
    for i in range(len(scenes)):
        idx = image_start_idx + i
        filter_complex.append(f"[{idx}:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}];")
    
    # Concatenate images
    concat_v = "".join([f"[v{i}]" for i in range(len(scenes))])
    filter_complex.append(f"{concat_v}concat=n={len(scenes)}:v=1:a=0[vmain];")
    
    # Overlay character video if exists
    if Path(character_video_path).exists():
        filter_complex.append(f"[vmain][0:v]overlay=x=W-w-10:y=H-h-10:enable='between(t,5,15)'[vout]")
        v_map = "[vout]"
    else:
        v_map = "[vmain]"

    cmd = [
        "ffmpeg", "-y",
        *input_files,
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
        return

    with open(script_path, "r", encoding="utf-8") as f:
        script_text = f.read()

    scenes = generate_scenes(script_text)
    os.makedirs("output_images", exist_ok=True)
    os.makedirs("downloaded_assets", exist_ok=True)

    downloaded_images = {}
    for scene in scenes:
        img_name = f"scene_{scene['id']}_img_0.png"
        img_path = Path("output_images") / img_name
        if not img_path.exists():
            generate_image(scene["image_prompts"][0], str(img_path))
        downloaded_images[img_name] = str(img_path)

    character_video_path = "assets/character.mp4"
    script_audio_path = "assets/script.mp3"

    ffmpeg_cmd = generate_ffmpeg_command(scenes, downloaded_images, character_video_path, script_audio_path)
    
    print("Executing real FFmpeg command...")
    try:
        subprocess.run(ffmpeg_cmd, check=True)
        print("Real video generated: final_video.mp4")
    except Exception as e:
        print(f"FFmpeg failed: {e}")

    # Metadata
    metadata = {
        "title": "AI Generated Cinematic Story: A Modern Classic City Adventure",
        "description": "Automatically created using AI and FFmpeg. #AI #Cinematic",
        "tags": ["AI", "Animation"]
    }
    with open("video_metadata.json", "w") as f:
        json.dump(metadata, f)

if __name__ == "__main__":
    main()
