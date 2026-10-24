# Futbalový sen – Meta obrázky

Raz za 6 hodín stiahne SK feed zápasov (s pôvodnými fotkami), vyrobí ku každému zápasu obrázok
1080×1080 (dizajn C – vstupenka) a zverejní ho na GitHub Pages spolu so
súborom `images.csv` (`g:id;g:image_link`). Mergado ho importuje do Meta
projektu a prepíše ním fotku produktu.

- Feed: výstup projektu Google Nákupy [SK] v Mergade (dá sa prepísať premennou repozitára `FEED_URL`). Nie priamo web – GitHub server z USA dostane z futbalovysen.sk český feed s inými ID. Nie Meta feed z Mergada – ten už obsahuje vygenerované obrázky.
- Ak feed nie je slovenský (odkazy mimo futbalovysen.sk), generovanie skončí chybou a ostanú posledné dobré obrázky.
- Ručné spustenie: Actions → Meta obrázky → Run workflow
- Náhľad bez internetu: `python generate.py --sample out`
- Písmo Inter (SIL Open Font License), logo podľa dizajn manuálu.
