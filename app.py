import streamlit as st
import replicate
import os
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

# Seitenkonfiguration
st.set_page_config(
    page_title="Deine Bastel-Werkstatt",
    page_icon="✂️",
    layout="centered"
)

# Replicate Token laden
if "REPLICATE_API_TOKEN" in st.secrets:
    os.environ["REPLICATE_API_TOKEN"] = st.secrets["REPLICATE_API_TOKEN"]

# Styling
st.markdown("""
    <style>
    .main {
        background-color: #F0F8FF;
    }
    .stButton>button {
        background-color: #0984E3;
        color: white;
        font-size: 19px;
        font-weight: bold;
        border-radius: 12px;
        padding: 15px 30px;
        border: none;
        width: 100%;
        box-shadow: 0 4px 0 #0056b3;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #74B9FF;
        transform: translateY(-2px);
    }
    .stButton>button:active {
        transform: translateY(2px);
        box-shadow: none;
    }
    h1 {
        color: #2D3436;
        text-align: center;
        font-family: 'Arial', sans-serif;
    }
    .info-box {
        background-color: #FFEAA7;
        padding: 15px;
        border-radius: 10px;
        color: #896608;
        text-align: center;
        margin-bottom: 20px;
        border: 2px solid #FDCB6E;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("✂️ Deine Bastel-Werkstatt")
st.markdown('<div class="info-box">Erstelle deinen eigenen <b>Ausschneide-Bogen</b> (Paper Doll).<br>Wähle Figur & Thema und bestimme das Zubehör!</div>', unsafe_allow_html=True)

# Session State
if 'generated_image' not in st.session_state:
    st.session_state.generated_image = None

# --- INPUT BEREICH ---
st.subheader("1. Die Basis")
col1, col2 = st.columns(2)

with col1:
    child_name = st.text_input("Name des Kindes", placeholder="z.B. Leonie")
    # Dropdown für Figur
    char_selection = st.selectbox(
        "Figur-Typ", 
        ["Mädchen", "Junge", "Roboter", "Bär", "Katze", "Hund", "Dino", "Superhelden-Kind"]
    )

with col2:
    # Dropdown für Thema
    theme_selection = st.selectbox(
        "Themenwelt", 
        ["Weltraum / Astronaut", "Ritter / Mittelalter", "Pirat / Schatzsuche", 
         "Prinzessin / Märchen", "Polizei / Feuerwehr", "Arzt / Krankenhaus", 
         "Schule / Alltag", "Winter / Schnee", "Sommer / Strand"]
    )

st.subheader("2. Das Zubehör zum Ausschneiden")
st.markdown("Was soll die Figur anziehen/tragen?")
c1, c2, c3 = st.columns(3)

with c1:
    clothing_input = st.text_input("Kleidung (Körper)", placeholder="z.B. Raumanzug")
with c2:
    headwear_input = st.text_input("Kopfbedeckung", placeholder="z.B. Helm")
with c3:
    item_input = st.text_input("Gegenstand (Hand)", placeholder="z.B. Laserpistole")

# --- INTERNE LOGIK: ÜBERSETZUNG ---
# Wir mappen die deutschen Auswahlen auf perfekte englische Prompts für Flux
def get_english_prompts(char_sel, theme_sel):
    char_map = {
        "Mädchen": "cute little girl",
        "Junge": "cute little boy",
        "Roboter": "cute friendly robot",
        "Bär": "cute teddy bear",
        "Katze": "cute anthropomorphic cat",
        "Hund": "cute anthropomorphic dog",
        "Dino": "cute little dinosaur",
        "Superhelden-Kind": "cute superhero child"
    }
    
    theme_map = {
        "Weltraum / Astronaut": "Space and Astronaut theme",
        "Ritter / Mittelalter": "Medieval Knight theme",
        "Pirat / Schatzsuche": "Pirate Captain theme",
        "Prinzessin / Märchen": "Royal Princess Fairytale theme",
        "Polizei / Feuerwehr": "Police and Firefighter theme",
        "Arzt / Krankenhaus": "Doctor and Medical theme",
        "Schule / Alltag": "Casual School outfit theme",
        "Winter / Schnee": "Winter snow outfit theme",
        "Sommer / Strand": "Summer beach outfit theme"
    }
    
    return char_map.get(char_sel, "cute character"), theme_map.get(theme_sel, "general theme")

# --- HEADER & NAMEN EINFÜGEN ---
def process_image(image, name):
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    header_height = 220
    new_height = image.height + header_height
    new_image = Image.new("RGB", (image.width, new_height), "white")
    new_image.paste(image, (0, header_height))
    draw = ImageDraw.Draw(new_image)
    
    try:
        title_font_size = 130
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        title_font = ImageFont.truetype(font_path, title_font_size)
        subtitle_font = ImageFont.truetype(font_path, 40)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()

    text = f"{name}'s BASTELBOGEN" if name else "MEIN BASTELBOGEN"
    text = text.upper()
    
    left, top, right, bottom = draw.textbbox((0, 0), text, font=title_font)
    text_width = right - left
    text_x = (new_image.width - text_width) // 2
    text_y = 40
    
    draw.text((text_x, text_y), text, font=title_font, fill="white", stroke_width=6, stroke_fill="black")

    sub_text = "1. ANMALEN   ✂️   2. AUSSCHNEIDEN   👕   3. ANZIEHEN"
    l, t, r, b = draw.textbbox((0, 0), sub_text, font=subtitle_font)
    sub_x = (new_image.width - (r - l)) // 2
    draw.text((sub_x, text_y + 140), sub_text, fill="#555", font=subtitle_font)

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
    wm_draw.text((wm_x, wm_y), wm_text, fill=(200, 200, 200, 100), font=wm_font)
    
    return Image.alpha_composite(new_image.convert('RGBA'), watermark_layer).convert('RGB')

# --- GENERIERUNG MIT FLUX ---
def generate_craft_sheet(name, char_english, theme_english, cloth, head, item):
    try:
        # Prompt zusammenbauen mit den 3 spezifischen Inputs
        extras_prompt = ""
        if cloth: extras_prompt += f"1. Clothing: {cloth}. "
        if head: extras_prompt += f"2. Headwear: {head}. "
        if item: extras_prompt += f"3. Accessory/Item: {item}. "
        
        prompt = (
            f"A professional DIY paper doll activity sheet for kids. Black and white line art. "
            f"Layout: Knolling style flat lay. "
            f"LEFT SIDE: A standing base character ({char_english}), wearing only basic underwear, ready to be dressed. "
            f"RIGHT SIDE: Separate clothing items arranged neatly for cutting. "
            f"Theme: {theme_english}. "
            f"Specific items to include: {extras_prompt} "
            f"Style: Thick distinct black vector outlines, pure white background. "
            f"No shading, no grey, high contrast. "
            f"Educational worksheet style."
        )

        output = replicate.run(
            "black-forest-labs/flux-schnell",
            input={
                "prompt": prompt,
                "go_fast": True,
                "aspect_ratio": "2:3",
                "output_format": "png",
                "megapixels": "1"
            }
        )
        
        image_url = output[0]
        image_response = requests.get(image_url)
        return Image.open(BytesIO(image_response.content)), None
        
    except Exception as e:
        return None, f"Fehler: {str(e)}"

# Button
if st.button("✂️ Bastelbogen erstellen"):
    if not child_name:
        st.warning("Bitte gib zumindest einen Namen ein.")
    else:
        # Übersetzung holen
        char_en, theme_en = get_english_prompts(char_selection, theme_selection)
        
        with st.spinner(f"Werkstatt: {char_selection} wird als {theme_selection} ausgerüstet..."):
            raw_image, error = generate_craft_sheet(child_name, char_en, theme_en, clothing_input, headwear_input, item_input)
            
            if error:
                st.error(error)
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
        st.success("Fertig! Einmal drucken = 1 Stunde Beschäftigung.")
        st.markdown(f"""
            <a href="https://buy.stripe.com/dein_link" target="_blank" style="text-decoration: none;">
                <div style="background-color: #0984E3; color: white; padding: 15px; text-align: center; border-radius: 10px; font-weight: bold; font-size: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    🛒 Bastel-Set kaufen (3,99€)
                </div>
            </a>
        """, unsafe_allow_html=True)
