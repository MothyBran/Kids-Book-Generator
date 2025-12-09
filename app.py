import streamlit as st
import os
from PIL import Image
import requests
from io import BytesIO

# Direkte Authentifizierung mit dem Token aus Secrets (zuverlässiger!)
import replicate
replicate.Client(api_token=st.secrets["REPLICATE_API_TOKEN"])

# Den alten Block entfernen (nicht mehr nötig):
# if "REPLICATE_API_TOKEN" in st.secrets:
#     os.environ["REPLICATE_API_TOKEN"] = st.secrets["REPLICATE_API_TOKEN"]
# Seitenkonfiguration
st.set_page_config(
    page_title="NSFW AI Image Generator",
    page_icon="🔞",
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
st.title("🔞 NSFW AI Image Generator")

# Session State
if 'generated_image' not in st.session_state:
    st.session_state.generated_image = None

# Input-Felder
st.subheader("🔞 NSFW-Modell-Einstellungen")
col1, col2, col3 = st.columns(3)

with col1:
    figure = st.selectbox("Figur", ["Schlank", "Kurvig", "Athletisch", "Petite", "Vollschlank", "Muscular", "Hourglass", "BBW"])
    hair_color = st.selectbox("Haarfarbe", ["Blond", "Brunette", "Rot", "Schwarz", "Pink", "Blue", "Silver", "Ombre", "Platinblond", "Auburn"])
    hair_style = st.selectbox("Haarstil", ["Lang", "Kurz", "Geflochten", "Messy", "Ponytail", "Bun", "Wavy", "Straight", "Curly", "Bob"])

with col2:
    eye_color = st.selectbox("Augenfarbe", ["Blau", "Grün", "Braun", "Grau", "Violet", "Amber", "Hazel", "Red", "Black"])
    phenotype = st.selectbox("Phänotyp", ["Kaukasisch", "Asiatisch", "Lateinamerikanisch", "Afrikanisch", "Mittelmeer", "Indisch", "Gemischtrassig", "Arabisch", "Native American"])
    breast_size = st.selectbox("Brustumfang", ["Klein", "Mittel", "Groß", "Sehr groß", "Übergroß", "Petite", "Athletic"])

with col3:
    butt_size = st.selectbox("Gesäßgröße", ["Klein", "Mittel", "Groß", "Sehr groß", "Übergroß", "Firm", "Round"])
    pose = st.selectbox("Pose", ["Stehend", "Sitzend", "Liegend", "Verführerisch", "Action", "Kniend", "Tanzend", "Spielerisch", "Yoga", "Bending Over"])
    clothing_style = st.selectbox("Kleidungsstil", ["Krankenschwester", "Dessous", "Bikini", "Nude", "College Girl", "Latex", "School Uniform", "Maid", "Swimsuit", "Casual", "Leather", "Fantasy", "Sporty"])

environment = st.selectbox("Umgebung", ["Strand", "Schlafzimmer", "Badezimmer", "Büro", "Wald", "Pool", "Gym", "Forest", "City Street", "Space", "Beach at Night", "Luxury Hotel", "Dungeon"])

additional_prompt = st.text_input("Zusätzliche Prompt-Details", placeholder="z.B. smiling, detailed skin, high heels")

# FUNKTION: BILD VIA REPLICATE (NSFW-FLUX)
def generate_nsfw_image(figure, hair_color, hair_style, eye_color, phenotype, breast_size, butt_size, pose, clothing_style, environment, additional_prompt):
    try:
        # Der NSFW Prompt (Optimiert für detaillierte Bilder)
        input_prompt = (
            f"A highly detailed, realistic image of a {phenotype} woman with {figure} figure, {hair_color} {hair_style} hair, "
            f"{eye_color} eyes, {breast_size} breasts, {butt_size} butt, in a {pose} pose, wearing {clothing_style}, "
            f"in a {environment} setting. High resolution, detailed anatomy."
        )
        if additional_prompt:
            input_prompt += f" {additional_prompt}"

        # Aufruf an Replicate (NSFW-Flux-Modell)
        output = replicate.run(
    "black-forest-labs/flux-schnell",
    input={
        "prompt": input_prompt,
        "aspect_ratio": "1:1",  # Oder "16:9" etc.
        "output_format": "png",
        "safety_tolerance": 2  # Optional, für weniger Safeties
    }
)
        
        # Output ist eine Liste von URLs
        image_url = output[0]
        image_response = requests.get(image_url)
        return Image.open(BytesIO(image_response.content)), None
      
    except Exception as e:
        return None, f"Fehler: {str(e)}"

# Button
if st.button("✨ Bild generieren"):
    with st.spinner("Generiere NSFW-Bild... (Das kann einen Moment dauern!) 🚀"):
        raw_image, error = generate_nsfw_image(figure, hair_color, hair_style, eye_color, phenotype, breast_size, butt_size, pose, clothing_style, environment, additional_prompt)

        if error:
            st.error(error)
            st.info("Hast du den REPLICATE_API_TOKEN in den Secrets hinterlegt?")
        else:
            st.session_state.generated_image = raw_image
            st.rerun()

# Ergebnis
if st.session_state.generated_image:
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 6, 1])
    with col2:
        st.image(st.session_state.generated_image, use_container_width=True)
    st.success("Dein NSFW-Bild ist generiert! (NSFW-Inhalt: Nur für Erwachsene.)")
