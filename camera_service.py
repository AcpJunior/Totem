import os
import time
import subprocess
import glob

class CameraService:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.config = config_manager.config
        self.temp_folder = "/opt/Totem/temp"
        self._ensure_temp_folder()
    
    def _ensure_temp_folder(self):
        if not os.path.exists(self.temp_folder):
            try:
                os.makedirs(self.temp_folder, exist_ok=True)
                os.chmod(self.temp_folder, 0o777)
            except: pass
            
    # --- CORREÇÃO: Função para limpar temp ---
    def clear_temp_folder(self):
        """Remove todas as fotos da pasta temp para não misturar sessões"""
        try:
            files = glob.glob(os.path.join(self.temp_folder, "*"))
            for f in files:
                try: os.remove(f)
                except: pass
            print("🧹 Pasta Temp limpa.")
        except Exception as e:
            print(f"Erro ao limpar temp: {e}")

    def take_photo(self, callback=None):
        # 1. Mata processos da câmera (Força bruta para garantir liberação)
        os.system("sudo pkill -f gphoto2")
        os.system("sudo gio mount -u gphoto2 2> /dev/null")
        
        filename = f"foto_{int(time.time())}.jpg"
        filepath = os.path.join(self.temp_folder, filename)
        log_file = "/opt/Totem/debug_camera.txt"
        
        print(f"📸 Tentando salvar em: {filepath}")
        
        cmd = (
            f"gphoto2 "
            f"--auto-detect "
            f"--capture-image-and-download "
            f"--force-overwrite "
            f"--filename '{filepath}' "
            f"> {log_file} 2>&1"
        )
        
        exit_code = os.system(cmd)
        
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            print(f"✅ SUCESSO! Foto salva em: {filepath}")
            if callback:
                callback(filepath)
            return True, f"✅ Foto salva!\n{filename}"
        else:
            erro_msg = "Erro desconhecido"
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    erro_msg = f.read()
            
            print(f"❌ FALHA. Log: {erro_msg}")
            return False, f"❌ Erro na câmera. Veja debug_camera.txt"

    def _take_webcam_photo(self, c): return False, "Webcam off"
    def _get_webcam_device(self): return 0
