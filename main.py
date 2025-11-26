import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from PIL import Image, ImageTk, ImageOps
import os
import sys
import subprocess
import threading
import json
import time
import re

sys.path.append('/opt/Totem')

from config_manager import ConfigWindow, ConfigManager
from test_manager import TestWindow
from layout_editor import LayoutEditor
from photo_session import PhotoSession
from whatsapp_service import WhatsAppService 

# --- Janela de Input de Telefone ---
class PhoneInputDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("WhatsApp")
        self.geometry("500x350")
        self.configure(bg='#2c3e50')
        self.transient(parent)
        self.grab_set()
        
        self.phone_number = None
        
        x = parent.winfo_x() + (parent.winfo_width()//2) - 250
        y = parent.winfo_y() + (parent.winfo_height()//2) - 175
        self.geometry(f"+{x}+{y}")

        tk.Label(self, text="📱 Digite o WhatsApp", font=('Arial', 20, 'bold'), fg='white', bg='#2c3e50').pack(pady=(30,10))
        tk.Label(self, text="(DDD + Número)", font=('Arial', 12), fg='#bdc3c7', bg='#2c3e50').pack(pady=(0,20))
        
        self.entry_var = tk.StringVar()
        self.entry_var.trace('w', self.validate_input)
        
        self.entry = tk.Entry(self, textvariable=self.entry_var, font=('Arial', 24), justify='center', width=15)
        self.entry.pack(pady=10, ipady=10)
        self.entry.focus_force()
        
        self.lbl_error = tk.Label(self, text="", font=('Arial', 10, 'bold'), fg='#e74c3c', bg='#2c3e50')
        self.lbl_error.pack(pady=5)
        
        btn_frame = tk.Frame(self, bg='#2c3e50')
        btn_frame.pack(fill='x', pady=20, padx=40)
        
        tk.Button(btn_frame, text="CANCELAR", command=self.destroy, bg='#c0392b', fg='white', font=('Arial', 12, 'bold'), height=2, width=12).pack(side='left')
        tk.Button(btn_frame, text="ENVIAR ➤", command=self.confirm, bg='#27ae60', fg='white', font=('Arial', 12, 'bold'), height=2, width=12).pack(side='right')
        
        self.bind('<Return>', lambda e: self.confirm())
        self.bind('<Escape>', lambda e: self.destroy())

    def validate_input(self, *args):
        text = self.entry_var.get()
        clean = ''.join(filter(str.isdigit, text))
        if text != clean: self.entry_var.set(clean)
        self.lbl_error.config(text="")

    def confirm(self):
        phone = self.entry_var.get()
        if len(phone) < 10 or len(phone) > 11:
            self.lbl_error.config(text="⚠️ Número inválido! Digite DDD + 9xxxx-xxxx")
            return
        self.phone_number = phone
        self.destroy()

# --- Janela de Progresso ---
class ProgressWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Enviando...")
        self.geometry("500x250")
        self.configure(bg='#2c3e50')
        self.transient(parent)
        self.grab_set()
        self.overrideredirect(True)
        
        x = parent.winfo_x() + (parent.winfo_width()//2) - 250
        y = parent.winfo_y() + (parent.winfo_height()//2) - 125
        self.geometry(f"+{x}+{y}")
        
        main_frame = tk.Frame(self, bg='#2c3e50', highlightbackground='white', highlightthickness=2)
        main_frame.pack(fill='both', expand=True)

        tk.Label(main_frame, text="🚀 Enviando Fotos...", font=('Arial', 18, 'bold'), fg='white', bg='#2c3e50').pack(pady=(30,20))
        
        self.lbl_status = tk.Label(main_frame, text="Iniciando...", font=('Arial', 12), fg='#f1c40f', bg='#2c3e50')
        self.lbl_status.pack(pady=5)
        
        self.progress = ttk.Progressbar(main_frame, orient='horizontal', length=400, mode='determinate')
        self.progress.pack(pady=20)

    def update_progress(self, step, total, msg):
        self.lbl_status.config(text=msg)
        pct = (step / total) * 100
        self.progress['value'] = pct
        self.update()

class PhotoTotemApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Totem de Fotos - PAINEL DO OPERADOR")
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='#2c3e50')
        
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.whatsapp_service = WhatsAppService()
        
        self.session_window = None 
        self.current_card_path = None
        self.current_individual_photos = [] 
        
        self.center_window()
        self.root.bind('<Escape>', self.sair)
        self.root.bind('<Return>', self.action_nova_foto)
        self.root.bind('<space>', self.action_enviar)
        self.root.bind('p', self.action_imprimir)
        self.root.bind('P', self.action_imprimir)
        
        self.create_dashboard()
        self.root.after(1000, self.abrir_tela_totem)
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        self.root.geometry(f"{width}x{height}+0+0")
    
    def create_dashboard(self):
        self.main_frame = tk.Frame(self.root, bg='#2c3e50')
        self.main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        self.left_frame = tk.Frame(self.main_frame, bg='#34495e', width=300)
        self.left_frame.pack(side='left', fill='y', padx=(0, 20))
        self.left_frame.pack_propagate(False) 
        
        tk.Label(self.left_frame, text="TOTEM\nAcpJunior", font=('Arial', 24, 'bold'), fg='white', bg='#34495e').pack(pady=30)
        
        self.create_menu_button("🔄 RECARREGAR TELA TV", '#e67e22', self.recarregar_tela_totem)
        self.create_menu_button("CONFIGURAÇÕES", '#3498db', self.configuracoes)
        self.create_menu_button("LAYOUTS", '#9b59b6', self.layouts)
        self.create_menu_button("WHATSAPP", '#27ae60', self.config_whatsapp) 
        self.create_menu_button("TESTES", '#f39c12', self.testes)
        
        tk.Button(self.left_frame, text="SAIR DO SISTEMA", font=('Arial', 12), bg='#c0392b', fg='white', command=self.sair).pack(side='bottom', fill='x', pady=20, padx=20)

        self.right_frame = tk.Frame(self.main_frame, bg='#ecf0f1')
        self.right_frame.pack(side='right', fill='both', expand=True)
        
        self.preview_frame = tk.Frame(self.right_frame, bg='black')
        self.preview_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        self.lbl_preview = tk.Label(self.preview_frame, text="AGUARDANDO FOTO...", font=('Arial', 20), fg='gray', bg='black')
        self.lbl_preview.pack(expand=True, fill='both')
        
        self.action_frame = tk.Frame(self.right_frame, bg='#ecf0f1', height=100)
        self.action_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self.btn_nova = tk.Button(self.action_frame, text="NOVA FOTO (Enter)", font=('Arial', 16, 'bold'), bg='#27ae60', fg='white', height=2, command=self.action_nova_foto)
        self.btn_nova.pack(side='left', fill='x', expand=True, padx=5)
        
        self.btn_enviar = tk.Button(self.action_frame, text="ENVIAR WHATS (Espaço)", font=('Arial', 16, 'bold'), bg='#3498db', fg='white', height=2, command=self.action_enviar)
        self.btn_enviar.pack(side='left', fill='x', expand=True, padx=5)
        
        self.btn_print = tk.Button(self.action_frame, text="IMPRIMIR (P)", font=('Arial', 16, 'bold'), bg='#e67e22', fg='white', height=2, command=self.action_imprimir)
        self.btn_print.pack(side='left', fill='x', expand=True, padx=5)

    def create_menu_button(self, text, color, command):
        tk.Button(self.left_frame, text=text, font=('Arial', 12, 'bold'), bg=color, fg='white', height=2, command=command).pack(fill='x', padx=20, pady=10)

    def action_nova_foto(self, event=None):
        if not self.session_window or not self.session_window.window.winfo_exists():
            self.abrir_tela_totem()
        self.lbl_preview.config(image='', text="📸 TIRANDO FOTOS...", fg='#f1c40f')
        self.current_card_path = None
        self.current_individual_photos = []
        self.session_window.start_sequence()

    def action_enviar(self, event=None):
        if not self.current_card_path:
            messagebox.showwarning("Aviso", "Nenhuma sessão finalizada para enviar.")
            return

        dialog = PhoneInputDialog(self.root)
        self.root.wait_window(dialog)
        
        phone = dialog.phone_number
        if not phone: return
        
        files_to_send = [self.current_card_path]
        if self.current_individual_photos:
            files_to_send.extend(self.current_individual_photos)
        
        progress_win = ProgressWindow(self.root)
        self.root.update()

        def envio_thread():
            def update_status_wrapper(step, total, msg):
                self.root.after(0, lambda: progress_win.update_progress(step, total, msg))

            success, msg = self.whatsapp_service.send_files_process(phone, files_to_send, update_status_wrapper)
            
            def on_finish():
                progress_win.destroy()
                if success:
                    messagebox.showinfo("Sucesso", "✅ Fotos enviadas com sucesso!")
                    self.lbl_preview.config(text="✅ PRONTO PARA O PRÓXIMO", fg='#2ecc71')
                    self.show_preview(self.current_card_path)
                else:
                    if messagebox.askretrycancel("Erro", f"Falha ao enviar: {msg}\nTentar outro número?"):
                        self.action_enviar()
                    else:
                        self.show_preview(self.current_card_path)

            self.root.after(0, on_finish)

        threading.Thread(target=envio_thread, daemon=True).start()

    def action_imprimir(self, event=None):
        if not self.current_card_path:
            messagebox.showwarning("Aviso", "Nenhuma foto disponível!")
            return
            
        printer = self.config.get('impressora_selecionada')
        if not printer:
            messagebox.showerror("Erro", "Nenhuma impressora configurada!")
            return
            
        original_text = self.btn_print['text']
        self.btn_print.config(text="🖨️ ENVIANDO...", state='disabled')
        
        def run_print():
            try:
                layout_json = "/opt/Totem/templates/config_card.json"
                target_w, target_h = 1800, 1200 
                media = "w288h432" 
                borderless = self.config.get('print_borderless', False)
                
                if os.path.exists(layout_json):
                    with open(layout_json) as f:
                        d = json.load(f)
                        target_w = d.get('card_width', 1800)
                        target_h = d.get('card_height', 1200)
                        sz = d.get('print_paper_size', '')
                        if "A4" in sz: media="A4"
                        elif "A5" in sz: media="A5"
                        elif "A6" in sz: media="A6"
                
                print_file = self.current_card_path
                temp_print = self.current_card_path.replace(".jpg", "_print_ready.jpg")
                
                with Image.open(print_file) as img:
                    img_resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    img_resized.save(temp_print, quality=100)
                    print_file = temp_print

                cmd = ['lp', '-d', printer, '-o', f'media={media}', '-o', 'fit-to-page']
                if borderless: cmd.extend(['-o', 'stpi-border=borderless'])
                cmd.append(print_file)
                
                print(f"🚀 Executando Print: {cmd}")
                subprocess.run(cmd, timeout=20)
                self.root.after(0, lambda: messagebox.showinfo("Sucesso", "Enviado para impressora!"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha na impressão: {e}"))
            finally:
                self.root.after(0, lambda: self.btn_print.config(text=original_text, state='normal'))
        threading.Thread(target=run_print, daemon=True).start()

    def on_session_complete(self, card_path, individual_photos=None):
        self.current_card_path = card_path
        self.current_individual_photos = individual_photos if individual_photos else []
        self.show_preview(card_path)

    def show_preview(self, path):
        try:
            img = Image.open(path)
            fw = self.preview_frame.winfo_width()
            fh = self.preview_frame.winfo_height()
            if fw < 50: fw=600; fh=400
            img.thumbnail((fw, fh), Image.Resampling.LANCZOS)
            self.tk_img = ImageTk.PhotoImage(img)
            self.lbl_preview.config(image=self.tk_img, text="")
        except Exception as e:
            print(f"Erro preview: {e}")

    def abrir_tela_totem(self):
        # --- CORREÇÃO: Força recarregar configuração do disco ---
        self.config = self.config_manager.load_config() 
        
        if self.session_window and self.session_window.window.winfo_exists():
            self.session_window.window.lift()
            return
        
        # Passa o config manager atualizado
        self.session_window = PhotoSession(self.root, self.config_manager, self.on_session_complete)

    def recarregar_tela_totem(self):
        if self.session_window: 
            try: self.session_window.destroy()
            except: pass
        self.abrir_tela_totem()

    def configuracoes(self): ConfigWindow(self.root)
    def testes(self): TestWindow(self.root, self.config_manager)
    def layouts(self): LayoutEditor(self.root)
    def config_whatsapp(self): self.whatsapp_service.open_config_window(self.root)
    
    def sair(self, event=None):
        if messagebox.askyesno("Sair", "Deseja fechar todo o sistema?"):
            if self.session_window: 
                try: self.session_window.destroy()
                except: pass
            self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoTotemApp(root)
    try: root.mainloop()
    except: pass
