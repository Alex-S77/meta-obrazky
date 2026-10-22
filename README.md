# Futbalový sen – Meta obrázky

Raz za 6 hodín stiahne Meta feed z Mergada, vyrobí ku každému zápasu obrázok
1080×1080 (dizajn C – vstupenka) a zverejní ho na GitHub Pages spolu so
súborom `images.csv` (`g:id;g:image_link`). Mergado ho importuje do Meta
projektu a prepíše ním fotku produktu.

- Feed: Meta projekt v Mergade (dá sa prepísať premennou repozitára `FEED_URL`)
- Ručné spustenie: Actions → Meta obrázky → Run workflow
- Náhľad bez internetu: `python generate.py --sample out`
- Písmo Inter (SIL Open Font License), logo podľa dizajn manuálu.
