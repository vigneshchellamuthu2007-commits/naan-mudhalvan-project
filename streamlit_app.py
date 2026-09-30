"""
ComicCraft – Streamlit Web Application
AI-Powered Comic Story Creator
"""

import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv

# Load local .env if present
load_dotenv()

# Import ComicCraft core logic
from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_all_images
from app.layout_builder import build_comic_layout
from app.exporters import save_pdf

# ─── Page Configuration ───────────────────────────────────────────────
st.set_page_config(
    page_title="ComicCraft - AI Comic Story Creator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS for Premium Comic Styling ─────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bangers&family=Inter:wght@400;600;700;800&display=swap');
    
    .comic-title {
        font-family: 'Bangers', cursive;
        font-size: 3.2rem;
        color: #FF5722;
        text-shadow: 3px 3px 0px #000;
        letter-spacing: 2px;
        margin-bottom: 0px;
    }
    .comic-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .panel-card {
        background: #ffffff;
        border: 3px solid #111;
        border-radius: 12px;
        box-shadow: 6px 6px 0px #111;
        padding: 16px;
        margin-bottom: 20px;
        transition: transform 0.2s ease;
    }
    .panel-badge {
        display: inline-block;
        background: #FFD700;
        color: #000;
        font-weight: 800;
        padding: 4px 10px;
        border-radius: 20px;
        border: 2px solid #000;
        font-size: 0.85rem;
        margin-bottom: 8px;
    }
    .dialogue-box {
        background: #f1f5f9;
        border-left: 4px solid #3b82f6;
        padding: 8px 12px;
        border-radius: 4px;
        font-style: italic;
        margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ─── Secret / API Key Management ─────────────────────────────────────
# Check Streamlit secrets first, then environment variables
gemini_key = None
if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
    gemini_key = st.secrets["GEMINI_API_KEY"]
elif os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "your_gemini_api_key_here":
    gemini_key = os.getenv("GEMINI_API_KEY")

hf_key = None
if hasattr(st, "secrets") and "HF_API_KEY" in st.secrets:
    hf_key = st.secrets["HF_API_KEY"]
elif os.getenv("HF_API_KEY") and os.getenv("HF_API_KEY") != "your_huggingface_api_key_here":
    hf_key = os.getenv("HF_API_KEY")

# ─── Sidebar Configuration ───────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/comic-book.png", width=70)
    st.title("ComicCraft Settings")
    
    st.markdown("### 🔑 API Keys")
    user_gemini_key = st.text_input(
        "Google Gemini API Key",
        value=gemini_key if gemini_key else "",
        type="password",
        help="Get your free key from https://aistudio.google.com/app/apikey"
    )
    if user_gemini_key:
        os.environ["GEMINI_API_KEY"] = user_gemini_key
    
    user_hf_key = st.text_input(
        "Hugging Face Token (Optional)",
        value=hf_key if hf_key else "",
        type="password",
        help="Optional: For cloud AI image generation from https://huggingface.co/settings/tokens"
    )
    if user_hf_key:
        os.environ["HF_API_KEY"] = user_hf_key

    st.markdown("---")
    st.markdown("### ℹ️ About Project")
    st.info("**ComicCraft** is an AI Comic Story Generator created for the Naan Mudhalvan Initiative.")

# ─── Header ───────────────────────────────────────────────────────────
st.markdown('<div class="comic-title">⚡ ComicCraft</div>', unsafe_allow_html=True)
st.markdown('<div class="comic-subtitle">Turn your imagination into AI-powered comic books with story, panels, & PDF export!</div>', unsafe_allow_html=True)

# ─── Form Inputs ──────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    story_prompt = st.text_area(
        "📖 Story Concept / Plot Idea",
        placeholder="e.g. A young student invents an AI gadget that can speak to animals in Chennai...",
        height=120,
        help="Describe what your comic is about (min 10 characters)"
    )

with col2:
    character_name = st.text_input(
        "🦸 Main Character Name",
        value="Kavi",
        placeholder="e.g. Kavi, Arjun, Maya"
    )
    
    col_a, col_b = st.columns(2)
    with col_a:
        setting = st.selectbox(
            "🌍 Setting",
            ["School", "Forest", "City", "Space", "Village", "Fantasy World"]
        )
        tone = st.selectbox(
            "🎭 Tone",
            ["Adventure", "Funny", "Dramatic", "Light-hearted", "Emotional", "Mystery"]
        )
    with col_b:
        art_style = st.selectbox(
            "🎨 Art Style",
            ["Comic Book", "Anime", "Cartoon", "Pixel Art", "Realistic", "Fantasy"]
        )

# ─── Generate Button & Pipeline ──────────────────────────────────────
if st.button("🚀 Generate Full Comic Book", type="primary", use_container_width=True):
    if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_gemini_api_key_here":
        st.error("❌ Please provide a valid Google Gemini API Key in the sidebar or .env file!")
    elif not story_prompt or len(story_prompt.strip()) < 10:
        st.warning("⚠️ Story prompt must be at least 10 characters long.")
    elif not character_name or len(character_name.strip()) < 1:
        st.warning("⚠️ Please provide a Character Name.")
    else:
        with st.status("🎨 Crafting your comic story with AI...", expanded=True) as status:
            try:
                st.write("📝 Step 1/5: Outlining 5-panel story arc with Gemini Flash...")
                outline = generate_outline(
                    story_prompt=story_prompt,
                    character_name=character_name,
                    setting=setting,
                    tone=tone,
                    art_style=art_style
                )
                
                st.write("💬 Step 2/5: Generating narrations and dialogues with Gemini Pro...")
                enriched = generate_story(
                    outline=outline,
                    character_name=character_name,
                    setting=setting,
                    tone=tone
                )
                
                st.write("🖼️ Step 3/5: Generating artwork for each panel...")
                with_images = generate_all_images(enriched, art_style=art_style)
                
                st.write("📐 Step 4/5: Building comic layout...")
                layout = build_comic_layout(with_images)
                
                st.write("📄 Step 5/5: Exporting printable PDF...")
                story_title = f"{character_name}'s Adventure"
                pdf_path = save_pdf(layout, story_title=story_title)
                
                status.update(label="🎉 Comic generated successfully!", state="complete", expanded=False)
                
                st.session_state["generated_comic"] = {
                    "layout": layout,
                    "pdf_path": pdf_path,
                    "title": story_title,
                    "character": character_name,
                    "art_style": art_style
                }
            except Exception as e:
                status.update(label="❌ Generation failed!", state="error")
                st.error(f"Error during comic generation: {str(e)}")

# ─── Display Results ─────────────────────────────────────────────────
if "generated_comic" in st.session_state:
    data = st.session_state["generated_comic"]
    st.markdown("---")
    
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.subheader(f"📚 {data['title']}")
        st.caption(f"Character: {data['character']} | Style: {data['art_style']}")
    with col_t2:
        # PDF download button
        pdf_file = Path(data["pdf_path"])
        if pdf_file.exists():
            with open(pdf_file, "rb") as f:
                st.download_button(
                    label="📥 Download Comic PDF",
                    data=f.read(),
                    file_name=pdf_file.name,
                    mime="application/pdf",
                    use_container_width=True
                )

    # Render Comic Panels
    panels = data["layout"]
    cols = st.columns(2)
    for i, panel in enumerate(panels):
        with cols[i % 2]:
            st.markdown(f'<div class="panel-badge">Panel {panel.get("panel_number", i+1)}: {panel.get("title", "")}</div>', unsafe_allow_html=True)
            
            img_path = panel.get("image_path")
            if img_path:
                clean_path = img_path.lstrip("/")
                if Path(clean_path).exists():
                    st.image(clean_path, use_container_width=True)
                elif Path(img_path).exists():
                    st.image(img_path, use_container_width=True)
            
            st.markdown(f"**📖 Narration:** {panel.get('narration', '')}")
            
            if panel.get("dialogue"):
                st.markdown(f'<div class="dialogue-box">💬 <strong>{data["character"]}:</strong> "{panel.get("dialogue")}"</div>', unsafe_allow_html=True)
            if panel.get("caption"):
                st.caption(f"📌 {panel.get('caption')}")
            st.markdown("<br>", unsafe_allow_html=True)
