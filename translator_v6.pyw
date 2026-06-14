# -*- coding: utf-8 -*-
"""
================================================================================
   GLOBAL REAL-TIME TRANSLATOR & OVERLAY FOR PC (WINDOWS) - V6 (Albion OCR Edition)
   Created by: Colin
   
   Bu script bilgisayarınızda arka planda ve minimalist bir kontrol panelinde (GUI) çalışır.
   Yenilikler (V6 - Albion Online Seçilemeyen Yazı Çeviri Modu):
   1. OYUN İÇİ SEÇİLEMEYEN MESAJ ÇEVİRİSİ (HOVER OCR): Albion Online gibi oyunlarda chat ekranındaki 
      yazıları fare ile seçme şansınız yoktur. Bu sürümde bu sorunu KÖKLÜCE ÇÖZDÜK!
      Artık farenizi oyun içindeki yabancı mesajın üzerine götürüp "Ctrl + Q" tuşlarına basmanız yeterli!
      Program fare imlecinin altındaki bölgenin milisaniyelik ekran görüntüsünü alır, 
      Windows'un yerleşik yüksek performanslı UWP OCR (Yazı Algılama) motorunu kullanarak yazıyı okur, 
      otomatik Türkçe'ye çevirir ve yeşil renkli pop-up'ı fare imlecinizin tam üstünde açar!
   2. SIFIR EK KÜTÜPHANE YÜKLEME: Windows 10/11'in kendi yerleşik OCR motorunu PowerShell 
      üzerinden arka planda çalıştırdığımız için bilgisayarınıza hiçbir ağır yapay zeka/OCR 
      kütüphanesi kurmanıza gerek kalmaz! Tamamen çevrimdışı, hafif ve ışık hızındadır.
   3. IŞIK HIZINDA OYUN DEĞİŞTİRME (Ctrl+A Yöntemi): Yazılan Türkçe mesajlar "Ctrl+Space" 
      kısayoluyla milisaniyeler içinde anında İngilizceye (veya hedef dile) değiştirilir.
   4. KONSOLSUZ ARKA PLAN (.pyw): CMD ekranı açılmadan arka planda çalışır, gizli simgelere küçülür.
================================================================================
"""

import sys
import os
import time
import json
import threading
import subprocess
import tempfile
import traceback
import ctypes
import shutil
import urllib.request
import urllib.parse
import urllib.error
import tkinter as tk
from tkinter import ttk
import pyperclip
from pynput import keyboard, mouse
from pynput.keyboard import Controller, Key

# --- SİSTEM TEPSİSİ (TRAY) VE RESİM MODÜLLERİNİ GÜVENLİ YÜKLE ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

try:
    import pystray
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageGrab, ImageOps, ImageStat
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

if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
    RESOURCE_DIR = getattr(sys, "_MEIPASS", APP_DIR)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = APP_DIR
CONFIG_PATH = os.path.join(APP_DIR, "settings.json")
LOG_PATH = os.path.join(APP_DIR, "global_translator.log")
ICON_PATH = os.path.join(RESOURCE_DIR, "assets", "monstranslate_icon.ico")
ICON_PNG_PATH = os.path.join(RESOURCE_DIR, "assets", "monstranslate_icon.png")
EASYOCR_MODEL_DIR = os.path.join(RESOURCE_DIR, "assets", "easyocr_models")
LAST_OCR_CAPTURE_PATH = os.path.join(APP_DIR, "last_ocr_capture.png")
LAST_OCR_RAW_CAPTURE_PATH = os.path.join(APP_DIR, "last_ocr_raw_capture.png")
OCR_DEBUG_LOG_PATH = os.path.join(APP_DIR, "ocr_debug.log")
EASYOCR_READER = None

DEFAULT_CONFIG = {
    "typing_target": "İngilizce",
    "translation_engine": "google_free",
    "gemini_api_key": "",
    "gemini_model": "gemini-3.5-flash",
    "fallback_to_google": True,
    "replace_mode": "select_all",
    "ocr_enabled": True,
    "ocr_engine": "auto",
    "ocr_profile": "chat_line",
    "ocr_preprocess": True,
    "ocr_fixed_area": None,
    "ocr_width": 600,
    "ocr_height": 36,
    "ocr_left_offset": 100,
    "popup_seconds": 2,
    "typing_popup_seconds": 2,
    "typing_popup_enabled": True,
    "typing_buffer_seconds": 12,
    "shortcut_replace": "Ctrl+Space",
    "shortcut_ocr": "Ctrl+Q",
    "shortcut_select_ocr_area": "Ctrl+Shift+Q",
    "shortcut_exit": "Ctrl+Shift+E"
}

TRANSLATION_ENGINES = {
    "Google Ücretsiz": "google_free",
    "Google AI Studio": "gemini",
    "MyMemory Ücretsiz": "mymemory"
}

OCR_ENGINES = {
    "Otomatik (Ã–nerilen)": "auto",
    "EasyOCR (Yerel)": "easyocr",
    "Tesseract (Yerel)": "tesseract",
    "Windows OCR (Yedek)": "windows"
}

REPLACE_MODES = {
    "Seçili alanı değiştir": "select_all",
    "Sadece panoya kopyala": "clipboard_only"
}

OCR_PROFILES = {
    "Küçük Chat Satırı": {"code": "chat_line", "width": 600, "height": 36, "left_offset": 100},
    "Geniş Chat Alanı": {"code": "wide_chat", "width": 900, "height": 90, "left_offset": 180},
    "Fare Çevresi": {"code": "around_cursor", "width": 420, "height": 160, "left_offset": 210}
}

SHORTCUT_ACTIONS = {
    "shortcut_replace": "Yazılan çeviriyi uygula",
    "shortcut_ocr": "Fare altındaki metni OCR ile çevir",
    "shortcut_select_ocr_area": "OCR alanı seç",
    "shortcut_exit": "Uygulamadan çık"
}


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
            loaded = json.load(config_file)
    except (OSError, json.JSONDecodeError):
        loaded = {}

    config = DEFAULT_CONFIG.copy()
    if isinstance(loaded, dict):
        config.update({key: loaded[key] for key in config if key in loaded})
    return config


def save_config(config):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as config_file:
            json.dump(config, config_file, ensure_ascii=False, indent=2)
    except OSError:
        pass


def normalize_shortcut(shortcut):
    parts = []
    seen = set()
    aliases = {
        "control": "ctrl",
        "ctrl": "ctrl",
        "shift": "shift",
        "alt": "alt",
        "option": "alt",
        "space": "space",
        "esc": "esc",
        "escape": "esc",
        "enter": "enter",
        "return": "enter",
        "tab": "tab"
    }
    for raw_part in str(shortcut).replace(" ", "").split("+"):
        if not raw_part:
            continue
        part = aliases.get(raw_part.lower(), raw_part.lower())
        if len(part) == 1:
            part = part.upper()
        if part not in seen:
            parts.append(part)
            seen.add(part)
    modifiers = [part for part in ("ctrl", "shift", "alt") if part in seen]
    keys = [part for part in parts if part not in {"ctrl", "shift", "alt"}]
    return "+".join(modifiers + keys)


def key_name_from_event(key):
    if key == keyboard.Key.space:
        return "space"
    if key == keyboard.Key.esc:
        return "esc"
    if key == keyboard.Key.enter:
        return "enter"
    if key == keyboard.Key.tab:
        return "tab"
    if hasattr(key, "char") and key.char is not None:
        char = key.char
        if len(char) == 1 and ord(char) < 32:
            return chr(ord(char) + 64)
        return char.upper()
    return None


def shortcut_matches(shortcut, key, ctrl_pressed, shift_pressed, alt_pressed):
    normalized = normalize_shortcut(shortcut)
    if not normalized:
        return False
    parts = set(normalized.split("+"))
    key_name = key_name_from_event(key)
    if not key_name:
        return False
    expected_keys = parts - {"ctrl", "shift", "alt"}
    return (
        len(expected_keys) == 1
        and key_name in expected_keys
        and ("ctrl" in parts) == ctrl_pressed
        and ("shift" in parts) == shift_pressed
        and ("alt" in parts) == alt_pressed
    )


def log_error(context, error=None):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {context}\n")
            if error is not None:
                log_file.write("".join(traceback.format_exception_only(type(error), error)))
            log_file.write("\n")
    except OSError:
        pass


def log_ocr_debug(message, data=None):
    try:
        with open(OCR_DEBUG_LOG_PATH, "a", encoding="utf-8") as log_file:
            log_file.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")
            if data is not None:
                try:
                    log_file.write(" " + json.dumps(data, ensure_ascii=False, default=str))
                except TypeError:
                    log_file.write(f" {data}")
            log_file.write("\n")
    except OSError:
        pass


def check_windows_ocr_available():
    ps_script = """
    [void][Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType=WindowsRuntime]
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
    if ($null -eq $engine) {
        Write-Output "MISSING"
    } else {
        Write-Output "OK"
    }
    """
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        process = subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", ps_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            startupinfo=startupinfo
        )
        stdout, stderr = process.communicate(timeout=8)
        if process.returncode != 0:
            log_error(f"OCR support check failed: {stderr.strip()}")
            return False
        return stdout.strip() == "OK"
    except Exception as e:
        log_error("OCR support check crashed", e)
        return False


def find_tesseract_executable():
    candidates = [
        shutil.which("tesseract"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return ""


def check_easyocr_available():
    try:
        import importlib.util
        if not importlib.util.find_spec("easyocr"):
            return False
        model_dir = EASYOCR_MODEL_DIR if os.path.exists(EASYOCR_MODEL_DIR) else os.path.join(os.path.expanduser("~"), ".EasyOCR", "model")
        needed = ["craft_mlt_25k.pth", "english_g2.pth"]
        return all(os.path.exists(os.path.join(model_dir, name)) for name in needed)
    except Exception:
        return False


def ocr_image_via_easyocr(image_path):
    global EASYOCR_READER
    try:
        if EASYOCR_READER is None:
            import easyocr
            model_dir = EASYOCR_MODEL_DIR if os.path.exists(EASYOCR_MODEL_DIR) else os.path.join(os.path.expanduser("~"), ".EasyOCR", "model")
            EASYOCR_READER = easyocr.Reader(
                ["en"],
                gpu=False,
                download_enabled=False,
                verbose=False,
                model_storage_directory=model_dir
            )
        results = EASYOCR_READER.readtext(image_path, detail=0, paragraph=True)
        text = " ".join(str(item).strip() for item in results if str(item).strip())
        return text.strip()
    except Exception as e:
        log_ocr_debug("easyocr_error", {"image": image_path, "error": repr(e)})
        return ""


def ocr_image_via_tesseract(image_path):
    exe_path = find_tesseract_executable()
    if not exe_path:
        return ""
    try:
        process = subprocess.Popen(
            [exe_path, image_path, "stdout", "-l", "eng", "--psm", "6"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(timeout=15)
        log_ocr_debug("tesseract_result", {
            "image": image_path,
            "returncode": process.returncode,
            "stdout_len": len(stdout or ""),
            "stdout_sample": (stdout or "")[:180],
            "stderr_len": len(stderr or ""),
            "stderr_sample": (stderr or "")[:240]
        })
        if process.returncode != 0:
            return ""
        return (stdout or "").strip()
    except Exception as e:
        log_ocr_debug("tesseract_error", {"image": image_path, "error": repr(e)})
        return ""


# --- YERLEŞİK WINDOWS OCR MOTORU (POWERSHELL WRAPPER) ---
def ocr_image_via_powershell(image_path):
    # Windows 10/11 yerleşik UWP OCR kütüphanesini PowerShell üzerinden çağırır
    ps_script = """
    param([string]$imgPath)

    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    [void][Windows.Security.Credentials.WebAccountProvider, Windows.Security.Credentials, ContentType=WindowsRuntime]
    [void][Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType=WindowsRuntime]
    [void][Windows.Media.Ocr.OcrResult, Windows.Media.Ocr, ContentType=WindowsRuntime]
    [void][Windows.Globalization.Language, Windows.Globalization, ContentType=WindowsRuntime]
    [void][Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType=WindowsRuntime]
    [void][Windows.Graphics.Imaging.SoftwareBitmap, Windows.Graphics.Imaging, ContentType=WindowsRuntime]
    [void][Windows.Graphics.Imaging.BitmapPixelFormat, Windows.Graphics.Imaging, ContentType=WindowsRuntime]
    [void][Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime]
    [void][Windows.Storage.Streams.IRandomAccessStream, Windows.Storage.Streams, ContentType=WindowsRuntime]

    function AwaitOperation {
        param($AsyncOperation, [Type]$ResultType)
        $method = [System.WindowsRuntimeSystemExtensions].GetMethods() |
            Where-Object { $_.ToString() -eq "System.Threading.Tasks.Task``1[TResult] AsTask[TResult](Windows.Foundation.IAsyncOperation``1[TResult])" } |
            Select-Object -First 1
        $task = $method.MakeGenericMethod($ResultType).Invoke($null, @($AsyncOperation))
        $task.Wait()
        return $task.Result
    }
    
    function RunOcr {
        param([string]$path)

        $engine = $null
        foreach ($tag in @("en-US", "tr-TR")) {
            try {
                $lang = [Windows.Globalization.Language]::new($tag)
                $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
                if ($null -ne $engine) { break }
            } catch {}
        }
        if ($null -eq $engine) {
            $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
        }
        if ($null -eq $engine) {
            return "[OCR Hatası: Windows OCR dili bulunamadı]"
        }

        $file = AwaitOperation ([Windows.Storage.StorageFile]::GetFileFromPathAsync($path)) ([Windows.Storage.StorageFile])
        $stream = AwaitOperation ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
        $decoder = AwaitOperation ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
        $bitmap = AwaitOperation ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
        $bitmap = [Windows.Graphics.Imaging.SoftwareBitmap]::Convert($bitmap, [Windows.Graphics.Imaging.BitmapPixelFormat]::Gray8)
        
        $result = AwaitOperation ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
        return $result.Text
    }
    
    RunOcr $imgPath
    """
    
    try:
        # Siyah CMD ekranı çıkmasını önlemek için startup info kullanıyoruz
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        script_file = tempfile.NamedTemporaryFile(prefix="global_translator_ocr_", suffix=".ps1", mode="w", encoding="utf-8", delete=False)
        script_path = script_file.name
        script_file.write(ps_script)
        script_file.close()
        process = subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", script_path, image_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            startupinfo=startupinfo
        )
        stdout, stderr = process.communicate()
        log_ocr_debug("powershell_result", {
            "image": image_path,
            "returncode": process.returncode,
            "stdout_len": len(stdout or ""),
            "stdout_sample": (stdout or "")[:160],
            "stderr_len": len(stderr or ""),
            "stderr_sample": (stderr or "")[:300]
        })
        if stderr and stderr.strip():
            log_error(f"OCR PowerShell error: {stderr.strip()}")
            return f"[OCR Hatası: {stderr.strip()}]"
        return (stdout or "").strip()
    except Exception as e:
        log_error("OCR failed", e)
        return f"[OCR Hatası: {e}]"
    finally:
        try:
            if "script_path" in locals() and os.path.exists(script_path):
                os.remove(script_path)
        except Exception:
            pass

# --- DİNAMİK SİSTEM TEPSİSİ İKONU OLUŞTURMA ---
def create_tray_image():
    if TRAY_SUPPORTED and os.path.exists(ICON_PNG_PATH):
        try:
            return Image.open(ICON_PNG_PATH).resize((64, 64), Image.Resampling.LANCZOS)
        except Exception:
            pass
    img = Image.new('RGBA', (64, 64), color=(30, 30, 46, 255))
    d = ImageDraw.Draw(img)
    d.ellipse([8, 8, 56, 56], fill=(137, 180, 250, 255))
    try:
        d.line([(32, 16), (32, 48)], fill=(255, 255, 255, 255), width=6)
        d.line([(20, 16), (44, 16)], fill=(255, 255, 255, 255), width=6)
    except Exception:
        pass
    return img


def language_name_from_code(lang_code):
    for name, code in LANGUAGES.items():
        if code == lang_code:
            return name
    return lang_code


def clean_text_for_request(text):
    if not text:
        return ""
    return text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore").strip()


def extract_gemini_text(data):
    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "".join(part.get("text", "") for part in parts).strip()
    except (KeyError, IndexError, TypeError):
        return ""


def parse_gemini_translation(raw_text):
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        data = json.loads(cleaned)
        translation = str(data.get("translation", "")).strip()
        detected = str(data.get("detected_language", "auto")).strip() or "auto"
        return translation, detected
    except (json.JSONDecodeError, AttributeError):
        return cleaned, "auto"


def translate_text_gemini(text, source_lang, target_lang, config):
    text = clean_text_for_request(text)
    api_key = config.get("gemini_api_key", "").strip()
    if not api_key:
        return "[Google AI Studio API anahtarı eksik]", "auto", "gemini_missing_key"

    model = config.get("gemini_model", "gemini-3.5-flash").strip() or "gemini-3.5-flash"
    target_name = language_name_from_code(target_lang)
    source_name = "otomatik algıla" if source_lang == "auto" else language_name_from_code(source_lang)
    prompt = (
        "You are a translation engine. Return only compact JSON with keys "
        '"translation" and "detected_language". '
        f"Translate from {source_name} to {target_name}. "
        "Use ISO 639-1 language code for detected_language when possible. "
        f"Text: {text}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 512
        }
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model)}:generateContent"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=7) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        log_error(f"Gemini HTTP error {e.code}: {body[:1000]}")
        return f"[Gemini Hatası: HTTP {e.code}]", "auto", "gemini_error"
    except Exception as e:
        log_error("Gemini request failed", e)
        return "[Gemini Hatası]", "auto", "gemini_error"
    translated, detected = parse_gemini_translation(extract_gemini_text(data))
    return translated, detected, "gemini"


def translate_text_google_free(text, source_lang, target_lang):
    text = clean_text_for_request(text)
    if not text:
        return "", "auto", "none"
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={source_lang}&tl={target_lang}&dt=t&q={urllib.parse.quote(text, safe='')}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=5) as response:
        data = json.loads(response.read().decode("utf-8"))
        translated = "".join([part[0] for part in data[0] if part[0]])

        detected_lang = 'auto'
        if len(data) > 2 and isinstance(data[2], str):
            detected_lang = data[2]

        return translated, detected_lang, "google_free"


def translate_text_mymemory(text, source_lang, target_lang):
    text = clean_text_for_request(text)
    if not text:
        return "", "auto", "none"
    if len(text.encode("utf-8")) > 500:
        text = text.encode("utf-8")[:500].decode("utf-8", errors="ignore")
    source = source_lang if source_lang != "auto" else ("tr" if target_lang != "tr" else "en")
    url = (
        "https://api.mymemory.translated.net/get?"
        f"q={urllib.parse.quote(text, safe='')}&langpair={urllib.parse.quote(source + '|' + target_lang, safe='')}"
    )
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=7) as response:
        data = json.loads(response.read().decode("utf-8"))
    translated = data.get("responseData", {}).get("translatedText", "")
    if not translated:
        return "[MyMemory çeviri sonucu boş]", source, "mymemory_error"
    return translated, source, "mymemory"


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tip or not self.text:
            return
        x = self.widget.winfo_rootx() + 18
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self.tip = tk.Toplevel(self.widget)
        self.tip.overrideredirect(True)
        self.tip.attributes("-topmost", True)
        self.tip.configure(bg="#11111B")
        self.tip.geometry(f"+{x}+{y}")
        tk.Label(
            self.tip,
            text=self.text,
            justify="left",
            wraplength=320,
            font=("Segoe UI", 8),
            fg="#CDD6F4",
            bg="#11111B",
            padx=10,
            pady=7
        ).pack()

    def hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


def preprocess_ocr_image(image):
    if not TRAY_SUPPORTED:
        return image
    processed = image.convert("L")
    if ImageStat.Stat(processed).mean[0] < 120:
        processed = ImageOps.invert(processed)
    processed = ImageOps.autocontrast(processed)
    processed = ImageEnhance.Contrast(processed).enhance(2.8)
    processed = ImageEnhance.Sharpness(processed).enhance(2.0)
    max_side = max(processed.width, processed.height)
    scale = 3
    if max_side * scale > 2400:
        scale = 2
    if max_side * scale > 2400:
        scale = 1
    if scale > 1:
        processed = processed.resize((processed.width * scale, processed.height * scale), Image.Resampling.LANCZOS)
    processed = processed.filter(ImageFilter.SHARPEN)
    return processed


def prepare_image_for_windows_ocr(image):
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    padding = 40
    background = 255 if image.mode == "L" else (255, 255, 255)
    canvas = Image.new(image.mode, (image.width + padding * 2, image.height + padding * 2), background)
    canvas.paste(image, (padding, padding))
    return canvas


def split_large_ocr_bbox(bbox):
    left, top, right, bottom = [int(v) for v in bbox]
    width = max(1, right - left)
    height = max(1, bottom - top)
    attempts = [("secili alan", (left, top, right, bottom))]

    if height > 220:
        strip_h = 150
        step = 105
        y = top
        index = 1
        while y < bottom:
            strip_bottom = min(bottom, y + strip_h)
            attempts.append((f"secili alan satir {index}", (left, y, right, strip_bottom)))
            if strip_bottom >= bottom:
                break
            y += step
            index += 1

    if width > 1000:
        center = (left + right) // 2
        attempts.append(("secili alan sol", (left, top, center + 80, bottom)))
        attempts.append(("secili alan sag", (center - 80, top, right, bottom)))

    return attempts


def clamp_ocr_bbox(bbox, screen_w, screen_h):
    left, top, right, bottom = [int(v) for v in bbox]
    left = max(0, min(screen_w - 2, left))
    top = max(0, min(screen_h - 2, top))
    right = max(left + 1, min(screen_w, right))
    bottom = max(top + 1, min(screen_h, bottom))
    return (left, top, right, bottom)


def get_ocr_engine_order(engine_code):
    if engine_code == "easyocr":
        return ["easyocr"]
    if engine_code == "tesseract":
        return ["tesseract"]
    if engine_code == "windows":
        return ["windows"]
    return ["easyocr", "tesseract", "windows"]


def read_ocr_with_retries(image_path, attempts=2, engine_code="auto"):
    for engine_name in get_ocr_engine_order(engine_code):
        for index in range(attempts):
            if engine_name == "easyocr":
                text = (ocr_image_via_easyocr(image_path) or "").strip()
            elif engine_name == "tesseract":
                text = (ocr_image_via_tesseract(image_path) or "").strip()
            else:
                text = (ocr_image_via_powershell(image_path) or "").strip()

            log_ocr_debug("ocr_engine_attempt", {
                "engine": engine_name,
                "image": image_path,
                "try": index + 1,
                "text_len": len(text or ""),
                "text_sample": (text or "")[:180]
            })
            if text and not text.startswith("[OCR Hatası") and not text.startswith("[OCR HatasÄ±"):
                return text
            if index < attempts - 1:
                time.sleep(0.12)
    return ""


def build_ocr_attempts(mx, my, width, height, left_offset):
    attempts = []
    candidates = [
        ("profil", left_offset, width, height),
        ("yakın", min(160, max(80, width // 3)), min(width, 360), min(height, 90)),
        ("satır", min(140, max(80, width // 4)), max(width, 640), min(max(height, 44), 70)),
        ("merkez", min(width // 2, 220), min(width, 440), min(max(height, 120), 180)),
    ]
    seen = set()
    for name, offset, w, h in candidates:
        bbox = (
            int(mx - offset),
            int(my - (h // 2)),
            int(mx - offset + w),
            int(my + (h // 2))
        )
        if bbox in seen:
            continue
        seen.add(bbox)
        attempts.append((name, bbox))
    return attempts


# --- API ÇEVİRİ FONKSİYONU ---
def translate_text(text, source_lang='auto', target_lang='tr', config=None):
    text = clean_text_for_request(text)
    if not text:
        return "", "auto", "none"
    try:
        if config and config.get("translation_engine") == "gemini":
            translated, detected_lang, engine_used = translate_text_gemini(text, source_lang, target_lang, config)
            if translated and not translated.startswith("[Gemini Hatası"):
                return translated, detected_lang, engine_used
            if not config.get("fallback_to_google", True):
                return translated, detected_lang, engine_used
            log_error("Gemini failed, falling back to Google free translator")

        if config and config.get("translation_engine") == "mymemory":
            return translate_text_mymemory(text, source_lang, target_lang)

        return translate_text_google_free(text, source_lang, target_lang)
    except Exception as e:
        log_error("Translation request failed", e)
        return f"[Çeviri Hatası]", 'auto', "error"

# --- KLAVYE KANCASI ---
class KeyTracker:
    def __init__(self, on_update, on_replace_trigger, on_ocr_trigger, on_select_ocr_area_trigger, on_exit_trigger, root_ref, get_shortcuts, get_buffer_timeout):
        self.buffer = ""
        self.on_update = on_update
        self.on_replace_trigger = on_replace_trigger
        self.on_ocr_trigger = on_ocr_trigger
        self.on_select_ocr_area_trigger = on_select_ocr_area_trigger
        self.on_exit_trigger = on_exit_trigger
        self.root = root_ref
        self.get_shortcuts = get_shortcuts
        self.get_buffer_timeout = get_buffer_timeout
        
        self.ctrl_pressed = False
        self.shift_pressed = False
        self.alt_pressed = False
        self.active = True
        self.last_key_time = time.time()
        
        self.check_loop()
        
    def check_loop(self):
        try:
            if self.active and self.buffer and (time.time() - self.last_key_time > self.get_buffer_timeout()):
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
            if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                self.alt_pressed = True
                return
                
            # Normal Windows kopyala/yapıştır/kes işlemlerine hiç karışma.
            key_name = key_name_from_event(key)
            if self.ctrl_pressed and key_name in {"V", "C", "X"}:
                return

            shortcuts = self.get_shortcuts()
            
            if shortcut_matches(shortcuts.get("shortcut_exit"), key, self.ctrl_pressed, self.shift_pressed, self.alt_pressed):
                self.on_exit_trigger()
                return
                
            if shortcut_matches(shortcuts.get("shortcut_ocr"), key, self.ctrl_pressed, self.shift_pressed, self.alt_pressed):
                self.on_ocr_trigger()
                return

            if shortcut_matches(shortcuts.get("shortcut_select_ocr_area"), key, self.ctrl_pressed, self.shift_pressed, self.alt_pressed):
                self.on_select_ocr_area_trigger()
                return
                
            if shortcut_matches(shortcuts.get("shortcut_replace"), key, self.ctrl_pressed, self.shift_pressed, self.alt_pressed):
                self.on_replace_trigger()
                return
                
            if self.ctrl_pressed or self.alt_pressed:
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
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            self.alt_pressed = False

# --- FARE KANCASI (NORMAL SEÇİMLER İÇİN) ---
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
                threading.Thread(target=self.trigger_copy_and_translate, args=(x, y), daemon=True).start()
                
    def trigger_copy_and_translate(self, x, y):
        time.sleep(0.12)
        try:
            old_clipboard = pyperclip.paste()
            pyperclip.copy("")
        except Exception as e:
            log_error("Clipboard read failed before selection translation", e)
            return
        
        self.kb_controller.press(Key.ctrl)
        self.kb_controller.press('c')
        self.kb_controller.release('c')
        self.kb_controller.release(Key.ctrl)
        
        time.sleep(0.12)
        
        try:
            copied_text = pyperclip.paste().strip()
        except Exception as e:
            log_error("Clipboard read failed after copy shortcut", e)
            copied_text = ""
        try:
            if copied_text and copied_text != old_clipboard:
                self.on_text_selected(copied_text, x, y)
        finally:
            try:
                pyperclip.copy(old_clipboard)
            except Exception as e:
                log_error("Clipboard restore failed after selection translation", e)

# --- EŞZAMANLI ÇEVİRİ MOTORU ---
class ThreadedTranslator:
    def __init__(self, callback, get_target_lang, get_config):
        self.callback = callback
        self.get_target_lang = get_target_lang
        self.get_config = get_config
        self.lock = threading.Lock()
        self.pending_text = ""
        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()
        
    def request_translation(self, text):
        with self.lock:
            self.pending_text = text

    def stop(self):
        self.running = False
            
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
                    self.callback("", "none")
                else:
                    time.sleep(0.2)
                    with self.lock:
                        if self.pending_text != text_to_translate:
                            continue
                    target_code = LANGUAGES.get(self.get_target_lang(), "en")
                    translated, _, engine_used = translate_text(text_to_translate, 'tr', target_code, self.get_config())
                    self.callback(translated, engine_used)
            time.sleep(0.02)

# --- ANA KONTROL PANELİ VE OVERLAY UYGULAMASI ---
class TranslationApp:
    def __init__(self):
        # 1. Ana Pencere Ayarları
        self.root = tk.Tk()
        self.root.title("MonsTranslate")
        if os.path.exists(ICON_PATH):
            try:
                self.root.iconbitmap(ICON_PATH)
            except Exception:
                pass
        elif os.path.exists(ICON_PNG_PATH):
            try:
                self.root.iconphoto(True, tk.PhotoImage(file=ICON_PNG_PATH))
            except Exception:
                pass
        self.root.geometry("620x900")
        self.root.configure(bg="#1E1E2E")
        self.root.minsize(560, 720)
        self.root.resizable(True, True)
        
        self.c_bg = "#1E1E2E"
        self.c_card = "#252538"
        self.c_card_alt = "#2B2D42"
        self.c_accent = "#89B4FA"
        self.c_green = "#A6E3A1"
        self.c_red = "#F38BA8"
        self.c_text = "#CDD6F4"
        self.c_subtext = "#BAC2DE"
        
        self.config = load_config()
        log_ocr_debug("app_started", {
            "version": "ocr-debug-2026-06-14",
            "config_ocr_enabled": self.config.get("ocr_enabled"),
            "config_fixed_area": self.config.get("ocr_fixed_area")
        })
        self.typing_target_var = tk.StringVar(value=self.config["typing_target"])
        self.translation_engine_var = tk.StringVar(value=self._translation_engine_label(self.config["translation_engine"]))
        self.gemini_api_key_var = tk.StringVar(value=self.config["gemini_api_key"])
        self.gemini_model_var = tk.StringVar(value=self.config["gemini_model"])
        self.replace_mode_var = tk.StringVar(value=self._replace_mode_label(self.config["replace_mode"]))
        self.ocr_enabled_var = tk.BooleanVar(value=bool(self.config["ocr_enabled"]))
        self.ocr_engine_var = tk.StringVar(value=self._ocr_engine_label(self.config.get("ocr_engine", "auto")))
        self.ocr_profile_var = tk.StringVar(value=self._ocr_profile_label(self.config["ocr_profile"]))
        self.ocr_preprocess_var = tk.BooleanVar(value=bool(self.config["ocr_preprocess"]))
        self.ocr_width_var = tk.IntVar(value=int(self.config["ocr_width"]))
        self.ocr_height_var = tk.IntVar(value=int(self.config["ocr_height"]))
        self.popup_seconds_var = tk.IntVar(value=int(self.config["popup_seconds"]))
        self.typing_popup_seconds_var = tk.IntVar(value=int(self.config["typing_popup_seconds"]))
        self.typing_popup_enabled_var = tk.BooleanVar(value=bool(self.config["typing_popup_enabled"]))
        self.typing_buffer_seconds_var = tk.IntVar(value=int(self.config["typing_buffer_seconds"]))
        self.shortcut_replace_var = tk.StringVar(value=self.config["shortcut_replace"])
        self.shortcut_ocr_var = tk.StringVar(value=self.config["shortcut_ocr"])
        self.shortcut_select_ocr_area_var = tk.StringVar(value=self.config["shortcut_select_ocr_area"])
        self.shortcut_exit_var = tk.StringVar(value=self.config["shortcut_exit"])
        self.is_paused = False
        
        self.tracker = None
        self.mouse_tracker = None
        self.tray_icon = None
        
        self.build_ui()
        self.update_ocr_state_labels()
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

        self.lbl_hover_source = tk.Label(
            self.hover_win,
            text="",
            font=("Segoe UI", 8),
            fg=self.c_subtext,
            bg="#11111B",
            wraplength=430,
            justify="left",
            anchor="w"
        )
        self.lbl_hover_source.pack(fill="x", padx=16, pady=(12, 2))
        
        self.lbl_hover = tk.Label(
            self.hover_win, 
            text="", 
            font=("Segoe UI", 11, "bold"), fg=self.c_green, bg="#11111B", 
            wraplength=430, justify="left", anchor="w"
        )
        self.lbl_hover.pack(fill="x", padx=16, pady=(0, 12))
        
        self.hover_win.bind("<Button-1>", lambda e: self.hover_win.withdraw())
        self.hover_win.withdraw()
        
        self.last_translation = ""
        self.hover_timer = None
        self.typing_hide_timer = None
        self.kb_controller = Controller()
        
        self.translator_engine = ThreadedTranslator(
            lambda text, engine_used: self.root.after(0, lambda: self.on_translation_ready(text, engine_used)),
            lambda: self.typing_target_var.get(),
            lambda: self.config.copy()
        )
        
        if TRAY_SUPPORTED:
            self.setup_tray()
        self.update_api_key_state()
        self.root.after(400, self.run_startup_checks)

    def _replace_mode_label(self, mode_code):
        for label, code in REPLACE_MODES.items():
            if code == mode_code:
                return label
        return "Seçili alanı değiştir"

    def _translation_engine_label(self, engine_code):
        for label, code in TRANSLATION_ENGINES.items():
            if code == engine_code:
                return label
        return "Google Ücretsiz"

    def _ocr_engine_label(self, engine_code):
        for label, code in OCR_ENGINES.items():
            if code == engine_code:
                return label
        return "Otomatik (Önerilen)"

    def test_selected_engine(self):
        config = self.config.copy()
        engine = config.get("translation_engine", "google_free")
        if engine == "gemini":
            if not config.get("gemini_api_key"):
                return False, "gemini_missing_key"
            _, _, engine_used = translate_text_gemini("test", "en", "tr", config)
            return engine_used == "gemini", engine_used
        if engine == "mymemory":
            _, _, engine_used = translate_text_mymemory("hello", "en", "tr")
            return engine_used == "mymemory", engine_used
        _, _, engine_used = translate_text_google_free("hello", "en", "tr")
        return engine_used == "google_free", engine_used

    def _ocr_profile_label(self, profile_code):
        for label, profile in OCR_PROFILES.items():
            if profile["code"] == profile_code:
                return label
        return "Küçük Chat Satırı"

    def save_current_config(self, event=None):
        self.config["typing_target"] = self.typing_target_var.get()
        self.config["translation_engine"] = TRANSLATION_ENGINES.get(self.translation_engine_var.get(), "google_free")
        entered_api_key = self.gemini_api_key_var.get().strip()
        if entered_api_key:
            self.config["gemini_api_key"] = entered_api_key
        self.config["gemini_model"] = self.gemini_model_var.get().strip() or "gemini-3.5-flash"
        self.config["replace_mode"] = REPLACE_MODES.get(self.replace_mode_var.get(), "select_all")
        self.config["ocr_enabled"] = bool(self.ocr_enabled_var.get())
        self.config["ocr_engine"] = OCR_ENGINES.get(self.ocr_engine_var.get(), "auto")
        self.config["ocr_profile"] = OCR_PROFILES.get(self.ocr_profile_var.get(), OCR_PROFILES["Küçük Chat Satırı"])["code"]
        self.config["ocr_preprocess"] = bool(self.ocr_preprocess_var.get())
        self.config["ocr_width"] = self._safe_int(self.ocr_width_var.get(), 600, 120, 1400)
        self.config["ocr_height"] = self._safe_int(self.ocr_height_var.get(), 36, 20, 240)
        self.config["popup_seconds"] = self._safe_int(self.popup_seconds_var.get(), 2, 1, 15)
        self.config["typing_popup_seconds"] = self._safe_int(self.typing_popup_seconds_var.get(), 2, 1, 10)
        self.config["typing_popup_enabled"] = bool(self.typing_popup_enabled_var.get())
        self.config["typing_buffer_seconds"] = self._safe_int(self.typing_buffer_seconds_var.get(), 12, 3, 60)
        self.config["shortcut_replace"] = normalize_shortcut(self.shortcut_replace_var.get()) or DEFAULT_CONFIG["shortcut_replace"]
        self.config["shortcut_ocr"] = normalize_shortcut(self.shortcut_ocr_var.get()) or DEFAULT_CONFIG["shortcut_ocr"]
        self.config["shortcut_select_ocr_area"] = normalize_shortcut(self.shortcut_select_ocr_area_var.get()) or DEFAULT_CONFIG["shortcut_select_ocr_area"]
        self.config["shortcut_exit"] = normalize_shortcut(self.shortcut_exit_var.get()) or DEFAULT_CONFIG["shortcut_exit"]
        self.shortcut_replace_var.set(self.config["shortcut_replace"])
        self.shortcut_ocr_var.set(self.config["shortcut_ocr"])
        self.shortcut_select_ocr_area_var.set(self.config["shortcut_select_ocr_area"])
        self.shortcut_exit_var.set(self.config["shortcut_exit"])
        save_config(self.config)
        self.update_api_key_state()
        self.root.after(0, self.update_ocr_state_labels)

    def clear_api_key(self):
        self.gemini_api_key_var.set("")
        self.config["gemini_api_key"] = ""
        save_config(self.config)
        self.update_api_key_state()
        self.set_status("AI Studio API anahtarı temizlendi", self.c_red)

    def update_api_key_state(self):
        if not hasattr(self, "lbl_api_key_state"):
            return
        key_len = len(self.config.get("gemini_api_key", ""))
        if key_len:
            self.lbl_api_key_state.config(text=f"API Key: kayıtlı ({key_len} karakter)", fg=self.c_green)
        else:
            self.lbl_api_key_state.config(text="API Key: kayıt bekliyor", fg=self.c_subtext)

    def apply_ocr_profile(self, event=None):
        profile = OCR_PROFILES.get(self.ocr_profile_var.get())
        if not profile:
            return
        self.config["ocr_fixed_area"] = None
        self.ocr_width_var.set(profile["width"])
        self.ocr_height_var.set(profile["height"])
        self.config["ocr_left_offset"] = profile["left_offset"]
        self.save_current_config()

    def clear_ocr_area(self):
        self.config["ocr_fixed_area"] = None
        self.save_current_config()
        self.update_ocr_state_labels()
        self.set_status("OCR alani sifirlandi", self.c_green)

    def update_ocr_state_labels(self):
        if hasattr(self, "lbl_ocr_area_state"):
            fixed_area = self.config.get("ocr_fixed_area")
            if isinstance(fixed_area, list) and len(fixed_area) == 4:
                width = max(0, int(fixed_area[2]) - int(fixed_area[0]))
                height = max(0, int(fixed_area[3]) - int(fixed_area[1]))
                self.lbl_ocr_area_state.config(text=f"OCR Alani: secili alan ({width}x{height})", fg=self.c_green)
            else:
                self.lbl_ocr_area_state.config(text="OCR Alani: profil/fare cevresi", fg=self.c_subtext)

        if hasattr(self, "lbl_check_ocr"):
            ocr_enabled = bool(self.config.get("ocr_enabled", True))
            current_text = self.lbl_check_ocr.cget("text")
            if not ocr_enabled:
                self.lbl_check_ocr.config(text="Windows OCR: hazir ama uygulamada kapali", fg=self.c_red)
            elif "uygulamada kapali" in current_text:
                self.lbl_check_ocr.config(text="Windows OCR: kontrol bekliyor", fg=self.c_subtext)

    def select_ocr_area(self):
        overlay = tk.Toplevel(self.root)
        overlay.attributes("-fullscreen", True)
        overlay.attributes("-topmost", True)
        overlay.attributes("-alpha", 0.24)
        overlay.configure(bg="black")
        overlay.cursor = "crosshair"

        canvas = tk.Canvas(overlay, bg="black", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        state = {"start_root": None, "start_canvas": None, "rect": None}

        def on_press(event):
            state["start_root"] = (event.x_root, event.y_root)
            state["start_canvas"] = (event.x, event.y)
            if state["rect"]:
                canvas.delete(state["rect"])
            state["rect"] = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="#A6E3A1", width=2)

        def on_drag(event):
            if not state["start_canvas"] or not state["rect"]:
                return
            x0, y0 = state["start_canvas"]
            canvas.coords(state["rect"], x0, y0, event.x, event.y)

        def on_release(event):
            if not state["start_root"]:
                overlay.destroy()
                return
            x0, y0 = state["start_root"]
            x1, y1 = event.x_root, event.y_root
            left, right = sorted((int(x0), int(x1)))
            top, bottom = sorted((int(y0), int(y1)))
            overlay.destroy()
            if right - left < 20 or bottom - top < 20:
                self.set_status("OCR alanı çok küçük seçildi", self.c_red)
                return
            self.config["ocr_fixed_area"] = [left, top, right, bottom]
            self.ocr_width_var.set(right - left)
            self.ocr_height_var.set(bottom - top)
            self.save_current_config()
            self.update_ocr_state_labels()
            self.set_status("OCR alanı kaydedildi", self.c_green)

        def cancel(event=None):
            overlay.destroy()
            self.set_status("OCR alan seçimi iptal edildi", self.c_red)

        overlay.bind("<Escape>", cancel)
        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_release)

    def _safe_int(self, value, fallback, minimum, maximum):
        try:
            number = int(value)
        except (TypeError, ValueError, tk.TclError):
            number = fallback
        return max(minimum, min(maximum, number))

    def set_trackers(self, tracker, mouse_tracker):
        self.tracker = tracker
        self.mouse_tracker = mouse_tracker

    def add_tooltip(self, widget, text):
        ToolTip(widget, text)

    def get_shortcuts(self):
        return {
            "shortcut_replace": self.config.get("shortcut_replace", DEFAULT_CONFIG["shortcut_replace"]),
            "shortcut_ocr": self.config.get("shortcut_ocr", DEFAULT_CONFIG["shortcut_ocr"]),
            "shortcut_select_ocr_area": self.config.get("shortcut_select_ocr_area", DEFAULT_CONFIG["shortcut_select_ocr_area"]),
            "shortcut_exit": self.config.get("shortcut_exit", DEFAULT_CONFIG["shortcut_exit"])
        }

    def get_buffer_timeout(self):
        return self._safe_int(self.config.get("typing_buffer_seconds", 12), 12, 3, 60)

    def run_startup_checks(self):
        self.lbl_check_packages.config(text="Paketler: kontrol ediliyor...", fg=self.c_subtext)
        self.lbl_check_ocr.config(text="OCR motorları: kontrol ediliyor...", fg=self.c_subtext)
        self.lbl_check_api.config(text="AI Studio API: kontrol ediliyor...", fg=self.c_subtext)
        if hasattr(self, "lbl_check_engine"):
            self.lbl_check_engine.config(text="Son Motor: AI test çalışıyor...", fg=self.c_accent)
        if hasattr(self, "btn_refresh_checks"):
            self.btn_refresh_checks.config(text="Test...")

        def worker():
            packages_ok = bool(TRAY_SUPPORTED)
            easyocr_ok = check_easyocr_available()
            tesseract_ok = bool(find_tesseract_executable())
            windows_ocr_ok = check_windows_ocr_available()
            self.save_current_config()
            selected_engine = self.config["translation_engine"]
            api_key_ready = bool(self.config["gemini_api_key"])
            api_test_ok, api_test_engine = self.test_selected_engine()

            def update_ui():
                if hasattr(self, "btn_refresh_checks"):
                    self.btn_refresh_checks.config(text="AI Test")
                if packages_ok:
                    self.lbl_check_packages.config(text="Paketler: hazır", fg=self.c_green)
                else:
                    self.lbl_check_packages.config(text="Paketler: Pillow/pystray eksik olabilir", fg=self.c_red)

                if easyocr_ok:
                    self.lbl_check_ocr.config(text="OCR: EasyOCR hazır (ana motor)", fg=self.c_green)
                elif tesseract_ok:
                    self.lbl_check_ocr.config(text="OCR: Tesseract hazır", fg=self.c_green)
                elif windows_ocr_ok:
                    self.lbl_check_ocr.config(text="OCR: sadece Windows OCR hazır", fg=self.c_red)
                else:
                    self.lbl_check_ocr.config(text="OCR: çalışan yerel motor bulunamadı", fg=self.c_red)

                self.update_ocr_state_labels()

                if selected_engine == "gemini" and api_test_ok:
                    self.lbl_check_api.config(text="Google AI Studio: çalışıyor", fg=self.c_green)
                elif selected_engine == "gemini" and api_key_ready:
                    self.lbl_check_api.config(text="Google AI Studio: kota/hata, ücretsiz motora düşer", fg=self.c_red)
                elif selected_engine == "gemini":
                    self.lbl_check_api.config(text="Google AI Studio: anahtar bekleniyor", fg=self.c_red)
                elif selected_engine == "mymemory" and api_test_ok:
                    self.lbl_check_api.config(text="MyMemory Ücretsiz: çalışıyor", fg=self.c_green)
                elif selected_engine == "mymemory":
                    self.lbl_check_api.config(text="MyMemory Ücretsiz: çalışmadı", fg=self.c_red)
                elif api_test_ok:
                    self.lbl_check_api.config(text="Google Ücretsiz: çalışıyor", fg=self.c_green)
                else:
                    self.lbl_check_api.config(text="Google Ücretsiz: çalışmadı", fg=self.c_red)
                self.update_engine_status(api_test_engine)

            self.root.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def open_shortcut_window(self):
        win = tk.Toplevel(self.root)
        win.title("Kısayollar")
        win.geometry("460x350")
        win.configure(bg=self.c_bg)
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        tk.Label(
            win,
            text="Kısayol Atamaları",
            font=("Segoe UI", 14, "bold"),
            fg=self.c_text,
            bg=self.c_bg
        ).pack(anchor="w", padx=18, pady=(16, 3))

        tk.Label(
            win,
            text="Örnek: Ctrl+Q, Ctrl+Alt+Q, Ctrl+Shift+E, Alt+Space",
            font=("Segoe UI", 8),
            fg=self.c_subtext,
            bg=self.c_bg
        ).pack(anchor="w", padx=18, pady=(0, 12))

        form = tk.Frame(win, bg=self.c_card)
        form.pack(fill="x", padx=18, pady=(0, 10))

        entries = [
            ("shortcut_replace", SHORTCUT_ACTIONS["shortcut_replace"], self.shortcut_replace_var),
            ("shortcut_ocr", SHORTCUT_ACTIONS["shortcut_ocr"], self.shortcut_ocr_var),
            ("shortcut_select_ocr_area", SHORTCUT_ACTIONS["shortcut_select_ocr_area"], self.shortcut_select_ocr_area_var),
            ("shortcut_exit", SHORTCUT_ACTIONS["shortcut_exit"], self.shortcut_exit_var)
        ]

        for _, label_text, variable in entries:
            row = tk.Frame(form, bg=self.c_card)
            row.pack(fill="x", padx=14, pady=8)
            tk.Label(
                row,
                text=label_text,
                font=("Segoe UI", 9, "bold"),
                fg=self.c_text,
                bg=self.c_card
            ).pack(side="left")
            entry = tk.Entry(
                row,
                textvariable=variable,
                width=18,
                bg="#11111B",
                fg=self.c_text,
                insertbackground=self.c_text,
                relief="flat"
            )
            entry.pack(side="right")

        status_lbl = tk.Label(
            win,
            text="Değişiklikler kaydedilince hemen aktif olur.",
            font=("Segoe UI", 8),
            fg=self.c_subtext,
            bg=self.c_bg
        )
        status_lbl.pack(anchor="w", padx=18, pady=(0, 8))

        def save_shortcuts():
            normalized = {
                key: normalize_shortcut(variable.get())
                for key, _, variable in entries
            }
            if any(not value for value in normalized.values()):
                status_lbl.config(text="Boş kısayol bırakılamaz.", fg=self.c_red)
                return
            if len(set(normalized.values())) != len(normalized):
                status_lbl.config(text="Aynı kısayol iki işleve atanamaz.", fg=self.c_red)
                return

            self.shortcut_replace_var.set(normalized["shortcut_replace"])
            self.shortcut_ocr_var.set(normalized["shortcut_ocr"])
            self.shortcut_select_ocr_area_var.set(normalized["shortcut_select_ocr_area"])
            self.shortcut_exit_var.set(normalized["shortcut_exit"])
            self.save_current_config()
            status_lbl.config(text="Kaydedildi.", fg=self.c_green)

        btns = tk.Frame(win, bg=self.c_bg)
        btns.pack(fill="x", padx=18, pady=(0, 14))

        tk.Button(
            btns,
            text="Kaydet",
            font=("Segoe UI", 9, "bold"),
            fg=self.c_bg,
            bg=self.c_accent,
            activeforeground=self.c_text,
            activebackground="#313244",
            bd=0,
            height=2,
            cursor="hand2",
            command=save_shortcuts
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        tk.Button(
            btns,
            text="Kapat",
            font=("Segoe UI", 9, "bold"),
            fg=self.c_text,
            bg="#313244",
            activeforeground=self.c_text,
            activebackground="#45475A",
            bd=0,
            height=2,
            cursor="hand2",
            command=win.destroy
        ).pack(side="left", fill="x", expand=True, padx=(6, 0))

    def build_ui(self):
        self.main_canvas = tk.Canvas(self.root, bg=self.c_bg, highlightthickness=0)
        self.main_scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.main_canvas.yview)
        self.main_canvas.configure(yscrollcommand=self.main_scrollbar.set)
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.main_scrollbar.pack(side="right", fill="y")

        self.content_frame = tk.Frame(self.main_canvas, bg=self.c_bg)
        self.content_window = self.main_canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        def update_scroll_region(event=None):
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

        def update_content_width(event):
            self.main_canvas.itemconfig(self.content_window, width=event.width)

        def on_mousewheel(event):
            self.main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.content_frame.bind("<Configure>", update_scroll_region)
        self.main_canvas.bind("<Configure>", update_content_width)
        self.root.bind_all("<MouseWheel>", on_mousewheel)
        parent = self.content_frame

        # Üst Minimalist Başlık
        header = tk.Frame(parent, bg=self.c_bg)
        header.pack(fill="x", padx=18, pady=(16, 8))

        title_lbl = tk.Label(
            header,
            text="MonsTranslate", 
            font=("Segoe UI", 15, "bold"), fg=self.c_text, bg=self.c_bg
        )
        title_lbl.pack(anchor="w")
        
        subtitle_lbl = tk.Label(
            header,
            text="Canlı çeviri, OCR overlay ve akıllı motor seçimi", 
            font=("Segoe UI", 9), fg=self.c_subtext, bg=self.c_bg
        )
        subtitle_lbl.pack(anchor="w", pady=(2, 0))

        action_bar = tk.Frame(parent, bg=self.c_bg)
        action_bar.pack(fill="x", padx=18, pady=(0, 8))

        self.btn_pause = tk.Button(
            action_bar,
            text="Sistemi Duraklat",
            font=("Segoe UI", 9, "bold"), fg=self.c_bg, bg=self.c_accent,
            activeforeground=self.c_text, activebackground="#313244",
            bd=0, height=2, cursor="hand2", command=self.toggle_pause
        )
        self.btn_pause.pack(side="left", fill="x", expand=True, padx=(0, 6))

        btn_shortcuts_top = tk.Button(
            action_bar,
            text="Kısayollar",
            font=("Segoe UI", 9, "bold"),
            fg=self.c_text,
            bg="#313244",
            activeforeground=self.c_text,
            activebackground="#45475A",
            bd=0,
            height=2,
            cursor="hand2",
            command=self.open_shortcut_window
        )
        btn_shortcuts_top.pack(side="left", fill="x", expand=True, padx=(6, 6))
        self.add_tooltip(btn_shortcuts_top, "OCR, çeviriyi uygula ve çıkış işlemleri için kısayol atama penceresini açar.")

        btn_close = tk.Button(
            action_bar,
            text="Kapat",
            font=("Segoe UI", 9, "bold"), fg=self.c_text, bg=self.c_red,
            activeforeground="#1E1E2E", activebackground="#E06C75",
            bd=0, height=2, cursor="hand2", command=self.terminate
        )
        btn_close.pack(side="left", fill="x", expand=True, padx=(6, 0))

        # DURUM GÖSTERGESİ
        status_frame = tk.Frame(parent, bg=self.c_bg)
        status_frame.pack(fill="x", padx=20, pady=(2, 6))
        
        self.status_canvas = tk.Canvas(status_frame, width=12, height=12, bg=self.c_bg, highlightthickness=0)
        self.status_canvas.pack(side="left", padx=(5, 5))
        self.status_led = self.status_canvas.create_oval(2, 2, 10, 10, fill=self.c_green, outline="")
        
        self.lbl_status_text = tk.Label(
            status_frame, text="Sistem Aktif - Fare Altını Çevirebilir", 
            font=("Segoe UI", 8, "bold"), fg=self.c_green, bg=self.c_bg,
            wraplength=500, justify="left"
        )
        self.lbl_status_text.pack(side="left")

        checks_card = tk.Frame(parent, bg=self.c_card_alt, bd=0)
        checks_card.pack(fill="x", padx=18, pady=(0, 8))

        checks_header = tk.Frame(checks_card, bg=self.c_card_alt)
        checks_header.pack(fill="x", padx=15, pady=(8, 4))

        tk.Label(
            checks_header,
            text="Sistem Kontrolü",
            font=("Segoe UI", 10, "bold"),
            fg=self.c_accent,
            bg=self.c_card_alt
        ).pack(side="left")

        self.btn_refresh_checks = tk.Button(
            checks_header,
            text="AI Test",
            font=("Segoe UI", 8, "bold"),
            fg=self.c_text,
            bg="#313244",
            activeforeground=self.c_text,
            activebackground="#45475A",
            bd=0,
            padx=8,
            cursor="hand2",
            command=self.run_startup_checks
        )
        self.btn_refresh_checks.pack(side="right")
        self.add_tooltip(self.btn_refresh_checks, "Seçili çeviri motoruna gerçek test isteği atar ve hangi motorun çalıştığını gösterir.")

        self.lbl_check_packages = tk.Label(
            checks_card, text="Paketler: kontrol bekliyor",
            font=("Segoe UI", 8), fg=self.c_subtext, bg=self.c_card_alt, anchor="w"
        )
        self.lbl_check_packages.pack(fill="x", padx=15, pady=(0, 2))

        self.lbl_check_ocr = tk.Label(
            checks_card, text="Windows OCR: kontrol bekliyor",
            font=("Segoe UI", 8), fg=self.c_subtext, bg=self.c_card_alt, anchor="w"
        )
        self.lbl_check_ocr.pack(fill="x", padx=15, pady=(0, 2))

        self.lbl_check_api = tk.Label(
            checks_card, text="AI Studio API: kontrol bekliyor",
            font=("Segoe UI", 8), fg=self.c_subtext, bg=self.c_card_alt, anchor="w"
        )
        self.lbl_check_api.pack(fill="x", padx=15, pady=(0, 2))

        self.lbl_check_engine = tk.Label(
            checks_card, text="Son Motor: henüz çeviri yapılmadı",
            font=("Segoe UI", 8), fg=self.c_subtext, bg=self.c_card_alt, anchor="w"
        )
        self.lbl_check_engine.pack(fill="x", padx=15, pady=(0, 10))
        
        # TEK KOMBİNE AYAR KARTI
        card = tk.Frame(parent, bg=self.c_card, bd=0)
        card.pack(fill="x", padx=18, pady=6)

        tk.Label(card, text="Çeviri", font=("Segoe UI", 10, "bold"), fg=self.c_accent, bg=self.c_card).pack(anchor="w", padx=15, pady=(12, 6))
        
        frame_write = tk.Frame(card, bg=self.c_card)
        frame_write.pack(fill="x", padx=15, pady=(0, 8))
        
        tk.Label(frame_write, text="✍️ Yazma Çevirisi:", font=("Segoe UI", 9, "bold"), fg=self.c_accent, bg=self.c_card).pack(side="left")
        self.combo_write_target = ttk.Combobox(
            frame_write, 
            textvariable=self.typing_target_var, 
            values=list(LANGUAGES.keys())[:-1], 
            width=10, state="readonly"
        )
        self.combo_write_target.pack(side="right")
        self.combo_write_target.bind("<<ComboboxSelected>>", self.save_current_config)
        self.add_tooltip(self.combo_write_target, "Yazdığın Türkçe metnin çevrileceği hedef dil.")

        frame_engine = tk.Frame(card, bg=self.c_card)
        frame_engine.pack(fill="x", padx=15, pady=(0, 8))

        tk.Label(frame_engine, text="Çeviri Motoru:", font=("Segoe UI", 9, "bold"), fg=self.c_text, bg=self.c_card).pack(side="left")
        self.combo_translation_engine = ttk.Combobox(
            frame_engine,
            textvariable=self.translation_engine_var,
            values=list(TRANSLATION_ENGINES.keys()),
            width=19,
            state="readonly"
        )
        self.combo_translation_engine.pack(side="right")
        self.combo_translation_engine.bind("<<ComboboxSelected>>", self.save_current_config)
        self.add_tooltip(self.combo_translation_engine, "Çeviri için kullanılacak servis. API key olmadan denemek için Google Ücretsiz veya MyMemory Ücretsiz seçilebilir.")

        frame_api = tk.Frame(card, bg=self.c_card)
        frame_api.pack(fill="x", padx=15, pady=(0, 8))

        tk.Label(frame_api, text="AI Studio API Key:", font=("Segoe UI", 9, "bold"), fg=self.c_text, bg=self.c_card).pack(side="left")
        self.entry_gemini_key = tk.Entry(
            frame_api,
            textvariable=self.gemini_api_key_var,
            show="*",
            width=25,
            bg="#11111B",
            fg=self.c_text,
            insertbackground=self.c_text,
            relief="flat"
        )
        self.entry_gemini_key.pack(side="right")
        self.entry_gemini_key.bind("<FocusOut>", self.save_current_config)
        self.entry_gemini_key.bind("<Return>", self.save_current_config)
        self.add_tooltip(self.entry_gemini_key, "Google AI Studio API anahtarını buraya gir. Google Ücretsiz ve MyMemory için gerekmez.")

        frame_model = tk.Frame(card, bg=self.c_card)
        frame_model.pack(fill="x", padx=15, pady=(0, 12))

        tk.Label(frame_model, text="Gemini Model:", font=("Segoe UI", 9, "bold"), fg=self.c_text, bg=self.c_card).pack(side="left")
        self.entry_gemini_model = tk.Entry(
            frame_model,
            textvariable=self.gemini_model_var,
            width=25,
            bg="#11111B",
            fg=self.c_text,
            insertbackground=self.c_text,
            relief="flat"
        )
        self.entry_gemini_model.pack(side="right")
        self.entry_gemini_model.bind("<FocusOut>", self.save_current_config)
        self.entry_gemini_model.bind("<Return>", self.save_current_config)
        self.add_tooltip(self.entry_gemini_model, "Google AI Studio için kullanılacak Gemini model adı.")

        frame_api_tools = tk.Frame(card, bg=self.c_card)
        frame_api_tools.pack(fill="x", padx=15, pady=(0, 12))

        self.lbl_api_key_state = tk.Label(
            frame_api_tools,
            text="API Key: kayıt bekliyor",
            font=("Segoe UI", 8),
            fg=self.c_subtext,
            bg=self.c_card
        )
        self.lbl_api_key_state.pack(side="left")

        btn_clear_api = tk.Button(
            frame_api_tools,
            text="API Key Temizle",
            font=("Segoe UI", 8, "bold"),
            fg=self.c_red,
            bg="#313244",
            activeforeground="#1E1E2E",
            activebackground=self.c_red,
            bd=0,
            padx=8,
            cursor="hand2",
            command=self.clear_api_key
        )
        btn_clear_api.pack(side="right")
        self.add_tooltip(btn_clear_api, "Kayıtlı Google AI Studio API anahtarını bilinçli olarak siler.")

        tk.Frame(card, height=1, bg="#3B3D55").pack(fill="x", padx=15, pady=(0, 10))
        tk.Label(card, text="Gelen Metin ve OCR", font=("Segoe UI", 10, "bold"), fg=self.c_green, bg=self.c_card).pack(anchor="w", padx=15, pady=(0, 6))
        
        frame_select = tk.Frame(card, bg=self.c_card)
        frame_select.pack(fill="x", padx=15, pady=(0, 10))
        
        tk.Label(frame_select, text="🖱️ Gelen Çeviri:", font=("Segoe UI", 9, "bold"), fg=self.c_green, bg=self.c_card).pack(side="left")
        tk.Label(frame_select, text="[Otomatik Akıllı OCR]", font=("Segoe UI", 9, "italic"), fg=self.c_green, bg=self.c_card).pack(side="right")

        frame_ocr_toggle = tk.Frame(card, bg=self.c_card)
        frame_ocr_toggle.pack(fill="x", padx=15, pady=(0, 8))

        self.check_ocr_enabled = tk.Checkbutton(
            frame_ocr_toggle,
            text="OCR özelliği aktif",
            variable=self.ocr_enabled_var,
            command=self.save_current_config,
            font=("Segoe UI", 9, "bold"),
            fg=self.c_text,
            bg=self.c_card,
            activeforeground=self.c_text,
            activebackground=self.c_card,
            selectcolor="#11111B"
        )
        self.check_ocr_enabled.pack(side="left")
        self.add_tooltip(self.check_ocr_enabled, "Kapalıyken OCR kısayolu ekran görüntüsü almaz. Anti-cheat riski olan oyunlarda kapalı tut.")

        btn_select_ocr_area = tk.Button(
            frame_ocr_toggle,
            text="Alan Seç",
            font=("Segoe UI", 8, "bold"),
            fg=self.c_text,
            bg="#313244",
            activeforeground=self.c_text,
            activebackground="#45475A",
            bd=0,
            padx=8,
            cursor="hand2",
            command=self.select_ocr_area
        )
        btn_select_ocr_area.pack(side="right")
        self.add_tooltip(btn_select_ocr_area, "Ekranda sürükleyerek sabit OCR alanı seçer. Sonra OCR bu alanı okur.")

        btn_clear_ocr_area = tk.Button(
            frame_ocr_toggle,
            text="Alani Sifirla",
            font=("Segoe UI", 8, "bold"),
            fg=self.c_subtext,
            bg="#313244",
            activeforeground=self.c_text,
            activebackground="#45475A",
            bd=0,
            padx=8,
            cursor="hand2",
            command=self.clear_ocr_area
        )
        btn_clear_ocr_area.pack(side="right", padx=(0, 6))
        self.add_tooltip(btn_clear_ocr_area, "Secili sabit OCR alanini kaldirir ve profil/fare cevresi okumasina doner.")

        self.lbl_ocr_area_state = tk.Label(
            card,
            text="OCR Alani: profil/fare cevresi",
            font=("Segoe UI", 8),
            fg=self.c_subtext,
            bg=self.c_card,
            anchor="w"
        )
        self.lbl_ocr_area_state.pack(fill="x", padx=15, pady=(0, 8))

        frame_ocr_engine = tk.Frame(card, bg=self.c_card)
        frame_ocr_engine.pack(fill="x", padx=15, pady=(0, 8))

        tk.Label(frame_ocr_engine, text="OCR Motoru:", font=("Segoe UI", 9, "bold"), fg=self.c_text, bg=self.c_card).pack(side="left")
        self.combo_ocr_engine = ttk.Combobox(
            frame_ocr_engine,
            textvariable=self.ocr_engine_var,
            values=list(OCR_ENGINES.keys()),
            width=19,
            state="readonly"
        )
        self.combo_ocr_engine.pack(side="right")
        self.combo_ocr_engine.bind("<<ComboboxSelected>>", self.save_current_config)
        self.add_tooltip(self.combo_ocr_engine, "Otomatik mod once EasyOCR, sonra Tesseract, en son Windows OCR dener.")

        frame_profile = tk.Frame(card, bg=self.c_card)
        frame_profile.pack(fill="x", padx=15, pady=(0, 8))

        tk.Label(frame_profile, text="OCR Profili:", font=("Segoe UI", 9, "bold"), fg=self.c_text, bg=self.c_card).pack(side="left")
        self.combo_ocr_profile = ttk.Combobox(
            frame_profile,
            textvariable=self.ocr_profile_var,
            values=list(OCR_PROFILES.keys()),
            width=19,
            state="readonly"
        )
        self.combo_ocr_profile.pack(side="right")
        self.combo_ocr_profile.bind("<<ComboboxSelected>>", self.apply_ocr_profile)
        self.add_tooltip(self.combo_ocr_profile, "OCR'ın okuyacağı alan tipini seçer: chat satırı, geniş chat veya fare çevresi.")

        frame_preprocess = tk.Frame(card, bg=self.c_card)
        frame_preprocess.pack(fill="x", padx=15, pady=(0, 8))

        self.check_ocr_preprocess = tk.Checkbutton(
            frame_preprocess,
            text="OCR görüntüsünü netleştir",
            variable=self.ocr_preprocess_var,
            command=self.save_current_config,
            font=("Segoe UI", 9, "bold"),
            fg=self.c_text,
            bg=self.c_card,
            activeforeground=self.c_text,
            activebackground=self.c_card,
            selectcolor="#11111B"
        )
        self.check_ocr_preprocess.pack(side="left")
        self.add_tooltip(self.check_ocr_preprocess, "Ekran görüntüsünü OCR öncesi büyütür, kontrastı artırır ve koyu arka planlı yazıları daha okunur hale getirir.")

        frame_mode = tk.Frame(card, bg=self.c_card)
        frame_mode.pack(fill="x", padx=15, pady=(0, 10))

        tk.Label(frame_mode, text="Yapıştırma Modu:", font=("Segoe UI", 9, "bold"), fg=self.c_text, bg=self.c_card).pack(side="left")
        self.combo_replace_mode = ttk.Combobox(
            frame_mode,
            textvariable=self.replace_mode_var,
            values=list(REPLACE_MODES.keys()),
            width=19,
            state="readonly"
        )
        self.combo_replace_mode.pack(side="right")
        self.combo_replace_mode.bind("<<ComboboxSelected>>", self.save_current_config)
        self.add_tooltip(self.combo_replace_mode, "Seçili alanı değiştir: aktif yazı kutusunu çeviriyle değiştirir. Sadece panoya kopyala: metni değiştirmez, çeviriyi panoya alır.")

        frame_ocr = tk.Frame(card, bg=self.c_card)
        frame_ocr.pack(fill="x", padx=15, pady=(0, 10))

        tk.Label(frame_ocr, text="OCR Alanı:", font=("Segoe UI", 9, "bold"), fg=self.c_text, bg=self.c_card).pack(side="left")

        self.spin_ocr_width = tk.Spinbox(
            frame_ocr, from_=120, to=1400, increment=20, width=5,
            textvariable=self.ocr_width_var, command=self.save_current_config
        )
        self.spin_ocr_width.pack(side="right")
        self.spin_ocr_width.bind("<FocusOut>", self.save_current_config)
        self.spin_ocr_width.bind("<Return>", self.save_current_config)
        self.add_tooltip(self.spin_ocr_width, "OCR alanının genişliği. Yazı yatayda kaçıyorsa artır.")

        tk.Label(frame_ocr, text="G", font=("Segoe UI", 8), fg=self.c_subtext, bg=self.c_card).pack(side="right", padx=(8, 3))

        self.spin_ocr_height = tk.Spinbox(
            frame_ocr, from_=20, to=240, increment=4, width=5,
            textvariable=self.ocr_height_var, command=self.save_current_config
        )
        self.spin_ocr_height.pack(side="right")
        self.spin_ocr_height.bind("<FocusOut>", self.save_current_config)
        self.spin_ocr_height.bind("<Return>", self.save_current_config)
        self.add_tooltip(self.spin_ocr_height, "OCR alanının yüksekliği. Çok satırlı metin için artır, yanlış yazı okuyorsa azalt.")

        tk.Label(frame_ocr, text="Y", font=("Segoe UI", 8), fg=self.c_subtext, bg=self.c_card).pack(side="right", padx=(8, 3))

        frame_popup = tk.Frame(card, bg=self.c_card)
        frame_popup.pack(fill="x", padx=15, pady=(0, 10))

        tk.Label(frame_popup, text="Popup Süresi:", font=("Segoe UI", 9, "bold"), fg=self.c_text, bg=self.c_card).pack(side="left")
        self.spin_popup_seconds = tk.Spinbox(
            frame_popup, from_=1, to=15, increment=1, width=5,
            textvariable=self.popup_seconds_var, command=self.save_current_config
        )
        self.spin_popup_seconds.pack(side="right")
        self.spin_popup_seconds.bind("<FocusOut>", self.save_current_config)
        self.spin_popup_seconds.bind("<Return>", self.save_current_config)
        self.add_tooltip(self.spin_popup_seconds, "OCR veya seçili metin çeviri balonunun ekranda kalma süresi.")
        tk.Label(frame_popup, text="sn", font=("Segoe UI", 8), fg=self.c_subtext, bg=self.c_card).pack(side="right", padx=(0, 6))

        frame_typing_popup = tk.Frame(card, bg=self.c_card)
        frame_typing_popup.pack(fill="x", padx=15, pady=(0, 10))

        self.check_typing_popup = tk.Checkbutton(
            frame_typing_popup,
            text="Yazma popup'ı",
            variable=self.typing_popup_enabled_var,
            command=self.save_current_config,
            font=("Segoe UI", 9, "bold"),
            fg=self.c_text,
            bg=self.c_card,
            activeforeground=self.c_text,
            activebackground=self.c_card,
            selectcolor="#11111B"
        )
        self.check_typing_popup.pack(side="left")
        self.add_tooltip(self.check_typing_popup, "Yazarken altta çıkan çeviri önerisi balonunu açar veya kapatır.")

        self.spin_typing_popup_seconds = tk.Spinbox(
            frame_typing_popup, from_=1, to=10, increment=1, width=5,
            textvariable=self.typing_popup_seconds_var, command=self.save_current_config
        )
        self.spin_typing_popup_seconds.pack(side="right")
        self.spin_typing_popup_seconds.bind("<FocusOut>", self.save_current_config)
        self.spin_typing_popup_seconds.bind("<Return>", self.save_current_config)
        self.add_tooltip(self.spin_typing_popup_seconds, "Yazma çevirisi balonunun kaç saniye görüneceği.")
        tk.Label(frame_typing_popup, text="sn", font=("Segoe UI", 8), fg=self.c_subtext, bg=self.c_card).pack(side="right", padx=(0, 6))

        frame_buffer = tk.Frame(card, bg=self.c_card)
        frame_buffer.pack(fill="x", padx=15, pady=(0, 10))

        tk.Label(frame_buffer, text="Yazı Hafızası:", font=("Segoe UI", 9, "bold"), fg=self.c_text, bg=self.c_card).pack(side="left")
        self.spin_typing_buffer_seconds = tk.Spinbox(
            frame_buffer, from_=3, to=60, increment=1, width=5,
            textvariable=self.typing_buffer_seconds_var, command=self.save_current_config
        )
        self.spin_typing_buffer_seconds.pack(side="right")
        self.spin_typing_buffer_seconds.bind("<FocusOut>", self.save_current_config)
        self.spin_typing_buffer_seconds.bind("<Return>", self.save_current_config)
        self.add_tooltip(self.spin_typing_buffer_seconds, "Programın yazdığın cümleyi kaç saniye hatırlayacağı. Uzun cümle yazıyorsan artır.")
        tk.Label(frame_buffer, text="sn", font=("Segoe UI", 8), fg=self.c_subtext, bg=self.c_card).pack(side="right", padx=(0, 6))

        if not TRAY_SUPPORTED:
            lbl_warning = tk.Label(
                parent, 
                text="⚠️ Sistem tepsisi için terminale şunu yazın:\npip install pystray pillow", 
                font=("Segoe UI", 7, "bold"), fg=self.c_red, bg=self.c_bg, justify="center"
            )
            lbl_warning.pack(pady=(5, 16))
        else:
            lbl_info = tk.Label(
                parent, 
                text="💡 İpucu: Fareyi Albion sohbetine götürüp Ctrl+Q basın!", 
                font=("Segoe UI", 8, "italic"), fg=self.c_subtext, bg=self.c_bg
            )
            lbl_info.pack(pady=(5, 16))

    def setup_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem("Göster / Aç", self.restore_from_tray, default=True),
            pystray.MenuItem("Duraklat / Başlat", self.toggle_pause),
            pystray.MenuItem("Kapat", self.terminate)
        )
        img = create_tray_image()
        self.tray_icon = pystray.Icon("monstranslate", img, "MonsTranslate", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def on_minimize(self, event):
        if TRAY_SUPPORTED and self.root.state() == 'iconic':
            self.root.withdraw()

    def restore_from_tray(self):
        self.root.deiconify()
        self.root.state('normal')
        self.root.lift()
        self.root.focus_force()

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        
        if self.tracker:
            self.tracker.active = not self.is_paused
        if self.mouse_tracker:
            self.mouse_tracker.active = not self.is_paused
            
        if self.is_paused:
            self.set_status("Sistem Durduruldu - Pasif", self.c_red)
            self.btn_pause.config(text="Sistemi Başlat", bg=self.c_green)
            self.hide_typing_popup()
            self.hover_win.withdraw()
        else:
            self.set_status("Sistem Aktif - Fare Altını Çevirebilir", self.c_green)
            self.btn_pause.config(text="Sistemi Duraklat", bg=self.c_accent)
            
    def clear_buffer_manually(self):
        if self.tracker:
            self.tracker.buffer = ""
        self.handle_typing_update("")

    def hide_typing_popup(self, reset_buffer=True):
        if self.typing_hide_timer:
            self.root.after_cancel(self.typing_hide_timer)
            self.typing_hide_timer = None
        if reset_buffer and self.tracker:
            self.tracker.buffer = ""
            self.last_translation = ""
            self.translator_engine.request_translation("")
        self.typing_win.withdraw()

    def schedule_typing_popup_hide(self):
        if self.typing_hide_timer:
            self.root.after_cancel(self.typing_hide_timer)
        self.save_current_config()
        self.typing_hide_timer = self.root.after(
            self.config["typing_popup_seconds"] * 1000,
            lambda: self.hide_typing_popup(reset_buffer=False)
        )

    def set_status(self, text, color=None):
        color = color or self.c_green
        self.lbl_status_text.config(text=text, fg=color)
        self.status_canvas.itemconfig(self.status_led, fill=color)

    def update_engine_status(self, engine_used):
        labels = {
            "gemini": ("Son Motor: Google AI Studio", self.c_green),
            "google_free": ("Son Motor: Google Ücretsiz", self.c_accent),
            "mymemory": ("Son Motor: MyMemory Ücretsiz", self.c_green),
            "mymemory_error": ("Son Motor: MyMemory hata verdi", self.c_red),
            "gemini_error": ("Son Motor: Gemini hata verdi", self.c_red),
            "gemini_missing_key": ("Son Motor: Gemini anahtarı eksik", self.c_red),
            "error": ("Son Motor: çeviri hatası", self.c_red),
            "none": ("Son Motor: henüz çeviri yapılmadı", self.c_subtext)
        }
        text, color = labels.get(engine_used, (f"Son Motor: {engine_used}", self.c_subtext))
        if hasattr(self, "lbl_check_engine"):
            self.lbl_check_engine.config(text=text, fg=color)
        
    def on_translation_ready(self, translated_text, engine_used="none"):
        self.last_translation = translated_text
        self.update_engine_status(engine_used)
        self.save_current_config()
        if not translated_text:
            self.hide_typing_popup(reset_buffer=False)
        elif not self.config["typing_popup_enabled"]:
            self.hide_typing_popup(reset_buffer=False)
        else:
            self.lbl_translation.config(text=translated_text)
            if not self.typing_win.winfo_viewable() and not self.is_paused:
                self.typing_win.deiconify()
            self.schedule_typing_popup_hide()
                
    def handle_typing_update(self, buffer_text):
        if not buffer_text.strip():
            self.hide_typing_popup(reset_buffer=False)
        self.translator_engine.request_translation(buffer_text)
        
    def replace_text(self):
        if not self.last_translation or self.is_paused:
            return
            
        self.hide_typing_popup(reset_buffer=False)
        
        if self.tracker:
            self.tracker.buffer = ""
        
        self.save_current_config()
        if self.config["replace_mode"] == "clipboard_only":
            pyperclip.copy(self.last_translation)
            self.set_status("Çeviri panoya kopyalandı", self.c_green)
            return

        # --- IŞIK HIZINDA SEÇ & YAPIŞTIR (Ctrl+A / Ctrl+V) ---
        self.kb_controller.release(Key.ctrl)
        time.sleep(0.01)
        
        old_clipboard = pyperclip.paste()
        pyperclip.copy(self.last_translation)
        
        with self.kb_controller.pressed(Key.ctrl):
            self.kb_controller.press('a')
            self.kb_controller.release('a')
            
        time.sleep(0.01)
        
        with self.kb_controller.pressed(Key.ctrl):
            self.kb_controller.press('v')
            self.kb_controller.release('v')
            
        def restore_clipboard():
            time.sleep(0.5)
            pyperclip.copy(old_clipboard)
        threading.Thread(target=restore_clipboard, daemon=True).start()
        
    def translate_hovered_text(self, text, x, y):
        # Normal fare seçimi yapıldığında tetiklenen çeviri
        if self.is_paused:
            return
            
        def fetch_hover():
            self.save_current_config()
            translated, detected_lang, engine_used = translate_text(text, source_lang='auto', target_lang='tr', config=self.config)
            
            if detected_lang == "tr":
                giden_dil_ismi = self.typing_target_var.get()
                giden_dil_kodu = LANGUAGES.get(giden_dil_ismi, "en")
                translated, _, engine_used = translate_text(text, source_lang='tr', target_lang=giden_dil_kodu, config=self.config)
            
            self.root.after(0, lambda: self.show_hover_popup(translated, x, y, source_text=text))
            self.root.after(0, lambda: self.update_engine_status(engine_used))
            
        threading.Thread(target=fetch_hover, daemon=True).start()
        
    def translate_hover_ocr(self):
        # --- ALBİON ONLINE GİBİ OYUNLAR İÇİN HOVER OCR YÖNTEMİ ---
        if self.is_paused:
            return
        self.save_current_config()
        if not self.config.get("ocr_enabled", True):
            px, py = self.root.winfo_pointerx(), self.root.winfo_pointery()
            self.show_hover_popup("[OCR kapalı]", px, py, auto_hide=True, duration_ms=1600)
            self.set_status("OCR kapalı", self.c_red)
            return
            
        # 1. Fare konumunu al
        from pynput.mouse import Controller as MouseController
        mouse_ctrl = MouseController()
        mx, my = mouse_ctrl.position
        
        ocr_width = self.config["ocr_width"]
        ocr_height = self.config["ocr_height"]
        ocr_left_offset = self.config["ocr_left_offset"]
        self.set_status("OCR okunuyor...", self.c_accent)
        self.hover_win.withdraw()

        fixed_area = self.config.get("ocr_fixed_area")
        if isinstance(fixed_area, list) and len(fixed_area) == 4:
            ocr_attempts = split_large_ocr_bbox(tuple(int(v) for v in fixed_area))
        else:
            ocr_attempts = build_ocr_attempts(mx, my, ocr_width, ocr_height, ocr_left_offset)
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        ocr_attempts = [
            (attempt_name, clamp_ocr_bbox(bbox, screen_w, screen_h))
            for attempt_name, bbox in ocr_attempts
        ]
        log_ocr_debug("ocr_start", {
            "mouse": [mx, my],
            "fixed_area": fixed_area,
            "screen": [screen_w, screen_h],
            "ocr_engine": self.config.get("ocr_engine", "auto"),
            "attempts": [{"name": name, "bbox": list(bbox)} for name, bbox in ocr_attempts],
            "preprocess": bool(self.config.get("ocr_preprocess"))
        })
            
        # 3. GUI'nin donmasını önlemek için arka planda OCR ve çeviri yap
        def run_ocr_thread():
            time.sleep(0.08)
            recognized_text = ""
            matched_attempt = ""

            for attempt_name, bbox in ocr_attempts:
                temp_file = tempfile.NamedTemporaryFile(prefix="global_translator_ocr_", suffix=".png", delete=False)
                temp_img_path = temp_file.name
                temp_file.close()

                try:
                    raw_img = ImageGrab.grab(bbox)
                    log_ocr_debug("capture_ok", {
                        "attempt": attempt_name,
                        "bbox": list(bbox),
                        "raw_size": [raw_img.width, raw_img.height],
                        "raw_mode": raw_img.mode
                    })
                    try:
                        raw_img.save(LAST_OCR_RAW_CAPTURE_PATH)
                    except Exception as save_error:
                        log_error("Could not save raw OCR capture", save_error)
                    image_variants = [("ham", raw_img)]
                    if self.config["ocr_preprocess"]:
                        image_variants.append(("net", preprocess_ocr_image(raw_img)))

                    for variant_name, img in image_variants:
                        ocr_img = prepare_image_for_windows_ocr(img)
                        try:
                            ocr_img.save(LAST_OCR_CAPTURE_PATH)
                        except Exception as save_error:
                            log_error("Could not save last OCR capture", save_error)
                        ocr_img.save(temp_img_path)
                        candidate_text = read_ocr_with_retries(temp_img_path, engine_code=self.config.get("ocr_engine", "auto"))
                        if not candidate_text and os.path.exists(LAST_OCR_CAPTURE_PATH):
                            candidate_text = read_ocr_with_retries(LAST_OCR_CAPTURE_PATH, attempts=2, engine_code=self.config.get("ocr_engine", "auto"))
                        log_ocr_debug("candidate_result", {
                            "attempt": attempt_name,
                            "variant": variant_name,
                            "image_size": [ocr_img.width, ocr_img.height],
                            "text_len": len(candidate_text or ""),
                            "text_sample": (candidate_text or "")[:180]
                        })
                        if candidate_text:
                            recognized_text = candidate_text
                            matched_attempt = f"{attempt_name}/{variant_name}"
                            break
                except Exception as e:
                    log_ocr_debug("attempt_exception", {"attempt": attempt_name, "error": repr(e)})
                    log_error(f"Screen capture/OCR failed for attempt {attempt_name}", e)
                finally:
                    try:
                        if os.path.exists(temp_img_path):
                            os.remove(temp_img_path)
                    except Exception:
                        log_error(f"Could not remove temporary OCR image: {temp_img_path}")

                if recognized_text:
                    break
                
            if not recognized_text.strip():
                log_ocr_debug("ocr_failed_no_text", {"attempt_count": len(ocr_attempts)})
                self.root.after(0, lambda: self.show_hover_popup("[Yazı algılanamadı]", mx, my, auto_hide=True, duration_ms=1600))
                self.root.after(0, lambda: self.set_status("Yazı algılanamadı - son görüntü kaydedildi", self.c_red))
                return
                
            # Akıllı otomatik çeviriyi çalıştır
            self.root.after(0, lambda: self.set_status("Çeviri yapılıyor...", self.c_accent))
            translated, detected_lang, engine_used = translate_text(recognized_text, source_lang='auto', target_lang='tr', config=self.config)
            log_ocr_debug("translation_result", {
                "recognized_len": len(recognized_text),
                "recognized_sample": recognized_text[:180],
                "detected_lang": detected_lang,
                "engine_used": engine_used,
                "translated_sample": (translated or "")[:180]
            })
            
            # Eğer algılanan yazı zaten Türkçe ise, seçilmiş olan giden dile çevir
            if detected_lang == "tr":
                giden_dil_ismi = self.typing_target_var.get()
                giden_dil_kodu = LANGUAGES.get(giden_dil_ismi, "en")
                translated, _, engine_used = translate_text(recognized_text, source_lang='tr', target_lang=giden_dil_kodu, config=self.config)
                
            self.root.after(0, lambda: self.show_hover_popup(translated, mx, my, source_text=f"{recognized_text} ({matched_attempt})"))
            self.root.after(0, lambda: self.update_engine_status(engine_used))
            self.root.after(0, lambda: self.set_status("Sistem Aktif - Fare Altını Çevirebilir", self.c_green))
            
        threading.Thread(target=run_ocr_thread, daemon=True).start()
        
    def show_hover_popup(self, text, x, y, source_text="", auto_hide=True, duration_ms=None):
        if self.is_paused:
            return
            
        if self.hover_timer:
            self.root.after_cancel(self.hover_timer)
            self.hover_timer = None

        if source_text:
            self.lbl_hover_source.config(text=f"Algılanan: {source_text}")
            self.lbl_hover_source.pack(fill="x", padx=16, pady=(12, 2))
        else:
            self.lbl_hover_source.config(text="")
            self.lbl_hover_source.pack_forget()
        self.lbl_hover.config(text=text)
        self.hover_win.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        popup_w = max(self.hover_win.winfo_reqwidth(), 180)
        px = min(max(0, x + 16), max(0, screen_w - popup_w - 12))
        py = max(0, y + 18)
        self.hover_win.geometry(f"+{px}+{py}")
        self.hover_win.deiconify()
        
        if auto_hide:
            self.save_current_config()
            hide_after = duration_ms if duration_ms is not None else self.config["popup_seconds"] * 1000
            self.hover_timer = self.root.after(hide_after, self.hover_win.withdraw)
        
    def terminate(self):
        self.save_current_config()
        if hasattr(self, "translator_engine"):
            self.translator_engine.stop()
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
        on_ocr_trigger=app.translate_hover_ocr,
        on_select_ocr_area_trigger=app.select_ocr_area,
        on_exit_trigger=app.terminate,
        root_ref=app.root,
        get_shortcuts=app.get_shortcuts,
        get_buffer_timeout=app.get_buffer_timeout
    )
    
    mouse_tracker = MouseSelectionTracker(
        on_text_selected=app.translate_hovered_text
    )
    
    app.set_trackers(tracker, mouse_tracker)
    
    kbd_listener = keyboard.Listener(
        on_press=tracker.on_press,
        on_release=tracker.on_release
    )
    kbd_listener.start()
    
    mouse_listener = mouse.Listener(
        on_click=mouse_tracker.on_click
    )
    mouse_listener.start()
    
    app.run()
