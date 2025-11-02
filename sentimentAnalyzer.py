import json
from datetime import datetime
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline

def load_parsed_articles(filename='parsed_articles.json'):
    """
    Load parsed articles from JSON file
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: {filename} not found")
        return None
    except Exception as e:
        print(f"Error loading articles: {e}")
        return None


def analyze_with_textblob(text):
    """
    Analyze sentiment using TextBlob
    Returns polarity (-1 to 1) and subjectivity (0 to 1)
    """
    blob = TextBlob(text)
    return {
        'polarity': blob.sentiment.polarity,
        'subjectivity': blob.sentiment.subjectivity,
        'classification': 'positive' if blob.sentiment.polarity > 0 else 'negative' if blob.sentiment.polarity < 0 else 'neutral'
    }


def analyze_with_vader(text, analyzer):
    """
    Analyze sentiment using VADER
    Returns compound score (-1 to 1) and breakdown
    """
    scores = analyzer.polarity_scores(text)
    return {
        'compound': scores['compound'],
        'positive': scores['pos'],
        'neutral': scores['neu'],
        'negative': scores['neg'],
        'classification': 'positive' if scores['compound'] >= 0.05 else 'negative' if scores['compound'] <= -0.05 else 'neutral'
    }


def analyze_with_transformer(text, sentiment_pipeline):
    """
    Analyze sentiment using Hugging Face Transformers
    Returns label and confidence score
    """
    # Use truncation parameter to handle long texts
    result = sentiment_pipeline(text, truncation=True, max_length=512)[0]
    return {
        'label': result['label'],
        'score': result['score'],
        'classification': result['label'].lower()
    }


def analyze_context_sentiments(context_text):
    """
    Run all three sentiment analyzers on a single context
    """
    print(f"  Analyzing context (length: {len(context_text.split())} words)...")
    
    # Initialize analyzers
    vader_analyzer = SentimentIntensityAnalyzer()
    transformer_pipeline = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    
    # Run all three analyses
    textblob_result = analyze_with_textblob(context_text)
    vader_result = analyze_with_vader(context_text, vader_analyzer)
    transformer_result = analyze_with_transformer(context_text, transformer_pipeline)
    
    return {
        'textblob': textblob_result,
        'vader': vader_result,
        'transformer': transformer_result
    }


def process_articles(data):
    """
    Process all articles and add sentiment analysis
    """
    articles = data.get('articles', [])
    total = len(articles)
    
    print(f"\nAnalyzing sentiment for {total} articles...\n")
    
    for i, article in enumerate(articles, 1):
        print(f"[{i}/{total}] Processing: {article.get('title', 'Untitled')}")
        
        contexts = article.get('contexts', [])
        print(f"  Found {len(contexts)} context(s)")
        
        # Analyze each context
        for j, context in enumerate(contexts, 1):
            print(f"  Context {j}/{len(contexts)}:")
            context_text = context.get('context', '')
            
            if context_text:
                sentiment_results = analyze_context_sentiments(context_text)
                context['sentiment_analysis'] = sentiment_results
            else:
                print("    Warning: Empty context")
        
        print()
    
    return data


def save_sentiment_results(data, filename='sentiment_analysis.json'):
    """
    Save articles with sentiment analysis to JSON file
    """
    output_data = {
        'analyzed_at': datetime.now().isoformat(),
        'models_used': ['TextBlob', 'VADER', 'Transformers (DistilBERT)'],
        'original_metadata': {
            'parsed_at': data.get('parsed_at'),
            'keywords_searched': data.get('keywords_searched'),
            'words_before': data.get('words_before'),
            'words_after': data.get('words_after')
        },
        'total_articles': data.get('total_articles_with_keywords'),
        'articles': data.get('articles', [])
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"✓ Saved sentiment analysis to {filename}")
        return True
    except Exception as e:
        print(f"Error saving results: {e}")
        return False


def print_summary(data):
    """
    Print summary of sentiment analysis
    """
    articles = data.get('articles', [])
    total_contexts = sum(len(article.get('contexts', [])) for article in articles)
    
    # Aggregate sentiment classifications
    textblob_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    vader_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    transformer_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    
    for article in articles:
        for context in article.get('contexts', []):
            sentiment = context.get('sentiment_analysis', {})
            
            if 'textblob' in sentiment:
                textblob_counts[sentiment['textblob']['classification']] += 1
            if 'vader' in sentiment:
                vader_counts[sentiment['vader']['classification']] += 1
            if 'transformer' in sentiment:
                transformer_counts[sentiment['transformer']['classification']] += 1
    
    print("\n" + "="*60)
    print("SENTIMENT ANALYSIS SUMMARY")
    print("="*60)
    print(f"Total contexts analyzed: {total_contexts}")
    print(f"\nTextBlob Results:")
    print(f"  Positive: {textblob_counts['positive']}")
    print(f"  Neutral: {textblob_counts['neutral']}")
    print(f"  Negative: {textblob_counts['negative']}")
    print(f"\nVADER Results:")
    print(f"  Positive: {vader_counts['positive']}")
    print(f"  Neutral: {vader_counts['neutral']}")
    print(f"  Negative: {vader_counts['negative']}")
    print(f"\nTransformer Results:")
    print(f"  Positive: {transformer_counts['positive']}")
    print(f"  Neutral: {transformer_counts['neutral']}")
    print(f"  Negative: {transformer_counts['negative']}")
    print("="*60)


def main():
    """
    Main function to run sentiment analysis
    """
    print("Loading parsed articles...")
    data = load_parsed_articles('parsed_articles.json')
    
    if not data:
        print("Failed to load articles")
        return
    
    # Process all articles with sentiment analysis
    processed_data = process_articles(data)
    
    # Save results
    save_sentiment_results(processed_data)
    
    # Print summary
    print_summary(processed_data)


if __name__ == "__main__":
    main()