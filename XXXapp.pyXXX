import streamlit as st
import replicate
import os
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# Seitenkonfiguration
st.set_page_config(
    page_title="Dein persönliches Malbuch",
    page_icon="🎨",
    layout="centered"
)

# Replicate Token aus Secrets laden
if "REPLICATE_API_TOKEN" in st.secrets:
    os.environ["REPLICATE_API_TOKEN"] = st.secrets["REPLICATE_API_TOKEN"]

# Styling
st.markdown("""
    <style>
    .main {
        background-color: #FFF9F0;
    }
    .stButton>button {
        background-color: #6C5CE7; /* Neues Lila für Replicate-Power */
        color: white;
        font-size: 18px;
        font-weight: bold;
        border-radius: 10px;
        padding: 12px 24px;
        border: none;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #5849BE;
    }
    h1 {
        color: #6C5CE7;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("🎨 Dein persönliches Malbuch")

# Session State
if 'generated_image' not in st.session_state:
    st.session_state.generated_image = None

# Input-Felder
st.subheader("✏️ Dein Kind")
col1, col2 = st.columns(2)
with col1:
    child_name = st.text_input("Name", placeholder="z.B. Leo")
    theme = st.text_input("Thema", placeholder="z.B. Piratenschiff")
with col2:
    hobby = st.text_input("Hobby", placeholder="z.B. Schatz suchen")
    companion = st.text_input("Tierfreund", placeholder="z.B. frecher Papagei")

# Stil-Auswahl (Flux versteht Stile sehr gut)
drawing_style = st.selectbox(
    "🎨 Zeichenstil",
    options=["Klar & Einfach (4-6 Jahre)", "Comic Detail (6-8 Jahre)", "Disney-Stil (Alle Alter)"],
    index=0
)

# --- FUNKTION: HEADER & NAMEN EINFÜGEN ---
def process_image(image, name):
    """Fügt den Namen als Outline oben hinzu + Wasserzeichen"""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Header erstellen
    header_height = 200 # Etwas mehr Platz für den Namen
    new_height = image.height + header_height
    new_image = Image.new("RGB", (image.width, new_height), "white")
    new_image.paste(image, (0, header_height))
    
    draw = ImageDraw.Draw(new_image)
    
    # Schriftart laden
    try:
        title_font_size = 140
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        title_font = ImageFont.truetype(font_path, title_font_size)
    except:
        title_font = ImageFont.load_default()

    text = name.upper() if name else "MALBUCH"
    
    # Zentrieren
    left, top, right, bottom = draw.textbbox((0, 0), text, font=title_font)
    text_width = right - left
    text_height = bottom - top
    
    text_x = (new_image.width - text_width) // 2
    text_y = (header_height - text_height) // 2 - 20
    
    # Name als "Outline" zum Ausmalen (Weiß mit schwarzem Rand)
    draw.text((text_x, text_y), text, font=title_font, fill="white", stroke_width=6, stroke_fill="black")

    # Wasserzeichen
    watermark_layer = Image.new('RGBA', new_image.size, (255, 255, 255, 0))
    wm_draw = ImageDraw.Draw(watermark_layer)
    wm_text = "VORSCHAU"
    wm_font_size = int(new_image.width * 0.18)
    
    try:
        wm_font = ImageFont.truetype(font_path, wm_font_size)
    except:
        wm_font = ImageFont.load_default()
        
    l, t, r, b = wm_draw.textbbox((0, 0), wm_text, font=wm_font)
    wm_x = (new_image.width - (r - l)) // 2
    wm_y = (new_image.height - (b - t)) // 2
    
    wm_draw.text((wm_x, wm_y), wm_text, fill=(200, 200, 200, 120), font=wm_font)
    
    return Image.alpha_composite(new_image.convert('RGBA'), watermark_layer).convert('RGB')

# --- FUNKTION: BILD VIA REPLICATE (FLUX) ---
def generate_coloring_page(name, theme, hobby, companion, drawing_style):
    try:
        # Stil-Prompt Logik
        if "Disney" in drawing_style:
            style_prompt = "style of disney animation sketch, cute, big eyes, soft curves"
        elif "Comic" in drawing_style:
            style_prompt = "classic comic book style, dynamic lines, clear details"
        else:
            style_prompt = "simple children's coloring book style, thick lines, minimal details, chibi"

        # Der FLUX Prompt (Optimiert für Line Art)
        # Flux mag natürliche Sprache
        input_prompt = (
            f"A professional black and white coloring book page of a child named {name}. "
            f"The child is dressed as {theme} and is {hobby}. "
            f"A cute {companion} is next to the child. "
            f"Full body shot, vertical composition. "
            f"{style_prompt}. "
            f"Technical requirements: colorless, white background, clean black lines, vector style outlines, no shading, no gray, no fill, high contrast. "
            f"Make it a complete scene but keep the background simple and line-art only."
        )

        # Aufruf an Replicate (Flux-Schnell)
        output = replicate.run(
            "black-forest-labs/flux-schnell",
            input={
                "prompt": input_prompt,
                "go_fast": True,      # Optimiert für Speed
                "aspect_ratio": "2:3", # Perfektes Hochformat für Bücher!
                "output_format": "png",
                "safety_tolerance": 2
            }
        )
        
        # Output ist eine Liste von URLs
        image_url = output[0]
        image_response = requests.get(image_url)
        return Image.open(BytesIO(image_response.content)), None
        
    except Exception as e:
        return None, f"Fehler: {str(e)}"

# Button
if st.button("✨ Vorschau erstellen (Flux Power)"):
    if not child_name or not theme:
        st.warning("Bitte Name und Thema eingeben.")
    else:
        with st.spinner("Flux generiert dein Bild... (Das geht fix!) 🚀"):
            raw_image, error = generate_coloring_page(child_name, theme, hobby, companion, drawing_style)
            
            if error:
                st.error(error)
                st.info("Hast du den REPLICATE_API_TOKEN in den Secrets hinterlegt?")
            else:
                final_image = process_image(raw_image, child_name)
                st.session_state.generated_image = final_image
                st.rerun()

# Ergebnis
if st.session_state.generated_image:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        st.image(st.session_state.generated_image, use_container_width=True)
        st.success("Sieh dir die sauberen Linien an! Perfekt zum Drucken.")
        
        st.markdown(f"""
            <a href="https://buy.stripe.com/dein_link" target="_blank" style="text-decoration: none;">
                <div style="background-color: #6C5CE7; color: white; padding: 15px; text-align: center; border-radius: 10px; font-weight: bold; font-size: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    🛒 Bild kaufen (3,99€)
                </div>
            </a>
        """, unsafe_allow_html=True)
