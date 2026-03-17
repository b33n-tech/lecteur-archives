import streamlit as st
import zipfile
import tempfile
import os
import re
import json
from PIL import Image


st.set_page_config(
    page_title="Lecteur annoté",
    layout="wide"
)

st.title("📖 Lecteur annoté")


# -----------------------------
# SESSION STATE INIT
# -----------------------------

if "images" not in st.session_state:
    st.session_state.images = []

if "index" not in st.session_state:
    st.session_state.index = 0

if "zoom" not in st.session_state:
    st.session_state.zoom = 1.0

if "notes" not in st.session_state:
    st.session_state.notes = {}


# -----------------------------
# JSON LOAD / SAVE
# -----------------------------

JSON_PATH = "notes.json"


def load_notes():

    if os.path.exists(JSON_PATH):

        with open(JSON_PATH, "r") as f:
            data = json.load(f)

        notes = {}

        for row in data:
            notes[row["page"]] = row["note"]

        return notes

    return {}


def save_notes():

    data = []

    for page, note in st.session_state.notes.items():

        data.append(
            {
                "page": page,
                "note": note
            }
        )

    with open(JSON_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# load once
if st.session_state.notes == {}:
    st.session_state.notes = load_notes()


# -----------------------------
# uploader
# -----------------------------

zip_file = st.file_uploader(
    "Upload ZIP images",
    type=["zip"]
)


# -----------------------------
# find images
# -----------------------------

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


# -----------------------------
# load zip
# -----------------------------

if zip_file is not None and len(st.session_state.images) == 0:

    tmpdir = tempfile.mkdtemp()

    with zipfile.ZipFile(zip_file, "r") as z:
        z.extractall(tmpdir)

    files = find_images(tmpdir)

    if len(files) == 0:
        st.error("No images")
        st.stop()

    st.session_state.images = files
    st.session_state.index = 0


# -----------------------------
# reader
# -----------------------------

if len(st.session_state.images) > 0:

    images = st.session_state.images
    total = len(images)
    i = st.session_state.index

    # navigation

    col1, col2, col3, col4, col5 = st.columns([1,1,4,1,1])

    with col1:
        if st.button("⏮"):
            st.session_state.index = 0

    with col2:
        if st.button("⬅"):
            if i > 0:
                st.session_state.index -= 1

    with col4:
        if st.button("➡"):
            if i < total - 1:
                st.session_state.index += 1

    with col5:
        if st.button("⏭"):
            st.session_state.index = total - 1

    st.session_state.index = st.slider(
        "Page",
        0,
        total - 1,
        st.session_state.index
    )

    st.session_state.zoom = st.slider(
        "Zoom",
        0.5,
        3.0,
        float(st.session_state.zoom),
        0.1
    )

    i = st.session_state.index

    img_path = images[i]
    page_name = os.path.basename(img_path)

    # layout

    left, right = st.columns([3, 2])

    # ---------------- LEFT IMAGE

    with left:

        st.write(f"{page_name} ({i+1}/{total})")

        img = Image.open(img_path)

        if st.session_state.zoom != 1:

            w, h = img.size

            img = img.resize(
                (
                    int(w * st.session_state.zoom),
                    int(h * st.session_state.zoom)
                )
            )

        st.image(img)

    # ---------------- RIGHT NOTES

    with right:

        st.subheader("Notes")

        current_note = st.session_state.notes.get(page_name, "")

        note = st.text_area(
            "Note pour cette page",
            value=current_note,
            height=300
        )

        if st.button("💾 Sauver note"):

            st.session_state.notes[page_name] = note

            save_notes()

            st.success("Sauvé")
