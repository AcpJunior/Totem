import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import os
from PIL import Image, ImageTk

# Importações dos serviços
from camera_service import CameraService
from display_service import DisplayService
from liveview_service import LiveviewService

class TestManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.camera_service = CameraService(config_manager)
        self.display_service = DisplayService(config_manager)
        self.liveview_service = LiveviewService(config_manager)
    
    def test_camera(self, callback=None):
        """Testa câmera usando o serviço"""
        return self.camera_service.take_photo(callback)
    
    def test_liveview(self, video_label, status_callback):
        """Testa liveview usando o serviço"""
        return self.liveview_service.start_liveview(video_label, status_callback)
    
    def stop_liveview(self):
        """Para liveview usando o serviço"""
        self.liveview_service.stop_liveview()
    
    def test_display(self):
        """Testa tela usando o serviço"""
        return self.display_service.show_test_pattern()
    
    def test_storage(self):
        """Testa armazenamento"""
        try:
            pasta = self.config_manager.config['pasta_saida']
            os.makedirs(pasta, exist_ok=True)
            test_file = f"{pasta}/teste_totem.txt"
            with open(test_file, 'w') as f:
                f.write(f"Teste OK: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            return True, f"✅ Armazenamento OK!\nPasta: {pasta}"
        except Exception as e:
            return False, f"❌ Erro armazenamento: {str(e)}"
    
    def test_printer(self):
        """Testa impressora"""
        try:
            printer = self.config_manager.config['impressora_selecionada']
            if not printer or not self.config_manager.config['usar_impressora']:
                return True, "ℹ️  Impressão desabilitada"
            import subprocess
            result = subprocess.run(['lpstat', '-p', printer], capture_output=True)
            return (True, f"✅ Impressora OK: {printer}") if result.returncode == 0 else (False, "❌ Impressora não encontrada")
        except Exception as e:
            return False, f"❌ Erro impressora: {str(e)}"

class TestWindow:
    def __init__(self, parent, config_manager):
        self.parent = parent
        self.config_manager = config_manager
        self.test_manager = TestManager(config_manager)
        self.create_window()
    
    def create_window(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("🧪 Testes - Totem de Fotos")
        self.window.attributes('-fullscreen', True)
        self.window.configure(bg='#1a1a1a')
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Header
        header = tk.Frame(self.window, bg='#2c3e50', height=100)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(header, text="🧪 TESTES DO SISTEMA", font=('Arial', 24, 'bold'), fg='white', bg='#2c3e50').pack(expand=True)
        
        # Notebook
        main_frame = tk.Frame(self.window, bg='#1a1a1a')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        style = ttk.Style()
        style.configure('Test.TNotebook', background='#1a1a1a')
        notebook = ttk.Notebook(main_frame, style='Test.TNotebook')
        notebook.pack(fill='both', expand=True)
        
        self.create_camera_tab(notebook)
        self.create_liveview_tab(notebook)
        self.create_system_tab(notebook)
        
        # Botão Fechar
        tk.Button(self.window, text="🚪 FECHAR", font=('Arial', 14), bg='#e74c3c', fg='white', 
                 command=self.window.destroy, height=2).pack(fill='x', side='bottom')

    def create_camera_tab(self, notebook):
        frame = tk.Frame(notebook, bg='#1a1a1a')
        notebook.add(frame, text="📷 CÂMERA")
        frame.columnconfigure(1, weight=1)
        
        # Botão Testar
        tk.Button(frame, text="🎯 TESTAR CÂMERA", font=('Arial', 14, 'bold'), bg='#3498db', fg='white',
                 command=self.test_camera, height=2).grid(row=0, column=0, pady=20, padx=20, sticky='ew')
        
        # Resultado Texto
        self.camera_result = tk.Label(frame, text="Clique para testar", font=('Arial', 12), bg='#1a1a1a', fg='white')
        self.camera_result.grid(row=0, column=1, sticky='w', padx=20)
        
        # Área da Imagem
        self.photo_label = tk.Label(frame, bg='#34495e', text="A foto aparecerá aqui", fg='white')
        self.photo_label.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=20, pady=10)
        frame.rowconfigure(1, weight=1)

    def create_liveview_tab(self, notebook):
        frame = tk.Frame(notebook, bg='#1a1a1a')
        notebook.add(frame, text="🔴 LIVEVIEW")
        
        btn_frame = tk.Frame(frame, bg='#1a1a1a')
        btn_frame.pack(pady=20)
        
        self.start_btn = tk.Button(btn_frame, text="▶️ INICIAR", font=('Arial', 12), bg='#27ae60', fg='white',
                                 command=self.start_liveview, width=15)
        self.start_btn.pack(side='left', padx=10)
        
        self.stop_btn = tk.Button(btn_frame, text="⏹️ PARAR", font=('Arial', 12), bg='#e74c3c', fg='white',
                                command=self.stop_liveview, width=15, state='disabled')
        self.stop_btn.pack(side='left', padx=10)
        
        self.liveview_status = tk.Label(frame, text="", bg='#1a1a1a', fg='white')
        self.liveview_status.pack()
        
        self.video_label = tk.Label(frame, bg='black')
        self.video_label.pack(expand=True, fill='both', padx=20, pady=20)

    def create_system_tab(self, notebook):
        frame = tk.Frame(notebook, bg='#1a1a1a')
        notebook.add(frame, text="⚙️ OUTROS")
        
        tk.Button(frame, text="💾 TESTAR DISCO", command=self.test_pasta, bg='#9b59b6', fg='white', font=('Arial', 12)).pack(pady=10, fill='x', padx=50)
        self.pasta_result = tk.Label(frame, text="", bg='#1a1a1a', fg='white')
        self.pasta_result.pack()
        
        tk.Button(frame, text="🖨️ TESTAR IMPRESSORA", command=self.test_impressora, bg='#34495e', fg='white', font=('Arial', 12)).pack(pady=10, fill='x', padx=50)
        self.impressora_result = tk.Label(frame, text="", bg='#1a1a1a', fg='white')
        self.impressora_result.pack()
        
        tk.Button(frame, text="🖥️ TESTAR TELA", command=self.test_tela, bg='#f39c12', fg='white', font=('Arial', 12)).pack(pady=10, fill='x', padx=50)
        self.tela_result = tk.Label(frame, text="", bg='#1a1a1a', fg='white')
        self.tela_result.pack()

    # --- LÓGICA DE TESTE DA CÂMERA CORRIGIDA ---
    def test_camera(self):
        # 1. Para o Liveview para não travar
        self.stop_liveview()
        
        self.camera_result.config(text="📸 Capturando... Aguarde...", fg='#f39c12')
        self.photo_label.config(text="⏳ Processando imagem...", image="")
        
        # 2. Callback que será executado quando a foto estiver salva
        def on_file_saved(filepath):
            print(f"📸 Callback recebido para: {filepath}")
            # Agenda a exibição na thread principal com atraso de segurança
            self.window.after(1000, lambda: self._safe_show_image(filepath))

        # 3. Executa em background
        def run_test():
            try:
                success, msg = self.test_manager.test_camera(on_file_saved)
                # Atualiza texto de status
                color = '#27ae60' if success else '#e74c3c'
                self.window.after(0, lambda: self.camera_result.config(text=msg, fg=color))
            except Exception as e:
                self.window.after(0, lambda: self.camera_result.config(text=f"Erro: {e}", fg='#e74c3c'))

        threading.Thread(target=run_test, daemon=True).start()

    def _safe_show_image(self, filepath):
        """Carrega a imagem de forma segura na UI"""
        try:
            if not os.path.exists(filepath):
                self.photo_label.config(text=f"❌ Arquivo não encontrado:\n{filepath}")
                return

            # Tenta garantir permissão de leitura
            try:
                os.chmod(filepath, 0o644)
            except:
                pass

            print(f"🖼️ Carregando imagem na tela: {filepath}")
            
            # Carrega imagem
            img = Image.open(filepath)
            
            # Redimensiona mantendo proporção
            # Pega tamanho da área disponível
            lbl_w = self.photo_label.winfo_width()
            lbl_h = self.photo_label.winfo_height()
            if lbl_w < 100: lbl_w = 600 # Fallback se a janela ainda não renderizou
            if lbl_h < 100: lbl_h = 400
            
            img.thumbnail((lbl_w, lbl_h), Image.Resampling.LANCZOS)
            
            # Converte para Tkinter
            photo = ImageTk.PhotoImage(img)
            
            # Exibe
            self.photo_label.config(image=photo, text="")
            self.photo_label.image = photo # CRUCIAL: Manter referência
            
            print("✅ Imagem exibida com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao exibir imagem: {e}")
            self.photo_label.config(text=f"Erro ao abrir imagem:\n{str(e)}")

    # --- MÉTODOS AUXILIARES ---
    def start_liveview(self):
        def update_status(msg):
            self.liveview_status.config(text=msg, fg='#27ae60' if '✅' in msg else '#e74c3c')
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        threading.Thread(target=lambda: self.test_manager.test_liveview(self.video_label, update_status), daemon=True).start()

    def stop_liveview(self):
        self.test_manager.stop_liveview()
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.video_label.config(image="")
        self.liveview_status.config(text="Parado")

    def test_pasta(self):
        success, msg = self.test_manager.test_storage()
        self.pasta_result.config(text=msg, fg='#27ae60' if success else '#e74c3c')

    def test_impressora(self):
        success, msg = self.test_manager.test_printer()
        self.impressora_result.config(text=msg, fg='#27ae60' if success else '#e74c3c')

    def test_tela(self):
        success, msg = self.test_manager.test_display()
        self.tela_result.config(text=msg, fg='#27ae60' if success else '#e74c3c')
