# =========================================
# ULTIMATE STEGANOGRAPHY SYSTEM
# =========================================

import numpy as np
import streamlit as st
from PIL import Image
import tempfile
import base64
import hashlib
from cryptography.fernet import Fernet

# =========================================
# 1. KEY GENERATION
# =========================================
def generate_key(password):
    return base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())

def encrypt_data(data, password):
    key = generate_key(password)
    cipher = Fernet(key)
    return cipher.encrypt(data)

def decrypt_data(data, password):
    key = generate_key(password)
    cipher = Fernet(key)
    return cipher.decrypt(data)

# =========================================
# 2. CAPACITY CHECK
# =========================================
def check_capacity(image, data_length):
    max_bytes = image.size[0] * image.size[1] * 3 // 8
    return data_length <= max_bytes

# =========================================
# 3. ENCODE FUNCTION
# =========================================
def encode_image(image, secret_data):

    # Add hash for integrity check
    hash_val = hashlib.sha256(secret_data).digest()
    final_data = hash_val + secret_data

    data_len = len(final_data)
    header = format(data_len, '032b')

    binary_data = header + ''.join(format(byte, '08b') for byte in final_data)

    img = np.array(image)
    data_index = 0

    for row in img:
        for pixel in row:
            for i in range(3):
                if data_index < len(binary_data):
                    pixel[i] = (int(pixel[i]) & 254) | int(binary_data[data_index])
                    data_index += 1

    return img

# =========================================
# 4. DECODE FUNCTION
# =========================================
def decode_image(image):

    img = np.array(image)
    binary_data = ""

    for row in img:
        for pixel in row:
            for i in range(3):
                binary_data += str(pixel[i] & 1)

    data_len = int(binary_data[:32], 2)
    binary_data = binary_data[32:]

    data_bytes = []
    for i in range(0, data_len * 8, 8):
        byte = binary_data[i:i+8]
        data_bytes.append(int(byte, 2))

    extracted = bytes(data_bytes)

    # Separate hash and data
    hash_original = extracted[:32]
    actual_data = extracted[32:]

    # Verify integrity
    if hashlib.sha256(actual_data).digest() != hash_original:
        raise ValueError("Data integrity check failed")

    return actual_data

# =========================================
# 5. STREAMLIT UI
# =========================================
st.set_page_config(page_title="Ultimate Steganography", layout="centered")

st.title("🕵️ Ultimate Steganography System")

option = st.radio("Select Mode", ["Encode", "Decode"])

# =========================================
# ENCODE
# =========================================
if option == "Encode":

    uploaded_image = st.file_uploader("Upload Cover Image", type=["png"])
    message = st.text_area("Enter Secret Message (Optional)")
    file_upload = st.file_uploader("Or Upload File", type=None)
    password = st.text_input("Enter Password", type="password")

    if st.button("🔐 Hide Data"):

        if uploaded_image and password and (message or file_upload):

            image = Image.open(uploaded_image).convert("RGB")

            if file_upload:
                secret_data = file_upload.read()
            else:
                secret_data = message.encode()

            encrypted = encrypt_data(secret_data, password)

            # Capacity check
            if not check_capacity(image, len(encrypted)):
                st.error("❌ Image too small for this data")
            else:
                with st.spinner("Encoding..."):
                    stego_img = encode_image(image, encrypted)

                st.success("✅ Data Hidden Successfully!")
                st.image(stego_img)

                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                Image.fromarray(stego_img).save(temp_file.name)

                with open(temp_file.name, "rb") as f:
                    st.download_button("⬇️ Download Stego Image", f, file_name="stego.png")

        else:
            st.warning("⚠️ Fill all fields")

# =========================================
# DECODE
# =========================================
elif option == "Decode":

    uploaded_image = st.file_uploader("Upload Stego Image", type=["png"])
    password = st.text_input("Enter Password", type="password")

    if st.button("🔍 Extract Data"):

        if uploaded_image and password:

            image = Image.open(uploaded_image).convert("RGB")

            try:
                with st.spinner("Decoding..."):
                    encrypted_data = decode_image(image)
                    decrypted_data = decrypt_data(encrypted_data, password)

                try:
                    text = decrypted_data.decode()
                    st.success(f"🔓 Message: {text}")
                except:
                    st.success("📁 File Extracted Successfully!")

                    st.download_button(
                        "⬇️ Download File",
                        decrypted_data,
                        file_name="hidden_file"
                    )

            except Exception as e:
                st.error("❌ Wrong password / corrupted image")

        else:
            st.warning("⚠️ Upload image and enter password")