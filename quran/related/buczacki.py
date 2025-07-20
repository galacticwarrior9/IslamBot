import requests
from bs4 import BeautifulSoup, Tag
import json
import re
import time
import argparse
from datetime import datetime, timezone
from collections import defaultdict
import colorama
from colorama import Fore, Style
import urllib.parse
import random
import signal
from fake_useragent import UserAgent
import sys

# Initialize colorama
colorama.init()

# Global flag to track interruption
interrupted = False

class BuczackiScraper:
    def __init__(self):
        self.base_url = "https://pl.wikisource.org"
        self.index_url = f"{self.base_url}/wiki/Koran_(t%C5%82um._Buczacki,_1858)"
        self.metadata = {
            "id": "buczacki",
            "name": "Koran (tłum. Buczacki, 1858)",
            "translator": "Jan Murza Tarak Buczacki",
            "language": "pl",
            "publication_year": 1858,
            "source": self.index_url,
            "license": "Tekst jest własnością publiczną (public domain). Szczegóły licencji na stronach autorów: Władysław Kościuszko, Mahomet i tłumacza: Jan Murza Tarak Buczacki.",
            "revision": datetime.now().strftime("%Y-%m-%d"),
            "generator": "Tim Abdiukov/BuczackiScraper v1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat() + "Z",
            "notes": "Scraped from Wikisource.  WARSZAWA.  NAKŁAD A. NOWOLECKIEGO."
        }
        self.sura_data = {}
        self.session = requests.Session()

        # Initialize UserAgent
        ua = UserAgent(min_version="136.0", fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
        self.session.headers.update({
            "User-Agent": ua.chrome
        })

        # Register signal handler
        signal.signal(signal.SIGINT, self.signal_handler)

    @staticmethod
    def roman_to_int(r):
        """Very small helper (supports I–CXIV)."""
        roman_map = dict(I=1, V=5, X=10, L=50, C=100)
        val, prev = 0, 0
        for ch in reversed(r):
            cur = roman_map[ch]
            val += -cur if cur < prev else cur
            prev = cur
        return val

    def signal_handler(self, signum, frame):
        """Handle SIGINT (Ctrl+C) by setting global interrupted flag"""
        global interrupted
        interrupted = True
        print(f"\n{Fore.YELLOW}Interrupt received. Finishing current sura and saving partial results...{Style.RESET_ALL}")

    def fetch_with_retry(self, url, max_retries=10):
        """Fetch URL with exponential backoff and retries"""
        for attempt in range(max_retries):
            try:
                if args.debug:
                    print(f"Fetching URL ({attempt+1}/{max_retries}): {Fore.CYAN}{urllib.parse.unquote(url)}{Style.RESET_ALL}")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                if args.debug:
                    print(f"Successfully fetched {Fore.GREEN}{urllib.parse.unquote(url)}{Style.RESET_ALL}")
                return response
            except (requests.RequestException, ConnectionError) as e:
                if attempt < max_retries - 1:
                    backoff = 2 ** attempt + (attempt * 0.5) + random.randint(0,2)
                    print(f"{Fore.YELLOW}Retry {attempt+1}/{max_retries} for {urllib.parse.unquote(url)} - waiting {backoff:.1f}s{Style.RESET_ALL}")
                    time.sleep(backoff)
                else:
                    print(f"{Fore.RED}Failed to fetch {urllib.parse.unquote(url)} after {max_retries} attempts{Style.RESET_ALL}")
        return None

    def parse_index(self):
        """
        Collects every “Rozdział …” link that belongs to the Buczacki
        translation.  Works against the live HTML no matter what order the
        templates render in.
        """
        print(f"Fetching index page: {Fore.CYAN}{urllib.parse.unquote(self.index_url)}{Style.RESET_ALL}")
        resp = self.fetch_with_retry(self.index_url)
        if not resp:
            print(f"{Fore.RED}Failed to retrieve index page{Style.RESET_ALL}")
            return False

        soup = BeautifulSoup(resp.text, "html.parser")

        # 1) Find the summary block.
        summary = soup.find("div", class_="ws-summary")
        if not summary:
            print(f"{Fore.RED}Could not locate <div class='ws-summary'>{Style.RESET_ALL}")
            return

        # 2) Every chapter link looks like …/Rozdział_I, …/Rozdział_II, …
        chap_links = summary.select('a[href*="/Rozdzia%C5%82_"]')
        if not chap_links:
            print(f"{Fore.RED}No chapter links found in summary{Style.RESET_ALL}")
            return

        for a in chap_links:
            href = a["href"]
            # Extract the roman numeral (I, II, …) from the URL and
            # map it to 1‑114.
            roman = href.rsplit("_", 1)[-1]       # 'I', 'II', …
            sura_num = self.roman_to_int(roman)        # own helper

            if sura_num is None or not (1 <= sura_num <= 114):
                continue

            name_pl = a.get_text(strip=True) or f"Sura {sura_num}"
            page_url = urllib.parse.urljoin(self.base_url, href)

            self.sura_data[sura_num] = {
                "name": "",                 # Arabic name not supplied on this page
                "translated_name": name_pl,
                "note": "",
                "page_url": page_url,
                "verses": {}
            }

            print(f"Registered sura {Fore.CYAN}{sura_num}{Style.RESET_ALL}: {name_pl}")

        sura_count = len(self.sura_data)
        color = Fore.BLUE if sura_count > 0 else Fore.RED
        print(f"Index processing complete: {color}{sura_count} suras registered{Style.RESET_ALL}")

        # Add verification for exactly 114 suras
        if sura_count != 114:
            print(f"{Fore.RED}CRITICAL ERROR: Expected 114 suras, found {sura_count}. Halting execution.{Style.RESET_ALL}")
            return False
        return True

    def clean_verse_text(self, text):
        """Clean verse text by removing extra spaces and footnote markers"""
        # Remove footnote markers like [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def clean_note_text(self, text):
        """
        Clean note text by:
        1. Replacing literal '\n' strings and actual newlines with spaces
        2. Removing square-bracketed numbers like [5] or [67]
        3. Collapsing multiple spaces
        """
        text = text.replace('\\n', ' ')
        # Remove square-bracketed numbers
        text = re.sub(r'\[\d+\]', '', text)
        # Collapse multiple consecutive spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def parse_sura_page(self, sura_num, sura_info):
        """Parse individual sura page to extract verses and footnotes"""
        global interrupted
        if interrupted:
            return

        print(f"Processing sura    {Fore.CYAN}{sura_num}{Style.RESET_ALL}: {Fore.CYAN}{sura_info['translated_name']}{Style.RESET_ALL}")
        response = self.fetch_with_retry(sura_info['page_url'])
        if not response:
            print(f"{Fore.RED}Failed to retrieve sura {sura_num}{Style.RESET_ALL}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract note if exists
        note_div = soup.find('div', class_='center')
        if note_div:
            sura_info['note'] = note_div.get_text(strip=True)

        # Find verses container
        text_container = soup.find('div', class_='prp-pages-output')
        if not text_container:
            print(f"{Fore.RED}Text container not found for sura {sura_num}{Style.RESET_ALL}")
            return

        verses = {}
        current_verse = None
        verse_text_parts = []
        footnote_refs = {}

        # Process all paragraphs in the container
        paragraphs = text_container.find_all('p')
        for p in paragraphs:
            if interrupted:
                break

            if not p.get_text(strip=True):
                continue

            for element in p.children:
                if interrupted:
                    break

                # ── NEW: handle “1.” style verse markers ───────────────────────────
                if isinstance(element, str):
                    m = re.match(r'^\s*(\d+)\.\s*(.*)', element)
                    if m:
                        # finish the previous verse first
                        if current_verse and verse_text_parts:
                            verses[current_verse] = {
                                "text": self.clean_verse_text(''.join(verse_text_parts)),
                                "footnotes": []
                            }
                        current_verse = m.group(1)
                        verse_text_parts = [m.group(2)]
                        continue     # go to next child
                elif isinstance(element, Tag):
                    # Verse number detection
                    if element.name == 'span' and 'class' in element.attrs and 'ws-pagenum' in element['class']:
                        continue  # Skip page numbers

                    # Verse number marker
                    if element.name == 'b' and element.get_text(strip=True).isdigit():
                        if current_verse and verse_text_parts:
                            raw_text = ''.join(verse_text_parts).strip()
                            if args.clean_verse_text:
                                verse_text = self.clean_verse_text(raw_text)
                            else:
                                verse_text = raw_text
                            verses[current_verse] = {
                                "text": verse_text,
                                "footnotes": []
                            }
                            verse_text_parts = []
                        current_verse = element.get_text(strip=True)

                    # Footnote reference
                    elif element.name == 'sup' and element.get('id', '').startswith('cite_ref'):
                        ref_id = element['id'][9:]  # obcina 'cite_ref-'
                        footnote_refs[ref_id] = current_verse

                    # Regular text
                    elif current_verse:
                        verse_text_parts.append(element.get_text(strip=True))

        # Handle last verse
        if current_verse and verse_text_parts and not interrupted:
            raw_text = ''.join(verse_text_parts).strip()
            if args.clean_verse_text:
                verse_text = self.clean_verse_text(raw_text)
            else:
                verse_text = raw_text
            verses[current_verse] = {
                "text": verse_text,
                "footnotes": []
            }

        # Process footnotes if not interrupted
        if not interrupted:
            # Wikisource zmienił szablon: <div class="refsection"><ol class="references">
            references_div = (
                soup.find('div', class_='references-small')
                or soup.find('div', class_='refsection')
            )
            if references_div:
                for li in references_div.select('li[id^="cite_note"]'):
                    if interrupted:
                        break
                    note_id = li['id'][10:]  # obcina dokładnie 'cite_note-'
                    note_text = li.get_text(strip=True)
                    if note_id in footnote_refs:
                        verse_num = footnote_refs[note_id]
                        if verse_num in verses:
                            verses[verse_num]["footnotes"].append({
                                "marker": note_id,
                                "text": note_text
                            })

        # Save results
        sura_info['verses'] = verses
        verse_count = len(verses)
        footnote_count = 0

        # Count total footnotes and remove empty arrays
        for v_num, v_data in verses.items():
            if 'footnotes' in v_data and not v_data['footnotes']:
                del v_data['footnotes']  # Remove if no footnotes
            else:
                footnote_count += len(v_data.get('footnotes', []))

        color = Fore.GREEN if verse_count > 0 else Fore.RED
        print(f"Extracted for sura {Fore.CYAN}{sura_num}{Style.RESET_ALL}: "
              f"{color}{verse_count} verses{Style.RESET_ALL}, "
              f"{Fore.MAGENTA}{footnote_count} footnotes{Style.RESET_ALL}")

    def calculate_verse_count(self):
        """Calculate total number of verses across all suras"""
        count = 0
        for sura in self.sura_data.values():
            if 'verses' in sura:
                count += len(sura['verses'])

        do_verse_count_in_meta = False
        if(do_verse_count_in_meta):
            self.metadata['verse_count'] = count
        return count

    def export_to_json(self, partial=False):
        """Export collected data to JSON file"""

        if self.calculate_verse_count() == 0:
            print(f"{Fore.YELLOW}No verses to export{Style.RESET_ALL}")
            return

        output = {
            "metadata": self.metadata,
            "verses": {}
        }

        # Include only suras with verses
        for sura_num, sura_info in self.sura_data.items():
            if 'verses' in sura_info and sura_info['verses']:
                if args.clean_note_text:
                    note = self.clean_note_text(sura_info["note"])
                else:
                    note = sura_info["note"]

                output["verses"][str(sura_num)] = {
                    "name": sura_info["name"],
                    "translated_name": sura_info["translated_name"],
                    "note": sura_info["note"],
                    "verses": sura_info["verses"]
                }

        # Handle partial exports
        if partial:
            self.metadata['notes'] += " (PARTIAL EXPORT)"
            filename = "buczacki_partial.json"
            print(f"{Fore.YELLOW}Exporting partial results{Style.RESET_ALL}")
        else:
            filename = "buczacki.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"{Style.BRIGHT}Export complete:{Style.RESET_ALL} Quran verses saved to {Fore.CYAN}{filename}{Style.RESET_ALL}")

    def run(self):
        """Main method to run the scraping process"""
        global interrupted
        start_time = time.time()

        print(f"{Style.BRIGHT}Starting Buczacki Quran Scraper{Style.RESET_ALL}")
        try:
            # Verify we have exactly 114 suras before proceeding
            if not self.parse_index():
                return
            print(f"{Fore.GREEN}Successfully fetched index with exactly 114 suras.{Style.RESET_ALL}\r\n")
            time.sleep(2)  # Wait before processing suras

            # Process each sura
            for i, (sura_num, sura_info) in enumerate(self.sura_data.items()):
                if interrupted:
                    break
                self.parse_sura_page(sura_num, sura_info)
                time.sleep(1)  # Be polite to the server

            # Export results
            if interrupted:
                self.export_to_json(partial=True)
            else:
                self.export_to_json()

        except Exception as e:
            print(f"{Fore.RED}{Style.BRIGHT}Critical error: {str(e)}{Style.RESET_ALL}")
            # Try to save partial results on critical errors too
            if self.calculate_verse_count() > 0:
                self.metadata['notes'] += " (PARTIAL EXPORT - ERROR)"
                self.export_to_json(partial=True)

        elapsed = time.time() - start_time
        status = f"{Fore.RED}INTERRUPTED{Style.RESET_ALL}" if interrupted else f"{Fore.GREEN}COMPLETED{Style.RESET_ALL}"
        print(f"{Style.BRIGHT}\nOperation {status} in {Fore.CYAN}{elapsed:.2f} seconds{Style.RESET_ALL}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape Buczacki Quran translation from Wikisource')
    parser.add_argument('--no-clean-verse-texts', action='store_false', dest='clean_verse_text',
                        help='Disable cleaning of verse (ayat) text after parsing')
    parser.add_argument('--no-clean-note-texts', action='store_false', dest='clean_note_text',
                        help='Disable cleaning of note text after parsing')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    scraper = BuczackiScraper()
    if args.debug:
        print(f"{Style.BRIGHT}{Fore.YELLOW}DEBUG MODE ENABLED{Style.RESET_ALL}")

    scraper.run()
