# scraper.py
import requests
import time
from bs4 import BeautifulSoup
import csv
import os
from urllib.parse import urljoin, quote_plus
import config

def build_search_url(search_term, location, start=0):
    """Build Indeed search URL with parameters"""
    base_url = config.INDEED_SEARCH_URL
    params = {
        'q': search_term,
        'l': location,
        'start': start
    }
    
    # Build URL manually to avoid issues
    url = f"{base_url}?q={quote_plus(search_term)}&l={quote_plus(location)}&start={start}"
    return url

def extract_job_data(job_card):
    """Extract data from a single job card"""
    try:
        # Job title and link - try multiple selectors
        title_elem = None
        title_selectors = [
            {'name': 'h2', 'attrs': {'data-testid': 'job-title'}},
            {'name': 'h2', 'attrs': {'class': 'jobTitle'}},
            {'name': 'a', 'attrs': {'data-testid': 'job-title'}},
            {'name': 'span', 'attrs': {'title': True}},  # Sometimes title is in span with title attribute
        ]
        
        for selector in title_selectors:
            title_elem = job_card.find(selector['name'], selector['attrs'])
            if title_elem:
                print(f"Found title using: {selector}")
                break
        
        if title_elem:
            # If it's an h2, look for a link inside it
            if title_elem.name == 'h2':
                title_link = title_elem.find('a')
                title = title_link.get_text(strip=True) if title_link else title_elem.get_text(strip=True)
                job_url = urljoin(config.INDEED_BASE_URL, title_link['href']) if title_link and title_link.get('href') else "N/A"
            else:
                title = title_elem.get_text(strip=True)
                job_url = urljoin(config.INDEED_BASE_URL, title_elem['href']) if title_elem.get('href') else "N/A"
        else:
            title = "N/A"
            job_url = "N/A"
            print("❌ Could not find job title")
        
        # Company name - try multiple selectors
        company_elem = None
        company_selectors = [
            {'name': 'span', 'attrs': {'data-testid': 'company-name'}},
            {'name': 'span', 'attrs': {'class': 'companyName'}},
            {'name': 'a', 'attrs': {'data-testid': 'company-name'}},
        ]
        
        for selector in company_selectors:
            company_elem = job_card.find(selector['name'], selector['attrs'])
            if company_elem:
                break
        
        company = company_elem.get_text(strip=True) if company_elem else "N/A"
        
        # Location - try multiple selectors
        location_elem = None
        location_selectors = [
            {'name': 'div', 'attrs': {'data-testid': 'job-location'}},
            {'name': 'div', 'attrs': {'class': 'companyLocation'}},
            {'name': 'span', 'attrs': {'class': 'locationsContainer'}},
        ]
        
        for selector in location_selectors:
            location_elem = job_card.find(selector['name'], selector['attrs'])
            if location_elem:
                break
        
        location = location_elem.get_text(strip=True) if location_elem else "N/A"
        
        # Salary (optional) - try multiple selectors
        salary_elem = None
        salary_selectors = [
            {'name': 'span', 'attrs': {'class': 'salary-snippet'}},
            {'name': 'div', 'attrs': {'data-testid': 'salary-snippet'}},
            {'name': 'span', 'attrs': {'data-testid': 'salary-snippet'}},
        ]
        
        for selector in salary_selectors:
            salary_elem = job_card.find(selector['name'], selector['attrs'])
            if salary_elem:
                break
        
        salary = salary_elem.get_text(strip=True) if salary_elem else "N/A"
        
        # Job summary/snippet - try multiple selectors
        summary_elem = None
        summary_selectors = [
            {'name': 'div', 'attrs': {'class': 'job-snippet'}},
            {'name': 'div', 'attrs': {'data-testid': 'job-snippet'}},
            {'name': 'div', 'attrs': {'class': 'summary'}},
        ]
        
        for selector in summary_selectors:
            summary_elem = job_card.find(selector['name'], selector['attrs'])
            if summary_elem:
                break
        
        summary = summary_elem.get_text(strip=True) if summary_elem else "N/A"
        summary = summary[:200] + "..." if len(summary) > 200 else summary  # Truncate long summaries
        
        job_data = {
            'title': title,
            'company': company,
            'location': location,
            'salary': salary,
            'summary': summary,
            'url': job_url
        }
        
        # Only return data if we found at least a title
        if title != "N/A":
            return job_data
        else:
            print("Skipping job card - no title found")
            return None
    
    except Exception as e:
        print(f"Error extracting job data: {e}")
        return None

def scrape_page(search_term, location, start=0):
    """Scrape a single page of Indeed results"""
    url = build_search_url(search_term, location, start)
    print(f"Scraping: {url}")
    
    try:
        response = requests.get(url, headers=config.HEADERS, timeout=config.TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # DEBUG: Save HTML to file to inspect structure
        with open('debug_indeed.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("DEBUG: Saved HTML to debug_indeed.html")
        
        # Try multiple selectors for job cards
        job_cards = []
        
        # Method 1: Most common current selector
        job_cards = soup.find_all('div', {'data-testid': 'slider_item'})
        print(f"Method 1 (slider_item): Found {len(job_cards)} job cards")
        
        if not job_cards:
            # Method 2: Alternative selector
            job_cards = soup.find_all('div', class_='job_seen_beacon')
            print(f"Method 2 (job_seen_beacon): Found {len(job_cards)} job cards")
        
        if not job_cards:
            # Method 3: Table-based layout
            job_cards = soup.find_all('td', class_='resultContent')
            print(f"Method 3 (resultContent): Found {len(job_cards)} job cards")
        
        if not job_cards:
            # Method 4: Try finding by data-jk attribute (job key)
            job_cards = soup.find_all('div', {'data-jk': True})
            print(f"Method 4 (data-jk): Found {len(job_cards)} job cards")
        
        if not job_cards:
            # Method 5: Look for any div containing job titles
            job_cards = soup.find_all('div', string=lambda text: text and 'engineer' in text.lower())
            print(f"Method 5 (contains 'engineer'): Found {len(job_cards)} job cards")
        
        if not job_cards:
            print("❌ No job cards found with any method!")
            print("Available div classes on page:")
            divs = soup.find_all('div', class_=True)[:10]  # Show first 10 divs with classes
            for div in divs:
                print(f"  - {div.get('class')}")
            return []
        
        print(f"✅ Found {len(job_cards)} job cards on this page")
        
        jobs = []
        for i, card in enumerate(job_cards):
            job_data = extract_job_data(card)
            if job_data:
                jobs.append(job_data)
            else:
                print(f"Failed to extract data from job card {i+1}")
        
        return jobs
    
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return []
    except Exception as e:
        print(f"Parsing error: {e}")
        return []

def save_to_csv(jobs, filename):
    """Save jobs to CSV file"""
    if not jobs:
        print("No jobs to save")
        return
    
    filepath = os.path.join(config.OUTPUT_DIR, filename)
    
    # Check if file exists to decide whether to write headers
    file_exists = os.path.isfile(filepath)
    
    with open(filepath, 'a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['title', 'company', 'location', 'salary', 'summary', 'url'])
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerows(jobs)
    
    print(f"Saved {len(jobs)} jobs to {filepath}")

def scrape_indeed_jobs():
    """Main function to scrape jobs from Indeed"""
    print("Starting Indeed job scraper...")
    
    # Handle both single search term and multiple search terms
    search_terms = config.SEARCH_TERMS if hasattr(config, 'SEARCH_TERMS') else [config.SEARCH_TERM]
    locations = config.LOCATIONS if hasattr(config, 'LOCATIONS') else [config.LOCATION]
    
    print(f"Search terms: {search_terms}")
    print(f"Locations: {locations}")
    print(f"Max pages per search: {config.MAX_PAGES}")
    
    all_jobs = []
    
    for search_term in search_terms:
        for location in locations:
            print(f"\n--- Searching for '{search_term}' in '{location}' ---")
            
            for page in range(config.MAX_PAGES):
                start = page * 10  
                
                jobs = scrape_page(search_term, location, start)
                all_jobs.extend(jobs)
                
                print(f"Page {page + 1}: Found {len(jobs)} jobs")
                
                # Don't delay after the last request
                if page < config.MAX_PAGES - 1:
                    print(f"Waiting {config.REQUEST_DELAY} seconds...")
                    time.sleep(config.REQUEST_DELAY)
    
    # Save all jobs to CSV
    if all_jobs:
        save_to_csv(all_jobs, config.OUTPUT_FILE)
        print(f"\n✅ Scraping completed! Total jobs found: {len(all_jobs)}")
        print(f"Results saved to: {os.path.join(config.OUTPUT_DIR, config.OUTPUT_FILE)}")
    else:
        print("\n❌ No jobs were found. Check your search terms or try different locations.")

if __name__ == "__main__":
    scrape_indeed_jobs()
