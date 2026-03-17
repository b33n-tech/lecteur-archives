import streamlit as st
import zipfile
import tempfile
import os
import re
import json
from PIL import Image

st.set_page_config(page_title="Lecteur archiviste avancé", layout="wide")
st.title("📖 Lecteur annoté + tags + frise")

# ---------------- STATE INIT ----------------
def init_state(key, value):
    if key not in st.session_state:
        st.session_state[key] = value

init_state("images", [])
init_state("index", 0)
init_state("zoom", 1.0)
init_state("notes", {})
init_state("tags", {})

NOTES_JSON = "notes.json"
TAGS_JSON = "tags.json"

# ---------------- LOAD / SAVE ----------------
def load_json(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
        d = {}
        for row in data:
            if "note" in row:
                d[row["page"]] = row["note"]
            elif "tags" in row:
                d[row["page"]] = row["tags"]
        return d
    return {}

def save_notes():
    data = [{"page": page, "note": note} for page, note in st.session_state.notes.items()]
    with open(NOTES_JSON, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def save_tags():
    data = [{"page": page, "tags": tags} for page, tags in st.session_state.tags.items()]
    with open(TAGS_JSON, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if st.session_state.notes == {}:
    st.session_state.notes = load_json(NOTES_JSON)
if st.session_state.tags == {}:
    st.session_state.tags = load_json(TAGS_JSON)

# ---------------- TAGS BASE ----------------
BASE_TAGS = ["Titre", "Planche/illustration", "Index", "Table", "Chapitre", "Page blanche", "Autre"]
TAG_COLORS = {
    "Titre": "#FF6F61",
    "Planche/illustration": "#6B5B95",
    "Index": "#88B04B",
    "Table": "#F7CAC9",
    "Chapitre": "#92A8D1",
    "Page blanche": "#F1E05A",
    "Autre": "#D2691E"
}

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
    st.session_state.index = 0

# ---------------- READER ----------------
if len(st.session_state.images) > 0:
    images = st.session_state.images
    total = len(images)
    i = st.session_state.index

    # -------- NAVIGATION --------
    col1, col2, col3, col4, col5 = st.columns([1,1,4,1,1])
    with col1:
        if st.button("⏮"): st.session_state.index = 0
    with col2:
        if st.button("⬅") and i>0: st.session_state.index -=1
    with col4:
        if st.button("➡") and i<total-1: st.session_state.index +=1
    with col5:
        if st.button("⏭"): st.session_state.index = total-1

    st.session_state.index = st.slider("Page", 0, total-1, st.session_state.index)
    st.session_state.zoom = st.slider("Zoom", 0.5, 3.0, float(st.session_state.zoom), 0.1)
    i = st.session_state.index

    img_path = images[i]
    page = os.path.basename(img_path)

    left, mid, right = st.columns([3,2,2])

    # -------- IMAGE LEFT --------
    with left:
        st.write(f"{page} ({i+1}/{total})")
        img = Image.open(img_path)
        if st.session_state.zoom != 1:
            w,h = img.size
            img = img.resize((int(w*st.session_state.zoom), int(h*st.session_state.zoom)))
        st.image(img)

    # -------- NOTES MID --------
    with mid:
        st.subheader("Notes")
        note = st.text_area("Note pour cette page", value=st.session_state.notes.get(page,""), height=300)
        if st.button("💾 Sauver note"):
            st.session_state.notes[page] = note
            save_notes()
            st.success("Note sauvegardée !")
        if os.path.exists(NOTES_JSON):
            with open(NOTES_JSON, "r") as f:
                st.download_button("Télécharger notes.json", f, file_name="notes.json")

    # -------- TAGS RIGHT --------
    with right:
        st.subheader("Tags")
        current_tags = st.session_state.tags.get(page, [])
        selected = st.multiselect("Tags existants", BASE_TAGS, default=[t for t in current_tags if t in BASE_TAGS])
        new_tag = st.text_input("Ajouter tag personnalisé")
        if st.button("💾 Sauver tags"):
            tags = selected.copy()
            if new_tag: tags.append(new_tag)
            st.session_state.tags[page] = tags
            save_tags()
            st.success("Tags sauvegardés !")
        if os.path.exists(TAGS_JSON):
            with open(TAGS_JSON, "r") as f:
                st.download_button("Télécharger tags.json", f, file_name="tags.json")

    # -------- FRISE DES TAGS --------
    st.subheader("Frise des tags")
    frise_cols = st.columns(total)
    for idx, col in enumerate(frise_cols):
        page_name = os.path.basename(images[idx])
        tags = st.session_state.tags.get(page_name, [])
        color = "#CCCCCC"
        if tags:
            # si plusieurs tags, on prend la couleur du premier tag
            color = TAG_COLORS.get(tags[0], "#000000")
        if col.button(" ", key=f"frise_{idx}", help=", ".join(tags)):
            st.session_state.index = idx
        col.markdown(f"""<div style="width:100%; height:15px; background-color:{color};"></div>""", unsafe_allow_html=True)
