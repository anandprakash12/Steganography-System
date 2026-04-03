# STEGANOGRAPHY SYSTEM (Hide Data in Images)
import numpy as np
import streamlit as st
from PIL import Image
import tempfile
import base64
import hashlib
from cryptography.fernet import Fernet

# 1. PASSWORD-BASED KEY GENERATION
def generate_key(password):
    return base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())

def encrypt_message(message, password):
    key = generate_key(password)
    cipher = Fernet(key)
    return cipher.encrypt(message.encode())

def decrypt_message(encrypted_data, password):
    key = generate_key(password)
    cipher = Fernet(key)
    return cipher.decrypt(encrypted_data).decode()

# 2. ENCODE (LSB)
def encode_image(image, secret_data):
    data_len = len(secret_data)
    header = format(data_len, '032b')  # 32-bit length
    data = header + ''.join(format(byte, '08b') for byte in secret_data)
    img = np.array(image)
    data_index = 0

    for row in img:
        for pixel in row:
            for i in range(3):
                if data_index < len(data):
                    pixel[i] = (int(pixel[i]) & 254) | int(data[data_index])
                    data_index += 1
    return img

# 3. DECODE (LSB)
def decode_image(image):
    img = np.array(image)
    binary_data = ""
    for row in img:
        for pixel in row:
            for i in range(3):
                binary_data += str(pixel[i] & 1)
    # Extract length first (32 bits)
    data_len = int(binary_data[:32], 2)
    binary_data = binary_data[32:]
    data_bytes = []
    for i in range(0, data_len * 8, 8):
        byte = binary_data[i:i+8]
        data_bytes.append(int(byte, 2))
    return bytes(data_bytes)

# 4. PSNR CALCULATION
def calculate_psnr(original, stego):
    original = np.array(original)
    stego = np.array(stego)
    mse = np.mean((original - stego) ** 2)
    if mse == 0:
        return 100
    return 20 * np.log10(255.0 / np.sqrt(mse))

# 5. STREAMLIT UI
st.title("Steganography System")
option = st.selectbox("Choose Option", ["Encode", "Decode"])

# ENCODE
if option == "Encode":
    uploaded_file = st.file_uploader("Upload Image", type=["png"])
    message = st.text_area("Enter Secret Message")
    password = st.text_input("Enter Password", type="password")

    if st.button("Hide Message"):
        if uploaded_file and message and password:
            # image = Image.open(uploaded_file)
            image = Image.open(uploaded_file).convert("RGB")
            # Encrypt with password
            encrypted = encrypt_message(message, password)
            # Encode
            stego_img = encode_image(image, encrypted)
            # PSNR
            psnr_value = calculate_psnr(image, stego_img)
            st.success("Message Hidden Successfully!")
            st.write(f"PSNR: {psnr_value:.2f} dB")
            st.image(stego_img, caption="Stego Image")
            # Save file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            # cv2.imwrite(temp_file.name, stego_img)
            Image.fromarray(stego_img).save(temp_file.name)
            with open(temp_file.name, "rb") as f:
                st.download_button("Download Image", f, file_name="stego.png")
        else:
            st.warning("Please fill all fields")

# DECODE
elif option == "Decode":
    uploaded_file = st.file_uploader("Upload Stego Image", type=["png"])
    password = st.text_input("Enter Password", type="password")

    if st.button("Extract Message"):
        if uploaded_file and password:
            # image = Image.open(uploaded_file)
            image = Image.open(uploaded_file).convert("RGB")
            encrypted_data = decode_image(image)
            try:
                decrypted = decrypt_message(encrypted_data, password)
                st.success(f"Hidden Message: {decrypted}")
            except:
                st.error("Failed to decrypt message (Wrong password or image)")
        else:
            st.warning("Please upload image and enter password")