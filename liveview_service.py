import cv2
import threading
import time
from PIL import Image, ImageTk
import re

class LiveviewService:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.config = config_manager.config
        self.running = False
        self.thread = None
        self.cap = None
    
    def start_liveview(self, video_label, status_callback):
        """Inicia liveview - FUNCIONANDO"""
        if self.running:
            return False, "Já está em execução"
        
        self.running = True
        
        # Decide qual câmera usar
        if self.config['liveview_fonte'] == 'camera_externa' and self.config['camera_liveview']:
            camera_config = self.config['camera_liveview']
        else:
            camera_config = self.config['camera_principal']
        
        device_num = self._get_webcam_device(camera_config)
        
        self.thread = threading.Thread(
            target=self._liveview_loop,
            args=(device_num, video_label, status_callback),
            daemon=True
        )
        self.thread.start()
        
        return True, "Liveview iniciado"
    
    def stop_liveview(self):
        """Para o liveview"""
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
    
    def _liveview_loop(self, device_num, video_label, status_callback):
        """Loop principal do liveview - FUNCIONANDO"""
        # Encontra webcam funcionando
        self.cap = self._find_working_webcam(device_num)
        if not self.cap:
            status_callback("❌ Nenhuma webcam encontrada")
            self.running = False
            return
        
        status_callback("✅ Liveview ativo - Procurando câmera...")
        
        frame_count = 0
        start_time = time.time()
        
        while self.running:
            try:
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    frame_count += 1
                    
                    # Converte BGR para RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Redimensiona para o label
                    label_width = video_label.winfo_width()
                    label_height = video_label.winfo_height()
                    
                    if label_width > 10 and label_height > 10:
                        h, w = frame_rgb.shape[:2]
                        ratio = min(label_width/w, label_height/h)
                        new_w = int(w * ratio)
                        new_h = int(h * ratio)
                        frame_resized = cv2.resize(frame_rgb, (new_w, new_h))
                    else:
                        frame_resized = cv2.resize(frame_rgb, (640, 480))
                    
                    # Converte para ImageTk
                    img = Image.fromarray(frame_resized)
                    imgtk = ImageTk.PhotoImage(image=img)
                    
                    # Atualiza interface
                    video_label.imgtk = imgtk
                    video_label.configure(image=imgtk)
                    
                    # Atualiza status com FPS
                    current_time = time.time()
                    if current_time - start_time >= 1:
                        fps = frame_count / (current_time - start_time)
                        status_callback(f"✅ Liveview ativo - {fps:.1f} FPS")
                        frame_count = 0
                        start_time = current_time
                        
                else:
                    status_callback("❌ Erro ao capturar frame")
                    break
                    
            except Exception as e:
                print(f"Erro liveview: {e}")
                status_callback("❌ Erro no liveview")
                break
            
            time.sleep(0.033)  # ~30 FPS
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        status_callback("⏹️ Liveview finalizado")
        self.running = False
    
    def _find_working_webcam(self, start_device):
        """Encontra webcam funcionando"""
        for i in range(max(0, start_device-1), start_device + 3):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    # Configura
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    print(f"✅ Webcam encontrada: /dev/video{i}")
                    return cap
                else:
                    cap.release()
            else:
                cap.release()
        return None
    
    def _get_webcam_device(self, camera_config):
        """Obtém dispositivo da webcam"""
        if '/dev/video' in camera_config:
            match = re.search(r'/dev/video(\d+)', camera_config)
            if match:
                return int(match.group(1))
        return 0
