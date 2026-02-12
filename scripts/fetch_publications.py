import json
import requests
from scholarly import scholarly
import os
from datetime import datetime

# Configuration
GOOGLE_SCHOLAR_ID = "272CSLUAAAAJ"  # Replace with actual ID if different, though I wasn't given one, I will need to search for it or ask. 
# Wait, the user provided ORCID: 0000-0001-8931-453X.
# I need to find the Google Scholar ID. I will add a search step or ask the user.
# For now, I'll structure the script to search by name if ID is missing or just rely on ORCID if Scholar fails.
# Actually, the user requirement said "Fetch ... from Google Scholar (and ORCID ...)"
# I'll implement the logic to search for the user by name if ID isn't provided, but best to ask or find it.
# AUTHOR_NAME = "Patrycja Lebiecka-Johansen"

AUTHOR_NAME = "Patrycja Lebiecka-Johansen"
ORCID_ID = "0000-0001-8931-453X"
OUTPUT_FILE = "assets/data/publications.json"

def fetch_orcid_publications(orcid_id):
    print(f"Fetching ORCID data for {orcid_id}...")
    url = f"https://pub.orcid.org/v3.0/{orcid_id}/works"
    headers = {"Accept": "application/json"}
    response = requests.get(url, headers=headers)
    
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
                
                # External IDs (DOI, etc.)
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
                    "authors": [] # ORCID summary often lacks full author lists, might need details fetch
                })
            except Exception as e:
                print(f"Skipping an ORCID entry due to error: {e}")
                
    return works

def fetch_google_scholar_publications(author_name):
    print(f"Searching Google Scholar for {author_name}...")
    try:
        search_query = scholarly.search_author(author_name)
        author = next(search_query)
        scholarly.fill(author, sections=['publications'])
        
        works = []
        for pub in author['publications']:
            title = pub.get('bib', {}).get('title')
            year = pub.get('bib', {}).get('pub_year')
            
            # Scholarly sometimes fills limited data. 
            # To get full details (like url), we might need `scholarly.fill(pub)`.
            # Doing this for all pubs might be slow/rate-limited. 
            # I'll stick to basic info for now and fill if needed.
            
            works.append({
                "title": title,
                "year": int(year) if year and year.isdigit() else 0,
                "url": pub.get('pub_url'), # Often requires fill()
                "source": "Google Scholar",
                "venue": pub.get('bib', {}).get('venue') or pub.get('bib', {}).get('journal'),
                "authors": pub.get('bib', {}).get('author', '').split(' and ') # simplistic splitting
            })
        return works
    except StopIteration:
        print("Author not found on Google Scholar.")
        return []
    except Exception as e:
        print(f"Error fetching Google Scholar data: {e}")
        return []

def merge_publications(orcid_pubs, scholar_pubs):
    # Simple merge by title (normalized)
    merged = {}
    
    def normalize(text):
        return ''.join(e for e in text if e.isalnum()).lower()

    for p in scholar_pubs:
        key = normalize(p['title'])
        merged[key] = p
        
    for p in orcid_pubs:
        key = normalize(p['title'])
        if key in merged:
            # Update/Enrich existing (prefer ORCID for DOI/Links typically)
            if p.get('url'):
                merged[key]['url'] = p['url']
            if p.get('venue'): # specific check
                 if not merged[key].get('venue'):
                     merged[key]['venue'] = p['venue']
        else:
            merged[key] = p
            
    return sorted(merged.values(), key=lambda x: x['year'], reverse=True)

if __name__ == "__main__":
    # Create output directory if not exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    orcid_data = fetch_orcid_publications(ORCID_ID)
    scholar_data = fetch_google_scholar_publications(AUTHOR_NAME)
    
    final_list = merge_publications(orcid_data, scholar_data)
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(final_list, f, indent=2)
        
    print(f"Saved {len(final_list)} publications to {OUTPUT_FILE}")
