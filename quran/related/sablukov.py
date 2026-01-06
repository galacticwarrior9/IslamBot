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

global args
interrupted = False  # Global flag to track interruption

class SablukovScraper:
    def __init__(self, edition="VT", clean_sura_names=True):
        self.edition = edition.upper()
        self.base_url = "https://ru.wikisource.org"
        self.clean_sura_names = clean_sura_names
        self.index_url = f"{self.base_url}/wiki/Коран_(Мухаммед;_Саблуков)/1894_(ВТ)"
        if self.edition == "DO":
            self.index_url = f"{self.base_url}/wiki/Коран_(Мухаммед;_Саблуков)/1894_(ДО)"

        self.metadata = {
            "id": f"sablukov_{self.edition.lower()}",
            "name": f"Коран (Саблуков) {'Дореформенная орфография' if edition=='DO' else 'Современная орфография'}",
            "translator": "Гордий Семёнович Саблуков",
            "language": "ru",
            "publication_year": 1894,
            "source": self.index_url,
            "license": "Это произведение перешло в общественное достояние в России согласно ст. 1281 ГК РФ, и в странах, где срок охраны авторского права действует на протяжении жизни автора плюс 70 лет или менее, или оно было обнародовано анонимно или под псевдонимом и личность автора не была раскрыта в этот срок.",
            "revision": datetime.now().strftime("%Y-%m-%d"),
            "generator": "Tim Abdiukov/SablukovScraper v1.0.2",
            "generated_at": datetime.now(timezone.utc).isoformat() + "Z",
            "notes": "Перевод Корана на русский язык"
        }

        self.sura_data = {}
        self.session = requests.Session()

        # Ініціалізація UserAgent
        ua = UserAgent(min_version="136.0", fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")

        self.session.headers.update({
            "User-Agent": ua.chrome
        })
        # Register signal handler
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle SIGINT (Ctrl+C) by setting global interrupted flag"""
        global interrupted
        interrupted = True
        print(f"\n{Fore.YELLOW}Interrupt received. Finishing current sura and saving partial results...{Style.RESET_ALL}")

    def fetch_with_retry(self, url, max_retries=10):
        for attempt in range(max_retries):
            try:
                if(args.debug): print(f"Fetching URL ({attempt+1}/{max_retries}): {Fore.CYAN}{urllib.parse.unquote(url)}{Style.RESET_ALL}")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                if(args.debug): print(f"Successfully fetched {Fore.GREEN}{urllib.parse.unquote(url)}{Style.RESET_ALL}")
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
        print(f"Fetching index page: {Fore.CYAN}{urllib.parse.unquote(self.index_url)}{Style.RESET_ALL}")
        response = self.fetch_with_retry(self.index_url)
        if not response:
            print(f"{Fore.RED}Failed to retrieve index page{Style.RESET_ALL}")
            return False

        soup = BeautifulSoup(response.content, 'html.parser')

        # Save HTML for inspection
        if args.debug:
            with open(f"index_{self.edition}.html", "w", encoding="utf-8") as f:
                f.write(str(soup))

        toc_container = soup.find('div', class_='prp-pages-output')
        if not toc_container:
            print(f"{Fore.RED}Could not find table of contents container{Style.RESET_ALL}")
            return

        toc_table = toc_container.find('table')
        if not toc_table:
            print(f"{Fore.RED}Table of contents not found{Style.RESET_ALL}")
            return

        rows = toc_table.find_all('tr')
        print(f"Found {len(rows)} rows in table of contents")

        for i, row in enumerate(rows):
            cols = row.find_all('td')
            if len(cols) < 4:
                if args.debug:
                    print(f"{Fore.YELLOW}Skipping malformed row {i} (only {len(cols)} columns){Style.RESET_ALL}")
                continue

            try:
                # Validate sura number
                sura_num_str = cols[1].text.strip().rstrip(':')
                if not sura_num_str.isdigit():
                    print(f"{Fore.YELLOW}Skipping row {i}: '{sura_num_str}' is not a digit{Style.RESET_ALL}")
                    continue

                sura_num = int(sura_num_str)
                if not (1 <= sura_num <= 999):
                    print(f"{Fore.YELLOW}Skipping row {i}: Sura number {sura_num} out of range{Style.RESET_ALL}")
                    continue

                # Validate link
                link = cols[2].find('a')
                if not link or not link.get('href'):
                    print(f"{Fore.YELLOW}Skipping row {i}: No valid link found{Style.RESET_ALL}")
                    continue

                page_url = f"{self.base_url}{link['href']}"
                if "://" not in page_url:
                    print(f"{Fore.YELLOW}Skipping row {i}: Invalid URL format '{page_url}'{Style.RESET_ALL}")
                    continue

                # Validate Arabic name
                sura_name_ar = cols[3].text.strip()
                if not any('\u0600' <= char <= '\u06FF' for char in sura_name_ar):
                    print(f"{Fore.YELLOW}Skipping row {i}: No Arabic characters in name '{sura_name_ar}'{Style.RESET_ALL}")
                    continue

                # Validate and Sanitize Russian name
                sura_name_ru = link.text.strip()
                if not any('\u0410' <= char <= '\u044F' for char in sura_name_ru):
                    print(f"{Fore.YELLOW}Skipping row {i}: No Russian characters in name '{sura_name_ru}'{Style.RESET_ALL}")
                    continue

                if self.clean_sura_names:
                    cleaned_name = re.sub(r'[^\w!?.\)]+\([Сс]т.+\d\)', '', sura_name_ru).strip()
                    if cleaned_name:
                        if cleaned_name != sura_name_ru and args.debug:
                            print(f"Cleaned sura name: '{sura_name_ru}' → '{cleaned_name}'")
                        sura_name_ru = cleaned_name
                    else:
                        print(f"{Fore.YELLOW}Cleaning resulted in empty name for sura {sura_num}{Style.RESET_ALL}")

                # Validate page reference if present
                page_ref = ""
                if len(cols) >= 5:
                    page_num_match = re.search(r'/(\d+)\.', cols[4].text)
                    if page_num_match:
                        page_ref_str = page_num_match.group(1)
                        if page_ref_str.isdigit():
                            page_ref_int = int(page_ref_str)
                            if 1 <= page_ref_int <= 5000:  # Reasonable page number range
                                page_ref = page_ref_str
                            else:
                                print(f"{Fore.YELLOW}Page reference {page_ref_int} out of range for sura {sura_num}{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.YELLOW}Invalid page reference '{page_ref_str}' for sura {sura_num}{Style.RESET_ALL}")

                # All validations passed - register sura
                self.sura_data[sura_num] = {
                    "name": sura_name_ar,
                    "translated_name": sura_name_ru,
                    "note": "",
                    "page_url": page_url,
                    "page_ref": page_ref,
                    "verses": {}
                }
                print(f"Registered sura {Fore.CYAN}{sura_num}{Style.RESET_ALL}: {sura_name_ru}")
            except Exception as e:
                print(f"{Fore.RED}Error parsing row {i}: {str(e)}{Style.RESET_ALL}")

        sura_count = len(self.sura_data)
        color = Fore.BLUE if sura_count > 0 else Fore.RED
        print(f"Index processing complete: {color}{sura_count} suras registered{Style.RESET_ALL}")

        if sura_count != 114:
            print(f"{Fore.RED}CRITICAL ERROR: Expected 114 suras, found {sura_count}. Halting execution.{Style.RESET_ALL}")
            return False
        return True

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

    def clean_verse_text(self, text):
        """
        Clean verse text by:
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
        global interrupted
        if interrupted:
            return

        print(f"Processing sura    {Fore.CYAN}{sura_num}{Style.RESET_ALL}: {Fore.CYAN}{sura_info['translated_name']}{Style.RESET_ALL}")
        response = self.fetch_with_retry(sura_info['page_url'])
        if not response:
            print(f"{Fore.RED}Failed to retrieve sura {sura_num}{Style.RESET_ALL}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        title_div = soup.find('div', class_='div-center')
        if title_div:
            next_div = title_div.find_next_sibling('div', class_='div-center')
            if next_div and next_div.find('b'):
                sura_info['note'] = next_div.get_text(strip=True)

        text_container = soup.find('div', class_='prp-pages-output')
        if not text_container:
            print(f"{Fore.RED}Text container not found for sura {sura_num}{Style.RESET_ALL}")
            return

        verses = {}
        current_verse = None
        verse_text_parts = []
        footnote_refs = {}
        paragraphs = text_container.find_all('p')

        if not paragraphs:
            print(f"{Fore.RED}No paragraphs found for sura {sura_num}{Style.RESET_ALL}")
            return

        # Special handling for first verse which doesn't have a verse number marker
        first_paragraph = paragraphs[0]
        if first_paragraph.get_text(strip=True):
            # Extract text from first paragraph as verse 1
            if args.clean_verse_text:
                verse_text = self.clean_verse_text(first_paragraph.get_text(strip=True))
            else:
                verse_text = first_paragraph.get_text(strip=True)

            verses["1"] = {"text": verse_text, "footnotes": []}
            # Remove first paragraph from processing list
            paragraphs = paragraphs[1:]

        for p in paragraphs:
            if interrupted:
                break

            if not p.get_text(strip=True):
                continue

            current_verse = None
            verse_text_parts = []
            pre_marker_text = []  # To store text before the first verse marker
            for element in p.children:
                if interrupted:
                    break

                if isinstance(element, str):
                    if current_verse:
                        verse_text_parts.append(element)
                    else:
                        pre_marker_text.append(element)
                elif isinstance(element, Tag):
                    if element.name == 'span' and 'style' in element.attrs and 'color:#00F' in element['style']:
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

                        verse_num = element.get_text(strip=True)
                        if verse_num.isdigit():
                            current_verse = verse_num
                            # Add any pre-marker text to this verse
                            verse_text_parts = pre_marker_text
                            pre_marker_text = []
                    elif element.name == 'sup' and 'id' in element.attrs and element['id'].startswith('cite_ref'):
                        ref_id = element['id'].split('-')[-1]
                        footnote_refs[ref_id] = current_verse
                    elif element.name == 'br':
                        continue
                    elif current_verse:
                        verse_text_parts.append(element.get_text(strip=True))
                    else:
                        pre_marker_text.append(element.get_text(strip=True))

            # After processing all elements
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

        if not interrupted:
            references_div = soup.find('div', class_='references-small')
            if references_div:
                for li in references_div.find_all('li'):
                    if interrupted:
                        break
                    if 'id' in li.attrs and li['id'].startswith('cite_note'):
                        # Extract the numeric part after the dash (e.g., '1' from 'cite_note-1')
                        note_id = li['id'].split('-')[-1]
                        note_text = li.get_text(strip=True)
                        if note_id in footnote_refs:
                            verse_num = footnote_refs[note_id]
                            if verse_num in verses:
                                # Initialize footnotes list if not exists
                                if 'footnotes' not in verses[verse_num]:
                                    verses[verse_num]['footnotes'] = []

                                verses[verse_num]['footnotes'].append({
                                    "marker": note_id,
                                    "text": note_text
                                })

        # Count and report footnotes
        if not interrupted:
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

            if args.debug:
                for v_num, v_data in verses.items():
                    text_preview = v_data['text'][:50] + '...' if len(v_data['text']) > 50 else v_data['text']
                    print(f"Verse {v_num}: {text_preview}")

    def calculate_verse_count(self):
        count = 0
        for sura in self.sura_data.values():
            if 'verses' in sura:
                count += len(sura['verses'])

        do_verse_count_in_meta = False
        if(do_verse_count_in_meta):
            self.metadata['verse_count'] = count
        return count

    def export_to_json(self, partial=False):
        verse_count = self.calculate_verse_count()
        if verse_count == 0:
            print(f"{Fore.YELLOW}No verses to export{Style.RESET_ALL}")
            return

        output = {
            "metadata": self.metadata,
            "verses": {}
        }

        # Only include suras that have verses
        for sura_num, sura_info in self.sura_data.items():

            if 'verses' in sura_info and sura_info['verses']:
                if args.clean_note_text:
                    note = self.clean_note_text(sura_info["note"])
                else:
                    note = sura_info["note"]

                output["verses"][sura_num] = {
                    "name": sura_info["name"],
                    "translated_name": sura_info["translated_name"],
                    "note": note,
                    "verses": sura_info["verses"]
                }

        # Update metadata for partial exports
        if partial:
            self.metadata['notes'] += " (PARTIAL EXPORT)"
            filename = f"sablukov_{self.edition.lower()}_partial.json"
            print(f"{Fore.YELLOW}Exporting partial results{Style.RESET_ALL}")
        else:
            filename = f"sablukov_{self.edition.lower()}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"{Style.BRIGHT}Export complete:{Style.RESET_ALL} Quran verses saved to {Fore.CYAN}{filename}{Style.RESET_ALL}")

    def run(self):
        global interrupted
        start_time = time.time()
        print(f"{Style.BRIGHT}Starting Sablukov Quran Scraper{Style.RESET_ALL}")
        print(f"Processing edition: {Fore.CYAN}{self.edition}{Style.RESET_ALL} ({'Modern' if self.edition=='VT' else 'Pre-reform'} Russian)")

        try:
            # Verify we have exactly 114 suras before proceeding
            if not self.parse_index():
                return

            print(f"{Fore.GREEN}Successfully fetched index with exactly 114 suras.{Style.RESET_ALL}\r\n")
            time.sleep(2)  # Wait before processing suras

            for i, (sura_num, sura_info) in enumerate(self.sura_data.items()):
                if interrupted:
                    break
                self.parse_sura_page(sura_num, sura_info)
                time.sleep(1)

            if interrupted:
                self.export_to_json(partial=True)
            else:
                self.export_to_json()

        except Exception as e:
            print(f"{Fore.RED}{Style.BRIGHT}Critical error: {str(e)}{Style.RESET_ALL}")
            if self.calculate_verse_count() > 0:
                self.metadata['notes'] += " (PARTIAL EXPORT - ERROR)"
                self.export_to_json(partial=True)

        elapsed = time.time() - start_time
        status = f"{Fore.RED}INTERRUPTED{Style.RESET_ALL}" if interrupted else f"{Fore.GREEN}COMPLETED{Style.RESET_ALL}"
        print(f"{Style.BRIGHT}\nOperation {status} in {Fore.CYAN}{elapsed:.2f} seconds{Style.RESET_ALL}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape Sablukov Quran translation from Wikisource')
    parser.add_argument('edition', type=str, choices=['VT', 'DO'],
                        help='Translation edition: VT (modern Russian) or DO (pre-reform Russian)')
    parser.add_argument('--no-clean-sura-names', action='store_false', dest='clean_sura_names',
                        help='Disable cleaning of sura names in index')
    parser.add_argument('--no-clean-verse-texts', action='store_false', dest='clean_verse_text',
                        help='Disable cleaning of verse (ayat) text after parsing')
    parser.add_argument('--no-clean-note-texts', action='store_false', dest='clean_note_text',
                        help='Disable cleaning of note text after parsing')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])


    scraper = SablukovScraper(edition=args.edition, clean_sura_names=args.clean_sura_names)

    if args.debug:
        print(f"{Style.BRIGHT}{Fore.YELLOW}DEBUG MODE ENABLED{Style.RESET_ALL}")
        scraper.parse_index()
        print(f"{Style.BRIGHT}Sura data:{Style.RESET_ALL}")
        for sura_num, data in scraper.sura_data.items():
            print(f"Sura {sura_num}: {data['translated_name']} - {urllib.parse.unquote(data['page_url'])}")
    else:
        scraper.run()
