import os

# Job Search Parameters
SEARCH_TERM = ["Software Engineer", "Data Scientist", "Web Developer", "Internship","Cashier","Sales consultent", "Customer Service Representative", "Project Manager", "Marketing Specialist","Tech Intern","Co-op Student"]
LOCATIONS = ["OTTAWA"]
MAX_PAGES = 2

# Indeed Specific Parameters
INDEED_URL = "https://ca.indeed.com"
INDEED_SEARCH_URL = "https://ca.indeed.com/jobs"

# Request settings
REQUEST_DELAY = 2 # seconds between requests to avoid being blocked
TIMEOUT = 10 

# Headers to avoid being blocked
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-CA,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# Output settings
OUTPUT_DIR = "data"
OUTPUT_FILE = "job.csv"

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
