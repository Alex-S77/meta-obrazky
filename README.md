# Futbalový sen – Meta obrázky

Raz za 6 hodín stiahne feed zápasov z webu (s pôvodnými fotkami), vyrobí ku každému zápasu obrázok
1080×1080 (dizajn C – vstupenka) a zverejní ho na GitHub Pages spolu so
súborom `images.csv` (`g:id;g:image_link`). Mergado ho importuje do Meta
projektu a prepíše ním fotku produktu.

- Feed: https://futbalovysen.sk/?fs_feed=zapasy (dá sa prepísať premennou repozitára `FEED_URL`). Nie Meta feed z Mergada – ten už obsahuje vygenerované obrázky.
- Ručné spustenie: Actions → Meta obrázky → Run workflow
- Náhľad bez internetu: `python generate.py --sample out`
- Písmo Inter (SIL Open Font License), logo podľa dizajn manuálu.
