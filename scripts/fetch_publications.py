import json
import requests
from scholarly import scholarly
import os
import time

# Configuration
GOOGLE_SCHOLAR_ID = "272CSLUAAAAJ"
AUTHOR_NAME = "Patrycja Lebiecka-Johansen"
ORCID_ID = "0000-0001-8931-453X"
OUTPUT_FILE = "assets/data/publications.json"

def fetch_orcid_publications(orcid_id):
    print(f"Fetching ORCID data for {orcid_id}...")
    url = f"https://pub.orcid.org/v3.0/{orcid_id}/works"
    headers = {"Accept": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Error fetching ORCID data: {response.status_code}")
            return []

        data = response.json()
        works = []
        
        for group in data.get("group", []):
            for work_summary in group.get("work-summary", []):
                try:
                    title = work_summary["title"]["title"]["value"]
                    year = work_summary.get("publication-date", {}).get("year", {}).get("value")
                    url = work_summary.get("url", {}).get("value") if work_summary.get("url") else None
                    
                    # External IDs
                    external_ids = work_summary.get("external-ids", {}).get("external-id", [])
                    doi = next((item["external-id-value"] for item in external_ids if item["external-id-type"] == "doi"), None)
                    
                    if doi and not url:
                        url = f"https://doi.org/{doi}"

                    works.append({
                        "title": title,
                        "year": int(year) if year else 0,
                        "url": url,
                        "source": "ORCID",
                        "venue": work_summary.get("journal-title", {}).get("value"),
                        # ORCID summary lacks full authors. We will rely on Google Scholar for the full list when merging,
                        # or if this is the only source, we accept it as is.
                        "authors": [] 
                    })
                except Exception as e:
                    print(f"Skipping an ORCID entry due to error: {e}")
                    
        return works
    except Exception as e:
        print(f"Exception fetching ORCID: {e}")
        return []

def fetch_google_scholar_publications(author_id):
    print(f"Searching Google Scholar for ID {author_id}...")
    try:
        author = scholarly.search_author_id(author_id)
        # Verify we found the right person
        print(f"Found author: {author.get('name')}")
        
        # Fill basic publication list
        scholarly.fill(author, sections=['publications'])
        
        works = []
        # Limit to avoid timeouts if list is huge, though for this user it should be fine.
        pubs = author['publications']
        print(f"Found {len(pubs)} publications. Fetching details...")
        
        for i, pub in enumerate(pubs):
            try:
                # IMPORTANT: Fill the publication to get the full author list
                # This makes an extra network call per paper.
                scholarly.fill(pub)
                
                title = pub.get('bib', {}).get('title')
                year = pub.get('bib', {}).get('pub_year')
                
                # 'author' field is usually a string "A Author, B Author"
                author_str = pub.get('bib', {}).get('author', '')
                if ' and ' in author_str:
                    authors = author_str.split(' and ')
                else:
                    authors = [a.strip() for a in author_str.split(',')]

                works.append({
                    "title": title,
                    "year": int(year) if year and str(year).isdigit() else 0,
                    "url": pub.get('pub_url'), 
                    "source": "Google Scholar",
                    "venue": pub.get('bib', {}).get('venue') or pub.get('bib', {}).get('journal'),
                    "authors": authors
                })
                
                # Polite delay
                time.sleep(0.5) 
                
            except Exception as e:
                print(f"Error processing publication {i}: {e}")
                
        return works
    except Exception as e:
        print(f"Error fetching Google Scholar data: {e}")
        return []

def load_existing_publications():
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def merge_publications(existing_pubs, scholar_pubs, orcid_pubs):
    merged = {}
    
    def normalize(text):
        if not text: return ""
        return ''.join(e for e in text if e.isalnum()).lower()

    # 1. Load Existing (Highest Priority - prohibits overwriting manual edits)
    for p in existing_pubs:
        key = normalize(p['title'])
        merged[key] = p
        
    # 2. Process fetched data (Only add if new)
    fetched_list = scholar_pubs + orcid_pubs
    
    for p in fetched_list:
        key = normalize(p['title'])
        if key not in merged:
            # New publication found! verify it's not just a minor title variation
            merged[key] = p
        else:
            # Entry exists. We generally trust the "existing" one (manual).
            # Optional: We could try to fill missing fields if the existing one is sparse, 
            # but users want control. Let's strictly preserve provided fields.
            pass
            
    return sorted(merged.values(), key=lambda x: x['year'], reverse=True)

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    existing_data = load_existing_publications()
    print(f"Loaded {len(existing_data)} existing publications.")

    # Run fetch
    scholar_data = fetch_google_scholar_publications(GOOGLE_SCHOLAR_ID)
    orcid_data = fetch_orcid_publications(ORCID_ID)
    
    final_list = merge_publications(existing_data, orcid_data, scholar_data)
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(final_list, f, indent=2)
        
    print(f"Saved {len(final_list)} publications to {OUTPUT_FILE}")
