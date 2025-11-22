import tkinter as tk
from tkinter import ttk, colorchooser, filedialog, messagebox
from PIL import Image, ImageDraw, ImageTk, ImageEnhance, ImageOps
import json
import os

class LayoutEditor:
    def __init__(self, parent):
        self.parent = parent
        self.template_dir = "/opt/Totem/templates"
        self.ensure_template_dir()
        
        # Dimensões da tela do operador
        self.screen_w = self.parent.winfo_screenwidth()
        self.screen_h = self.parent.winfo_screenheight()
        
        # --- CONFIGURAÇÕES DE PAPEL (300 DPI) ---
        self.PAPER_SPECS = {
            "A6 (10x15cm)": (1748, 1181),
            "A5 (15x21cm)": (2480, 1748),
            "A4 (21x30cm)": (3508, 2480)
        }
        
        # Estado Inicial
        self.current_paper = "A6 (10x15cm)"
        self.paper_orientation = "Paisagem" # ou Retrato
        self.real_width = 1748
        self.real_height = 1181
        
        # Cores e Ferramentas
        self.primary_color = "#ffffff"
        self.secondary_color = "#000000"
        self.font_color = "#ffffff"
        self.gradient_direction = "Vertical"
        self.active_texture = None
        
        # Slots
        self.slots = [] 
        self.drawing_slot = False
        self.moving_slot = None
        self.start_x = 0; self.start_y = 0
        self.last_mouse_x = 0; self.last_mouse_y = 0
        
        # Imagens
        self.base_image = None
        self.display_image = None
        self.tk_image = None
        
        self.create_window()
        self.load_existing_config() # Carrega e já aplica tamanho
        
        # Se não carregou imagem, cria branca
        if self.base_image is None:
            self.reset_canvas_to_size()

    def ensure_template_dir(self):
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir, exist_ok=True)
            try: os.chmod(self.template_dir, 0o777)
            except: pass

    def create_window(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Editor de Layouts")
        self.window.attributes('-fullscreen', True)
        self.window.configure(bg='#2c3e50')
        self.window.transient(self.parent)
        self.window.focus_force()
        
        # Header
        header = tk.Frame(self.window, bg='#2c3e50', height=60)
        header.pack(fill='x', side='top')
        tk.Label(header, text="🎨 EDITOR DE LAYOUT", font=('Arial', 18, 'bold'), fg='white', bg='#2c3e50').pack(side='left', padx=20, pady=10)
        tk.Button(header, text="❌ FECHAR", font=('Arial', 11, 'bold'), bg='#c0392b', fg='white', command=self.window.destroy, width=12).pack(side='right', padx=10, pady=10)
        tk.Button(header, text="💾 SALVAR", font=('Arial', 11, 'bold'), bg='#27ae60', fg='white', command=self.save_all, width=12).pack(side='right', padx=10, pady=10)

        # Notebook
        style = ttk.Style(); style.theme_use('clam')
        style.configure('TNotebook', background='#2c3e50', borderwidth=0)
        style.configure('TNotebook.Tab', font=('Arial', 12, 'bold'), padding=[20, 10], background='#34495e', foreground='#bdc3c7')
        style.map('TNotebook.Tab', background=[('selected', '#3498db')], foreground=[('selected', 'white')])

        self.notebook = ttk.Notebook(self.window, style='TNotebook')
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.create_background_tab()
        self.create_card_tab()
        self.create_config_tab()

    # --- ABA 1: FUNDO ---
    def create_background_tab(self):
        frame = tk.Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(frame, text=" 1. Fundo ")
        cont = tk.Frame(frame, bg='#ecf0f1'); cont.pack(fill='both', expand=True)
        
        sidebar = tk.Frame(cont, bg='#bdc3c7', width=300)
        sidebar.pack(side='left', fill='y'); sidebar.pack_propagate(False)
        
        self.add_lbl(sidebar, "CORES")
        self.btn_cor1 = tk.Button(sidebar, text="Cor Principal", bg='white', command=lambda: self.pick_color(1)); self.btn_cor1.pack(fill='x', padx=10, pady=2)
        self.btn_cor2 = tk.Button(sidebar, text="Cor Secundária", bg='black', fg='white', command=lambda: self.pick_color(2)); self.btn_cor2.pack(fill='x', padx=10, pady=2)
        tk.Button(sidebar, text="Cor Sólida", command=self.apply_solid).pack(fill='x', padx=10, pady=2)
        
        self.add_lbl(sidebar, "EFEITOS")
        gf = tk.Frame(sidebar, bg='#bdc3c7'); gf.pack(fill='x', padx=10)
        self.grad_combo = ttk.Combobox(gf, values=["Vertical", "Horizontal", "Diagonal"], state='readonly', width=10); self.grad_combo.current(0); self.grad_combo.pack(side='left')
        tk.Button(gf, text="Degradê", command=self.apply_gradient, bg='#8e44ad', fg='white').pack(side='left', padx=5, fill='x', expand=True)

        self.add_lbl(sidebar, "TEXTURAS")
        tk.Button(sidebar, text="Bolinhas", command=lambda: self.toggle_texture('dots')).pack(fill='x', padx=10, pady=2)
        tk.Button(sidebar, text="Metal", command=lambda: self.toggle_texture('metal')).pack(fill='x', padx=10, pady=2)
        tk.Button(sidebar, text="Papel", command=lambda: self.toggle_texture('paper')).pack(fill='x', padx=10, pady=2)
        
        self.add_lbl(sidebar, "EXTRAS")
        tk.Button(sidebar, text="Importar Imagem", command=self.import_image).pack(fill='x', padx=10, pady=2)
        tk.Button(sidebar, text="Limpar Tela", bg='#c0392b', fg='white', command=self.reset_canvas_to_size).pack(side='bottom', fill='x', padx=10, pady=20)

        # Preview Container (Centralizado)
        cent = tk.Frame(cont, bg='#95a5a6'); cent.pack(side='right', fill='both', expand=True)
        # IMPORTANTE: O Canvas não tem tamanho fixo aqui, ele será ajustado no update_preview
        self.canvas_bg = tk.Canvas(cent, bg='white', bd=0, highlightthickness=0)
        self.canvas_bg.place(relx=0.5, rely=0.5, anchor="center") # Centraliza absoluto
        self.lbl_info_bg = tk.Label(cent, text="", bg='#95a5a6', fg='white'); self.lbl_info_bg.pack(side='bottom', pady=10)

    # --- ABA 2: LAYOUT ---
    def create_card_tab(self):
        frame = tk.Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(frame, text=" 2. Layout ")
        toolbar = tk.Frame(frame, bg='#34495e', height=50); toolbar.pack(fill='x')
        tk.Button(toolbar, text="1 Foto", command=self.preset_1).pack(side='left', padx=5)
        tk.Button(toolbar, text="2 Fotos", command=self.preset_2).pack(side='left', padx=5)
        tk.Button(toolbar, text="3 Fotos", command=self.preset_3).pack(side='left', padx=5)
        tk.Button(toolbar, text="Limpar", command=self.clear_slots, bg='#e74c3c', fg='white').pack(side='right', padx=10)
        tk.Button(toolbar, text="Desfazer", command=self.undo_slot).pack(side='right', padx=5)
        
        da = tk.Frame(frame, bg='#7f8c8d'); da.pack(fill='both', expand=True)
        self.canvas_card = tk.Canvas(da, bg='white', cursor="crosshair", bd=0, highlightthickness=0)
        self.canvas_card.place(relx=0.5, rely=0.5, anchor="center")
        
        self.canvas_card.bind("<Button-1>", self.on_mouse_down)
        self.canvas_card.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas_card.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas_card.bind("<Button-3>", self.on_right_click)

    # --- ABA 3: CONFIGURAÇÕES (SEM PIXELS, SÓ PAPEL) ---
    def create_config_tab(self):
        frame = tk.Frame(self.notebook, bg='#ecf0f1')
        self.notebook.add(frame, text=" 3. Configurações ")
        cont = tk.Frame(frame, bg='#ecf0f1'); cont.pack(expand=True, fill='both', padx=20, pady=20)
        
        col1 = tk.Frame(cont, bg='#ecf0f1'); col1.pack(side='left', fill='both', expand=True, padx=10)
        col2 = tk.Frame(cont, bg='#ecf0f1'); col2.pack(side='left', fill='both', expand=True, padx=10)

        # --- GRUPO PAPEL (FIXO) ---
        gp = tk.LabelFrame(col1, text="🖨️ Papel e Impressão", font=('Arial', 12, 'bold'), bg='white', padx=10, pady=10)
        gp.pack(fill='x', pady=5)
        
        tk.Label(gp, text="Tamanho do Papel:", bg='white').pack(anchor='w')
        self.combo_paper = ttk.Combobox(gp, values=list(self.PAPER_SPECS.keys()), state='readonly', font=('Arial', 11))
        self.combo_paper.pack(fill='x', pady=5)
        self.combo_paper.bind("<<ComboboxSelected>>", self.on_paper_change)
        
        tk.Label(gp, text="Orientação do Papel:", bg='white').pack(anchor='w', pady=(5,0))
        self.combo_orient = ttk.Combobox(gp, values=["Paisagem", "Retrato"], state='readonly', font=('Arial', 11))
        self.combo_orient.pack(fill='x', pady=5)
        self.combo_orient.bind("<<ComboboxSelected>>", self.on_paper_change)
        
        tk.Label(gp, text="Tipo de Papel:", bg='white').pack(anchor='w', pady=(5,0))
        self.combo_type = ttk.Combobox(gp, values=["Comum", "Fotográfico", "Adesivo"], state='readonly'); self.combo_type.current(1); self.combo_type.pack(fill='x')
        
        self.var_border = tk.BooleanVar(value=False)
        tk.Checkbutton(gp, text="Imprimir sem bordas", variable=self.var_border, bg='white').pack(anchor='w', pady=10)

        # Outras Configs
        gt = tk.LabelFrame(col1, text="Tempos", font=('Arial', 11, 'bold'), bg='white', padx=10, pady=10); gt.pack(fill='x', pady=5)
        self.create_input(gt, 0, "Início (s):", "spin_start", 5)
        self.create_input(gt, 1, "Intervalo (s):", "spin_interval", 3)
        
        gm = tk.LabelFrame(col2, text="Mensagens", font=('Arial', 11, 'bold'), bg='white', padx=10, pady=10); gm.pack(fill='x', pady=5)
        self.create_input(gm, 0, "Antes:", "entry_start", "PREPARE-SE!", True)
        self.create_input(gm, 1, "Depois:", "entry_end", "FOTO SALVA!", True)
        
        gs = tk.LabelFrame(col2, text="Estilo", font=('Arial', 11, 'bold'), bg='white', padx=10, pady=10); gs.pack(fill='x', pady=5)
        self.combo_font = ttk.Combobox(gs, values=["Arial", "Comic Sans MS", "Times New Roman"], state='readonly'); self.combo_font.pack(fill='x')
        self.combo_font.current(1)
        tk.Button(gs, text="Cor Texto", command=self.pick_font_color).pack(fill='x', pady=5)

    # --- LÓGICA DE TAMANHO E VISUALIZAÇÃO (CRÍTICO) ---
    def on_paper_change(self, event=None):
        self.current_paper = self.combo_paper.get()
        self.paper_orientation = self.combo_orient.get()
        self.reset_canvas_to_size()

    def reset_canvas_to_size(self):
        # Pega dimensões base
        w, h = self.PAPER_SPECS.get(self.current_paper, (1748, 1181))
        
        # Ajusta orientação
        if self.paper_orientation == "Retrato":
            self.real_width = min(w, h)
            self.real_height = max(w, h)
        else:
            self.real_width = max(w, h)
            self.real_height = min(w, h)
            
        # Cria nova imagem base
        self.base_image = Image.new("RGB", (self.real_width, self.real_height), self.primary_color)
        self.draw = ImageDraw.Draw(self.base_image)
        self.slots = []
        self.active_texture = None
        
        self.update_pipeline()
        self.lbl_info_bg.config(text=f"Papel: {self.current_paper} ({self.paper_orientation}) - {self.real_width}x{self.real_height}px")

    def update_pipeline(self):
        # 1. Processa Imagem
        img = self.base_image.copy(); d = ImageDraw.Draw(img)
        
        # Texturas
        if self.active_texture:
            w, h = self.real_width, self.real_height
            if self.active_texture == 'dots':
                for x in range(0, w, 50):
                    for y in range(0, h, 50): d.ellipse([x,y,x+15,y+15], fill=self.secondary_color)
            elif self.active_texture == 'metal':
                for x in range(0, w, 5):
                    if x%50==0: d.line([(x,0),(x,h)], fill=self.secondary_color, width=3)
            elif self.active_texture == 'paper':
                nz = Image.effect_noise((w,h), 40).convert("RGB")
                img = Image.blend(img, nz, 0.15)
        
        self.display_image = img
        self.show_preview()

    def show_preview(self):
        """Calcula zoom para caber na tela sem cortar"""
        # Espaço útil na tela do editor (chute seguro)
        avail_w = self.screen_w * 0.65 # 65% da largura da tela (lado direito)
        avail_h = self.screen_h * 0.70 # 70% da altura
        
        # Calcula fator de escala (Zoom Fit)
        scale = min(avail_w / self.real_width, avail_h / self.real_height)
        
        self.preview_w = int(self.real_width * scale)
        self.preview_h = int(self.real_height * scale)
        
        # Redimensiona para visualização
        p = self.display_image.resize((self.preview_w, self.preview_h), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(p)
        
        # Configura tamanho dos canvas
        for c in [self.canvas_bg, self.canvas_card]:
            c.config(width=self.preview_w, height=self.preview_h)
            c.delete("all")
            c.create_image(0, 0, anchor="nw", image=self.tk_image, tags="bg")
            c.tag_lower("bg")
            
        self.redraw_slots()

    # --- AUXILIARES (Gradiente, Cores, Etc) ---
    def apply_gradient(self):
        d = self.grad_combo.get(); base = Image.new("RGB", (self.real_width,self.real_height), self.primary_color)
        if d == "Horizontal": g = Image.new("RGB", (2,1), self.primary_color); ImageDraw.Draw(g).point((1,0), fill=self.secondary_color); grad = g.resize((self.real_width,self.real_height), Image.Resampling.BICUBIC)
        elif d == "Vertical": g = Image.new("RGB", (1,2), self.primary_color); ImageDraw.Draw(g).point((0,1), fill=self.secondary_color); grad = g.resize((self.real_width,self.real_height), Image.Resampling.BICUBIC)
        else: g = Image.new("RGB", (2,2), self.primary_color); ImageDraw.Draw(g).point((1,1), fill=self.secondary_color); grad = g.resize((self.real_width,self.real_height), Image.Resampling.BILINEAR)
        self.base_image = grad; self.active_texture = None; self.update_pipeline()

    # ... (Mantém funções de cores, slots, mouse idênticas ao anterior, só ajustando redraw) ...
    def get_slot_at(self,x,y):
        sx=self.preview_w/self.real_width; sy=self.preview_h/self.real_height
        for i in reversed(range(len(self.slots))):
            s=self.slots[i]; rx,ry=s['x']*sx,s['y']*sy; rw,rh=s['w']*sx,s['h']*sy
            if rx<=x<=rx+rw and ry<=y<=ry+rh: return i
        return None
    def on_mouse_down(self,e):
        self.last_mouse_x=e.x; self.last_mouse_y=e.y
        idx=self.get_slot_at(e.x,e.y)
        if idx is not None: self.moving_slot=idx; self.drawing_slot=False; self.redraw_slots()
        else: self.drawing_slot=True; self.moving_slot=None; self.start_x=e.x; self.start_y=e.y
    def on_mouse_drag(self,e):
        if self.moving_slot is not None:
            dx=e.x-self.last_mouse_x; dy=e.y-self.last_mouse_y
            sx=self.real_width/self.preview_w; sy=self.real_height/self.preview_h
            self.slots[self.moving_slot]['x']+=int(dx*sx); self.slots[self.moving_slot]['y']+=int(dy*sy)
            self.last_mouse_x=e.x; self.last_mouse_y=e.y; self.redraw_slots()
        elif self.drawing_slot:
            self.canvas_card.delete("temp"); self.canvas_card.create_rectangle(self.start_x,self.start_y,e.x,e.y, outline="red", tags="temp")
    def on_mouse_up(self,e):
        if self.moving_slot is not None: self.moving_slot=None
        elif self.drawing_slot:
            self.drawing_slot=False; self.canvas_card.delete("temp"); x1,x2=sorted([self.start_x,e.x]); y1,y2=sorted([self.start_y,e.y])
            if x2-x1<20: return
            sx=self.real_width/self.preview_w; sy=self.real_height/self.preview_h
            self.slots.append({"id":len(self.slots)+1,"x":int(x1*sx),"y":int(y1*sy),"w":int((x2-x1)*sx),"h":int((y2-y1)*sy)})
            self.redraw_slots()
    def on_right_click(self,e):
        idx=self.get_slot_at(e.x,e.y); 
        if idx is not None: self.slots.pop(idx); self.redraw_slots()
    def redraw_slots(self):
        self.canvas_card.delete("slot"); sx=self.preview_w/self.real_width; sy=self.preview_h/self.real_height
        for i,s in enumerate(self.slots):
            x,y,w,h=s['x']*sx,s['y']*sy,s['w']*sx,s['h']*sy
            col="#f1c40f" if i==self.moving_slot else "#2ecc71"; wid=5 if i==self.moving_slot else 3
            self.canvas_card.create_rectangle(x,y,x+w,y+h, outline=col, width=wid, tags="slot")
            self.canvas_card.create_text(x+w/2,y+h/2, text=str(s['id']), fill=col, font=('Arial',14,'bold'), tags="slot")
    def undo_slot(self): 
        if self.slots: self.slots.pop(); self.redraw_slots()
    def clear_slots(self): self.slots=[]; self.redraw_slots()
    def pick_color(self,t):
        c=colorchooser.askcolor()[1]
        if c: 
            if t==1: self.primary_color=c; self.btn_cor1.config(bg=c)
            else: self.secondary_color=c; self.btn_cor2.config(bg=c)
    def pick_font_color(self): c=colorchooser.askcolor()[1]; self.font_color=c if c else self.font_color
    def apply_solid(self): 
        self.active_texture=None; self.draw.rectangle([0,0,self.real_width,self.real_height], fill=self.primary_color)
        self.base_image=Image.new("RGB",(self.real_width,self.real_height),self.primary_color); self.update_pipeline()
    def toggle_texture(self, t): self.active_texture=None if self.active_texture==t else t; self.update_pipeline()
    def import_image(self):
        f=filedialog.askopenfilename(filetypes=[("Img", "*.jpg *.png")])
        if f: i=Image.open(f).resize((self.real_width,self.real_height)); self.base_image=i; self.active_texture=None; self.update_pipeline()
    def reset_canvas_to_size_button(self): self.reset_canvas_to_size() # Wrapper
    def add_lbl(self, p, t): tk.Label(p, text=t, bg='#95a5a6', fg='white', font=('Arial', 10, 'bold')).pack(fill='x', pady=(15,2))
    def create_input(self, p, r, l, a, d, txt=False):
        tk.Label(p, text=l, bg='white').grid(row=r, column=0, sticky='e'); w=tk.Entry(p) if txt else tk.Spinbox(p, from_=1,to=60,width=5); w.insert(0,d); w.grid(row=r,column=1,sticky='w'); setattr(self,a,w)
    
    # PRESETS
    def preset_1(self): self.slots=[{"id":1,"x":50,"y":50,"w":self.real_width-100,"h":self.real_height-100}]; self.redraw_slots()
    def preset_2(self):
        m=50; self.slots=[]
        if self.real_height > self.real_width:
            h=(self.real_height-(m*3))//2; self.slots=[{"id":1,"x":m,"y":m,"w":self.real_width-(m*2),"h":h},{"id":2,"x":m,"y":m+h+m,"w":self.real_width-(m*2),"h":h}]
        else:
            w=(self.real_width-(m*3))//2; self.slots=[{"id":1,"x":m,"y":m,"w":w,"h":self.real_height-(m*2)},{"id":2,"x":m+w+m,"y":m,"w":w,"h":self.real_height-(m*2)}]
        self.redraw_slots()
    def preset_3(self):
        m=40; self.slots=[]
        if self.real_height > self.real_width:
            h=(self.real_height-(m*4))//3; w=int(self.real_width*0.7)
            self.slots=[{"id":1,"x":m,"y":m,"w":w,"h":h},{"id":2,"x":self.real_width-w-m,"y":m+h+m,"w":w,"h":h},{"id":3,"x":m,"y":m+(h+m)*2,"w":w,"h":h}]
        else:
            w=(self.real_width-(m*4))//3; h=int(self.real_height*0.7)
            self.slots=[{"id":1,"x":m,"y":m,"w":w,"h":h},{"id":2,"x":m+w+m,"y":self.real_height-h-m,"w":w,"h":h},{"id":3,"x":m+(w+m)*2,"y":m,"w":w,"h":h}]
        self.redraw_slots()

    def load_existing_config(self):
        try:
            p = os.path.join(self.template_dir, "config_card.json")
            if os.path.exists(p):
                with open(p) as f: d = json.load(f)
                self.spin_start.delete(0,"end"); self.spin_start.insert(0, d.get('countdown_start',5))
                self.spin_interval.delete(0,"end"); self.spin_interval.insert(0, d.get('countdown_interval',3))
                self.entry_start.delete(0,"end"); self.entry_start.insert(0, d.get('msg_start',''))
                self.entry_end.delete(0,"end"); self.entry_end.insert(0, d.get('msg_end',''))
                self.slots = d.get('slots',[])
                self.combo_font.set(d.get('font_family','Arial'))
                self.font_color = d.get('font_color','#ffffff')
                
                # Papel
                self.current_paper = d.get('print_paper_size', "A6 (10x15cm)")
                self.combo_paper.set(self.current_paper)
                self.paper_orientation = d.get('paper_orientation', "Paisagem")
                self.combo_orient.set(self.paper_orientation)
                self.combo_type.set(d.get('print_paper_type', 'Fotográfico'))
                self.var_border.set(d.get('print_borderless', False))
                
                self.reset_canvas_to_size()
                
                bg = os.path.join(self.template_dir, "background.png")
                if os.path.exists(bg):
                    i = Image.open(bg).resize((self.real_width,self.real_height))
                    self.base_image = i
                    self.update_pipeline()
        except: pass

    def save_all(self):
        try:
            bg_p = os.path.join(self.template_dir, "background.png")
            self.display_image.save(bg_p)
            try: c_st = int(self.spin_start.get())
            except: c_st=5
            try: c_it = int(self.spin_interval.get())
            except: c_it=3
            d = {
                "slots": self.slots, "countdown_start": c_st, "countdown_interval": c_it,
                "msg_start": self.entry_start.get(), "msg_end": self.entry_end.get(),
                "font_family": self.combo_font.get(), "font_color": self.font_color,
                "print_paper_size": self.combo_paper.get(),
                "print_paper_type": self.combo_type.get(),
                "print_borderless": self.var_border.get(),
                "paper_orientation": self.combo_orient.get(),
                "card_width": self.real_width, "card_height": self.real_height
            }
            jp = os.path.join(self.template_dir, "config_card.json")
            with open(jp,'w') as f: json.dump(d, f, indent=4)
            try: os.chmod(bg_p, 0o777); os.chmod(jp, 0o777)
            except: pass
            messagebox.showinfo("Sucesso", "✅ Layout Salvo! Atualize o Totem.")
            self.window.destroy()
        except Exception as e: messagebox.showerror("Erro", str(e))
