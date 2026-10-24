# Futbalový sen – Meta obrázky

Každú hodinu stiahne SK feed zápasov (s pôvodnými fotkami), vyrobí ku každému zápasu obrázok
1080×1080 (dizajn C – vstupenka) a zverejní ho na GitHub Pages spolu so
súborom `images.csv` (`g:id;g:image_link`). Mergado ho importuje do Meta
projektu a prepíše ním fotku produktu.

- Feed: https://futbalovysen.sk/?fs_feed=zapasy (dá sa prepísať premennou repozitára `FEED_URL`). Nie Meta feed z Mergada – ten už obsahuje vygenerované obrázky.
- Web má chybu v cache: tá istá adresa niekedy vráti český feed (fotbalovysen.cz, iné ID). Generátor preto pridá do adresy `nocache` a skúša až 8× za sebou; keď slovenský feed nedostane, beh potichu preskočí nasadenie (bez chybového mailu) a ostanú posledné dobré obrázky.
- Overenú SK kópiu feedu zverejní ako `feed-sk.xml`. Z nej importujú SK projekty v Mergade, aby sa do nich nedostal český feed.
- Ručné spustenie: Actions → Meta obrázky → Run workflow
- Náhľad bez internetu: `python generate.py --sample out`
- Písmo Inter (SIL Open Font License), logo podľa dizajn manuálu.
