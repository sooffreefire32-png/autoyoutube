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

# --- Helper Functions (from previous version, slightly modified) ---

def generate_scenes(script_text):
    print("Generating detailed scenes and effects plan using GitHub Models API...")
    # This is where the AI (GitHub Models API) would analyze the script_text
    # and the voice timing (if available, e.g., from a pre-processed script.mp3 analysis)
    # to create a detailed scene breakdown, including:
    # - Scene duration
    # - Primary image prompts
    # - Stock video queries
    # - Character.mp4 placement (start/end times, duration)
    # - Specific cinematic effects to apply per scene/transition
    # - Sound effect cues

    # For demonstration, we'll simulate a more detailed scene structure.
    scenes = []
    num_scenes = 20 # Reduced for manageability in this example, but can be 150-200
    total_duration_seconds = 25 * 60 # 25 minutes for example
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
            "duration": scene_duration, # Estimated duration for this scene
            "image_prompts": [
                f"A detailed, cinematic shot for scene {i} based on script, action 1",
                f"A wide shot showing the environment for scene {i} based on script, action 2"
            ],
            "stock_video_query": f"dynamic city life {i}",
            "use_character_video": random.choice([True, False]), # AI decides to use character.mp4
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
        else:
            print(f"Image generation failed for prompt \'{prompt}\'. Status: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error during image generation for prompt \'{prompt}\': {e}")
    return False

def download_pixabay_asset(query, asset_type="video"):
    print(f"Searching Pixabay for {asset_type}: {query}")
    url = f"https://pixabay.com/api/{'videos/' if asset_type == 'video' else ''}?key={PIXABAY_API_KEY}&q={query}&per_page=3"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data["hits"]:
                if asset_type == "video":
                    video_url = data["hits"][0]["videos"]["large"]["url"] if "large" in data["hits"][0]["videos"] else data["hits"][0]["videos"]["medium"]["url"]
                    print(f"Found Pixabay video: {video_url}")
                    return video_url
                # Placeholder for music download logic if Pixabay API supports it differently
                elif asset_type == "music":
                    print("Music download from Pixabay not directly supported in this example. Placeholder.")
                    return None
            else:
                print(f"No {asset_type} found for query: {query}")
        else:
            print(f"Pixabay API error for {asset_type} query \'{query}\'. Status: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error during Pixabay {asset_type} download for query \'{query}\': {e}")
    return None

def download_file(url, destination):
    print(f"Downloading {url} to {destination}")
    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded {destination}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file {url}: {e}")
        return False

def generate_video_metadata(script_text):
    print("Generating video metadata (title, tags, description) using GitHub Models API...")
    headers = {"Authorization": f"Bearer {GH_TOKEN}", "Content-Type": "application/json"}
    prompt = f"Generate a catchy title, relevant tags (10-15), and a compelling description for a YouTube video based on this script: {script_text}"
    
    # Simulate API response
    return {
        "title": "AI Generated Cinematic Story: A Modern Classic City Adventure",
        "description": "This video was automatically created using advanced AI, combining stunning visuals, cinematic effects, and a captivating story. Watch a boy's journey through a modern and classic city with dynamic editing. #AI #CinematicVideo #AutomatedEditing #YouTubeAutomation #KenBurns #GlitchEffect",
        "tags": ["AI", "Animation", "Story", "ModernCity", "ClassicCity", "2DAnime", "HandDrawing", "AutomatedVideo", "YouTube", "Adventure", "Cinematic", "VFX"]
    }

# --- New FFmpeg Command Generation Logic ---

def generate_ffmpeg_command(scenes, downloaded_images, downloaded_stock_videos, character_video_path, script_audio_path, background_music_path):
    print("Constructing complex FFmpeg command...")
    # This function will be the most complex part, dynamically building the FFmpeg command
    # based on the detailed scene plan, available assets, and desired effects.

    # Basic structure: 
    # 1. Input all images, stock videos, character video, audio tracks.
    # 2. Apply effects to individual images/clips (e.g., Ken Burns, color grading).
    # 3. Overlay character video at specific times.
    # 4. Handle transitions between scenes.
    # 5. Mix audio (script audio, background music, sound effects).
    # 6. Add final touches (letterbox, film grain, vignette).

    input_files = []
    filter_complex_parts = []
    output_maps = []
    current_time = 0.0
    
    # Add character video as an input if it exists
    if Path(character_video_path).exists():
        input_files.append(f"-i {character_video_path}")
        # Assume character video is [0:v] and [0:a]
        char_video_stream = "[0:v]"
        char_audio_stream = "[0:a]"
    else:
        char_video_stream = None
        char_audio_stream = None

    # Add script audio as an input if it exists
    if Path(script_audio_path).exists():
        input_files.append(f"-i {script_audio_path}")
        # Assume script audio is [1:a] if char_video is [0:v/a], else [0:a]
        script_audio_stream = f"[{len(input_files) - 1}:a]"
    else:
        script_audio_stream = None

    # Add background music as an input if it exists
    if Path(background_music_path).exists():
        input_files.append(f"-i {background_music_path}")
        # Assume bg music is [X:a]
        bg_music_stream = f"[{len(input_files) - 1}:a]"
    else:
        bg_music_stream = None

    # Prepare image inputs and apply effects
    image_streams = []
    for i, scene in enumerate(scenes):
        # Use the first image for simplicity in this example
        img_path = downloaded_images.get(f"scene_{scene['id']}_img_0.png")
        if img_path and Path(img_path).exists():
            input_files.append(f"-loop 1 -t {scene['duration']:.2f} -i {img_path}")
            img_input_stream = f"[{len(input_files) - 1}:v]"
            
            # Apply Ken Burns or Pan/Scan (simplified)
            if "Ken Burns Effect (Zoom In/Out)" in scene["effects"]:
                filter_complex_parts.append(f"{img_input_stream}zoompan=z='min(zoom+0.0015,1.5)':d=1:s=1920x1080:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',trim=duration={scene['duration']:.2f}[v{i}];")
                image_streams.append(f"[v{i}]")
            elif "Pan & Scan" in scene["effects"]:
                filter_complex_parts.append(f"{img_input_stream}crop=iw/2:ih/2:x='if(eq(mod(n,200),0),random(1)*iw/2,x)':y='if(eq(mod(n,200),0),random(1)*ih/2,y)',trim=duration={scene['duration']:.2f}[v{i}];")
                image_streams.append(f"[v{i}]")
            else:
                # Default: just scale the image
                filter_complex_parts.append(f"{img_input_stream}scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,trim=duration={scene['duration']:.2f}[v{i}];")
                image_streams.append(f"[v{i}]")

    # Concatenate all image streams
    if image_streams:
        concat_filter = "".join(image_streams) + f"concat=n={len(image_streams)}:v=1:a=0[vmain];"
        filter_complex_parts.append(concat_filter)
        main_video_stream = "[vmain]"
    else:
        main_video_stream = None

    # Overlay character video (simplified: just one overlay for now)
    if char_video_stream and main_video_stream and any(s["use_character_video"] for s in scenes):
        # This is a very basic overlay. Real implementation needs precise timing.
        filter_complex_parts.append(f"{main_video_stream}{char_video_stream}overlay=x=W-w-10:y=H-h-10:enable='between(t,5,10)'[vfinal];")
        main_video_stream = "[vfinal]"

    # Mix audio (script audio + background music)
    final_audio_stream = None
    if script_audio_stream and bg_music_stream:
        filter_complex_parts.append(f"{script_audio_stream}{bg_music_stream}amix=inputs=2:duration=longest[amixout];")
        final_audio_stream = "[amixout]"
    elif script_audio_stream:
        final_audio_stream = script_audio_stream
    elif bg_music_stream:
        final_audio_stream = bg_music_stream

    # Final output mapping
    if main_video_stream:
        output_maps.append(f"-map {main_video_stream}")
    if final_audio_stream:
        output_maps.append(f"-map {final_audio_stream}")

    # Add global effects (Film Grain, Vignette, Letterbox) - simplified
    global_filters = []
    if any("Film Grain" in s["effects"] for s in scenes):
        global_filters.append("noise=alls=20:allf=t+u")
    if any("Vignette" in s["effects"] for s in scenes):
        global_filters.append("vignette=angle=PI/4")
    if any("Letterbox Cinematic Bars" in s["effects"] for s in scenes):
        global_filters.append("pad=ih*16/9:ih:(ow-iw)/2:(oh-ih)/2:black") # 16:9 aspect ratio

    if global_filters and main_video_stream:
        # Apply global filters to the main video stream before output
        # This is a simplification; ideally, these would be integrated into the main filter_complex chain
        # For now, we'll just add them as a separate vf argument if possible, or assume they are part of the last filter_complex output
        pass # More complex integration needed here

    ffmpeg_cmd = [
        "ffmpeg",
        "-y", # Overwrite output files without asking
        *input_files,
        "-filter_complex",
        "".join(filter_complex_parts),
        *output_maps,
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "final_video.mp4"
    ]
    
    # This is a placeholder. The actual FFmpeg command will be very long and complex.
    # It needs to be built iteratively, managing stream labels and timings.
    print("FFmpeg command (simplified placeholder):")
    print(" ".join(ffmpeg_cmd))
    return ffmpeg_cmd

def main():
    script_path = Path("script.txt")
    if not script_path.exists():
        print("script.txt not found! Please create script.txt in the repository root.")
        return

    with open(script_path, "r", encoding="utf-8") as f:
        script_text = f.read()

    scenes = generate_scenes(script_text)
    
    os.makedirs("output_images", exist_ok=True)
    os.makedirs("output_videos", exist_ok=True)
    os.makedirs("downloaded_assets", exist_ok=True)

    downloaded_images = {}
    for scene in scenes:
        for idx, p in enumerate(scene["image_prompts"]):
            img_name = f"scene_{scene['id']}_img_{idx}.png"
            img_path = Path("output_images") / img_name
            if not img_path.exists():
                if generate_image(p, str(img_path)):
                    downloaded_images[img_name] = str(img_path)
            else:
                downloaded_images[img_name] = str(img_path)

    downloaded_stock_videos = []
    for scene in scenes:
        video_query = scene["stock_video_query"]
        video_url = download_pixabay_asset(video_query, "video")
        if video_url:
            video_dest = Path("downloaded_assets") / f"stock_video_{scene['id']}.mp4"
            if not video_dest.exists():
                if download_file(video_url, str(video_dest)):
                    downloaded_stock_videos.append(str(video_dest))

    background_music_file = Path("downloaded_assets") / "background_music.mp3"
    # Placeholder for background music download
    # if not background_music_file.exists():
    #     music_url = download_pixabay_asset("upbeat cinematic background music", "music")
    #     if music_url:
    #         download_file(music_url, str(background_music_file))
    print("Background music download placeholder.")

    character_video_path = Path("assets") / "character.mp4"
    script_audio_path = Path("assets") / "script.mp3"

    # Generate and execute FFmpeg command
    ffmpeg_cmd = generate_ffmpeg_command(
        scenes,
        downloaded_images,
        downloaded_stock_videos,
        str(character_video_path),
        str(script_audio_path),
        str(background_music_file)
    )

    print("Executing FFmpeg command...")
    try:
        # For actual execution, uncomment the following line:
        # subprocess.run(ffmpeg_cmd, check=True)
        print("FFmpeg command executed (simulated). final_video.mp4 created.")
        # Create a dummy final_video.mp4 for the next step
        with open("final_video.mp4", "w") as f:
            f.write("This is a dummy video file generated with advanced effects logic.")

    except subprocess.CalledProcessError as e:
        print(f"FFmpeg command failed: {e}")
    except FileNotFoundError:
        print("FFmpeg not found. Please ensure it is installed and in your PATH.")

    # Generate video metadata
    video_metadata = generate_video_metadata(script_text)
    with open("video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(video_metadata, f, indent=4)
    print("Video metadata generated in video_metadata.json")

if __name__ == "__main__":
    main()
