# MonsTranslate

MonsTranslate, Windows icin gelistirilmis canli ceviri ve OCR destekli overlay aracidir. Yazdiginiz metni hizlica baska dile cevirebilir, secilen metni okuyabilir ve ekrandaki yazilari OCR ile algilayip ceviri popup'i olarak gosterebilir.

## One Cikan Ozellikler

- Canli yazma cevirisi
- `Ctrl + Space` ile yazilan metni ceviriyle degistirme
- Fareyle secilen metni otomatik cevirme
- Ekrandan sabit OCR alani secme
- EasyOCR tabanli yerel OCR motoru
- Google Ucretsiz, MyMemory Ucretsiz ve Google AI Studio ceviri motorlari
- API key ekleme ve test paneli
- Kisisellestirilebilir kisayollar
- Sistem tepsisi destegi
- Kaydirilabilir profesyonel kontrol paneli
- Anti-cheat riski olan oyunlar icin OCR ac/kapat ayari

## Ne Ise Yarar?

MonsTranslate ozellikle oyun, sohbet, web ve uygulama icindeki metinleri hizli anlamak icin tasarlandi. Secilemeyen metinlerde OCR kullanabilir, yazdiginiz Turkce cumleyi hedef dile cevirip aktif yazi kutusuna uygulayabilir.

Ornek kullanimlar:

- Oyun chat metinlerini cevirmek
- WhatsApp Web, Discord, tarayici veya uygulama metinlerini hizlica anlamak
- Turkce yazdiginiz mesaji Ingilizceye cevirip ayni kutuya yapistirmak
- Ekranda sabit bir bolgeyi OCR ile takip etmek

## Kurulum

En kolay kullanim icin GitHub Releases bolumunden installer dosyasini indirin:

```text
MonsTranslate_Setup.exe
```

Kurulumdan sonra uygulamayi Baslat Menusu veya masaustu kisayoluyla acabilirsiniz.

Portable tek dosya kullanmak isterseniz:

```text
MonsTranslate.exe
```

dosyasini dogrudan calistirabilirsiniz.

> Not: Program imzali olmadigi icin Windows ilk calistirmada guvenlik uyarisi gosterebilir.

## Kullanim

1. MonsTranslate'i acin.
2. `Sistem Kontrolu` bolumunde paket, OCR ve ceviri motoru durumunu kontrol edin.
3. Yazma cevirisi icin hedef dili secin.
4. OCR kullanacaksaniz `OCR ozelligi aktif` ayarini acik tutun.
5. Gerekirse `Alan Sec` ile ekrandan sabit OCR alani belirleyin.

## Varsayilan Kisayollar

- `Ctrl + Space`: Yazilan metni ceviriyle degistirir.
- `Ctrl + Q`: Fare altindaki veya secili OCR alanindaki metni okur ve cevirir.
- `Ctrl + Shift + Q`: Ekrandan sabit OCR alani secme modunu acar.
- `Ctrl + Shift + E`: Uygulamadan cikar.

Kisayollari paneldeki `Kisayollar` dugmesiyle degistirebilirsiniz.

## OCR Motorlari

MonsTranslate otomatik modda su sirayla OCR dener:

1. EasyOCR
2. Tesseract, sistemde kuruluysa
3. Windows OCR, yedek motor olarak

Release installer dosyasinda EasyOCR modelleri paketlenmis olarak gelir. Kaynak koddan calistirirken EasyOCR modellerinin kullanici klasorunde bulunmasi gerekebilir.

## Ceviri Motorlari

- `Google Ucretsiz`: API key istemez.
- `MyMemory Ucretsiz`: API key istemeden test edilebilir.
- `Google AI Studio`: Gemini API key ile calisir.

Google AI Studio kullanmak icin panelde API key alanina anahtarinizi girin ve `AI Test` ile kontrol edin.

## Gelistirici Kurulumu

Kaynak koddan calistirmak icin:

```powershell
pip install -r requirements.txt
python .\translator_v6.pyw
```

Exe olusturmak icin:

```powershell
pip install -r requirements-build.txt
python .\build_exe.py
```

Installer olusturmak icin Inno Setup gerekir:

```powershell
iscc .\installer\MonsTranslate.iss
```

Hazir ciktılar:

```text
dist\MonsTranslate.exe
installer_output\MonsTranslate_Setup.exe
```

## Dosyalar

- `translator_v6.pyw`: Ana uygulama
- `build_exe.py`: PyInstaller ile exe uretir
- `installer/MonsTranslate.iss`: Inno Setup installer betigi
- `assets/monstranslate_icon.ico`: Uygulama ikonu
- `settings.json`: Kullanici ayarlari
- `global_translator.log`: Genel hata kayitlari
- `ocr_debug.log`: OCR tani kayitlari

## Guvenlik Notu

OCR ozelligi ekran goruntusu alir. Anti-cheat kullanan oyunlarda risk almamak icin paneldeki `OCR ozelligi aktif` ayarini kapali tutun.

## Lisans

Bu proje MIT lisansi ile yayinlanmistir. Detaylar icin `LICENSE` dosyasina bakin.
