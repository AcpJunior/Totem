import os
import time
import subprocess

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

    def take_photo(self, callback=None):
        """
        Tira foto usando método SYSTEM e gera LOG de erro.
        """
        # 1. Mata processos da câmera (Força bruta)
        os.system("sudo pkill -f gphoto2")
        os.system("sudo gio mount -u gphoto2 2> /dev/null")
        
        # 2. Define caminhos
        filename = f"foto_{int(time.time())}.jpg"
        filepath = os.path.join(self.temp_folder, filename)
        log_file = "/opt/Totem/debug_camera.txt"
        
        print(f"📸 Tentando salvar em: {filepath}")
        
        # 3. Comando EXATO do seu teste, mas redirecionando a saída para um arquivo de texto
        # Isso vai nos dizer POR QUE está falhando se falhar
        cmd = (
            f"gphoto2 "
            f"--auto-detect "
            f"--capture-image-and-download "
            f"--force-overwrite "
            f"--filename '{filepath}' "
            f"> {log_file} 2>&1"
        )
        
        print(f"🚀 Executando: {cmd}")
        
        # 4. Executa bloqueando a thread até terminar
        exit_code = os.system(cmd)
        
        # 5. Verificação
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            print(f"✅ SUCESSO! Foto salva em: {filepath}")
            if callback:
                callback(filepath)
            return True, f"✅ Foto salva!\n{filename}"
        else:
            # Lê o log para saber o erro
            erro_msg = "Erro desconhecido"
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    erro_msg = f.read()
            
            print(f"❌ FALHA. Conteúdo do log:\n{erro_msg}")
            return False, f"❌ Erro na câmera. Veja debug_camera.txt\nDetalhe: {erro_msg[-100:]}" # Mostra os ultimos 100 caracteres

    # Auxiliares mantidos vazios para não quebrar
    def _take_webcam_photo(self, c): return False, "Webcam off"
    def _get_webcam_device(self): return 0
