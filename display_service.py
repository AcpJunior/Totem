import tkinter as tk
import subprocess
import time
import threading
import re

class DisplayService:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.config = config_manager.config
    
    def show_test_pattern(self, duration=10):
        """Mostra padrão de teste na tela configurada"""
        try:
            # 1. Prepara a janela
            test_window = tk.Toplevel()
            test_window.title("Teste de Tela")
            test_window.configure(bg='#2c3e50')
            test_window.withdraw()
            
            # 2. Obtém e trata as configurações
            tela_config = self.config.get('tela_totem', 'HDMI')
            
            # TRATAMENTO ROBUSTO DA ORIENTAÇÃO
            raw_orientacao = str(self.config.get('orientacao_tela', 'paisagem'))
            orientacao = raw_orientacao.lower().strip()
            
            print(f"⚙️ Configuração lida: Tela='{tela_config}' | Orientação='{raw_orientacao}'")
            
            # 3. Posicionamento (Lógica do monitor)
            x_pos, y_pos, width, height = self._get_monitor_geometry(tela_config)
            test_window.geometry(f"{width}x{height}+{x_pos}+{y_pos}")
            
            test_window.deiconify()
            test_window.update_idletasks()
            test_window.attributes('-fullscreen', True)
            test_window.focus_force()
            
            # 4. Criação do Conteúdo Baseada na Orientação
            main_frame = tk.Frame(test_window, bg='#2c3e50')
            main_frame.pack(expand=True, fill='both', padx=20, pady=20)
            
            # Verifica se contém a palavra 'retrato' ou 'portrait'
            if 'retrato' in orientacao or 'portrait' in orientacao:
                self._create_portrait_test(main_frame, raw_orientacao)
            else:
                self._create_landscape_test(main_frame, raw_orientacao)
            
            # Rodapé com informações técnicas
            footer = tk.Frame(main_frame, bg='#2c3e50')
            footer.pack(side='bottom', fill='x', pady=20)
            
            tk.Label(footer, 
                    text=f"📺 Monitor Detectado: {width}x{height} pos({x_pos},{y_pos})\n⚙️ Config Bruta: {raw_orientacao}", 
                    font=('Arial', 12), fg='#7f8c8d', bg='#2c3e50').pack()
            
            # 5. Fechamento
            self._setup_autoclose(test_window, duration)
            
            return True, f"✅ Teste aberto em {x_pos},{y_pos} ({raw_orientacao})"
            
        except Exception as e:
            print(f"❌ Erro display: {e}")
            return False, f"❌ Erro tela: {str(e)}"
    
    def _create_landscape_test(self, parent, config_value):
        """Layout Horizontal"""
        container = tk.Frame(parent, bg='#2c3e50', relief='ridge', bd=5)
        container.pack(expand=True, fill='both', padx=50, pady=50)
        
        tk.Label(container, text="🌄 MODO PAISAGEM", 
                font=('Arial', 50, 'bold'), fg='#2ecc71', bg='#2c3e50').pack(expand=True)
        
        tk.Label(container, text=f"(O sistema entendeu: '{config_value}')", 
                font=('Arial', 20), fg='white', bg='#2c3e50').pack(pady=20)
        
        tk.Label(container, text="Se sua tela está de pé, mude a rotação no LUBUNTU", 
                font=('Arial', 14), fg='#f1c40f', bg='#2c3e50').pack(pady=10)

    def _create_portrait_test(self, parent, config_value):
        """Layout Vertical (Retrato)"""
        # Cria um frame estreito para simular celular
        container = tk.Frame(parent, bg='#34495e', relief='ridge', bd=5)
        # Tenta ocupar o centro verticalmente
        container.place(relx=0.5, rely=0.5, anchor='center', relheight=0.9, relwidth=0.4)
        
        tk.Label(container, text="📱", font=('Arial', 60), bg='#34495e', fg='white').pack(pady=(30,10))
        
        tk.Label(container, text="MODO\nRETRATO", 
                font=('Arial', 40, 'bold'), fg='#3498db', bg='#34495e').pack(pady=20)
        
        tk.Label(container, text="SUCESSO!", 
                font=('Arial', 25, 'bold'), fg='#2ecc71', bg='#34495e').pack(pady=20)
        
        tk.Label(container, text=f"Config lida:\n'{config_value}'", 
                font=('Arial', 16), fg='white', bg='#34495e').pack(pady=20)
        
        tk.Label(container, text="Nota: Se este texto está de lado,\nvocê precisa rotacionar o monitor\nnas configurações do Linux.", 
                font=('Arial', 12), fg='#f1c40f', bg='#34495e', wraplength=300).pack(side='bottom', pady=30)

    def _get_monitor_geometry(self, target_name_part):
        # ... (MESMO CÓDIGO ANTERIOR DE GEOMETRIA) ...
        try:
            output = subprocess.check_output(['xrandr']).decode('utf-8')
            pattern = re.compile(r'^(\S+)\s+connected.*?(\d+)x(\d+)\+(\d+)\+(\d+)', re.MULTILINE)
            
            monitors = []
            for match in pattern.finditer(output):
                monitors.append({
                    'name': match.group(1),
                    'w': int(match.group(2)), 'h': int(match.group(3)),
                    'x': int(match.group(4)), 'y': int(match.group(5))
                })

            target = target_name_part.lower()
            # 1. Busca por nome
            for m in monitors:
                if target in m['name'].lower(): return m['x'], m['y'], m['w'], m['h']
            
            # 2. Busca secundário (HDMI)
            if 'hdmi' in target:
                for m in monitors:
                    if m['x'] > 0: return m['x'], m['y'], m['w'], m['h']
            
            # 3. Fallback
            if monitors: return monitors[0]['x'], monitors[0]['y'], monitors[0]['w'], monitors[0]['h']
        except: pass
        return 0, 0, 800, 600

    def _setup_autoclose(self, window, duration):
        def count():
            for i in range(duration, 0, -1):
                try:
                    time.sleep(1)
                except: break
            try: window.destroy()
            except: pass
        threading.Thread(target=count, daemon=True).start()
        
        btn = tk.Button(window, text="❌ FECHAR", command=window.destroy, 
                       bg='#e74c3c', fg='white', font=('Arial', 20, 'bold'))
        btn.place(relx=0.5, rely=0.9, anchor='center')
