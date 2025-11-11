# NB Avissøk - Visualiseringsverktøy

Søk i Nasjonalbibliotekets avisarkiv etter "historiske spel" (2015-2025) med interaktive grafer og statistikk.

## 🌐 Anbefalt: Web-visualisering (NY!)

**Enkleste måten å bruke verktøyet med flotte, interaktive grafer!**

### Hurtigstart

```bash
# 1. Installer avhengigheter
pip install -r requirements.txt

# 2. Start webserveren
python3 web_server.py

# 3. Åpne nettleseren på:
# http://localhost:5000
```

### Hva får du?

Web-løsningen gir deg umiddelbar visualisering med:

- 📈 **Interaktiv linjegraf** - Se utviklingen av artikler over tid
- 📊 **Stablede stolpediagram** - Sammenlign topp 10 aviser år for år
- 🥧 **Sektordiagram** - Se markedsandeler for hver avis
- 📉 **Sanntidsstatistikk** - Total artikler, antall aviser, trender
- 🎨 **Moderne design** - Responsiv og brukervennlig

**Ingen endringer i Python-koden!** Web-løsningen wrapper det eksisterende `search.py` scriptet.

### Slik fungerer det

1. Klikk på "Start søk" i nettleseren
2. Serveren kjører det eksisterende `search.py` scriptet
3. Resultatene (CSV-filer) blir automatisk lest og konvertert til grafer
4. Alle visualiseringer lastes øyeblikkelig!

---

## 💻 Alternativ: Kommandolinje (CLI)

Hvis du foretrekker terminal-output eller ikke trenger visualisering:

### Steg 1: Installer Python og dhlab

```bash
# Sjekk om du har Python 3
python3 --version

# Installer avhengigheter
pip install -r requirements.txt
```

### Steg 2: Kjør scriptet

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

## 📁 Filer i prosjektet

- **`web_server.py`** - Flask web-server for visualisering (NY!)
- **`index.html`** - Interaktiv frontend med grafer (NY!)
- **`search.py`** - Original søkescript (uendret)
- **`requirements.txt`** - Python-avhengigheter
- **`README.md`** - Denne filen

## 🔧 Tekniske detaljer

### Web-løsningen

Web-løsningen består av:

1. **Flask server** (`web_server.py`)
   - Kjører det eksisterende `search.py` scriptet
   - Leser genererte CSV-filer
   - Konverterer data til JSON for visualisering
   - Serverer HTML-frontend

2. **HTML Frontend** (`index.html`)
   - Moderne, responsivt design
   - Chart.js for interaktive grafer
   - Ingen server-side avhengigheter utenom Flask
   - Fungerer i alle moderne nettlesere

3. **Original script** (`search.py`)
   - Helt uendret!
   - Bruker dhlab-biblioteket
   - Genererer CSV-filer som vanlig

### Arkitektur

```
Bruker → Browser → Flask Server → search.py → NB API
                         ↓
                    CSV filer
                         ↓
                    JSON data
                         ↓
                    Chart.js
                         ↓
                  Interaktive grafer
```
