import streamlit as st
import zipfile
import tempfile
import os
import re
from PIL import Image


st.set_page_config(
    page_title="Lecteur JPG",
    layout="wide"
)

st.title("📖 Lecteur de pages numérisées")


zip_file = st.file_uploader(
    "Upload un fichier ZIP contenant les images",
    type=["zip"]
)


# ---------- trouver images ----------

def find_images(folder):

    imgs = []

    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                imgs.append(os.path.join(root, f))

    # tri numérique (important)
    def extract_number(path):
        name = os.path.basename(path)
        nums = re.findall(r"\d+", name)
        return int(nums[-1]) if nums else 0

    imgs.sort(key=extract_number)

    return imgs


# ---------- extraction zip ----------

if zip_file is not None:

    if "images" not in st.session_state:

        tmpdir = tempfile.mkdtemp()

        with zipfile.ZipFile(zip_file, "r") as z:
            z.extractall(tmpdir)

        files = find_images(tmpdir)

        if len(files) == 0:
            st.error("Aucune image trouvée dans le zip")
            st.stop()

        st.session_state.images = files
        st.session_state.index = 0


# ---------- affichage ----------

if "images" in st.session_state:

    images = st.session_state.images
    i = st.session_state.index

    col1, col2, col3 = st.columns([1, 6, 1])

    with col1:
        if st.button("⬅️"):
            if i > 0:
                st.session_state.index -= 1

    with col3:
        if st.button("➡️"):
            if i < len(images) - 1:
                st.session_state.index += 1

    i = st.session_state.index

    st.write(f"Page {i+1} / {len(images)}")

    try:

        img_path = images[i]

        img = Image.open(img_path)

        st.image(img, use_container_width=True)

    except Exception as e:

        st.error("Erreur chargement image")
        st.write(e)
