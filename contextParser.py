import json
import re
from datetime import datetime

# Configuration constants
WORDS_BEFORE = 40
WORDS_AFTER = 40
KEYWORDS = [
    'transnistria',
    'Trans-Dniester',
]

def load_articles(filename='scraped_articles.json'):
    """
    Load scraped articles from JSON file
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('articles', [])
    except FileNotFoundError:
        print(f"Error: {filename} not found")
        return []
    except Exception as e:
        print(f"Error loading articles: {e}")
        return []


def extract_keyword_context(text, keyword, words_before, words_after):
    """
    Extract context around a keyword (words before and after)
    Returns list of context snippets with position info
    """
    contexts = []
    
    # Split text into words (including hyphens as part of words)
    words = re.findall(r'\b[\w-]+\b', text)
    
    # Find all occurrences of the keyword (case insensitive)
    for i, word in enumerate(words):
        if keyword.lower() == word.lower():
            contexts.append({
                'keyword': keyword,
                'position': i
            })
    
    return contexts


def merge_overlapping_contexts(contexts):
    """
    Merge overlapping context windows to avoid duplicate text
    """
    if not contexts:
        return []
    
    # Sort by position
    sorted_contexts = sorted(contexts, key=lambda x: x['position'])
    
    merged = []
    current = sorted_contexts[0].copy()
    current['keywords_found'] = [current['keyword']]
    current['start'] = current['position'] - WORDS_BEFORE
    current['end'] = current['position'] + WORDS_AFTER
    
    for next_ctx in sorted_contexts[1:]:
        next_start = next_ctx['position'] - WORDS_BEFORE
        next_end = next_ctx['position'] + WORDS_AFTER
        
        # Check if contexts overlap
        if next_start <= current['end']:
            # Merge - extend the current context
            current['end'] = max(current['end'], next_end)
            current['keywords_found'].append(next_ctx['keyword'])
        else:
            # No overlap - save current and start new
            merged.append(current)
            current = next_ctx.copy()
            current['keywords_found'] = [current['keyword']]
            current['start'] = next_start
            current['end'] = next_end
    
    # Add the last context
    merged.append(current)
    
    return merged


def parse_article_for_keywords(article, keywords, words_before, words_after):
    """
    Parse a single article for all keywords
    """
    # Combine all content into one text block
    full_text = ' '.join(article.get('content', []))
    
    all_contexts = []
    keyword_counts = {}
    
    for keyword in keywords:
        contexts = extract_keyword_context(full_text, keyword, words_before, words_after)
        all_contexts.extend(contexts)
        keyword_counts[keyword] = len(contexts)
    
    # Merge overlapping contexts
    merged_contexts = merge_overlapping_contexts(all_contexts)
    
    # Reconstruct the actual text for merged contexts (including hyphens)
    words = re.findall(r'\b[\w-]+\b', full_text)
    final_contexts = []
    for ctx in merged_contexts:
        start_idx = max(0, ctx['start'])
        end_idx = min(len(words), ctx['end'] + 1)
        context_text = ' '.join(words[start_idx:end_idx])
        final_contexts.append({'context': context_text})
    
    return {
        'title': article.get('title'),
        'url': article.get('url'),
        'scraped_at': article.get('scraped_at'),
        'keyword_counts': keyword_counts,
        'total_mentions': sum(keyword_counts.values()),
        'contexts': final_contexts
    }


def parse_all_articles(articles, keywords, words_before, words_after):
    """
    Parse all articles for keywords
    """
    parsed_articles = []
    
    total = len(articles)
    print(f"Parsing {total} articles for keywords: {', '.join(keywords)}\n")
    
    for i, article in enumerate(articles, 1):
        title = article.get('title', 'Untitled')
        print(f"[{i}/{total}] Parsing: {title}")
        
        parsed = parse_article_for_keywords(article, keywords, words_before, words_after)
        
        if parsed['total_mentions'] > 0:
            parsed_articles.append(parsed)
            print(f"  ✓ Found {parsed['total_mentions']} keyword mentions\n")
        else:
            print(f"  - No keywords found\n")
    
    return parsed_articles


def save_parsed_articles(parsed_articles, filename='parsed_articles.json'):
    """
    Save parsed articles to JSON file
    """
    output_data = {
        'parsed_at': datetime.now().isoformat(),
        'keywords_searched': KEYWORDS,
        'words_before': WORDS_BEFORE,
        'words_after': WORDS_AFTER,
        'total_articles_with_keywords': len(parsed_articles),
        'articles': parsed_articles
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved parsed articles to {filename}")
        return True
    except Exception as e:
        print(f"Error saving parsed articles: {e}")
        return False


def print_summary(parsed_articles):
    """
    Print summary statistics
    """
    print("\n" + "="*60)
    print("PARSING SUMMARY")
    print("="*60)
    print(f"Keywords searched: {', '.join(KEYWORDS)}")
    print(f"Context window: {WORDS_BEFORE} words before, {WORDS_AFTER} words after")
    print(f"Articles with keyword mentions: {len(parsed_articles)}")
    
    # Count total mentions per keyword
    keyword_totals = {kw: 0 for kw in KEYWORDS}
    for article in parsed_articles:
        for kw, count in article['keyword_counts'].items():
            keyword_totals[kw] += count
    
    print("\nKeyword mention totals:")
    for kw, count in keyword_totals.items():
        print(f"  - {kw}: {count}")
    
    print("="*60)


def main():
    """
    Main function to parse articles for keywords
    """
    # Load articles
    articles = load_articles('scraped_articles.json')
    
    if not articles:
        print("No articles found to parse")
        return
    
    # Parse articles for keywords
    parsed_articles = parse_all_articles(articles, KEYWORDS, WORDS_BEFORE, WORDS_AFTER)
    
    # Save results
    save_parsed_articles(parsed_articles)
    
    # Print summary
    print_summary(parsed_articles)


if __name__ == "__main__":
    main()