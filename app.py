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
    theme = st.text_input("Thema", placeholder="z.B. Pirat")
with col2:
    hobby = st.text_input("Hobby", placeholder="z.B. Fußball")
    companion = st.text_input("Tierfreund", placeholder="z.B. Papagei")

# Stil-Auswahl
drawing_style = st.selectbox(
    "🎨 Zeichenstil",
    options=["Klar & Einfach (4-6 Jahre)", "Comic Detail (6-8 Jahre)", "Disney-Stil (Alle Alter)"],
    index=0
)

# --- FUNKTION: BILD BEARBEITEN (Name + Wasserzeichen) ---
def process_image(image, name):
    """Fügt den Namen oben hinzu und das Wasserzeichen"""
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # 1. Bild vergrößern für den Header (weißer Balken oben dran)
    header_height = 180
    new_height = image.height + header_height
    new_image = Image.new("RGB", (image.width, new_height), "white")
    new_image.paste(image, (0, header_height))
    
    draw = ImageDraw.Draw(new_image)
    
    # --- NAME EINFÜGEN (Python statt KI) ---
    try:
        # Versuche eine schöne dicke Schrift zu laden
        title_font_size = 120
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        title_font = ImageFont.truetype(font_path, title_font_size)
    except:
        title_font = ImageFont.load_default()

    # Text zentrieren
    text = name.upper() if name else "MEIN MALBUCH"
    
    # Bounding Box berechnen (neue Methode für Pillow 10+)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=title_font)
    text_width = right - left
    text_height = bottom - top
    
    text_x = (new_image.width - text_width) // 2
    text_y = (header_height - text_height) // 2 - 10 # Mittig im Header
    
    # Text zeichnen (Schwarz)
    draw.text((text_x, text_y), text, fill="black", font=title_font)

    # --- WASSERZEICHEN ---
    # Transparente Ebene für Wasserzeichen
    watermark_layer = Image.new('RGBA', new_image.size, (255, 255, 255, 0))
    wm_draw = ImageDraw.Draw(watermark_layer)
    
    wm_text = "VORSCHAU"
    wm_font_size = int(new_image.width * 0.18) # Groß quer drüber
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
    
    # Zusammenfügen
    final_image = Image.alpha_composite(new_image.convert('RGBA'), watermark_layer)
    return final_image.convert('RGB')

# --- FUNKTION: KI GENERIERUNG ---
def generate_coloring_page(name, theme, hobby, companion, drawing_style):
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # Stil-Mapping
        if "Disney" in drawing_style:
            style_prompt = "in a cute Disney-like animation style, large eyes, soft curves"
        elif "Comic" in drawing_style:
            style_prompt = "in a classic comic book style, dynamic pose, detailed but clear"
        else:
            style_prompt = "in a very simple, bold line art style (chibi), minimum details"

        # OPTIMIERTER PROMPT GEGEN DOPPELGÄNGER
        prompt_text = (
            f"A single, vertical, full-body coloring book page black and white line drawing. "
            f"Subject: One single character representing a child named {name}, dressed as {theme}, holding a {companion}. "
            f"Action: The character is {hobby}. "
            f"Style: {style_prompt}. Pure black and white vector lines. White background. "
            f"CONSTRAINTS: Do not split the image. Do not use panels. Do not use split screen. "
            f"Show ONLY ONE central figure. No background details, no shading, no greyscale. High contrast."
        )
        
        # Bild generieren
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
        with st.spinner("Maler-Roboter arbeiten... 🤖🎨"):
            # Syntax-Fehler hier behoben: "=" hinzugefügt
            raw_image, error = generate_coloring_page(child_name, theme, hobby, companion, drawing_style)
            
            if error:
                st.error(error)
            else:
                # Hier fügen wir den Namen per Python hinzu
                final_image = process_image(raw_image, child_name)
                st.session_state.generated_image = final_image
                st.rerun()

# Ergebnis Anzeige
if st.session_state.generated_image:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        st.image(st.session_state.generated_image, use_container_width=True)
        
        st.success("Gefällt dir das Bild? Die HD-Version ist noch schärfer!")
        
        # Kauf-Button
        st.markdown(f"""
            <a href="https://buy.stripe.com/dein_link" target="_blank" style="text-decoration: none;">
                <div style="background-color: #4CAF50; color: white; padding: 15px; text-align: center; border-radius: 10px; font-weight: bold; font-size: 20px;">
                    🛒 Bild kaufen (3,99€)
                </div>
            </a>
        """, unsafe_allow_html=True)
