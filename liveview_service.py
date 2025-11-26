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
        if self.running:
            return False, "Já está em execução"
        
        self.running = True
        
        # Relê a config para garantir que pegou a última alteração
        self.config = self.config_manager.config
        
        if self.config.get('liveview_fonte') == 'camera_externa':
            camera_config = self.config.get('camera_liveview', '')
        else:
            camera_config = self.config.get('camera_principal', '')
        
        device_num = self._get_webcam_device(camera_config)
        print(f"Iniciando Liveview na câmera index: {device_num} (Config: {camera_config})")
        
        self.thread = threading.Thread(
            target=self._liveview_loop,
            args=(device_num, video_label, status_callback),
            daemon=True
        )
        self.thread.start()
        
        return True, "Liveview iniciado"
    
    def stop_liveview(self):
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
    
    def _liveview_loop(self, device_num, video_label, status_callback):
        def safe_status(msg):
             if hasattr(video_label, 'after'):
                 video_label.after(0, lambda: status_callback(msg))
        
        self.cap = self._find_working_webcam(device_num)
        if not self.cap:
            safe_status("❌ Nenhuma webcam encontrada")
            self.running = False
            return
        
        safe_status("✅ Liveview ativo - Iniciando...")
        
        frame_count = 0
        start_time = time.time()
        
        while self.running:
            try:
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    frame_count += 1
                    
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    def update_ui_frame(f_rgb):
                        if not self.running: return
                        try:
                            l_w = video_label.winfo_width()
                            l_h = video_label.winfo_height()
                            
                            if l_w > 10 and l_h > 10:
                                h, w = f_rgb.shape[:2]
                                ratio = min(l_w/w, l_h/h)
                                new_w, new_h = int(w * ratio), int(h * ratio)
                                frame_resized = cv2.resize(f_rgb, (new_w, new_h))
                            else:
                                frame_resized = cv2.resize(f_rgb, (640, 480))
                            
                            img = Image.fromarray(frame_resized)
                            imgtk = ImageTk.PhotoImage(image=img)
                            
                            video_label.imgtk = imgtk
                            video_label.configure(image=imgtk)
                        except: pass

                    if hasattr(video_label, 'after'):
                        video_label.after(0, update_ui_frame, frame_rgb)
                    
                    current_time = time.time()
                    if current_time - start_time >= 1:
                        fps = frame_count / (current_time - start_time)
                        # safe_status(f"✅ Liveview ({fps:.1f} FPS)") # Comentado para não spammar texto
                        frame_count = 0
                        start_time = current_time
                        
                else:
                    safe_status("❌ Erro frame")
                    time.sleep(0.5)
                    # Tenta recuperar
                    self.cap.release()
                    self.cap = cv2.VideoCapture(device_num)
                    
            except Exception as e:
                print(f"Erro liveview: {e}")
                break
            
            time.sleep(0.033)
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        safe_status("⏹️ Parado")
        self.running = False
    
    def _find_working_webcam(self, target_device):
        """
        Tenta abrir PRIMEIRO o dispositivo alvo.
        Só tenta outros se o alvo falhar.
        """
        candidates = [target_device]
        # Adiciona vizinhos como fallback (opcional, remova se quiser rigidez total)
        candidates.extend([d for d in range(0, 10) if d != target_device])
        
        for i in candidates:
            if i < 0: continue
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        # Configurações ideais
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                        cap.set(cv2.CAP_PROP_FPS, 30)
                        print(f"✅ Webcam aberta com sucesso: /dev/video{i}")
                        
                        # Se abriu uma que NÃO é a alvo, avisa no log
                        if i != target_device:
                            print(f"⚠️ AVISO: Câmera alvo {target_device} falhou. Usando {i}.")
                            
                        return cap
                    else: cap.release()
            except: pass
            
            # Se falhou a câmera alvo e estamos na primeira tentativa, imprime erro
            if i == target_device:
                print(f"❌ Falha ao abrir câmera alvo: /dev/video{i}")

        return None
    
    def _get_webcam_device(self, camera_config):
        if not camera_config: return 0
        if '/dev/video' in camera_config:
            match = re.search(r'/dev/video(\d+)', camera_config)
            if match: return int(match.group(1))
        return 0
