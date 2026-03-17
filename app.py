import streamlit as st
import zipfile
import tempfile
import os
from PIL import Image

st.set_page_config(
    page_title="Lecteur d'images",
    layout="wide"
)

st.title("📖 Lecteur de pages JPG")

zip_file = st.file_uploader(
    "Upload zip contenant les pages JPG",
    type=["zip"]
)

if zip_file:

    if "images" not in st.session_state:

        tmpdir = tempfile.mkdtemp()

        with zipfile.ZipFile(zip_file, "r") as z:
            z.extractall(tmpdir)

        files = []

        for f in os.listdir(tmpdir):
            if f.lower().endswith(".jpg") or f.lower().endswith(".jpeg"):
                files.append(f)

        files.sort()

        st.session_state.images = files
        st.session_state.dir = tmpdir
        st.session_state.index = 0

    images = st.session_state.images
    folder = st.session_state.dir
    i = st.session_state.index

    col1, col2, col3 = st.columns([1,6,1])

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

    img_path = os.path.join(folder, images[i])

    img = Image.open(img_path)

    st.image(img, use_container_width=True)
