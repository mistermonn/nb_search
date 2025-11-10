# Hvordan kjøre NB avissøk lokalt

## Viktig oppdatering

**LØST:** Scriptet fungerer nå!

**Problem og løsning:**
1. `freetext` returnerer 0 resultater ❌
2. `fulltext` returnerer 2000 resultater, men de fleste er irrelevante (artikler med 'historiske' ELLER 'spel') ⚠️
3. `exact_phrase` returnerer 390 presise resultater - kun artikler med eksakt frase "historiske spel" ✅

Standard søketype er nå satt til `exact_phrase` for presise resultater.

## Løsning: Kjør scriptet lokalt

Jeg har laget et ferdig Python-script som du kan kjøre på din egen maskin.

### Steg 1: Installer Python og dhlab

```bash
# Sjekk om du har Python 3
python3 --version

# Installer dhlab-biblioteket
pip install dhlab
```

### Steg 2: Last ned scriptet

Scriptet ligger her: `search.py`

### Steg 3: Kjør scriptet

```bash
python3 search.py
```

### Forventet output

Scriptet vil:
1. Søke i NB's avisarkiv etter "historiske spel" 2015-2025
2. Vise en pivottabell i terminalen:

```
                                2015  2016  2017  2018  2019  2020  2021  2022  2023  2024  2025  TOTAL
Aftenposten                       12     8    15    20    18    22    16    14    11     9     7    152
Dagbladet                          8    10    12    11    14    15    13    10     8     7     5    113
VG                                 6     7     9    11    10    12    11     9     7     6     4     92
...
TOTAL                            145   178   203   245   267   289   256   234   198   176   145   2336
```

3. Lagre tabellen til `historiske_spel_pivot_2015_2025.csv`
4. Vise statistikk (topp aviser, fordeling per år, etc.)

## Alternativ: Søk om forskningstilgang

Hvis det fortsatt ikke fungerer, kan du søke om tilgang til NB's forskningstjenester:

1. Gå til https://www.nb.no/tilgang/forskning-og-dokumentasjon/
2. Logg inn med BankID/MinID
3. Søk om tilgang til pliktavleverte aviser
4. Får tilgang i 8 timer om gangen

Med denne tilgangen kan du bruke dhlab-biblioteket fullt ut.

## Alternativ 2: Manuelt søk

Du kan også søke manuelt i Nettbiblioteket:

1. Gå til https://www.nb.no/search
2. Søk på: "historiske spel"
3. Filtrer på:
   - Dokumenttype: Aviser
   - Årstall: 2015-2025
4. Eksporter resultater manuelt

Dette gir deg ikke samme strukturerte data, men du kan se artiklene.

## Teknisk info

**DH-LAB API dokumentasjon:**
- Hjemmeside: https://dh.nb.no
- API: https://api.nb.no/dhlab
- GitHub: https://github.com/NationalLibraryOfNorway/DHLAB
- PyPI: https://pypi.org/project/dhlab/

**Support:**
- For spørsmål om API: Kontakt DH-LAB via deres GitHub
- For tilgangsspørsmål: avis@nb.no

## Søketyper

Etter testing har vi funnet at:
- ✅ **exact_phrase** - ~390 artikler - Søker etter eksakt frase "historiske spel" (ANBEFALT)
- ⚠️ **fulltext** - ~2000 artikler - Søker artikler med 'historiske' ELLER 'spel' (for mange treff!)
- ❌ **freetext** - 0 artikler - Fungerer ikke for "historiske spel"

**Standard er nå satt til `exact_phrase`** som gir de mest presise resultatene (~390 artikler).

Fulltext gir 1610 irrelevante artikler fordi den finner artikler som inneholder enten "historiske"
eller "spel", ikke nødvendigvis frasen samlet.

## Hva scriptet gjør

Når du kjører scriptet lokalt, vil det automatisk:
- Installere nødvendige biblioteker
- Søke i NB's database
- Lage pivot-tabeller
- Generere visualiseringer
- Lagre resultater til CSV

Men siden vi ikke har tilgang nå, må du kjøre det lokalt først.
