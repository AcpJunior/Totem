import json
import os
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import glob
import re
from threading import Thread
import time

class ConfigManager:
    def __init__(self):
        self.config_dir = "/opt/Totem/config"
        self.config_file = os.path.join(self.config_dir, "config.json")
        self.default_config = {
            "camera_principal": "",
            "liveview_fonte": "camera",
            "camera_liveview": "",
            "pasta_saida": "/opt/Totem/fotos",
            "usar_impressora": False,
            "impressora_selecionada": "",
            "tela_totem": "principal",
            "orientacao_tela": "paisagem",
            "resolucao_camera": "1280x720"
        }
        self.ensure_config_dir()
        self.load_config()
    
    def ensure_config_dir(self):
        """Garante que o diretório de config existe"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)
    
    def load_config(self):
        """Carrega as configurações do arquivo JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                self.config = {**self.default_config, **loaded_config}
            else:
                self.config = self.default_config.copy()
                self.save_config()
        except Exception as e:
            print(f"Erro ao carregar config: {e}")
            self.config = self.default_config.copy()
            self.save_config()
        return self.config
    
    def save_config(self):
        """Salva as configurações no arquivo JSON"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar config: {e}")
            return False
    
    def get_cameras_usb(self):
        """Detecta câmeras conectadas"""
        cameras = []
        # 1. DSLR via gphoto2
        try:
            result = subprocess.run(['gphoto2', '--auto-detect'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'usb:' in line.lower() and not line.startswith('---'):
                        parts = line.split()
                        model = ' '.join(parts[:-1])
                        cameras.append({'device': 'gphoto2', 'nome': f"DSLR: {model}", 'tipo': 'dslr', 'display': f"📷 DSLR: {model}"})
        except: pass
        
        # 2. Webcams
        try:
            video_devices = sorted(glob.glob("/dev/video*"))
            for device in video_devices:
                try:
                    result = subprocess.run(['v4l2-ctl', '--device', device, '--info'], capture_output=True, text=True, timeout=2)
                    if result.returncode == 0 and 'Capture' in result.stdout:
                        cameras.append({'device': device, 'nome': device, 'tipo': 'webcam', 'display': f"📹 Webcam ({device})"})
                except: pass
        except: pass
        
        return cameras if cameras else [{'tipo': 'none', 'display': '❌ Nenhuma câmera detectada'}]
    
    def get_telas(self):
        """Obtém telas via xrandr"""
        telas = []
        try:
            result = subprocess.run(['xrandr'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if ' connected' in line:
                    parts = line.split()
                    telas.append({'nome': parts[0], 'display': f"🖥️ {parts[0]}"})
        except: pass
        return telas if telas else [{'nome': 'HDMI-1', 'display': '🖥️ HDMI-1 (Padrão)'}]
    
    def get_impressoras(self):
        """Obtém impressoras via lpstat"""
        impressoras = []
        try:
            result = subprocess.run(['lpstat', '-a'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if line.strip():
                    impressoras.append(line.split()[0])
        except: pass
        return impressoras if impressoras else ['Nenhuma impressora encontrada']

class ConfigWindow:
    def __init__(self, parent):
        self.parent = parent
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.create_window()
    
    def create_window(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Configurações do Totem")
        self.window.attributes('-fullscreen', True)
        self.window.configure(bg='#f8f9fa')
        self.window.transient(self.parent)
        self.window.focus_force()
        
        # --- HEADER ---
        header = tk.Frame(self.window, bg='#2c3e50', height=70)
        header.pack(fill='x', side='top')
        header.pack_propagate(False)
        
        tk.Label(header, text="⚙️ CONFIGURAÇÕES GERAIS", font=('Arial', 20, 'bold'), fg='white', bg='#2c3e50').pack(side='left', padx=30)
        
        tk.Button(header, text="❌ FECHAR", font=('Arial', 12, 'bold'), bg='#c0392b', fg='white', 
                 command=self.window.destroy, width=12).pack(side='right', padx=20)

        # --- CORPO ---
        main_frame = tk.Frame(self.window, bg='#f8f9fa')
        main_frame.pack(fill='both', expand=True, padx=40, pady=20)
        
        # Estilo das Abas
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background='#f8f9fa', borderwidth=0)
        style.configure('TNotebook.Tab', font=('Arial', 14, 'bold'), padding=[20, 12], background='#bdc3c7')
        style.map('TNotebook.Tab', background=[('selected', '#3498db')], foreground=[('selected', 'white')])
        
        notebook = ttk.Notebook(main_frame, style='TNotebook')
        notebook.pack(fill='both', expand=True)
        
        self.create_camera_tab(notebook)
        self.create_output_tab(notebook)
        self.create_display_tab(notebook)
        
        # Barra de Ação Inferior
        action_bar = tk.Frame(self.window, bg='#2c3e50', height=80)
        action_bar.pack(fill='x', side='bottom')
        
        tk.Button(action_bar, text="💾 SALVAR CONFIGURAÇÕES", font=('Arial', 14, 'bold'), bg='#27ae60', fg='white',
                 command=self.save_config, height=2, width=30).pack(pady=15)
        
        # Status Bar
        self.status_var = tk.StringVar(value="Pronto")
        tk.Label(self.window, textvariable=self.status_var, bg='#f8f9fa', fg='gray').pack(side='bottom', pady=5)

        # Atualização inicial em background
        Thread(target=self.initial_update, daemon=True).start()

    def initial_update(self):
        time.sleep(0.5)
        self.update_cameras()
        self.update_telas()
        self.update_impressoras()

    def create_section(self, parent, title):
        f = tk.Frame(parent, bg='#ecf0f1', pady=10, padx=10)
        f.pack(fill='x', pady=10)
        tk.Label(f, text=title, font=('Arial', 12, 'bold'), bg='#ecf0f1', fg='#2c3e50').pack(anchor='w')
        tk.Frame(f, bg='#bdc3c7', height=2).pack(fill='x', pady=5)
        return f

    def create_camera_tab(self, notebook):
        frame = tk.Frame(notebook, bg='#f8f9fa', padx=20, pady=20)
        notebook.add(frame, text=" 📷 CÂMERA ")
        
        sec = self.create_section(frame, "Dispositivo de Captura")
        
        tk.Label(sec, text="Câmera Principal:", bg='#ecf0f1', font=('Arial', 11)).pack(anchor='w')
        self.camera_var = tk.StringVar(value=self.config['camera_principal'])
        self.camera_combo = ttk.Combobox(sec, textvariable=self.camera_var, state='readonly', font=('Arial', 11), width=50)
        self.camera_combo.pack(anchor='w', pady=5)
        
        tk.Button(sec, text="🔄 Atualizar Lista", command=lambda: Thread(target=self.update_cameras).start(), bg='#3498db', fg='white').pack(anchor='w')

        # Liveview
        sec2 = self.create_section(frame, "Visualização (Liveview)")
        self.liveview_var = tk.StringVar(value=self.config['liveview_fonte'])
        tk.Radiobutton(sec2, text="Usar a mesma câmera da foto", variable=self.liveview_var, value="camera", bg='#ecf0f1', font=('Arial', 11)).pack(anchor='w')
        tk.Radiobutton(sec2, text="Usar câmera secundária (ex: webcam)", variable=self.liveview_var, value="camera_externa", bg='#ecf0f1', font=('Arial', 11)).pack(anchor='w')

    def create_output_tab(self, notebook):
        frame = tk.Frame(notebook, bg='#f8f9fa', padx=20, pady=20)
        notebook.add(frame, text=" 🖨️ IMPRESSÃO E ARQUIVOS ")
        
        # Arquivos
        sec = self.create_section(frame, "Armazenamento")
        tk.Label(sec, text="Pasta das Fotos:", bg='#ecf0f1').pack(anchor='w')
        
        f_path = tk.Frame(sec, bg='#ecf0f1')
        f_path.pack(fill='x')
        self.pasta_var = tk.StringVar(value=self.config['pasta_saida'])
        tk.Entry(f_path, textvariable=self.pasta_var, font=('Arial', 11)).pack(side='left', fill='x', expand=True)
        tk.Button(f_path, text="📂 Escolher", command=self.browse_folder).pack(side='left', padx=5)

        # Impressão
        sec2 = self.create_section(frame, "Configuração de Impressão")
        
        self.impressora_var = tk.BooleanVar(value=self.config['usar_impressora'])
        
        # CHECKBOX ALTERADO AQUI
        cb = tk.Checkbutton(sec2, text="Habilitar Impressão no Totem", variable=self.impressora_var, 
                           font=('Arial', 12, 'bold'), bg='#ecf0f1', command=self.toggle_impressora)
        cb.pack(anchor='w', pady=10)
        
        tk.Label(sec2, text="Impressora Selecionada:", bg='#ecf0f1').pack(anchor='w')
        self.impressora_combo = ttk.Combobox(sec2, state='readonly', font=('Arial', 11), width=40)
        self.impressora_combo.pack(anchor='w', pady=5)
        
        tk.Button(sec2, text="🔄 Buscar Impressoras", command=lambda: Thread(target=self.update_impressoras).start(), bg='#3498db', fg='white').pack(anchor='w')
        
        self.toggle_impressora() # Atualiza estado inicial

    def create_display_tab(self, notebook):
        frame = tk.Frame(notebook, bg='#f8f9fa', padx=20, pady=20)
        notebook.add(frame, text=" 🖥️ TELA ")
        
        sec = self.create_section(frame, "Exibição do Totem")
        tk.Label(sec, text="Tela Alvo (Onde o totem abre):", bg='#ecf0f1').pack(anchor='w')
        
        self.tela_var = tk.StringVar(value=self.config['tela_totem'])
        self.tela_combo = ttk.Combobox(sec, textvariable=self.tela_var, state='readonly', width=30)
        self.tela_combo.pack(anchor='w', pady=5)
        tk.Button(sec, text="🔄 Atualizar Telas", command=lambda: Thread(target=self.update_telas).start()).pack(anchor='w')
        
        sec2 = self.create_section(frame, "Orientação")
        self.orientacao_var = tk.StringVar(value=self.config['orientacao_tela'])
        tk.Radiobutton(sec2, text="Paisagem (Horizontal - TV Deitada)", variable=self.orientacao_var, value="paisagem", bg='#ecf0f1').pack(anchor='w')
        tk.Radiobutton(sec2, text="Retrato (Vertical - TV em Pé)", variable=self.orientacao_var, value="retrato", bg='#ecf0f1').pack(anchor='w')

    # --- FUNÇÕES DE UPDATE ---
    def update_cameras(self):
        self.status_var.set("Buscando câmeras...")
        cams = self.config_manager.get_cameras_usb()
        vals = [c['display'] for c in cams]
        self.camera_combo['values'] = vals
        
        curr = self.config['camera_principal']
        if curr and any(curr in c['nome'] or curr in c['display'] for c in cams):
            self.camera_var.set(next((c['display'] for c in cams if curr in c['nome'] or curr in c['display']), ""))
        elif vals:
            self.camera_combo.current(0)
        self.status_var.set(f"{len(cams)} câmeras encontradas")

    def update_impressoras(self):
        self.status_var.set("Buscando impressoras...")
        imps = self.config_manager.get_impressoras()
        self.impressora_combo['values'] = imps
        if self.config['impressora_selecionada'] in imps:
            self.impressora_combo.set(self.config['impressora_selecionada'])
        elif imps:
            self.impressora_combo.current(0)
        self.status_var.set("Impressoras atualizadas")

    def update_telas(self):
        telas = self.config_manager.get_telas()
        vals = [t['display'] for t in telas]
        self.tela_combo['values'] = vals
        # Tenta manter seleção ou selecionar HDMI
        curr = self.config['tela_totem']
        found = False
        for i, t in enumerate(telas):
            if curr in t['nome']:
                self.tela_combo.current(i)
                found = True
                break
        if not found and vals:
            self.tela_combo.current(0)

    def browse_folder(self):
        f = filedialog.askdirectory()
        if f: self.pasta_var.set(f)

    def toggle_impressora(self):
        st = 'readonly' if self.impressora_var.get() else 'disabled'
        self.impressora_combo.configure(state=st)

    def save_config(self):
        # Mapeia display name de volta para device/nome técnico se possível
        cam_display = self.camera_var.get()
        # Tenta achar o nome técnico (device ou nome curto) baseado no display
        # Simplificação: Salva o display name se não achar mapeamento, o camera_service lida com substrings
        
        new_conf = {
            'camera_principal': cam_display,
            'liveview_fonte': self.liveview_var.get(),
            'pasta_saida': self.pasta_var.get(),
            'usar_impressora': self.impressora_var.get(),
            'impressora_selecionada': self.impressora_combo.get(),
            'tela_totem': self.tela_var.get().replace("🖥️ ", "").split(" (")[0], # Limpa string
            'orientacao_tela': self.orientacao_var.get()
        }
        self.config_manager.config.update(new_conf)
        
        if self.config_manager.save_config():
            messagebox.showinfo("Sucesso", "Configurações salvas!")
            self.window.destroy()
        else:
            messagebox.showerror("Erro", "Erro ao salvar arquivo config.json")

