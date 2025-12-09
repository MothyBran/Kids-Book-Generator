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
    }
    .stButton>button:hover {
        background-color: #FF4D7D;
    }
    h1 {
        color: #FF6B9D;
        text-align: center;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 18px;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("🎨 Dein persönliches Malbuch")
st.markdown('<p class="subtitle">Erstelle eine einzigartige Malvorlage für dein Kind – mit Namen und Lieblingsthemen!</p>', unsafe_allow_html=True)

# Session State initialisieren
if 'generated_image' not in st.session_state:
    st.session_state.generated_image = None

# Input-Felder
st.subheader("✏️ Erzähl uns von deinem Kind")

col1, col2 = st.columns(2)

with col1:
    child_name = st.text_input("Name des Kindes", placeholder="z.B. Emma")
    theme = st.text_input("Themenwelt", placeholder="z.B. Ritter, Weltraum, Prinzessin")

with col2:
    hobby = st.text_input("Hobby", placeholder="z.B. singen, schwimmen, tanzen")
    companion = st.text_input("Begleiter", placeholder="z.B. Hund, Teddy, Drache")

st.markdown("---")

# Funktion zum Hinzufügen des Wasserzeichens
def add_watermark(image):
    """Fügt ein halbtransparentes 'VORSCHAU' Wasserzeichen hinzu"""
    # Konvertiere zu RGBA falls nötig
    if image.mode != 'RGBA':
        image = image.convert('RGBA')
    
    # Erstelle eine transparente Overlay-Ebene
    overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Versuche eine große Schriftart zu laden, fallback zu default
    try:
        font_size = 40
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Text und Position
    text = "VORSCHAU"
    
    # Berechne Textgröße
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Positioniere den Text diagonal
    width, height = image.size
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Zeichne den Text mit Transparenz (halbtransparent grau)
    draw.text((x, y), text, fill=(128, 128, 128, 180), font=font)
    
    # Kombiniere Original und Overlay
    watermarked = Image.alpha_composite(image, overlay)
    return watermarked.convert('RGB')

# Funktion zur Bildgenerierung
def generate_coloring_page(name, theme, hobby, companion):
    """Generiert eine Malvorlage mit DALL-E 2"""
    try:
        # OpenAI Client initialisieren
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # Prompt erstellen
        prompt_parts = [f"Black and white coloring book page for kids, simple lines, thick outlines, white background"]
        
        if theme:
            prompt_parts.append(f"theme: {theme}")
        
        if name:
            prompt_parts.append(f"featuring a happy child character named {name}")
        
        if hobby:
            prompt_parts.append(f"doing {hobby}")
        
        if companion:
            prompt_parts.append(f"with a cute {companion}")
        
        prompt = ", ".join(prompt_parts) + ". Style: simple coloring book, clear outlines, no shading, child-friendly."
        
        # Bild generieren
        response = client.images.generate(
            model="dall-e-2",
            prompt=prompt,
            size="256x256",
            n=1
        )
        
        # Bild herunterladen
        image_url = response.data[0].url
        image_response = requests.get(image_url)
        image = Image.open(BytesIO(image_response.content))
        
        # Wasserzeichen hinzufügen
        watermarked_image = add_watermark(image)
        
        return watermarked_image, None
        
    except Exception as e:
        return None, f"Fehler bei der Bildgenerierung: {str(e)}"

# Button zur Generierung
if st.button("🎨 Kostenlose Vorschau erstellen", type="primary"):
    # Validierung
    if not child_name and not theme:
        st.warning("⚠️ Bitte gib mindestens einen Namen oder ein Thema ein.")
    else:
        with st.spinner("✨ Deine Malvorlage wird erstellt... Das dauert einen Moment!"):
            image, error = generate_coloring_page(child_name, theme, hobby, companion)
            
            if error:
                st.error(f"❌ {error}")
                st.info("💡 Tipp: Überprüfe, ob dein OpenAI API Key in den Streamlit Secrets konfiguriert ist.")
            else:
                st.session_state.generated_image = image
                st.success("✅ Deine Vorschau ist fertig!")

# Bild anzeigen, wenn generiert
if st.session_state.generated_image is not None:
    st.markdown("---")
    st.subheader("🖼️ Deine Malvorlagen-Vorschau")
    
    # Bild zentriert anzeigen
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(st.session_state.generated_image, use_container_width=True)
    
    st.markdown("---")
    
    # Call to Action
    st.markdown("### 🌟 Gefällt dir die Vorschau?")
    st.markdown("Erhalte das Bild in **hochauflösender Qualität (1024x1024 Pixel)** ohne Wasserzeichen – perfekt zum Ausdrucken!")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <a href="https://buy.stripe.com/dein_link" target="_blank">
                <button style="
                    background-color: #4CAF50;
                    color: white;
                    padding: 15px 32px;
                    text-align: center;
                    font-size: 20px;
                    font-weight: bold;
                    border: none;
                    border-radius: 12px;
                    cursor: pointer;
                    width: 100%;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                ">
                    🎨 HD-Version kaufen (3,99€)
                </button>
            </a>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💎 **Was du bekommst:** Hochauflösendes Bild (1024x1024px) ohne Wasserzeichen, sofortiger Download")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #999; font-size: 14px;'>
        Made with ❤️ for creative kids | Powered by OpenAI DALL-E
    </div>
""", unsafe_allow_html=True)
