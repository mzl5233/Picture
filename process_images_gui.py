# =================================================================================
#
# Python Image Batch Processing Program (GUI Version with Progress Bar)
#
# Features:
# - Modern GUI interface with tkinter
# - Real-time progress bar
# - File selection dialog
# - Processing status display
# - Error handling and user feedback
#
# =================================================================================

import os
import sys
import random
import threading
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

# =================================================================================
# ==================== User Configuration Area ====================
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
# ==================== Resource Path Processing Function ====================
# =================================================================================

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Font file path configuration ---
FONT_NAME = "arial.ttf"
FONT_PATH = resource_path(FONT_NAME)

# =================================================================================
# ==================== Image Processing Functions ====================
# =================================================================================

def add_noise(image, amount=0.5):
    img_arr = np.array(image)
    noise = np.random.normal(0, amount * 2.55, img_arr.shape)
    noisy_arr = np.clip(img_arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(noisy_arr)

def process_image(input_path, output_path):
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
                return False

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
        return False

# =================================================================================
# ==================== GUI Application Class ====================
# =================================================================================

class ImageProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OZON图片批处理工具")
        self.root.geometry("700x650")
        self.root.resizable(True, True)
        
        # 设置样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 水印设置变量
        self.watermark_content = tk.StringVar(value=TEXT_WATERMARK_CONTENT)
        self.watermark_opacity = tk.IntVar(value=TEXT_WATERMARK_OPACITY)
        self.watermark_font_size = tk.IntVar(value=TEXT_WATERMARK_FONT_SIZE)
        self.watermark_color_r = tk.IntVar(value=TEXT_WATERMARK_COLOR[0])
        self.watermark_color_g = tk.IntVar(value=TEXT_WATERMARK_COLOR[1])
        self.watermark_color_b = tk.IntVar(value=TEXT_WATERMARK_COLOR[2])
        
        self.setup_ui()
        self.processing = False
        
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="OZON图片批处理工具", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 水印设置面板
        self.setup_watermark_panel(main_frame, 1)
        
        # 文件夹选择
        ttk.Label(main_frame, text="选择图片文件夹:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.folder_var = tk.StringVar()
        folder_entry = ttk.Entry(main_frame, textvariable=self.folder_var, width=50)
        folder_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)
        
        browse_btn = ttk.Button(main_frame, text="浏览", command=self.browse_folder)
        browse_btn.grid(row=2, column=2, pady=5)
        
        # 开始处理按钮
        self.process_btn = ttk.Button(main_frame, text="开始处理", command=self.start_processing)
        self.process_btn.grid(row=3, column=0, columnspan=3, pady=20)
        
        # 进度条
        ttk.Label(main_frame, text="处理进度:").grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        self.progress = ttk.Progressbar(main_frame, length=400, mode='determinate')
        self.progress.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # 状态标签
        self.status_var = tk.StringVar(value="等待开始...")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.grid(row=6, column=0, columnspan=3, pady=5)
        
        # 日志显示区域
        ttk.Label(main_frame, text="处理日志:").grid(row=7, column=0, sticky=tk.W, pady=(10, 5))
        self.log_text = ScrolledText(main_frame, height=12, width=70)
        self.log_text.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 配置行权重
        main_frame.rowconfigure(8, weight=1)
        
    def setup_watermark_panel(self, parent, row):
        """设置水印控制面板"""
        # 水印设置标题
        watermark_frame = ttk.LabelFrame(parent, text="水印设置", padding="10")
        watermark_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        watermark_frame.columnconfigure(1, weight=1)
        
        # 水印文字
        ttk.Label(watermark_frame, text="水印文字:").grid(row=0, column=0, sticky=tk.W, pady=5)
        watermark_entry = ttk.Entry(watermark_frame, textvariable=self.watermark_content, width=30)
        watermark_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)
        
        # 水印透明度
        ttk.Label(watermark_frame, text="透明度(%):").grid(row=1, column=0, sticky=tk.W, pady=5)
        opacity_scale = ttk.Scale(watermark_frame, from_=1, to=100, variable=self.watermark_opacity, 
                                 orient=tk.HORIZONTAL, length=200)
        opacity_scale.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)
        opacity_label = ttk.Label(watermark_frame, textvariable=self.watermark_opacity)
        opacity_label.grid(row=1, column=2, padx=(5, 0), pady=5)
        
        # 字体大小
        ttk.Label(watermark_frame, text="字体大小:").grid(row=2, column=0, sticky=tk.W, pady=5)
        font_size_spinbox = ttk.Spinbox(watermark_frame, from_=8, to=72, textvariable=self.watermark_font_size, 
                                       width=10)
        font_size_spinbox.grid(row=2, column=1, sticky=tk.W, padx=(5, 5), pady=5)
        
        # 水印颜色
        ttk.Label(watermark_frame, text="水印颜色:").grid(row=3, column=0, sticky=tk.W, pady=5)
        color_frame = ttk.Frame(watermark_frame)
        color_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)
        
        # R值
        ttk.Label(color_frame, text="R:").grid(row=0, column=0, padx=(0, 2))
        r_spinbox = ttk.Spinbox(color_frame, from_=0, to=255, textvariable=self.watermark_color_r, width=5)
        r_spinbox.grid(row=0, column=1, padx=(0, 5))
        
        # G值
        ttk.Label(color_frame, text="G:").grid(row=0, column=2, padx=(5, 2))
        g_spinbox = ttk.Spinbox(color_frame, from_=0, to=255, textvariable=self.watermark_color_g, width=5)
        g_spinbox.grid(row=0, column=3, padx=(0, 5))
        
        # B值
        ttk.Label(color_frame, text="B:").grid(row=0, column=4, padx=(5, 2))
        b_spinbox = ttk.Spinbox(color_frame, from_=0, to=255, textvariable=self.watermark_color_b, width=5)
        b_spinbox.grid(row=0, column=5, padx=(0, 5))
        
        # 颜色预览
        self.color_preview = tk.Canvas(color_frame, width=30, height=20, bg='gray')
        self.color_preview.grid(row=0, column=6, padx=(10, 0))
        
        # 绑定颜色更新事件
        self.watermark_color_r.trace('w', self.update_color_preview)
        self.watermark_color_g.trace('w', self.update_color_preview)
        self.watermark_color_b.trace('w', self.update_color_preview)
        
        # 初始化颜色预览
        self.update_color_preview()
        
    def update_color_preview(self, *args):
        """更新颜色预览"""
        try:
            r = self.watermark_color_r.get()
            g = self.watermark_color_g.get()
            b = self.watermark_color_b.get()
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.color_preview.configure(bg=color)
        except:
            pass
        
    def browse_folder(self):
        folder_path = filedialog.askdirectory(title="请选择要处理的图片文件夹")
        if folder_path:
            self.folder_var.set(folder_path)
            self.log_message(f"已选择文件夹: {folder_path}")
            
    def log_message(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def start_processing(self):
        if self.processing:
            return
            
        folder_path = self.folder_var.get().strip()
        if not folder_path:
            messagebox.showerror("错误", "请先选择图片文件夹！")
            return
            
        if not os.path.exists(folder_path):
            messagebox.showerror("错误", "选择的文件夹不存在！")
            return
            
        # 在新线程中处理图片
        self.processing = True
        self.process_btn.config(state='disabled')
        self.progress['value'] = 0
        
        thread = threading.Thread(target=self.process_images, args=(folder_path,))
        thread.daemon = True
        thread.start()
        
    def process_images(self, input_dir):
        try:
            output_dir = os.path.join(input_dir, OUTPUT_SUBFOLDER_NAME)
            os.makedirs(output_dir, exist_ok=True)
            
            file_list = [f for f in os.listdir(input_dir) if f.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS)]
            
            if not file_list:
                self.root.after(0, lambda: messagebox.showwarning("警告", "在选择的文件夹中没有找到支持的图片文件！"))
                return
                
            total_files = len(file_list)
            processed_files = 0
            successful_files = 0
            
            self.root.after(0, lambda: self.status_var.set(f"开始处理 {total_files} 张图片..."))
            self.root.after(0, lambda: self.log_message(f"找到 {total_files} 张图片，开始处理..."))
            
            for i, filename in enumerate(file_list):
                if not self.processing:  # 检查是否被取消
                    break
                    
                input_file_path = os.path.join(input_dir, filename)
                output_filename = os.path.splitext(filename)[0] + '.jpg'
                output_file_path = os.path.join(output_dir, output_filename)
                
                self.root.after(0, lambda f=filename: self.status_var.set(f"正在处理: {f}"))
                
                if self.process_single_image(input_file_path, output_file_path):
                    successful_files += 1
                    self.root.after(0, lambda f=filename: self.log_message(f"✓ 成功处理: {f}"))
                else:
                    self.root.after(0, lambda f=filename: self.log_message(f"✗ 处理失败: {f}"))
                
                processed_files += 1
                progress_value = (processed_files / total_files) * 100
                self.root.after(0, lambda v=progress_value: self.progress.config(value=v))
                
            # 处理完成
            self.root.after(0, lambda: self.status_var.set(f"处理完成！成功: {successful_files}/{total_files}"))
            self.root.after(0, lambda: self.log_message(f"\n=== 处理完成 ==="))
            self.root.after(0, lambda: self.log_message(f"成功处理: {successful_files} 张图片"))
            self.root.after(0, lambda: self.log_message(f"处理失败: {total_files - successful_files} 张图片"))
            self.root.after(0, lambda: self.log_message(f"结果保存在: {output_dir}"))
            
            if successful_files > 0:
                self.root.after(0, lambda: messagebox.showinfo("完成", f"图片处理完成！\n成功处理: {successful_files} 张\n结果保存在: {output_dir}"))
                
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"处理过程中发生错误: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("错误", f"处理过程中发生错误:\n{str(e)}"))
        finally:
            self.processing = False
            self.root.after(0, lambda: self.process_btn.config(state='normal'))
    
    def process_single_image(self, input_path, output_path):
        """处理单张图片，使用GUI设置的水印参数"""
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
                    return False

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
                    font = ImageFont.truetype(FONT_PATH, self.watermark_font_size.get())
                except IOError:
                    font = ImageFont.load_default()

                # 使用GUI设置的水印参数
                watermark_text = self.watermark_content.get()
                text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
                text_w = text_bbox[2] - text_bbox[0]
                text_h = text_bbox[3] - text_bbox[1]

                margin = 20
                text_pos = (target_w - text_w - margin, target_h - text_h - margin)

                # 使用GUI设置的颜色和透明度
                # 修正透明度计算：低透明度值应该产生更淡的颜色
                # 透明度百分比越高，水印越明显；越低，水印越淡
                alpha_value = int(255 * (self.watermark_opacity.get() / 100.0))
                color_r = self.watermark_color_r.get()
                color_g = self.watermark_color_g.get()
                color_b = self.watermark_color_b.get()
                
                # 对于低透明度，需要调整颜色使其更淡
                if self.watermark_opacity.get() < 10:  # 如果透明度小于10%
                    # 将颜色向白色方向混合，使水印更淡
                    blend_factor = self.watermark_opacity.get() / 10.0  # 0.1 到 1.0
                    color_r = int(color_r * blend_factor + 255 * (1 - blend_factor))
                    color_g = int(color_g * blend_factor + 255 * (1 - blend_factor))
                    color_b = int(color_b * blend_factor + 255 * (1 - blend_factor))
                
                text_color_with_alpha = (color_r, color_g, color_b, alpha_value)
                
                draw.text(text_pos, watermark_text, font=font, fill=text_color_with_alpha)

                final_image.convert("RGB").save(output_path, "JPEG", quality=95)
                return True

        except Exception as e:
            return False

# =================================================================================
# ==================== Main Entry Point ====================
# =================================================================================

def main():
    root = tk.Tk()
    app = ImageProcessorGUI(root)
    
    # 设置窗口图标（如果有的话）
    try:
        root.iconbitmap(default="icon.ico")
    except:
        pass
    
    root.mainloop()

if __name__ == "__main__":
    main() 