import streamlit as st
import zipfile
import tempfile
import os
import re
import json
import io
import pandas as pd
from PIL import Image

st.set_page_config(page_title="Mosaïque Tagger PRO", layout="wide")
st.title("📚 Tagging et export filtré")

# ---------------- STATE INIT ----------------
def init_state(key, value):
    if key not in st.session_state:
        st.session_state[key] = value

init_state("images", [])
init_state("selected", set())
init_state("tags", {})

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
    st.session_state.tmpdir = tmpdir

images = st.session_state.images
total = len(images)

# ---------------- FILTRAGE ----------------
filter_tag = st.selectbox("Afficher uniquement les pages avec tag", [""] + BASE_TAGS, index=0)

if filter_tag:
    filtered_images = [img for img in images if filter_tag in st.session_state.tags.get(os.path.basename(img),[])]
else:
    filtered_images = images

st.write(f"{len(filtered_images)} pages affichées sur {total}")

# ---------------- CONFIG MOSAÏQUE ----------------
cols_option = st.selectbox("Nombre d'images par page", [4,9,16,20,25,36,60], index=1)
cols_per_row = int(cols_option ** 0.5)
start_idx = st.number_input("Indice de départ pour la mosaïque", min_value=0, max_value=max(0,len(filtered_images)-1), value=0, step=cols_option)
end_idx = min(start_idx+cols_option, len(filtered_images))
current_images = filtered_images[start_idx:end_idx]

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
        for t in selected_tags:
            if t not in page_tags:
                page_tags.append(t)
        if new_tag and new_tag not in page_tags:
            page_tags.append(new_tag)
        st.session_state.tags[page] = page_tags
    st.success(f"Tags appliqués à {len(selected)} pages")

# ---------------- EXPORT ----------------
st.subheader("Exporter pages filtrées et tags")

if st.button("📥 Export ZIP + CSV + XLSX + JSON"):
    if not selected:
        st.warning("Sélectionnez au moins une page pour l'export")
    else:
        # dossier temporaire
        export_dir = tempfile.mkdtemp()
        for page in selected:
            src = [img for img in images if os.path.basename(img)==page][0]
            dst = os.path.join(export_dir, page)
            Image.open(src).save(dst)

        # JSON
        data_json = [{"page": page, "tags": st.session_state.tags.get(page,[])} for page in selected]
        json_bytes = json.dumps(data_json, indent=2, ensure_ascii=False).encode("utf-8")

        # CSV
        df = pd.DataFrame(data_json)
        csv_bytes = df.to_csv(index=False).encode("utf-8")

        # XLSX
        xlsx_buffer = io.BytesIO()
        df.to_excel(xlsx_buffer, index=False)
        xlsx_buffer.seek(0)

        # ZIP final
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            # ajouter images
            for file in os.listdir(export_dir):
                zipf.write(os.path.join(export_dir, file), arcname=file)
            # ajouter fichiers recap
            zipf.writestr("tags.json", json_bytes)
            zipf.writestr("tags.csv", csv_bytes)
            zipf.writestr("tags.xlsx", xlsx_buffer.read())
        zip_buffer.seek(0)
        st.download_button("Télécharger ZIP complet", zip_buffer, file_name="pages_tagged.zip")
