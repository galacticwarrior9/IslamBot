### Quran Translation scripts and data

This repository contains Python scripts to scrape Quran translations from Wikisource and convert them into structured JSON format.

#### 1. `sablukov.py`
- Scrapes **Gordiy Sablukov's Russian translation** (1894) in two editions:
  - `DO`: Pre-reform Russian (`sablukov_do.json`)
  - `VT`: Modern Russian (`sablukov_vt.json`)
#### 2. `buczacki.py`
- Scrapes **Jan Murza Tarak Buczacki's Polish translation** (1858)
- Output: `buczacki.json`
#### 3. `JSON_format.json`
- Example Quran translation JSON structure

---

### Key Features
- **Robust scraping** with retries and exponential backoff
- **Partial files** (`*_partial.json`) are generated on interruption or errors
- **Verse/text cleaning** options (remove footnotes, whitespace)
- **Colorized console output** for monitoring
- **Metadata inclusion** (translator, source, license, timestamps)
- **Signal handling** (Ctrl+C friendly)

---

### Installation
```
pip install -r requirements.txt
```

---

### Usage
Run all scrapers (takes ~5-10 minutes):
```
python sablukov.py DO      # Pre-reform Russian
python sablukov.py VT      # Modern Russian
python buczacki.py         # Polish
```

#### Command Options
| Flag | Description |
|------|-------------|
| `--no-clean-sura-names` | Keep original sura formatting (`sablukov.py` only) |
| `--no-clean-verse-texts` | Keep original verse formatting |
| `--no-clean-note-texts` | Keep original footnote formatting |
| `--debug` | Enable verbose debugging output |
| `--help` | Show help |
