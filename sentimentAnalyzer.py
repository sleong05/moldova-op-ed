import json
from datetime import datetime
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch
from scipy.special import softmax
import numpy as np

def load_parsed_articles(filename='jsons/parsed_articles.json'):
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


def analyze_with_finbert(text, model, tokenizer):
    """
    Analyze sentiment using FinBERT (financial news model)
    Returns standardized score (-1 to 1) based on 3-class probabilities
    """
    # Tokenize and get model outputs
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
    
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Get probabilities for each class
    scores = outputs.logits[0].detach().numpy()
    probs = softmax(scores)
    
    # FinBERT labels: 0=positive, 1=negative, 2=neutral
    pos_prob = float(probs[0])
    neg_prob = float(probs[1])
    neu_prob = float(probs[2])
    
    # Calculate sentiment score: positive - negative
    sentiment_score = pos_prob - neg_prob
    
    # Determine classification
    max_idx = np.argmax(probs)
    if max_idx == 0:
        classification = 'positive'
    elif max_idx == 1:
        classification = 'negative'
    else:
        classification = 'neutral'
    
    return {
        'score': float(sentiment_score),  # Standardized score from -1 to 1
        'positive_prob': pos_prob,
        'negative_prob': neg_prob,
        'neutral_prob': neu_prob,
        'classification': classification
    }


def analyze_context_sentiments(context_text, model, tokenizer):
    """
    Run FinBERT sentiment analysis on a single context
    """
    print(f"  Analyzing context (length: {len(context_text.split())} words)...")
    
    result = analyze_with_finbert(context_text, model, tokenizer)
    
    return result


def process_articles(data):
    """
    Process all articles and add sentiment analysis
    """
    print("\nInitializing FinBERT model...")
    print("Loading FinBERT (financial news model)...")
    
    # Initialize FinBERT
    model_name = "ProsusAI/finbert"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    
    print("✓ FinBERT loaded successfully\n")
    
    articles = data.get('articles', [])
    total = len(articles)
    
    print(f"Analyzing sentiment for {total} articles...\n")
    
    for i, article in enumerate(articles, 1):
        print(f"[{i}/{total}] Processing: {article.get('title', 'Untitled')}")
        
        contexts = article.get('contexts', [])
        print(f"  Found {len(contexts)} context(s)")
        
        # Analyze each context
        for j, context in enumerate(contexts, 1):
            print(f"  Context {j}/{len(contexts)}:")
            context_text = context.get('context', '')
            
            if context_text:
                sentiment_result = analyze_context_sentiments(context_text, model, tokenizer)
                context['sentiment_analysis'] = sentiment_result
            else:
                print("    Warning: Empty context")
        
        print()
    
    return data


def save_sentiment_results(data, filename='jsons/sentiment_analysis.json'):
    """
    Save articles with sentiment analysis to JSON file
    """
    output_data = {
        'analyzed_at': datetime.now().isoformat(),
        'model_used': 'FinBERT (ProsusAI/finbert)',
        'score_range': 'Scores range from -1 (most negative) to 1 (most positive)',
        'methodology': {
            'description': 'FinBERT is a BERT-based model fine-tuned on financial news from Reuters, Bloomberg, and SEC filings',
            'output': '3-class classification (positive, negative, neutral) with probability distribution',
            'score_calculation': 'score = positive_probability - negative_probability',
            'interpretation': 'Continuous score from -1 to +1, with neutral_probability indicating factual/objective content'
        },
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
    classification_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    
    # Aggregate scores for averages
    scores = []
    pos_probs = []
    neg_probs = []
    neu_probs = []
    
    for article in articles:
        for context in article.get('contexts', []):
            sentiment = context.get('sentiment_analysis', {})
            
            if sentiment:
                classification_counts[sentiment['classification']] += 1
                scores.append(sentiment['score'])
                pos_probs.append(sentiment['positive_prob'])
                neg_probs.append(sentiment['negative_prob'])
                neu_probs.append(sentiment['neutral_prob'])
    
    print("\n" + "="*70)
    print("FINBERT SENTIMENT ANALYSIS SUMMARY")
    print("="*70)
    print(f"Total contexts analyzed: {total_contexts}")
    
    print(f"\nClassification Distribution:")
    print(f"  Positive: {classification_counts['positive']} ({classification_counts['positive']/total_contexts*100:.1f}%)")
    print(f"  Neutral:  {classification_counts['neutral']} ({classification_counts['neutral']/total_contexts*100:.1f}%)")
    print(f"  Negative: {classification_counts['negative']} ({classification_counts['negative']/total_contexts*100:.1f}%)")
    
    if scores:
        print(f"\nSentiment Scores:")
        print(f"  Average score: {sum(scores)/len(scores):.3f}")
        print(f"  Score range: [{min(scores):.3f}, {max(scores):.3f}]")
        print(f"  Standard deviation: {np.std(scores):.3f}")
        
        print(f"\nAverage Probabilities:")
        print(f"  Positive: {sum(pos_probs)/len(pos_probs):.3f}")
        print(f"  Negative: {sum(neg_probs)/len(neg_probs):.3f}")
        print(f"  Neutral:  {sum(neu_probs)/len(neu_probs):.3f}")
    
    print("="*70)


def main():
    """
    Main function to run sentiment analysis
    """
    print("="*70)
    print("SENTIMENT ANALYSIS WITH FINBERT")
    print("="*70)
    
    print("\nLoading parsed articles...")
    data = load_parsed_articles('jsons/parsed_articles.json')
    
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