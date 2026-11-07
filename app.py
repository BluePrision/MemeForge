import os
import tempfile
import textwrap
import subprocess
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from google import genai
from google.genai import types

# Page Config
st.set_page_config(
    page_title="MemeForge Browser Edition",
    page_icon="🔥",
    layout="centered"
)

# Custom Dark Mode Styling
st.markdown("""
    <style>
    .main { background-color: #09090b; color: #f4f4f5; }
    .stTextInput input, .stSelectbox, .stTextArea textarea {
        background-color: #18181b !important; color: #ffffff !important;
        border: 1px solid #27272a !important; border-radius: 8px !important;
    }
    .stButton button {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
        color: white; border-radius: 8px; font-weight: 600; border: none; width: 100%; padding: 0.6rem;
    }
    .stButton button:hover { background: linear-gradient(135deg, #4f46e5 100%, #4338ca 100%); }
    h1 {
        background: linear-gradient(to right, #818cf8, #34d399);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🔥 MemeForge v3")
st.caption("Browser Edition — Full Video & 7-Caption Suite")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key_input = st.text_input("Gemini API Key", type="password", value=os.environ.get("GEMINI_API_KEY", ""))
    humor_style = st.selectbox(
        "Humor Style", 
        ["Gen-Z Meme Lord", "Sarcastic & Savage", "Relatable / Everyday", "Absurdist / Shitpost"]
    )

# Session State Initialization for Captions workflow
if "captions_list" not in st.session_state:
    st.session_state.captions_list = []

# Main Input Section
uploaded_file = st.file_uploader("Upload Video or Image (MP4, MOV, JPG, PNG)", type=["mp4", "mov", "avi", "jpg", "jpeg", "png", "webp"])

is_video = False
start_time = 0.0
end_time = 5.0
mute_audio = False

if uploaded_file is not None:
    file_ext = uploaded_file.name.split('.')[-1].lower()
    if file_ext in ["mp4", "mov", "avi"]:
        is_video = True
        st.info("📹 Video file detected!")
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.number_input("Start Time (sec)", min_value=0.0, value=0.0, step=0.5)
        with col2:
            end_time = st.number_input("End Time (sec)", min_value=0.5, value=5.0, step=0.5)
        mute_audio = st.checkbox("Mute original video audio", value=True)

context_prompt = st.text_area("Context / Situation", placeholder="e.g., When the code finally compiles on the first try...")

# Step 1: Generate Captions using Gemini 3.5 Flash
if st.button("🤖 Generate Captions"):
    if not api_key_input:
        st.error("Please enter your Gemini API Key in the sidebar.")
    elif not uploaded_file:
        st.error("Please upload a file first!")
    else:
        with st.spinner("Gemini 3.5 is cooking up 7 viral choices..."):
            try:
                client = genai.Client(api_key=api_key_input)
                prompt_text = f"""
                You are a top-tier viral meme creator. Style: {humor_style}.
                Context: {context_prompt}
                Generate exactly 7 short, punchy meme text captions (maximum 2 lines each) suitable for a 9:16 short top banner.
                Return ONLY the 7 captions separated by newlines, with no extra numbering, quotes, or markdown.
                """
                
                response = client.models.generate_content(
                    model='gemini-3.5-flash',
                    contents=[prompt_text]
                )
                
                lines = [line.strip() for line in response.text.strip().split('\n') if line.strip()]
                st.session_state.captions_list = lines[:7]
                st.success("7 Captions generated! Pick or edit your favorite below.")
            except Exception as e:
                st.error(f"Error calling Gemini: {e}")

# Helper to load Impact font cleanly
def get_impact_font(size):
    font_paths = ["impact.ttf", "Impact.ttf", "C:/Windows/Fonts/impact.ttf", "/Library/Fonts/Impact.ttf", "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf"]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        return ImageFont.load_default()

# Step 2: Select Caption, Edit It, & Render Final Short
if st.session_state.captions_list:
    st.markdown("### 🎯 Choose or Edit Your Caption")
    selected_option = st.selectbox("Quick-select from generated options:", st.session_state.captions_list)
    
    # Editable text box pre-filled with the selected choice
    final_caption_text = st.text_input("Edit final caption (feel free to tweak it):", value=selected_option)
    
    if st.button("🚀 2. Render Final Short"):
        with st.spinner("Rendering 9:16 Short (1/3 Text Banner + 2/3 Video)..."):
            try:
                # Save uploaded file locally temporarily
                input_suffix = "." + uploaded_file.name.split('.')[-1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=input_suffix) as tmp_in:
                    tmp_in.write(uploaded_file.getvalue())
                    tmp_in_path = tmp_in.name
                
                # Canvas Layout Specs: 1080x1920 total. Top 1/3 (640px) banner, Bottom 2/3 (1280px) clip.
                target_w = 1080
                target_h = 1920
                banner_h = 640
                clip_h = 1280

                if not is_video:
                    # --- IMAGE RENDERING PIPELINE ---
                    pil_img = Image.open(tmp_in_path)
                    canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
                    
                    # Resize and stretch to fit exactly into the 1080x1280 slot
                    resized_clip = pil_img.resize((target_w, clip_h), Image.Resampling.LANCZOS)
                    canvas.paste(resized_clip, (0, banner_h))
                    
                    # Draw Impact font text inside the 640px banner
                    draw = ImageDraw.Draw(canvas)
                    font_size = 75
                    font = get_impact_font(font_size)
                    
                    # Text wrapping for banner
                    wrapped_text = "\n".join(textwrap.wrap(final_caption_text, width=22))
                    
                    draw.multiline_text((target_w / 2, banner_h / 2), wrapped_text, fill="black", font=font, anchor="mm", align="center")
                    
                    out_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
                    canvas.save(out_path, "PNG")
                    
                    st.image(out_path, caption="Ready Short (Image)", use_container_width=True)
                    with open(out_path, "rb") as f:
                        st.download_button("📥 Download Short Image", f, file_name="memeforge_short.png", mime="image/png")
                
                else:
                    # --- VIDEO RENDERING PIPELINE (FFmpeg) ---
                    out_video_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
                    duration = max(0.5, end_time - start_time)
                    
                    # Create the 1080x640 white banner image with Impact font text
                    banner_img = Image.new("RGB", (target_w, banner_h), (255, 255, 255))
                    draw = ImageDraw.Draw(banner_img)
                    font = get_impact_font(75)
                    wrapped_text = "\n".join(textwrap.wrap(final_caption_text, width=22))
                    draw.multiline_text((target_w / 2, banner_h / 2), wrapped_text, fill="black", font=font, anchor="mm", align="center")
                    
                    banner_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
                    banner_img.save(banner_path)
                    
                    # FFmpeg filter complex: trim video, scale/stretch to exact 1080x1280 (2/3 space), and stack 640px banner on top
                    filter_complex = (
                        f"[0:v]trim=start={start_time}:duration={duration},setpts=PTS-STARTPTS,"
                        f"scale={target_w}:{clip_h},setsar=1[v_vid];"
                        f"[1:v]scale={target_w}:{banner_h}[v_banner];"
                        f"[v_banner][v_vid]vstack=inputs=2[v_out]"
                    )
                    
                    cmd = [
                        "ffmpeg", "-y",
                        "-ss", str(start_time),
                        "-i", tmp_in_path,
                        "-i", banner_path,
                        "-filter_complex", filter_complex,
                        "-map", "[v_out]",
                    ]
                    
                    if not mute_audio:
                        cmd += ["-map", "0:a?", "-shortest"]
                    else:
                        cmd += ["-an"]
                        
                    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", out_video_path]
                    
                    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    
                    st.success("Video Short rendered successfully!")
                    st.video(out_video_path)
                    
                    with open(out_video_path, "rb") as f:
                        st.download_button("📥 Download Short Video (.mp4)", f, file_name="memeforge_short.mp4", mime="video/mp4")
                        
            except Exception as e:
                st.error(f"Render Error (Ensure FFmpeg is installed on your system path): {e}")