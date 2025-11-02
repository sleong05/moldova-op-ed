import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def scrape_article(url):
    """
    Scrape article content from a given URL
    """
    try:
        # Send GET request to the URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find the article title
        title = None
        if soup.find('h1'):
            title = soup.find('h1').get_text(strip=True)
        
        # Common article content selectors (try multiple)
        article_content = []
        
        # Try to find article tag
        article = soup.find('article')
        if article:
            paragraphs = article.find_all('p')
        else:
            # Fallback to all paragraphs
            paragraphs = soup.find_all('p')
        
        # Extract text from paragraphs
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 20:  # Filter out short/empty paragraphs
                article_content.append(text)
        
        return {
            'title': title,
            'content': article_content,
            'url': url,
            'scraped_at': datetime.now().isoformat(),
            'paragraph_count': len(article_content)
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None
    except Exception as e:
        print(f"Error parsing the content: {e}")
        return None


def save_to_json(data, filename='article.json'):
    """
    Save article data to a JSON file
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Article saved to {filename}")
        return True
    except Exception as e:
        print(f"Error saving to JSON: {e}")
        return False


# Example usage
if __name__ == "__main__":
    # Replace with your target URL
    url = "https://www.bbc.com/news/world-europe-26627236"
    
    print(f"Scraping article from: {url}")
    article_data = scrape_article(url)
    
    if article_data:
        print(f"Successfully scraped: {article_data['title']}")
        print(f"Paragraphs found: {article_data['paragraph_count']}")
        
        # Save to JSON file
        save_to_json(article_data)
    else:
        print("Failed to scrape article")