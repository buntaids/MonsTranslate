# MonsTranslate Roadmap

## Current State

- v1.0.0 GitHub release yayinlandi.
- Windows installer ve portable exe hazir.
- Installer: `MonsTranslate_Setup.exe`
- Portable exe: `MonsTranslate.exe`
- EasyOCR ana OCR motoru olarak kullaniliyor.
- Tesseract ve Windows OCR yedek motor olarak tutuluyor.
- MIT lisansi eklendi.
- GUI kaydirilabilir ve yeniden boyutlandirilabilir.
- API key ekleme alani ve AI test paneli mevcut.
- Kisayol atama penceresi mevcut.
- Sabit OCR alani secme ozelligi mevcut.

## Published Links

- Repository: https://github.com/buntaids/MonsTranslate
- Release v1.0.0: https://github.com/buntaids/MonsTranslate/releases/tag/v1.0.0

## Next Improvements

- Temiz bir Windows makinede installer testi yapmak.
- Ilk acilis ve ilk OCR cagrisini hizlandirmak.
- EasyOCR model yukleme durumunu GUI'de daha net gostermek.
- OCR sonucundaki Turkce karakter bozulmalarini azaltmak.
- Gelen OCR cevirisi icin hedef dil secimi eklemek.
- Otomatik Windows baslangicinda calistir secenegi eklemek.
- Uygulama icinden update checker eklemek.
- Exe imzalama arastirmasi yapmak.
- README icin ekran goruntuleri veya GIF eklemek.
- GitHub issue template eklemek.
- Release build surecini otomatiklestirmek.

## Known Notes

- Exe ve installer buyuk, cunku EasyOCR, Torch ve OCR modelleri pakete dahil.
- Ilk OCR denemesi EasyOCR modeli bellekte yuklenirken yavas olabilir.
- Program imzali olmadigi icin Windows Defender veya SmartScreen uyari gosterebilir.
- OCR ozelligi ekran goruntusu aldigi icin anti-cheat kullanan oyunlarda kapali tutulmasi onerilir.
- Google AI Studio API kotasi dolarsa uygulama ucretsiz ceviri motoruna dusebilir.

## Suggested Future Prompt

Projeye daha sonra devam etmek icin su metin yeterli olur:

```text
MonsTranslate projesine kaldigimiz yerden devam edelim:
https://github.com/buntaids/MonsTranslate

ROADMAP.md dosyasini okuyup siradaki iyilestirmelerden devam et.
```
