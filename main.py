import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import sys
import subprocess
import threading
import json
import time

# Adiciona caminho local
sys.path.append('/opt/Totem')

# Importa módulos do sistema
from config_manager import ConfigWindow, ConfigManager
from test_manager import TestWindow
from layout_editor import LayoutEditor
from photo_session import PhotoSession

class PhotoTotemApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Totem de Fotos - PAINEL DO OPERADOR")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='#2c3e50')
        
        # Carrega configurações
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        
        # Variáveis de Estado
        self.session_window = None 
        self.current_card_path = None
        
        self.center_window()
        self.root.bind('<Escape>', self.sair)
        
        # Teclas de Atalho do Operador
        self.root.bind('<Return>', self.action_nova_foto)
        self.root.bind('<space>', self.action_enviar)
        self.root.bind('p', self.action_imprimir)
        self.root.bind('P', self.action_imprimir)
        
        self.create_dashboard()
        
        # Abre a tela da TV automaticamente após 1 segundo
        self.root.after(1000, self.abrir_tela_totem)
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        self.root.geometry(f"{width}x{height}+0+0")
    
    def create_dashboard(self):
        # Frame Principal
        self.main_frame = tk.Frame(self.root, bg='#2c3e50')
        self.main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # --- COLUNA ESQUERDA (MENU DE CONFIGURAÇÃO) ---
        self.left_frame = tk.Frame(self.main_frame, bg='#34495e', width=300)
        self.left_frame.pack(side='left', fill='y', padx=(0, 20))
        self.left_frame.pack_propagate(False) 
        
        # Título
        tk.Label(self.left_frame, text="TOTEM\nAcpJunior", font=('Arial', 24, 'bold'), 
                fg='white', bg='#34495e').pack(pady=30)
        
        # Botões de Menu
        self.create_menu_button("🔄 RECARREGAR TELA TV", '#e67e22', self.recarregar_tela_totem)
        self.create_menu_button("CONFIGURAÇÕES", '#3498db', self.configuracoes)
        self.create_menu_button("LAYOUTS", '#9b59b6', self.layouts)
        self.create_menu_button("TESTES", '#f39c12', self.testes)
        
        tk.Button(self.left_frame, text="SAIR DO SISTEMA", font=('Arial', 12), bg='#c0392b', fg='white',
                 command=self.sair).pack(side='bottom', fill='x', pady=20, padx=20)

        # --- COLUNA DIREITA (PAINEL DO OPERADOR) ---
        self.right_frame = tk.Frame(self.main_frame, bg='#ecf0f1')
        self.right_frame.pack(side='right', fill='both', expand=True)
        
        # Área de Preview (Foto Tirada)
        self.preview_frame = tk.Frame(self.right_frame, bg='black')
        self.preview_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        self.lbl_preview = tk.Label(self.preview_frame, text="AGUARDANDO FOTO...", 
                                  font=('Arial', 20), fg='gray', bg='black')
        self.lbl_preview.pack(expand=True, fill='both')
        
        # Área de Botões de Ação
        self.action_frame = tk.Frame(self.right_frame, bg='#ecf0f1', height=100)
        self.action_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self.btn_nova = tk.Button(self.action_frame, text="NOVA FOTO (Enter)", font=('Arial', 16, 'bold'),
                                bg='#27ae60', fg='white', height=2, command=self.action_nova_foto)
        self.btn_nova.pack(side='left', fill='x', expand=True, padx=5)
        
        self.btn_enviar = tk.Button(self.action_frame, text="PRÓXIMO (Espaço)", font=('Arial', 16, 'bold'),
                                  bg='#3498db', fg='white', height=2, command=self.action_enviar)
        self.btn_enviar.pack(side='left', fill='x', expand=True, padx=5)
        
        self.btn_print = tk.Button(self.action_frame, text="IMPRIMIR (P)", font=('Arial', 16, 'bold'),
                                 bg='#e67e22', fg='white', height=2, command=self.action_imprimir)
        self.btn_print.pack(side='left', fill='x', expand=True, padx=5)

    def create_menu_button(self, text, color, command):
        btn = tk.Button(self.left_frame, text=text, font=('Arial', 12, 'bold'),
                       bg=color, fg='white', height=2, command=command)
        btn.pack(fill='x', padx=20, pady=10)

    # --- LÓGICA DO OPERADOR ---
    def action_nova_foto(self, event=None):
        """Gatilho para começar sessão"""
        if not self.session_window or not self.session_window.window.winfo_exists():
            self.abrir_tela_totem()
            
        self.lbl_preview.config(image='', text="📸 TIRANDO FOTOS...", fg='#f1c40f')
        self.current_card_path = None
        self.session_window.start_sequence()

    def action_enviar(self, event=None):
        """Limpa a tela para o próximo cliente"""
        self.lbl_preview.config(image='', text="✅ PRONTO PARA O PRÓXIMO", fg='#2ecc71')
        self.current_card_path = None

    def action_imprimir(self, event=None):
        """Envia comando de impressão robusto"""
        if not self.current_card_path:
            messagebox.showwarning("Aviso", "Nenhuma foto disponível para imprimir!")
            return
            
        printer = self.config.get('impressora_selecionada')
        if not printer:
            messagebox.showerror("Erro", "Nenhuma impressora configurada!")
            return
            
        # Trava botão para feedback
        original_text = self.btn_print['text']
        self.btn_print.config(text="🖨️ ENVIANDO...", state='disabled')
        
        def run_print():
            try:
                # 1. Lê configurações do layout (papel e orientação desejada)
                layout_json = "/opt/Totem/templates/config_card.json"
                media = "w288h432" # Default 10x15 (A6)
                borderless = False
                paper_orient = "Paisagem"
                
                if os.path.exists(layout_json):
                    with open(layout_json) as f:
                        d = json.load(f)
                        sz = d.get('print_paper_size', '')
                        if "A4" in sz: media="A4"
                        elif "A5" in sz: media="A5"
                        borderless = d.get('print_borderless', False)
                        paper_orient = d.get('paper_orientation', "Paisagem")
                
                # 2. Prepara imagem para impressão (Rotação Física se necessário)
                # Algumas impressoras ignoram flags de orientação, então giramos o arquivo na força bruta
                print_file = self.current_card_path
                
                try:
                    with Image.open(self.current_card_path) as img:
                        w, h = img.size
                        is_img_portrait = h > w
                        want_portrait = "Retrato" in paper_orient
                        
                        # Lógica de Rotação: Se o papel é Retrato mas a imagem está Deitada (ou vice versa)
                        needs_rotation = False
                        if want_portrait and not is_img_portrait:
                            needs_rotation = True
                        elif not want_portrait and is_img_portrait:
                            needs_rotation = True
                            
                        if needs_rotation:
                            print("🔄 Rotacionando imagem para bater com o papel...")
                            # Cria arquivo temporário rotacionado
                            rotated = img.rotate(90, expand=True)
                            rot_path = self.current_card_path.replace(".jpg", "_print_rot.jpg")
                            rotated.save(rot_path, quality=95)
                            print_file = rot_path
                except Exception as e:
                    print(f"Erro ao processar rotação: {e}")

                # 3. Monta comando CUPS
                cmd = ['lp', '-d', printer, '-o', f'media={media}']
                
                # fit-to-page garante que não corte se sobrar borda
                cmd.append('-o'); cmd.append('fit-to-page')
                
                if borderless:
                    cmd.append('-o'); cmd.append('stpi-border=borderless')
                
                cmd.append(print_file)
                
                print(f"🚀 Executando: {cmd}")
                subprocess.run(cmd, timeout=20)
                
                self.root.after(0, lambda: messagebox.showinfo("Sucesso", "Enviado para impressora!"))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha na impressão: {e}"))
            finally:
                self.root.after(0, lambda: self.btn_print.config(text=original_text, state='normal'))
        
        threading.Thread(target=run_print, daemon=True).start()

    def on_session_complete(self, card_path):
        """Chamado quando o PhotoSession termina"""
        self.current_card_path = card_path
        self.show_preview(card_path)

    def show_preview(self, path):
        """Mostra a foto na tela do operador"""
        try:
            img = Image.open(path)
            # Redimensiona para caber no espaço
            fw = self.preview_frame.winfo_width()
            fh = self.preview_frame.winfo_height()
            if fw < 100: fw=600; fh=400
            
            img.thumbnail((fw, fh), Image.Resampling.LANCZOS)
            self.tk_img = ImageTk.PhotoImage(img)
            self.lbl_preview.config(image=self.tk_img, text="")
        except Exception as e:
            print(f"Erro preview: {e}")

    # --- GERENCIAMENTO DE JANELAS ---
    def abrir_tela_totem(self):
        """Abre a janela na TV"""
        if self.session_window and self.session_window.window.winfo_exists():
            self.session_window.window.lift()
            return
        # Passa self.on_session_complete como callback
        self.session_window = PhotoSession(self.root, self.config_manager, self.on_session_complete)

    def recarregar_tela_totem(self):
        """Botão útil se mudar o layout e quiser ver na hora"""
        if self.session_window:
            try: self.session_window.destroy()
            except: pass
        self.abrir_tela_totem()

    def configuracoes(self): ConfigWindow(self.root)
    def testes(self): TestWindow(self.root, self.config_manager)
    def layouts(self): LayoutEditor(self.root)
    
    def sair(self, event=None):
        if messagebox.askyesno("Sair", "Deseja fechar todo o sistema?"):
            if self.session_window: 
                try: self.session_window.destroy()
                except: pass
            self.root.quit()

def main():
    # Configuração para Linux/X11
    if os.name == 'posix': 
        # Tenta liberar lock do X se houver (opcional)
        pass
        
    root = tk.Tk()
    app = PhotoTotemApp(root)
    try: root.mainloop()
    except: pass

if __name__ == "__main__":
    main()
