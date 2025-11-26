import os
import time
import shutil
import tkinter as tk
from tkinter import messagebox, Toplevel
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import threading

class WhatsAppService:
    def __init__(self):
        self.base_dir = "/opt/Totem/redes"
        self.session_dir = os.path.join(self.base_dir, "whatsapp_session")
        self.ensure_dirs()
        
    def ensure_dirs(self):
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir, exist_ok=True)
            
    def is_logged_in(self):
        return os.path.exists(self.session_dir) and len(os.listdir(self.session_dir)) > 0

    def get_driver(self, headless=False):
        chrome_options = Options()
        chrome_options.add_argument(f"user-data-dir={self.session_dir}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1280,720")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        if headless:
            chrome_options.add_argument("--headless=new")
        
        chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def highlight(self, element, driver):
        try:
            driver.execute_script("arguments[0].setAttribute('style', 'border: 4px solid red; background: yellow;');", element)
        except: pass

    def force_click(self, element, driver):
        driver.execute_script("arguments[0].click();", element)

    def open_config_window(self, parent):
        win = Toplevel(parent)
        win.title("Configurar WhatsApp")
        win.geometry("500x400")
        win.configure(bg='#2c3e50')
        win.transient(parent)
        
        tk.Label(win, text="WhatsApp Conectado?", font=('Arial', 16, 'bold'), fg='white', bg='#2c3e50').pack(pady=20)
        
        status_text = "✅ CONECTADO" if self.is_logged_in() else "❌ DESCONECTADO"
        color = '#2ecc71' if self.is_logged_in() else '#e74c3c'
        lbl_status = tk.Label(win, text=status_text, font=('Arial', 14, 'bold'), fg=color, bg='#2c3e50')
        lbl_status.pack(pady=10)

        def conectar():
            if messagebox.askyesno("Conectar", "O navegador vai abrir VISÍVEL para você escanear.\n\n1. Escaneie o QR.\n2. Espere carregar.\n3. FECHE O NAVEGADOR MANUALMENTE.\n4. Clique em OK."):
                try:
                    os.system("pkill -f chrome")
                    time.sleep(1)
                    # Para conectar, SEMPRE headless=False (Visível)
                    driver = self.get_driver(headless=False)
                    driver.get("https://web.whatsapp.com")
                    while True:
                        try:
                            _ = driver.window_handles
                            time.sleep(1)
                        except: break
                    lbl_status.config(text="✅ Verifique status acima", fg='#f1c40f')
                    messagebox.showinfo("Fim", "Processo finalizado.")
                    win.destroy()
                except Exception as e:
                    messagebox.showerror("Erro", str(e))

        def desconectar():
            if messagebox.askyesno("Desconectar", "Apagar sessão?"):
                try:
                    os.system("pkill -f chrome")
                    time.sleep(1)
                    if os.path.exists(self.session_dir):
                        shutil.rmtree(self.session_dir)
                    lbl_status.config(text="❌ DESCONECTADO", fg='#e74c3c')
                    messagebox.showinfo("Sucesso", "Desconectado.")
                except Exception as e:
                    messagebox.showerror("Erro", str(e))

        tk.Button(win, text="📲 CONECTAR", command=conectar, bg='#27ae60', fg='white', font=('Arial', 12)).pack(fill='x', padx=30, pady=10)
        tk.Button(win, text="🗑️ DESCONECTAR", command=desconectar, bg='#c0392b', fg='white', font=('Arial', 12)).pack(fill='x', padx=30, pady=10)
        tk.Button(win, text="Fechar", command=win.destroy, bg='#7f8c8d', fg='white', font=('Arial', 12)).pack(fill='x', padx=30, pady=20)

    def send_files_process(self, phone, files, progress_callback):
        """
        progress_callback(current_step, total_steps, message)
        """
        driver = None
        try:
            total_steps = len(files) + 2 # +2 para abrir whats e finalizar
            current_step = 0
            
            progress_callback(0, total_steps, "Iniciando Sistema...")
            os.system("pkill -f chrome")
            time.sleep(0.5)

            # MODO OCULTO (Headless=True) AGORA ATIVADO
            driver = self.get_driver(headless=True)
            
            phone = "".join(filter(str.isdigit, phone))
            if not phone.startswith("55") and len(phone) > 9: phone = "55" + phone

            link = f"https://web.whatsapp.com/send?phone={phone}"
            driver.get(link)
            
            wait = WebDriverWait(driver, 60)

            progress_callback(1, total_steps, "Carregando WhatsApp...")
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, 'footer')))
            except:
                raise Exception("Falha no login ou número inválido.")

            current_step = 1
            
            for i, filepath in enumerate(files):
                if not os.path.exists(filepath): continue
                
                progress_callback(current_step, total_steps, f"Enviando foto {i+1}/{len(files)}...")
                
                # 1. Botão Anexar (Posição)
                attach_btn = None
                
                # Tenta por nome primeiro
                xpaths_attach = ['//div[@title="Anexar"]', '//span[@data-icon="plus"]']
                for xp in xpaths_attach:
                    try: attach_btn = driver.find_element(By.XPATH, xp); break
                    except: pass

                # Fallback por Posição (Ignorando Emoji)
                if not attach_btn:
                    try:
                        footer = driver.find_element(By.TAG_NAME, 'footer')
                        buttons = footer.find_elements(By.CSS_SELECTOR, 'div[role="button"], button')
                        for btn in buttons:
                            icon = btn.get_attribute('data-icon') or ""
                            if 'smiley' in icon or 'emoji' in (btn.get_attribute('title') or "").lower(): continue
                            attach_btn = btn
                            break
                    except: pass

                if not attach_btn: raise Exception("Botão Anexar não encontrado")

                self.force_click(attach_btn, driver)
                time.sleep(0.8)
                
                # 2. Input File
                file_input = driver.find_element(By.XPATH, '//input[@type="file"]')
                file_input.send_keys(filepath)
                
                # 3. Enviar
                progress_callback(current_step, total_steps, "Confirmando envio...")
                time.sleep(3) # Tempo para preview
                
                sent = False
                start_send = time.time()
                while time.time() - start_send < 5:
                    try:
                        send_btn = driver.find_element(By.XPATH, '//span[@data-icon="send"]')
                        self.force_click(send_btn, driver)
                        sent = True
                        break
                    except:
                        # Enter se demorar
                        if time.time() - start_send > 1.5:
                            try: 
                                ActionChains(driver).send_keys(Keys.ENTER).perform()
                                sent = True
                                break
                            except: pass
                        time.sleep(0.1)
                
                time.sleep(2) # Upload
                current_step += 1

            progress_callback(total_steps, total_steps, "Finalizando...")
            
            # DELAY EXTRA NO FINAL PARA GARANTIR A ULTIMA FOTO
            time.sleep(5) 
            
            return True, "Enviado!"

        except Exception as e:
            print(f"Erro WhatsApp: {e}")
            return False, f"Erro: {str(e)}"
        finally:
            if driver:
                try: driver.quit()
                except: pass
