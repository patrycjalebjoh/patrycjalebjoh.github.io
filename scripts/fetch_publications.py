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

def merge_publications(orcid_pubs, scholar_pubs):
    merged = {}
    
    def normalize(text):
        if not text: return ""
        return ''.join(e for e in text if e.isalnum()).lower()

    # Start with Google Scholar (richer author data)
    for p in scholar_pubs:
        key = normalize(p['title'])
        merged[key] = p
        
    # Merge ORCID (better links/DOIs)
    for p in orcid_pubs:
        key = normalize(p['title'])
        if key in merged:
            existing = merged[key]
            # update URL if ORCID has one and Scholar does not (or ORCID has DOI)
            if p.get('url') and 'doi.org' in p['url']:
                existing['url'] = p['url']
            elif p.get('url') and not existing.get('url'):
                existing['url'] = p['url']
                
            # If Scholar failed to get venue, take ORCID
            if not existing.get('venue') and p.get('venue'):
                existing['venue'] = p['venue']
        else:
            # If only in ORCID, add it.
            # However, authors might be empty lists.
            if not p['authors']:
                p['authors'] = ["Patrycja Lebiecka-Johansen"] # Fallback
            merged[key] = p
            
    return sorted(merged.values(), key=lambda x: x['year'], reverse=True)

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # Run fetch
    scholar_data = fetch_google_scholar_publications(GOOGLE_SCHOLAR_ID)
    orcid_data = fetch_orcid_publications(ORCID_ID)
    
    final_list = merge_publications(orcid_data, scholar_data)
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(final_list, f, indent=2)
        
    print(f"Saved {len(final_list)} publications to {OUTPUT_FILE}")
