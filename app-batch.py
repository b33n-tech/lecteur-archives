import streamlit as st
import zipfile
import tempfile
import os
import re
import json
from PIL import Image

st.set_page_config(page_title="Mosaïque Tagger", layout="wide")
st.title("📚 Tagging en mosaïque")

# ---------------- STATE INIT ----------------
def init_state(key, value):
    if key not in st.session_state:
        st.session_state[key] = value

init_state("images", [])
init_state("selected", set())
init_state("tags", {})

TAGS_JSON = "tags.json"

# ---------------- TAGS BASE ----------------
BASE_TAGS = ["Titre", "Planche/illustration", "Index", "Table", "Chapitre", "Page blanche", "Autre"]

# ---------------- UPLOAD ZIP ----------------
zip_file = st.file_uploader("Upload ZIP images", type=["zip"])

def find_images(folder):
    imgs = []
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                imgs.append(os.path.join(root, f))
    def extract_number(path):
        name = os.path.basename(path)
        nums = re.findall(r"\d+", name)
        return int(nums[-1]) if nums else 0
    imgs.sort(key=extract_number)
    return imgs

if zip_file is not None and len(st.session_state.images) == 0:
    tmpdir = tempfile.mkdtemp()
    with zipfile.ZipFile(zip_file, "r") as z:
        z.extractall(tmpdir)
    files = find_images(tmpdir)
    if len(files) == 0:
        st.error("No images found in zip")
        st.stop()
    st.session_state.images = files

images = st.session_state.images
total = len(images)

# ---------------- CONFIG MOSAÏQUE ----------------
cols_option = st.selectbox("Nombre d'images par page", [4,9,16,20,25,36,60], index=1)
cols_per_row = int(cols_option ** 0.5)  # ex: 9 → 3x3

start_idx = st.number_input("Page de mosaïque (indice de départ)", min_value=0, max_value=max(0,total-1), value=0, step=cols_option)

end_idx = min(start_idx + cols_option, total)
current_images = images[start_idx:end_idx]

st.write(f"Affichage images {start_idx+1} à {end_idx} / {total}")

# ---------------- MOSAÏQUE ----------------
selected = st.session_state.selected

for i in range(0, len(current_images), cols_per_row):
    row_imgs = current_images[i:i+cols_per_row]
    cols = st.columns(len(row_imgs))
    for col, img_path in zip(cols,row_imgs):
        page_name = os.path.basename(img_path)
        img = Image.open(img_path)
        img.thumbnail((150,150))
        with col:
            # Checkbox pour sélectionner
            checked = st.checkbox(page_name, value=(page_name in selected), key=f"chk_{page_name}")
            if checked:
                selected.add(page_name)
            else:
                selected.discard(page_name)
            st.image(img)

st.session_state.selected = selected

st.write(f"Pages sélectionnées: {len(selected)}")

# ---------------- TAGS ----------------
st.subheader("Appliquer tags aux pages sélectionnées")
selected_tags = st.multiselect("Tags existants", BASE_TAGS)
new_tag = st.text_input("Ajouter tag personnalisé")

if st.button("💾 Appliquer tags"):
    for page in selected:
        page_tags = st.session_state.tags.get(page, [])
        # ajouter tags existants
        for t in selected_tags:
            if t not in page_tags:
                page_tags.append(t)
        # ajouter tag perso
        if new_tag and new_tag not in page_tags:
            page_tags.append(new_tag)
        st.session_state.tags[page] = page_tags
    st.success(f"Tags appliqués à {len(selected)} pages")

# ---------------- DOWNLOAD JSON ----------------
if st.session_state.tags:
    data = [{"page": page, "tags": tags} for page, tags in st.session_state.tags.items()]
    st.download_button("📥 Télécharger tags.json", json.dumps(data, indent=2, ensure_ascii=False), file_name="tags.json")
