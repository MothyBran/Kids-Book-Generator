import streamlit as st
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# Seitenkonfiguration
st.set_page_config(
    page_title="Dein persönliches Malbuch",
    page_icon="🎨",
    layout="centered"
)

# Styling
st.markdown("""
    <style>
    .main {
        background-color: #FFF9F0;
    }
    .stButton>button {
        background-color: #FF6B9D;
        color: white;
        font-size: 18px;
        font-weight: bold;
        border-radius: 10px;
        padding: 12px 24px;
        border: none;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #FF4D7D;
    }
    h1 {
        color: #FF6B9D;
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
    theme = st.text_input("Thema", placeholder="z.B. Ritterburg")
with col2:
    hobby = st.text_input("Hobby", placeholder="z.B. Schwertkampf")
    companion = st.text_input("Tierfreund", placeholder="z.B. Drache")

# Stil-Auswahl
drawing_style = st.selectbox(
    "🎨 Zeichenstil",
    options=["Klar & Einfach (4-6 Jahre)", "Comic Detail (6-8 Jahre)", "Disney-Stil (Alle Alter)"],
    index=0
)

# --- FUNKTION: BILD BEARBEITEN (Name als Outline + Wasserzeichen) ---
def process_image(image, name):
    """Fügt den Namen als Outline (Ausmalbar) oben hinzu"""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Header für den Namen erstellen
    header_height = 180
    new_height = image.height + header_height
    new_image = Image.new("RGB", (image.width, new_height), "white")
    new_image.paste(image, (0, header_height))
    
    draw = ImageDraw.Draw(new_image)
    
    # --- NAME EINFÜGEN (KONTUR-STIL) ---
    try:
        title_font_size = 130
        # Pfad für Linux/Streamlit Cloud
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        title_font = ImageFont.truetype(font_path, title_font_size)
    except:
        title_font = ImageFont.load_default()

    text = name.upper() if name else "MEIN MALBUCH"
    
    # Text zentrieren
    left, top, right, bottom = draw.textbbox((0, 0), text, font=title_font)
    text_width = right - left
    text_height = bottom - top
    
    text_x = (new_image.width - text_width) // 2
    text_y = (header_height - text_height) // 2 - 10
    
    # 1. Die schwarze Umrandung (Stroke)
    # stroke_width=4 macht den Rand dick genug zum Ausmalen
    draw.text((text_x, text_y), text, font=title_font, fill="white", stroke_width=5, stroke_fill="black")

    # --- WASSERZEICHEN ---
    watermark_layer = Image.new('RGBA', new_image.size, (255, 255, 255, 0))
    wm_draw = ImageDraw.Draw(watermark_layer)
    
    wm_text = "VORSCHAU"
    wm_font_size = int(new_image.width * 0.18)
    try:
        wm_font = ImageFont.truetype(font_path, wm_font_size)
    except:
        wm_font = ImageFont.load_default()
        
    l, t, r, b = wm_draw.textbbox((0, 0), wm_text, font=wm_font)
    wm_w = r - l
    wm_h = b - t
    
    wm_x = (new_image.width - wm_w) // 2
    wm_y = (new_image.height - wm_h) // 2
    
    # Halbtransparentes Grau
    wm_draw.text((wm_x, wm_y), wm_text, fill=(200, 200, 200, 150), font=wm_font)
    
    final_image = Image.alpha_composite(new_image.convert('RGBA'), watermark_layer)
    return final_image.convert('RGB')

# --- FUNKTION: KI GENERIERUNG (VOLLE SZENE) ---
def generate_coloring_page(name, theme, hobby, companion, drawing_style):
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # Stil-Anpassung
        if "Disney" in drawing_style:
            style_desc = "Disney-style animation line art, soft curves, expressive eyes"
        elif "Comic" in drawing_style:
            style_desc = "classic American comic book line art, dynamic and detailed"
        else:
            style_desc = "clean, bold children's book illustration style"

        # PROMPT ÄNDERUNG: Volle Szene statt leerer Hintergrund
        prompt_text = (
            f"A vertical coloring book page (DIN A4 ratio). "
            f"The image must be a FULL SCENE filling the entire page from top to bottom. "
            f"Setting: A detailed and magical '{theme}' world (e.g. landscape, buildings, nature relevant to the theme). "
            f"Main Character: A happy child named {name} is in the center, {hobby}. "
            f"Companion: Accompanied by a cute {companion} interacting with the child. "
            f"Style: {style_desc}. Pure black and white outlines only. "
            f"Background Requirement: DO NOT leave the background empty. Fill the background with elements fitting the theme (trees, clouds, castles, houses) suitable for coloring. "
            f"Technical: Thick clean lines. No shading. No greyscale. No solid black fills."
        )
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt_text,
            size="1024x1792",
            quality="standard",
            n=1
        )
        
        image_url = response.data[0].url
        image_response = requests.get(image_url)
        return Image.open(BytesIO(image_response.content)), None
        
    except Exception as e:
        return None, f"Fehler: {str(e)}"

# Button
if st.button("✨ Vorschau erstellen"):
    if not child_name or not theme:
        st.warning("Bitte Name und Thema eingeben.")
    else:
        with st.spinner("✨ Die KI malt deine Themenwelt..."):
            raw_image, error = generate_coloring_page(child_name, theme, hobby, companion, drawing_style)
            
            if error:
                st.error(error)
            else:
                final_image = process_image(raw_image, child_name)
                st.session_state.generated_image = final_image
                st.rerun()

# Ergebnis Anzeige
if st.session_state.generated_image:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        st.image(st.session_state.generated_image, use_container_width=True)
        
        st.success("Tipp: Die HD-Version ist perfekt scharf und ideal zum Drucken!")
        
        st.markdown(f"""
            <a href="https://buy.stripe.com/dein_link" target="_blank" style="text-decoration: none;">
                <div style="background-color: #4CAF50; color: white; padding: 15px; text-align: center; border-radius: 10px; font-weight: bold; font-size: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    🛒 Bild kaufen (3,99€)
                </div>
            </a>
        """, unsafe_allow_html=True)
