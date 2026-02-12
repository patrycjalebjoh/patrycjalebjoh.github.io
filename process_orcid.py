import json

def process_orcid():
    with open('orcid_raw.json', 'r') as f:
        data = json.load(f)
        
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

                venue = work_summary.get("journal-title", {}).get("value")
                
                # Deduplication logic (simple)
                if not any(w['title'] == title for w in works):
                    works.append({
                        "title": title,
                        "year": int(year) if year else 0,
                        "url": url,
                        "source": "ORCID",
                        "venue": venue,
                        "authors": ["Patrycja Lebiecka-Johansen"] # Placeholder as ORCID summary lacks full author list
                    })
            except Exception as e:
                print(f"Skipping: {e}")

    # Sort
    works.sort(key=lambda x: x['year'], reverse=True)
    
    with open('assets/data/publications.json', 'w') as f:
        json.dump(works, f, indent=2)
        
    print(f"Processed {len(works)} publications from ORCID.")

if __name__ == "__main__":
    process_orcid()
