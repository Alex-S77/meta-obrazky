# Futbalový sen – Meta obrázky

Každú hodinu stiahne SK feed zápasov (s pôvodnými fotkami), vyrobí ku každému zápasu obrázok
1080×1080 (dizajn C – vstupenka) a zverejní ho na GitHub Pages spolu so
súborom `images.csv` (`g:id;g:image_link`). Mergado ho importuje do Meta
projektu a prepíše ním fotku produktu.

- Feed: https://futbalovysen.sk/?fs_feed=zapasy (dá sa prepísať premennou repozitára `FEED_URL`). Nie Meta feed z Mergada – ten už obsahuje vygenerované obrázky.
- Web má chybu v cache: tá istá adresa niekedy vráti český feed (fotbalovysen.cz, iné ID). Generátor preto pridá do adresy `nocache` a skúša až 8× za sebou; keď slovenský feed nedostane, beh potichu preskočí nasadenie (bez chybového mailu) a ostanú posledné dobré obrázky.
- Overenú SK kópiu feedu zverejní ako `feed-sk.xml`. Z nej importujú SK projekty v Mergade, aby sa do nich nedostal český feed.
- Ručné spustenie: Actions → Meta obrázky → Run workflow
- CZ (fotbalovydarek.cz): ten istý skript s `DARCEKY_COUNTRY=cz` (české texty, cena v Kč podľa feedu, logo `assets/darceky-logo-cz.png`, ak existuje). Zverejní `darceky-cz/` a `darceky-cz/images.csv`. Secrety `DARCEKY_CZ_IDS_FEED` (výstup Mergado projektu Facebook.com [CZ]) a `DARCEKY_CZ_PHOTO_FEED` (feed CZ obchodu). Bez nich sa CZ preskočí.
- Náhľad bez internetu: `python generate.py --sample out`
- Písmo Inter (SIL Open Font License), logo podľa dizajn manuálu.

## Futbalové darčeky (futbalovedarceky.sk)

V tom istom behu vyrobí obrázky aj pre Meta katalóg Darčekov (`darceky.py`) a zverejní ich v `darceky/` spolu s `darceky/images.csv`.

- Štýl prepína premenná repozitára `DARCEKY_STYLE`: `C` = karta (predvolené), `A` = vianočný. Zmena sa prejaví pri ďalšom behu.
- Zoznam produktov berie z výstupného feedu Meta projektu v Mergade (secret `DARCEKY_IDS_FEED`), fotky, názvy a ceny z feedu obchodu (secret `DARCEKY_PHOTO_FEED`). Bez týchto dvoch secretov sa Darčeky preskočia.
- Fotky sa ukladajú do cache, takže sa sťahujú iba nové alebo zmenené.
- Keď Darčeky zlyhajú, beh nič nenasadí a ostanú posledné dobré obrázky (Sen aj Darčeky).
- CZ (fotbalovydarek.cz): ten istý skript s `DARCEKY_COUNTRY=cz` (české texty, cena v Kč podľa feedu, logo `assets/darceky-logo-cz.png`, ak existuje). Zverejní `darceky-cz/` a `darceky-cz/images.csv`. Secrety `DARCEKY_CZ_IDS_FEED` (výstup Mergado projektu Facebook.com [CZ]) a `DARCEKY_CZ_PHOTO_FEED` (feed CZ obchodu). Bez nich sa CZ preskočí.
- Náhľad bez internetu: `python darceky.py --sample out C` (alebo `A`).
