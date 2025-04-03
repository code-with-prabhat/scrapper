import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import re
import base64
import json
import time
from datetime import datetime
import logging

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Set up logging
logging.basicConfig(
    filename=os.path.join('logs', f'image_scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Log script start
logging.info("Image Scraper Script Started")
logging.info(f"Current working directory: {os.getcwd()}")

def is_valid_image_url(url, extensions=None):
    """Check if the URL points to an image file."""
    # Default image extensions if none specified
    if extensions is None:
        extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
    
    # Convert extensions to lowercase and ensure they start with a dot
    extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' for ext in extensions]
    
    # Check for data URLs
    if url.startswith('data:image/'):
        # Check if the data URL image type matches our extensions
        img_type = re.search(r'data:image/(\w+);', url).group(1)
        return f'.{img_type}' in extensions
    
    # Check for image extensions in URL
    url_lower = url.lower()
    return any(url_lower.endswith(ext) for ext in extensions)

def extract_chapter_number(url):
    """Extract chapter number from URL."""
    try:
        # Try to find chapter number in URL
        chapter_match = re.search(r'chapter-(\d+)', url.lower())
        if chapter_match:
            return chapter_match.group(1)
        
        # If no chapter number found, use a timestamp
        return str(int(time.time()))
    except:
        return str(int(time.time()))

def create_run_folder(url):
    """Create a unique folder for this run."""
    # Get timestamp with different separators for date and time
    now = datetime.now()
    date_str = now.strftime("%d-%m-%Y")  # Day-Month-Year
    time_str = now.strftime("%H-%M-%S")  # Hour-Minute-Second
    timestamp = f"{date_str}_{time_str}"
    
    # Create folder name - only add chapter if found in URL
    chapter_match = re.search(r'chapter-(\d+)', url.lower())
    folder_name = f"run_{timestamp}" + (f"_chapter_{chapter_match.group(1)}" if chapter_match else "")
    
    # Create base directory for all downloads
    base_dir = "downloaded_images"
    # Create run-specific directory
    run_dir = os.path.join(base_dir, folder_name)
    os.makedirs(run_dir, exist_ok=True)
    
    logging.info(f"Created run folder: {run_dir}")
    return run_dir

def download_image(url, save_dir, extensions=None):
    """Download an image from URL and save it to the specified directory."""
    try:
        # Handle data URLs
        if url.startswith('data:image/'):
            # Extract the image data
            header, encoded = url.split(",", 1)
            data = base64.b64decode(encoded)
            
            # Get the image type from the header
            img_type = re.search(r'data:image/(\w+);', header).group(1)
            
            # Check if the image type is in the allowed extensions
            if extensions and f'.{img_type}' not in extensions:
                logging.info(f"Skipping data URL with unsupported extension: {img_type}")
                return False
            
            # Create filename
            filename = f"image_{int(time.time())}.{img_type}"
            filepath = os.path.join(save_dir, filename)
            
            # Save the image
            with open(filepath, 'wb') as f:
                f.write(data)
            
            logging.info(f"Downloaded: {filename} (from data URL)")
            return True
        
        # Create filename from URL
        filename = os.path.basename(urlparse(url).path)
        if not filename:
            filename = f"image_{int(time.time())}.jpg"
        
        # Clean the filename
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Check if the file has the correct extension
        if extensions:
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in extensions:
                logging.info(f"Skipping file with unsupported extension: {filename}")
                return False
        
        # Full path where image will be saved
        filepath = os.path.join(save_dir, filename)
        
        # Skip if file already exists
        if os.path.exists(filepath):
            logging.info(f"Skipping existing file: {filename}")
            return True
        
        # Download the image with custom headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': urlparse(url).netloc,
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
        
        # Check if content type is image
        content_type = response.headers.get('content-type', '').lower()
        if not any(img_type in content_type for img_type in ['image/', 'application/octet-stream']):
            logging.info(f"Skipping non-image content: {url}")
            return False
        
        # Save the image
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logging.info(f"Downloaded: {filename}")
        return True
    except requests.exceptions.Timeout:
        logging.error(f"Timeout downloading {url}")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading {url}: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error downloading {url}: {str(e)}")
        return False

def extract_images_from_json(html_content):
    """Extract image URLs from JSON data in the HTML."""
    try:
        # Look for JSON data containing image URLs
        json_pattern = r'var\s+chapter_preloaded_images\s*=\s*({.*?});'
        json_match = re.search(json_pattern, html_content, re.DOTALL)
        
        if json_match:
            json_data = json.loads(json_match.group(1))
            return list(json_data.values())
    except Exception as e:
        logging.error(f"Error extracting JSON data: {str(e)}")
    return []

def scrape_images(url, extensions=None):
    """Scrape all images from the given URL."""
    try:
        # Create unique folder for this run
        save_dir = create_run_folder(url)
        logging.info(f"Starting new scraping session for URL: {url}")
        logging.info(f"Save directory: {os.path.abspath(save_dir)}")
        
        # Send request to the website
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        logging.info(f"Fetching images from: {url}")
        if extensions:
            logging.info(f"Filtering for extensions: {', '.join(extensions)}")
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract images from JSON data first
        image_urls = extract_images_from_json(response.text)
        
        # Find all image tags
        img_tags = soup.find_all('img')
        
        # Also look for images in background-image CSS
        style_tags = soup.find_all('style')
        for style in style_tags:
            if style.string:
                # Find background-image URLs
                bg_images = re.findall(r'background-image:\s*url\([\'"]?(.*?)[\'"]?\)', style.string)
                for bg_url in bg_images:
                    img_tags.append({'src': bg_url})
        
        # Look for lazy-loaded images
        for img in img_tags:
            # Check for data-src attribute
            if img.get('data-src'):
                img['src'] = img['data-src']
            # Check for data-original attribute
            elif img.get('data-original'):
                img['src'] = img['data-original']
            # Check for data-lazy-src attribute
            elif img.get('data-lazy-src'):
                img['src'] = img['data-lazy-src']
        
        # Add image URLs from JSON to the list
        for img_url in image_urls:
            img_tags.append({'src': img_url})
        
        # Counter for successful downloads
        successful_downloads = 0
        skipped_urls = 0
        failed_urls = 0
        
        logging.info(f"Found {len(img_tags)} potential image sources")
        
        # Download each image
        for img in img_tags:
            # Get image URL
            img_url = img.get('src')
            if not img_url:
                logging.info("Skipping image with no source URL")
                skipped_urls += 1
                continue
            
            # Convert relative URL to absolute URL
            img_url = urljoin(url, img_url)
            
            # Skip if not a valid image URL
            if not is_valid_image_url(img_url, extensions):
                logging.info(f"Skipping invalid image URL: {img_url}")
                skipped_urls += 1
                continue
            
            # Download the image
            if download_image(img_url, save_dir, extensions):
                successful_downloads += 1
            else:
                failed_urls += 1
        
        logging.info("Scraping Summary:")
        logging.info(f"Total images found: {len(img_tags)}")
        logging.info(f"Successfully downloaded: {successful_downloads}")
        logging.info(f"Skipped: {skipped_urls}")
        logging.info(f"Failed: {failed_urls}")
        logging.info(f"Images saved in: {os.path.abspath(save_dir)}")
        
    except requests.exceptions.Timeout:
        logging.error("Request timed out. The website might be slow or unresponsive.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error accessing the website: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python image_scraper.py <website_url> [extension]")
        print("Example: python image_scraper.py https://example.com webp")
        sys.exit(1)
    
    url = sys.argv[1]
    extension = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Initialize extensions list
    extensions = None
    if extension:
        # Ensure extension starts with a dot
        extension = extension if extension.startswith('.') else f'.{extension}'
        extensions = [extension]
        logging.info(f"Will only download images with extension: {extension}")
    
    scrape_images(url, extensions) 