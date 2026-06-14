# -*- coding: utf-8 -*-
"""
================================================================================
   GLOBAL REAL-TIME TRANSLATOR & OVERLAY FOR PC (WINDOWS) - V5 (Sade & Akıllı)
   Created by: Colin
   
   Bu script bilgisayarınızda arka planda ve minimalist bir kontrol panelinde (GUI) çalışır.
   Yenilikler (V5.1 - Oyunlarda Silme Düzeltmesi):
   1. OYUNLARDA SİLME HATASI ÇÖZÜLDÜ (Albion Online vb.): Oyunlardaki FPS limitlerinden kaynaklanan
      harf kaçırma (sHello gibi başta harf kalması) sorunu çözüldü! Silme hızı oyun motorlarının
      giriş algılama frekansına (20ms gecikme) uyarlandı ve çakışmayı önlemek için CTRL tuşu 
      silme esnasında mantıksal olarak serbest bırakıldı.
   2. SİSTEM TEPSİSİNE KÜÇÜLME (SYSTEM TRAY): Uygulama simge durumuna küçültüldüğünde 
      ekran kartından/görev çubuğundan gizlenir ve "Gizli Simgeler" (System Tray) arasına katılır.
      Arka planda sessizce çalışmaya devam eder. Çift tıklayarak veya sağ tıklayarak geri açılabilir.
   3. OTOMATİK AKILLI DİL ALGILAMA (SIFIR AYAR): Seçim dilinde artık "Otomatik Akıllı Mod" aktif!
      Gelen mesaj Arapça, İngilizce, Rusça, Almanca veya İspanyolca ne olursa olsun sistem otomatik 
      algılar ve ek ayar yapmanıza gerek kalmadan doğrudan TÜRKÇE'ye çevirir. 
      Eğer seçtiğiniz kelime Türkçe ise otomatik olarak İNGİLİZCEYE (veya seçilen giden dile) çevirir.
   4. SADE & ÖZEL MİNİMALİST TASARIM: Kalabalık kılavuz metinleri kaldırıldı. Pencere boyutu 
      küçültülerek çok daha kompakt, temiz ve özel bir dashboard arayüzü oluşturuldu.
================================================================================
"""

import sys
import os
import time
import json
import threading
import urllib.request
import urllib.parse
import tkinter as tk
from tkinter import ttk, messagebox
import pyperclip
from pynput import keyboard, mouse
from pynput.keyboard import Controller, Key

# --- SİSTEM TEPSİSİ (TRAY) VE RESİM MODÜLLERİNİ GÜVENLİ YÜKLE ---
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_SUPPORTED = True
except ImportError:
    TRAY_SUPPORTED = False

# --- DİL SÖZLÜĞÜ VE KODLARI ---
LANGUAGES = {
    "İngilizce": "en",
    "Almanca": "de",
    "Fransızca": "fr",
    "İspanyolca": "es",
    "Rusça": "ru",
    "Arapça": "ar",
    "Türkçe": "tr"
}

# --- DİNAMİK SİSTEM TEPSİSİ İKONU OLUŞTURMA ---
def create_tray_image():
    # 64x64 boyutunda mavi arka planlı şık bir "T" ikonu çiz
    img = Image.new('RGBA', (64, 64), color=(30, 30, 46, 255))
    d = ImageDraw.Draw(img)
    d.ellipse([8, 8, 56, 56], fill=(137, 180, 250, 255)) # Accent mavi
    try:
        d.line([(32, 16), (32, 48)], fill=(255, 255, 255, 255), width=6)
        d.line([(20, 16), (44, 16)], fill=(255, 255, 255, 255), width=6)
    except Exception:
        pass
    return img

# --- API ÇEVİRİ FONKSİYONU ---
def translate_text(text, source_lang='auto', target_lang='tr'):
    if not text.strip():
        return ""
    try:
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source_lang}&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            translated = "".join([part[0] for part in data[0] if part[0]])
            
            detected_lang = 'auto'
            if len(data) > 2 and isinstance(data[2], str):
                detected_lang = data[2]
                
            return translated, detected_lang
    except Exception:
        return f"[Çeviri Hatası]", 'auto'

# --- KLAVYE KANCASI ---
class KeyTracker:
    def __init__(self, on_update, on_replace_trigger, on_exit_trigger, root_ref):
        self.buffer = ""
        self.on_update = on_update
        self.on_replace_trigger = on_replace_trigger
        self.on_exit_trigger = on_exit_trigger
        self.root = root_ref
        
        self.ctrl_pressed = False
        self.shift_pressed = False
        self.active = True
        self.last_key_time = time.time()
        
        self.check_loop()
        
    def check_loop(self):
        try:
            if self.active and self.buffer and (time.time() - self.last_key_time > 12.0):
                self.buffer = ""
                self.on_update("")
        except Exception:
            pass
        self.root.after(100, self.check_loop)
        
    def on_press(self, key):
        if not self.active:
            return
            
        try:
            self.last_key_time = time.time()
            
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = True
                return
            if key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                self.shift_pressed = True
                return
                
            char_pressed = None
            if hasattr(key, 'char') and key.char is not None:
                char_pressed = key.char.lower()
                
            is_e = (char_pressed == 'e' or char_pressed == '\x05')
            
            if self.ctrl_pressed and self.shift_pressed and is_e:
                self.on_exit_trigger()
                return
                
            if self.ctrl_pressed and key == keyboard.Key.space:
                self.on_replace_trigger()
                return
                
            if self.ctrl_pressed:
                return
                
            if hasattr(key, 'char') and key.char is not None:
                self.buffer += key.char
                self.on_update(self.buffer)
            elif key == keyboard.Key.space:
                self.buffer += " "
                self.on_update(self.buffer)
            elif key == keyboard.Key.backspace:
                if len(self.buffer) > 0:
                    self.buffer = self.buffer[:-1]
                    self.on_update(self.buffer)
            elif key in [keyboard.Key.enter, keyboard.Key.esc, keyboard.Key.tab]:
                self.buffer = ""
                self.on_update("")
        except Exception:
            pass
            
    def on_release(self, key):
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.ctrl_pressed = False
        if key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
            self.shift_pressed = False

# --- FARE KANCASI ---
class MouseSelectionTracker:
    def __init__(self, on_text_selected):
        self.on_text_selected = on_text_selected
        self.press_time = 0
        self.press_pos = (0, 0)
        self.last_release_time = 0
        self.kb_controller = Controller()
        self.active = True
        
    def on_click(self, x, y, button, pressed):
        if not self.active:
            return
            
        if button != mouse.Button.left:
            return
            
        if pressed:
            self.press_time = time.time()
            self.press_pos = (x, y)
        else:
            now = time.time()
            elapsed = now - self.press_time
            dx = x - self.press_pos[0]
            dy = y - self.press_pos[1]
            distance = (dx**2 + dy**2)**0.5
            
            is_double_click = (now - self.last_release_time < 0.35)
            self.last_release_time = now
            
            if (distance > 15 and elapsed > 0.1) or is_double_click:
                threading.Thread(target=self.trigger_copy_and_translate, args=(x, y)).start()
                
    def trigger_copy_and_translate(self, x, y):
        time.sleep(0.12)
        old_clipboard = pyperclip.paste()
        pyperclip.copy("")
        
        self.kb_controller.press(Key.ctrl)
        self.kb_controller.press('c')
        self.kb_controller.release('c')
        self.kb_controller.release(Key.ctrl)
        
        time.sleep(0.12)
        
        copied_text = pyperclip.paste().strip()
        if copied_text and copied_text != old_clipboard:
            self.on_text_selected(copied_text, x, y)
        else:
            pyperclip.copy(old_clipboard)

# --- EŞZAMANLI ÇEVİRİ MOTORU ---
class ThreadedTranslator:
    def __init__(self, callback, get_target_lang):
        self.callback = callback
        self.get_target_lang = get_target_lang
        self.lock = threading.Lock()
        self.pending_text = ""
        self.running = True
        self.thread = threading.Thread(target=self._worker)
        self.thread.daemon = True
        self.thread.start()
        
    def request_translation(self, text):
        with self.lock:
            self.pending_text = text
            
    def _worker(self):
        last_processed = ""
        while self.running:
            text_to_translate = None
            with self.lock:
                if self.pending_text != last_processed:
                    text_to_translate = self.pending_text
                    last_processed = text_to_translate
            
            if text_to_translate is not None:
                if not text_to_translate.strip():
                    self.callback("")
                else:
                    time.sleep(0.2)
                    with self.lock:
                        if self.pending_text != text_to_translate:
                            continue
                    target_code = LANGUAGES.get(self.get_target_lang(), "en")
                    translated, _ = translate_text(text_to_translate, 'tr', target_code)
                    self.callback(translated)
            time.sleep(0.02)

# --- ANA KONTROL PANELİ VE OVERLAY UYGULAMASI ---
class TranslationApp:
    def __init__(self):
        # 1. Ana Pencere Ayarları (Kompakt ve Sade)
        self.root = tk.Tk()
        self.root.title("🔄 Global Çevirici")
        self.root.geometry("380x370")
        self.root.configure(bg="#1E1E2E")
        self.root.resizable(False, False)
        
        # Tema Renkleri
        self.c_bg = "#1E1E2E"
        self.c_card = "#252538"
        self.c_accent = "#89B4FA"
        self.c_green = "#A6E3A1"
        self.c_red = "#F38BA8"
        self.c_text = "#CDD6F4"
        self.c_subtext = "#BAC2DE"
        
        # Değişkenler
        self.typing_target_var = tk.StringVar(value="İngilizce")
        self.is_paused = False
        
        self.tracker = None
        self.mouse_tracker = None
        self.tray_icon = None
        
        # Arayüzü İnşa Et
        self.build_ui()
        
        # Pencere Minimize Etkinlik Bağı
        self.root.bind("<Unmap>", self.on_minimize)
        
        # 2. Giden Mesaj Pop-up Overlay
        self.typing_win = tk.Toplevel(self.root)
        self.typing_win.overrideredirect(True)
        self.typing_win.attributes("-topmost", True)
        self.typing_win.attributes("-alpha", 0.94)
        self.typing_win.configure(bg="#1E1E2E")
        
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        w, h = 550, 70
        x = (screen_w - w) // 2
        y = screen_h - h - 85
        self.typing_win.geometry(f"{w}x{h}+{x}+{y}")
        
        self.top_frame = tk.Frame(self.typing_win, bg="#1E1E2E")
        self.top_frame.pack(fill="x", padx=12, pady=(6, 0))
        
        self.lbl_title = tk.Label(
            self.top_frame, 
            text="YAZILAN ÇEVİRİSİ (Ctrl+Boşluk ile Değiştir):", 
            font=("Segoe UI", 8, "bold"), fg=self.c_accent, bg="#1E1E2E"
        )
        self.lbl_title.pack(side="left")
        
        self.btn_clear = tk.Button(
            self.top_frame, 
            text="Temizle (ESC)", 
            font=("Segoe UI", 7, "bold"), fg=self.c_red, bg="#313244", 
            activeforeground="#1E1E2E", activebackground=self.c_red,
            bd=0, padx=6, pady=1, cursor="hand2",
            command=self.clear_buffer_manually
        )
        self.btn_clear.pack(side="right")
        
        self.lbl_translation = tk.Label(
            self.typing_win, 
            text="", 
            font=("Segoe UI", 11, "italic"), fg=self.c_text, bg="#1E1E2E", 
            anchor="w", justify="left"
        )
        self.lbl_translation.pack(fill="x", padx=12, pady=(2, 6))
        
        self.typing_win.bind("<Button-1>", lambda e: self.replace_text())
        self.typing_win.withdraw()
        
        # 3. Gelen Mesaj Pop-up Overlay
        self.hover_win = tk.Toplevel(self.root)
        self.hover_win.overrideredirect(True)
        self.hover_win.attributes("-topmost", True)
        self.hover_win.attributes("-alpha", 0.96)
        self.hover_win.configure(bg="#11111B")
        
        self.lbl_hover = tk.Label(
            self.hover_win, 
            text="", 
            font=("Segoe UI", 11, "bold"), fg=self.c_green, bg="#11111B", 
            wraplength=380, justify="left", anchor="w"
        )
        self.lbl_hover.pack(padx=16, pady=12)
        
        self.hover_win.bind("<Button-1>", lambda e: self.hover_win.withdraw())
        self.hover_win.withdraw()
        
        self.last_translation = ""
        self.hover_timer = None
        self.kb_controller = Controller()
        
        self.translator_engine = ThreadedTranslator(self.on_translation_ready, lambda: self.typing_target_var.get())
        
        # Sistem Tepsisini (Tray) Başlat
        if TRAY_SUPPORTED:
            self.setup_tray()

    def set_trackers(self, tracker, mouse_tracker):
        self.tracker = tracker
        self.mouse_tracker = mouse_tracker

    def build_ui(self):
        # Üst Minimalist Başlık
        title_lbl = tk.Label(
            self.root, 
            text="GLOBAL TRANSLATOR V5", 
            font=("Segoe UI", 12, "bold"), fg=self.c_accent, bg=self.c_bg
        )
        title_lbl.pack(pady=(15, 2))
        
        subtitle_lbl = tk.Label(
            self.root, 
            text="Sadeleştirilmiş Arka Plan Modu", 
            font=("Segoe UI", 8), fg=self.c_subtext, bg=self.c_bg
        )
        subtitle_lbl.pack(pady=(0, 15))
        
        # TEK KOMBİNE AYAR KARTI
        card = tk.Frame(self.root, bg=self.c_card, bd=0)
        card.pack(fill="x", padx=15, pady=5)
        
        # Giden Mesaj Ayarı
        frame_write = tk.Frame(card, bg=self.c_card)
        frame_write.pack(fill="x", padx=15, pady=10)
        
        tk.Label(frame_write, text="✍️ Yazma Çevirisi:", font=("Segoe UI", 9, "bold"), fg=self.c_accent, bg=self.c_card).pack(side="left")
        self.combo_write_target = ttk.Combobox(
            frame_write, 
            textvariable=self.typing_target_var, 
            values=list(LANGUAGES.keys())[:-1], 
            width=10, state="readonly"
        )
        self.combo_write_target.pack(side="right")
        
        # Gelen Mesaj Ayarı (Otomatik Akıllı Mod Bilgisi)
        frame_select = tk.Frame(card, bg=self.c_card)
        frame_select.pack(fill="x", padx=15, pady=(0, 10))
        
        tk.Label(frame_select, text="🖱️ Gelen Çeviri:", font=("Segoe UI", 9, "bold"), fg=self.c_green, bg=self.c_card).pack(side="left")
        tk.Label(frame_select, text="[Otomatik Akıllı Mod]", font=("Segoe UI", 9, "italic"), fg=self.c_green, bg=self.c_card).pack(side="right")

        # DURUM GÖSTERGESİ VE LED PANELİ
        status_frame = tk.Frame(self.root, bg=self.c_bg)
        status_frame.pack(fill="x", padx=20, pady=8)
        
        self.status_canvas = tk.Canvas(status_frame, width=12, height=12, bg=self.c_bg, highlightthickness=0)
        self.status_canvas.pack(side="left", padx=(5, 5))
        self.status_led = self.status_canvas.create_oval(2, 2, 10, 10, fill=self.c_green, outline="")
        
        self.lbl_status_text = tk.Label(
            status_frame, text="Sistem Aktif - Arka Planda Dinliyor", 
            font=("Segoe UI", 8, "bold"), fg=self.c_green, bg=self.c_bg
        )
        self.lbl_status_text.pack(side="left")
        
        # KONTROL DÜĞMELERİ
        self.btn_pause = tk.Button(
            self.root, 
            text="Sistemi Duraklat", 
            font=("Segoe UI", 9, "bold"), fg=self.c_bg, bg=self.c_accent,
            activeforeground=self.c_text, activebackground="#313244",
            bd=0, height=2, cursor="hand2", command=self.toggle_pause
        )
        self.btn_pause.pack(fill="x", padx=15, pady=5)
        
        # Kapatma Butonu
        btn_close = tk.Button(
            self.root, 
            text="UYGULAMAYI KAPAT", 
            font=("Segoe UI", 9, "bold"), fg=self.c_text, bg=self.c_red,
            activeforeground="#1E1E2E", activebackground="#E06C75",
            bd=0, height=2, cursor="hand2", command=self.terminate
        )
        btn_close.pack(fill="x", padx=15, pady=5)
        
        # Tray Modül Uyarısı
        if not TRAY_SUPPORTED:
            lbl_warning = tk.Label(
                self.root, 
                text="⚠️ Sistem tepsisi için terminale şunu yazın:\npip install pystray pillow", 
                font=("Segoe UI", 7, "bold"), fg=self.c_red, bg=self.c_bg, justify="center"
            )
            lbl_warning.pack(pady=5)
        else:
            lbl_info = tk.Label(
                self.root, 
                text="ℹ️ Simge durumuna küçüldüğünde arka planda çalışmaya devam eder.", 
                font=("Segoe UI", 7, "italic"), fg=self.c_subtext, bg=self.c_bg
            )
            lbl_info.pack(pady=5)

    def setup_tray(self):
        # Tray sağ tık menüsü
        menu = pystray.Menu(
            pystray.MenuItem("Göster / Aç", self.restore_from_tray, default=True),
            pystray.MenuItem("Duraklat / Başlat", self.toggle_pause),
            pystray.MenuItem("Kapat", self.terminate)
        )
        img = create_tray_image()
        self.tray_icon = pystray.Icon("global_translator", img, "Global Çevirici", menu)
        
        # Arayüz donmasını önlemek için ayrı thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def on_minimize(self, event):
        if TRAY_SUPPORTED and self.root.state() == 'iconic':
            self.root.withdraw() # Pencereyi gizle

    def restore_from_tray(self):
        self.root.deiconify()
        self.root.state('normal')
        self.root.command = self.root.lift()
        self.root.focus_force()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        
        if self.tracker:
            self.tracker.active = not self.is_paused
        if self.mouse_tracker:
            self.mouse_tracker.active = not self.is_paused
            
        if self.is_paused:
            self.status_canvas.itemconfig(self.status_led, fill=self.c_red)
            self.lbl_status_text.config(text="Sistem Durduruldu - Pasif", fg=self.c_red)
            self.btn_pause.config(text="Sistemi Başlat", bg=self.c_green)
            self.typing_win.withdraw()
            self.hover_win.withdraw()
        else:
            self.status_canvas.itemconfig(self.status_led, fill=self.c_green)
            self.lbl_status_text.config(text="Sistem Aktif - Arka Planda Dinliyor", fg=self.c_green)
            self.btn_pause.config(text="Sistemi Duraklat", bg=self.c_accent)
            
    def clear_buffer_manually(self):
        if self.tracker:
            self.tracker.buffer = ""
        self.handle_typing_update("")
        
    def on_translation_ready(self, translated_text):
        self.last_translation = translated_text
        if not translated_text:
            self.typing_win.withdraw()
        else:
            self.lbl_translation.config(text=translated_text)
            if not self.typing_win.winfo_viewable() and not self.is_paused:
                self.typing_win.deiconify()
                
    def handle_typing_update(self, buffer_text):
        self.translator_engine.request_translation(buffer_text)
        
    def replace_text(self):
        if not self.last_translation or self.is_paused:
            return
            
        self.typing_win.withdraw()
        
        buffer_len = len(self.tracker.buffer) if self.tracker else 0
        if self.tracker:
            self.tracker.buffer = ""
        
        # --- OYUNLAR İÇİN BULLETPROOF SİLME VE CTRL ÇAKIŞMASI DÜZELTMESİ ---
        # 1. Fiziksel veya yazılımsal CTRL tuşunu geçici olarak bırak (Çok kritik!)
        self.kb_controller.release(Key.ctrl)
        time.sleep(0.04) # İşletim sisteminin CTRL'nin bırakıldığını anlaması için kısa bir ara ver
        
        # 2. Silme Simülasyonu (Hızı 20 milisaniyeye sabitledik, böylece Albion vb. oyunlar harf kaçırmaz)
        for _ in range(buffer_len):
            self.kb_controller.press(Key.backspace)
            self.kb_controller.release(Key.backspace)
            time.sleep(0.02)
            
        # 3. Çevrilen metni panoya kopyala ve Ctrl+V ile yapıştır
        old_clipboard = pyperclip.paste()
        pyperclip.copy(self.last_translation)
        
        with self.kb_controller.pressed(Key.ctrl):
            self.kb_controller.press('v')
            self.kb_controller.release('v')
            
        def restore_clipboard():
            time.sleep(0.5)
            pyperclip.copy(old_clipboard)
        threading.Thread(target=restore_clipboard).start()
        
    def translate_hovered_text(self, text, x, y):
        if self.is_paused:
            return
            
        def fetch_hover():
            translated, detected_lang = translate_text(text, source_lang='auto', target_lang='tr')
            
            if detected_lang == "tr":
                giden_dil_ismi = self.typing_target_var.get()
                giden_dil_kodu = LANGUAGES.get(giden_dil_ismi, "en")
                translated, _ = translate_text(text, source_lang='tr', target_lang=giden_dil_kodu)
            
            self.root.after(0, lambda: self.show_hover_popup(translated, x, y))
            
        threading.Thread(target=fetch_hover).start()
        
    def show_hover_popup(self, text, x, y):
        if self.is_paused:
            return
            
        self.lbl_hover.config(text=text)
        self.hover_win.geometry(f"+{x + 15}+{y - 25}")
        self.hover_win.deiconify()
        
        if self.hover_timer:
            self.root.after_cancel(self.hover_timer)
        self.hover_timer = self.root.after(6000, self.hover_win.withdraw)
        
    def terminate(self):
        if TRAY_SUPPORTED and self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        sys.exit(0)
        
    def run(self):
        self.root.mainloop()

# --- ANA PROGRAM BAŞLANGICI ---
if __name__ == "__main__":
    app = TranslationApp()
    
    tracker = KeyTracker(
        on_update=app.handle_typing_update,
        on_replace_trigger=app.replace_text,
        on_exit_trigger=app.terminate,
        root_ref=app.root
    )
    
    mouse_tracker = MouseSelectionTracker(
        on_text_selected=app.translate_hovered_text
    )
    
    app.set_trackers(tracker, mouse_tracker)
    
    # Global Klavye Dinleyicisi
    kbd_listener = keyboard.Listener(
        on_press=tracker.on_press,
        on_release=tracker.on_release
    )
    kbd_listener.start()
    
    # Global Fare Dinleyicisi
    mouse_listener = mouse.Listener(
        on_click=mouse_tracker.on_click
    )
    mouse_listener.start()
    
    app.run()
