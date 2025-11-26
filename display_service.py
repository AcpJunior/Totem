import tkinter as tk
import time
import threading

class DisplayService:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.config = config_manager.config
    
    def show_test_pattern(self, duration=10):
        try:
            test_window = tk.Toplevel()
            test_window.title("Teste de Tela")
            test_window.configure(bg='#2c3e50')
            test_window.withdraw()
            
            tela_config = self.config.get('tela_totem', 'HDMI')
            raw_orientacao = str(self.config.get('orientacao_tela', 'paisagem'))
            orientacao = raw_orientacao.lower().strip()
            
            # USA A LÓGICA CENTRALIZADA
            x_pos, y_pos, width, height = self.config_manager.get_monitor_geometry(tela_config)
            
            test_window.geometry(f"{width}x{height}+{x_pos}+{y_pos}")
            test_window.deiconify()
            test_window.update_idletasks()
            test_window.attributes('-fullscreen', True)
            test_window.focus_force()
            
            main_frame = tk.Frame(test_window, bg='#2c3e50')
            main_frame.pack(expand=True, fill='both', padx=20, pady=20)
            
            if 'retrato' in orientacao or 'portrait' in orientacao:
                self._create_portrait_test(main_frame, raw_orientacao)
            else:
                self._create_landscape_test(main_frame, raw_orientacao)
            
            footer = tk.Frame(main_frame, bg='#2c3e50')
            footer.pack(side='bottom', fill='x', pady=20)
            tk.Label(footer, text=f"📺 Monitor: {width}x{height} pos({x_pos},{y_pos})", font=('Arial', 12), fg='#7f8c8d', bg='#2c3e50').pack()
            
            self._setup_autoclose(test_window, duration)
            return True, f"✅ Teste aberto em {x_pos},{y_pos}"
            
        except Exception as e:
            return False, f"❌ Erro tela: {str(e)}"
    
    def _create_landscape_test(self, parent, config_value):
        # ... (Mesmo código anterior) ...
        tk.Label(parent, text="🌄 MODO PAISAGEM", font=('Arial', 40), fg='#2ecc71', bg='#2c3e50').pack(expand=True)

    def _create_portrait_test(self, parent, config_value):
        # ... (Mesmo código anterior) ...
        tk.Label(parent, text="📱 MODO RETRATO", font=('Arial', 40), fg='#3498db', bg='#2c3e50').pack(expand=True)

    def _setup_autoclose(self, window, duration):
        def count():
            for i in range(duration, 0, -1):
                try: time.sleep(1)
                except: break
            try: window.destroy()
            except: pass
        threading.Thread(target=count, daemon=True).start()
        btn = tk.Button(window, text="❌ FECHAR", command=window.destroy, bg='#e74c3c', fg='white', font=('Arial', 20))
        btn.place(relx=0.5, rely=0.9, anchor='center')
