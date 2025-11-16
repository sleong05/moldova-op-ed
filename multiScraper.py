import json
from datetime import datetime
from scraper import scrape_article

def read_urls_from_file(filename='urls.txt'):
    """
    Read URLs from a text file (one URL per line)
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        return urls
    except FileNotFoundError:
        print(f"Error: {filename} not found")
        return []
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return []


def batch_scrape(urls):
    """
    Scrape multiple URLs and return successful and failed results
    """
    successful_articles = []
    failed_urls = []
    
    total = len(urls)
    print(f"Starting to scrape {total} URLs...\n")
    
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{total}] Scraping: {url}")
        
        article_data = scrape_article(url)
        
        if article_data:
            successful_articles.append(article_data)
            print(f"  ✓ Success: {article_data.get('title', 'No title')}\n")
        else:
            failed_urls.append({
                'url': url,
                'failed_at': datetime.now().isoformat()
            })
            print(f"  ✗ Failed\n")
    
    return successful_articles, failed_urls


def save_results(successful_articles, failed_urls):
    """
    Save successful articles and failed URLs to separate JSON files
    """
    # Save successful articles
    success_data = {
        'total_articles': len(successful_articles),
        'scraped_at': datetime.now().isoformat(),
        'articles': successful_articles
    }
    
    try:
        with open('jsons/scraped_articles.json', 'w', encoding='utf-8') as f:
            json.dump(success_data, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved {len(successful_articles)} articles to scraped_articles.json")
    except Exception as e:
        print(f"Error saving successful articles: {e}")
    
    # Save failed URLs
    failed_data = {
        'total_failed': len(failed_urls),
        'scraped_at': datetime.now().isoformat(),
        'failed_urls': failed_urls
    }
    
    try:
        with open('jsons/failed_urls.json', 'w', encoding='utf-8') as f:
            json.dump(failed_data, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved {len(failed_urls)} failed URLs to failed_urls.json")
    except Exception as e:
        print(f"Error saving failed URLs: {e}")


def main():
    """
    Main function to orchestrate the batch scraping
    """
    # Read URLs from file
    urls = read_urls_from_file('urls.txt')
    if not urls:
        print("No URLs found to scrape")
        return
    
    # Scrape all URLs
    successful_articles, failed_urls = batch_scrape(urls)
    
    # Save results
    print("\n" + "="*60)
    print("SCRAPING COMPLETE")
    print("="*60)
    save_results(successful_articles, failed_urls)
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total URLs processed: {len(urls)}")
    print(f"Successful: {len(successful_articles)}")
    print(f"Failed: {len(failed_urls)}")
    print("="*60)


if __name__ == "__main__":
    main()