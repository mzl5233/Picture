# =================================================================================
#
# Python Image Batch Processing Program (V23 - Python Syntax Corrected Version)
#
# Update Log:
# - V23.0: Fixed syntax errors in all comments in the script (changed // to #) to address
#          The "SyntaxError" issue that occurs when packaging with PyInstaller.
#
# =================================================================================

import os
import sys
import random
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import numpy as np
from tqdm import tqdm
import tkinter as tk
from tkinter import filedialog

# =================================================================================
# ==================== User Configuration Area (You can modify here) ====================
# =================================================================================

# --- Text Watermark Configuration ---
TEXT_WATERMARK_CONTENT = "Kaqiusha"
TEXT_WATERMARK_OPACITY = 3
TEXT_WATERMARK_FONT_SIZE = 24
TEXT_WATERMARK_COLOR = (128, 128, 128)
OUTPUT_SUBFOLDER_NAME = "JPEG-Treated-Python"

# --- Supported image formats ---
SUPPORTED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.tif', '.psd', '.webp')

# --- Size library configuration ---
SIZES_3_4 = [
    (900, 1200), (1200, 1600), (1500, 2000)
]
SIZES_1_1 = [
    (800, 800), (1000, 1000), (1200, 1200), (1600, 1600)
]

# --- Performance optimization parameters ---
MAX_WORKING_DIMENSION = 3000

# =================================================================================
# ==================== Resource Path Processing Function (Key to Packaging) ====================
# =================================================================================

def resource_path(relative_path):
    # Get the absolute path of the resource, compatible with both development mode and the mode after PyInstaller packaging
    try:
        # PyInstaller creates a temporary folder and stores the path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- IMPORTANT: Font file path configuration ---
FONT_NAME = "arial.ttf"
FONT_PATH = resource_path(FONT_NAME)

# =================================================================================
# ==================== Main program logic (no need to modify) ====================
# =================================================================================

def add_noise(image, amount=0.5):
    # Add Gaussian noise to the image
    img_arr = np.array(image)
    noise = np.random.normal(0, amount * 2.55, img_arr.shape)
    noisy_arr = np.clip(img_arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy_arr)

def process_image(input_path, output_path):
    # Core function for processing a single image
    try:
        with Image.open(input_path) as img:
            img = img.convert("RGBA")
            if img.width > MAX_WORKING_DIMENSION or img.height > MAX_WORKING_DIMENSION:
                img.thumbnail((MAX_WORKING_DIMENSION, MAX_WORKING_DIMENSION), Image.Resampling.LANCZOS)

            original_ratio = img.width / img.height
            if abs(original_ratio - 0.75) < 0.02:
                target_sizes = SIZES_3_4
            elif abs(original_ratio - 1.0) < 0.02:
                target_sizes = SIZES_1_1
            else:
                return 

            target_w, target_h = random.choice(target_sizes)
            img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)

            enhancer = ImageEnhance.Brightness(img)
            factor = 1 + (random.randint(-3, 3) / 100.0)
            base_layer = enhancer.enhance(factor)

            base_layer = add_noise(base_layer, amount=0.5)

            rotated_layer = base_layer.copy()
            rotated_layer = rotated_layer.rotate(random.uniform(-1, 1), expand=True, resample=Image.Resampling.BICUBIC)

            padding = 0.98
            scale_ratio = min((target_w * padding) / rotated_layer.width, (target_h * padding) / rotated_layer.height)
            new_size = (int(rotated_layer.width * scale_ratio), int(rotated_layer.height * scale_ratio))
            rotated_layer = rotated_layer.resize(new_size, Image.Resampling.LANCZOS)

            final_image = Image.new("RGBA", (target_w, target_h), (255, 255, 255, 255))

            paste_x = (target_w - rotated_layer.width) // 2
            paste_y = (target_h - rotated_layer.height) // 2
            final_image.paste(rotated_layer, (paste_x, paste_y), rotated_layer)

            draw = ImageDraw.Draw(final_image)
            try:
                font = ImageFont.truetype(FONT_PATH, TEXT_WATERMARK_FONT_SIZE)
            except IOError:
                font = ImageFont.load_default()

            text_bbox = draw.textbbox((0, 0), TEXT_WATERMARK_CONTENT, font=font)
            text_w = text_bbox[2] - text_bbox[0]
            text_h = text_bbox[3] - text_bbox[1]

            margin = 20
            text_pos = (target_w - text_w - margin, target_h - text_h - margin)

            opacity_value = int(255 * (TEXT_WATERMARK_OPACITY / 100.0))
            text_color_with_alpha = TEXT_WATERMARK_COLOR + (opacity_value,)
            draw.text(text_pos, TEXT_WATERMARK_CONTENT, font=font, fill=text_color_with_alpha)

            final_image.convert("RGB").save(output_path, "JPEG", quality=95)
            return True

    except Exception as e:
        print(f"\nError occurred while processing file {os.path.basename(input_path)}: {e}")
        return False

def select_folder():
    # Open a dialog box to allow the user to select a folder
    root = tk.Tk()
    root.withdraw() 
    folder_path = filedialog.askdirectory(title="Please select the image folder to process")
    return folder_path

if __name__ == "__main__":
    input_dir = select_folder()
    if not input_dir:
        print("No folder selected, the program has exited.")
        sys.exit()

    output_dir = os.path.join(input_dir, OUTPUT_SUBFOLDER_NAME)
    os.makedirs(output_dir, exist_ok=True)

    image_extensions = SUPPORTED_IMAGE_EXTENSIONS
    file_list = [f for f in os.listdir(input_dir) if f.lower().endswith(image_extensions)]

    if not file_list:
        print("No supported image files were found in the selected folder!")
        sys.exit()

    print(f"Found {len(file_list)} images. Processing will start soon...")

    for filename in tqdm(file_list, desc="Processing Progress"):
        input_file_path = os.path.join(input_dir, filename)
        output_filename = os.path.splitext(filename)[0] + '.jpg'
        output_file_path = os.path.join(output_dir, output_filename)

        process_image(input_file_path, output_file_path)

    print("\nAll images have been processed!")
    print(f"Results have been saved to: {output_dir}")