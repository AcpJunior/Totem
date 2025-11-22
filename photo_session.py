import tkinter as tk
from PIL import Image, ImageTk, ImageOps
import time
import threading
import os
import json
import shutil
import subprocess
import re
from datetime import datetime

# Importa os serviços
from camera_service import CameraService
from liveview_service import LiveviewService

class PhotoSession:
    def __init__(self, parent, config_manager, on_complete_callback):
        self.parent = parent
        self.config_manager = config_manager
        self.config = config_manager.config
        self.on_complete_callback = on_complete_callback
        
        # Caminhos
        self.template_dir = "/opt/Totem/templates"
        self.json_path = os.path.join(self.template_dir, "config_card.json")
        self.bg_path = os.path.join(self.template_dir, "background.png")
        self.output_folder = self.config.get('pasta_saida', '/opt/Totem/fotos')
        self.ensure_output_folder()
        
        # Serviços
        self.camera_service = CameraService(config_manager)
        self.liveview_service = LiveviewService(config_manager)
        
        self.load_layout_config()
        
        self.current_slot_index = 0
        self.captured_images = [] 
        self.photos_taken = []
        
        self.create_window()
        
    def ensure_output_folder(self):
        try:
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder, exist_ok=True)
                os.chmod(self.output_folder, 0o777)
        except: pass

    def load_layout_config(self):
        self.layout_data = {
            "slots": [], "countdown_start": 5, "countdown_interval": 3,
            "msg_start": "PREPARE-SE", "msg_end": "FIM!",
            "font_family": "Arial", "font_color": "#ffffff",
            "card_width": 1800, "card_height": 1200
        }
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, 'r') as f:
                    self.layout_data.update(json.load(f))
            except: pass

    def _get_monitor_geometry(self):
        target_name = self.config.get('tela_totem', 'HDMI').lower()
        geo = {'x': 0, 'y': 0, 'w': 800, 'h': 600}
        try:
            output = subprocess.check_output(['xrandr']).decode('utf-8')
            pattern = re.compile(r'^(\S+)\s+connected.*?(\d+)x(\d+)\+(\d+)\+(\d+)', re.MULTILINE)
            monitors = []
            for match in pattern.finditer(output):
                monitors.append({
                    'name': match.group(1).lower(),
                    'w': int(match.group(2)), 'h': int(match.group(3)),
                    'x': int(match.group(4)), 'y': int(match.group(5))
                })
            found = next((m for m in monitors if target_name in m['name']), None)
            if not found and 'hdmi' in target_name:
                found = next((m for m in monitors if m['x'] > 0), None)
            if found: geo = found
            elif monitors: geo = monitors[0]
        except: pass
        return geo['x'], geo['y'], geo['w'], geo['h']

    def create_window(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Totem Tela")
        self.window.configure(bg='black')
        
        x, y, w, h = self._get_monitor_geometry()
        self.window.geometry(f"{w}x{h}+{x}+{y}")
        self.window.update_idletasks()
        self.window.attributes('-fullscreen', True)
        
        self.screen_w = w; self.screen_h = h
        
        # Base do Layout (Resolução do Papel)
        self.layout_w = self.layout_data.get('card_width', 1800)
        self.layout_h = self.layout_data.get('card_height', 1200)
        
        # Fator de escala para mostrar na tela SEM DISTORÇÃO (Fit)
        # Usamos "contain" para garantir que o card inteiro apareça na tela
        self.scale = min(self.screen_w / self.layout_w, self.screen_h / self.layout_h)
        
        # Centralização (Offset)
        self.offset_x = (self.screen_w - (self.layout_w * self.scale)) // 2
        self.offset_y = (self.screen_h - (self.layout_h * self.scale)) // 2

        self.canvas = tk.Canvas(self.window, width=self.screen_w, height=self.screen_h, bg='black', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        self.reset_session()

    def reset_session(self):
        self.current_slot_index = 0
        self.captured_images = []
        self.photos_taken = []
        self.liveview_service.stop_liveview()
        self.canvas.delete("all")
        
        # 1. Fundo (COVER da tela toda)
        # Aqui carregamos a imagem e fazemos ela cobrir a tela para não ficar borda preta
        if os.path.exists(self.bg_path):
            img = Image.open(self.bg_path)
            # Usa ImageOps.fit para preencher a tela (Cover)
            img_cover = ImageOps.fit(img, (self.screen_w, self.screen_h), method=Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(img_cover)
            self.canvas.create_image(self.screen_w//2, self.screen_h//2, anchor="center", image=self.bg_photo, tags="background")
        else:
            self.canvas.create_rectangle(0,0,self.screen_w,self.screen_h, fill="#2c3e50", tags="background")

        # 2. Slots (Baseado no Layout Scaled)
        # Precisamos desenhar o "Card" virtual centralizado na tela
        slots = self.layout_data.get('slots', [])
        for i, slot in enumerate(slots):
            x, y, w, h = self.get_slot_rect_screen(slot)
            
            self.canvas.create_rectangle(x, y, x+w, y+h, fill="white", outline="#bdc3c7", width=2, tags=f"slot_bg_{i}")
            self.canvas.create_text(x + w//2, y + h//2, text=str(i+1), 
                                  font=('Arial', int(50*self.scale), 'bold'), fill="#bdc3c7", tags=f"slot_num_{i}")

    def start_sequence(self):
        self.reset_session()
        slots = self.layout_data.get('slots', [])
        if not slots: return
        self.process_next_slot()

    def process_next_slot(self):
        slots = self.layout_data.get('slots', [])
        if self.current_slot_index >= len(slots):
            self.finish_session()
            return
            
        if self.current_slot_index == 0:
            tempo = self.layout_data.get('countdown_start', 5)
            msg = self.layout_data.get('msg_start', 'PREPARE-SE')
        else:
            tempo = self.layout_data.get('countdown_interval', 3)
            msg = "PRÓXIMA..."
            
        # Liveview
        self.canvas.create_image(self.screen_w//2, self.screen_h//2, anchor="center", tags="liveview_feed")
        
        class SmoothUpdater:
            def __init__(self, session): self.session = session
            def configure(self, image=None):
                if image and self.session.canvas.find_withtag("liveview_feed"):
                    self.session.canvas.itemconfig("liveview_feed", image=image)
            def winfo_width(self): return int(self.session.screen_w * 0.85)
            def winfo_height(self): return int(self.session.screen_h * 0.85)

        updater = SmoothUpdater(self)
        self.liveview_service.start_liveview(updater, lambda m: None)
        self.update_message(msg)
        self.window.after(1500, lambda: self.start_countdown(tempo))

    def start_countdown(self, seconds):
        def count(n):
            if n > 0:
                self.update_message(str(n), color='#f1c40f' if n <= 3 else None)
                self.window.after(1000, lambda: count(n-1))
            else:
                self.update_message("SORRIA!", color='white')
                self.window.after(200, self.capture_photo)
        count(seconds)

    def capture_photo(self):
        self.liveview_service.stop_liveview()
        self.canvas.delete("liveview_feed")
        self.update_message("📸")
        self.window.update()
        
        def on_taken(filepath):
            self.window.after(10, lambda: self.place_photo_in_layout(filepath))
            
        threading.Thread(target=lambda: self.camera_service.take_photo(on_taken), daemon=True).start()

    def place_photo_in_layout(self, temp_path):
        self.update_message("")
        if not os.path.exists(temp_path):
            self.schedule_next()
            return

        try:
            filename = f"foto_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.current_slot_index+1}.jpg"
            final_path = os.path.join(self.output_folder, filename)
            shutil.copy2(temp_path, final_path)
            display_path = final_path
        except: display_path = temp_path

        self.photos_taken.append(display_path)
        slots = self.layout_data.get('slots', [])
        if self.current_slot_index < len(slots):
            slot = slots[self.current_slot_index]
            x, y, w, h = self.get_slot_rect_screen(slot)
            try:
                img = Image.open(display_path)
                # Lógica Cover (Preencher o slot cortando excesso)
                # O usuário quer ver a foto bonita no slot, não barras pretas
                img_cover = ImageOps.fit(img, (w, h), method=Image.Resampling.LANCZOS)
                
                tk_img = ImageTk.PhotoImage(img_cover)
                self.captured_images.append(tk_img)
                
                self.canvas.delete(f"slot_num_{self.current_slot_index}")
                # Desenha centralizado no rect
                self.canvas.create_image(x + w//2, y + h//2, anchor="center", image=tk_img, tags="photo")
                self.canvas.create_rectangle(x, y, x+w, y+h, outline="#2ecc71", width=4, tags="border")
            except: pass

        self.schedule_next()

    def schedule_next(self):
        self.current_slot_index += 1
        self.window.after(1000, self.process_next_slot)

    def update_message(self, text, color=None):
        self.canvas.delete("overlay_text")
        if not text: return
        if not color: color = self.layout_data.get('font_color', 'white')
        font_name = self.layout_data.get('font_family', 'Arial')
        cx, cy = self.screen_w // 2, self.screen_h // 2
        font_cfg = (font_name, 60, 'bold')
        self.canvas.create_text(cx+2, cy+2, text=text, font=font_cfg, fill="black", tags="overlay_text", anchor="center")
        self.canvas.create_text(cx, cy, text=text, font=font_cfg, fill=color, tags="overlay_text", anchor="center")
        self.canvas.tag_raise("overlay_text")

    def finish_session(self):
        card_path = self.generate_final_card_sync()
        msg = self.layout_data.get('msg_end', 'FIM!')
        self.update_message(msg)
        if self.on_complete_callback and card_path:
            self.window.after(0, lambda: self.on_complete_callback(card_path))

    def generate_final_card_sync(self):
        try:
            # Usa a resolução exata do layout
            cw = self.layout_data.get('card_width', 1800)
            ch = self.layout_data.get('card_height', 1200)
            
            if os.path.exists(self.bg_path):
                card = Image.open(self.bg_path).convert("RGBA").resize((cw, ch), Image.Resampling.LANCZOS)
            else:
                card = Image.new("RGBA", (cw, ch), "#2c3e50")

            slots = self.layout_data.get('slots', [])
            for i, p in enumerate(self.photos_taken):
                if i >= len(slots): break
                try:
                    s = slots[i]
                    img = Image.open(p).convert("RGBA")
                    # Fit (Cover) para o arquivo final também
                    img_cover = ImageOps.fit(img, (s['w'], s['h']), method=Image.Resampling.LANCZOS)
                    card.paste(img_cover, (s['x'], s['y']))
                except: pass

            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            fn = f"card_final_{ts}.jpg"
            fp = os.path.join(self.output_folder, fn)
            card.convert("RGB").save(fp, quality=95)
            try: os.chmod(fp, 0o777)
            except: pass
            return fp
        except: return None

    def get_slot_rect_screen(self, slot):
        # Aplica escala E offset para centralizar na tela
        x = int(slot['x'] * self.scale) + self.offset_x
        y = int(slot['y'] * self.scale) + self.offset_y
        w = int(slot['w'] * self.scale)
        h = int(slot['h'] * self.scale)
        return x, y, w, h
    
    def destroy(self):
        try:
            self.liveview_service.stop_liveview()
            self.window.destroy()
        except: pass
