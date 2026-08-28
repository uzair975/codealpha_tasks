"""
NLP Preprocessing Module for FAQ Chatbot
Handles text cleaning, tokenization, stemming with NLTK PorterStemmer, and stopword removal.
"""

import re
import string
import nltk
from nltk.stem import PorterStemmer

# Ensure required NLTK resources are available without unnecessary network requests
def _ensure_nltk_data():
    for resource, path in [
        ('tokenizers/punkt', 'punkt'),
        ('tokenizers/punkt_tab', 'punkt_tab'),
        ('corpora/stopwords', 'stopwords')
    ]:
        try:
            nltk.data.find(resource)
        except LookupError:
            try:
                nltk.download(path, quiet=True)
            except Exception:
                pass

_ensure_nltk_data()

try:
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    STOPWORDS = set(stopwords.words('english'))
except Exception:
    STOPWORDS = set()
    word_tokenize = None

stemmer = PorterStemmer()


def clean_text(text: str) -> str:
    """
    Cleans raw text by converting to lowercase, removing punctuation/special
    characters, and normalizing whitespace. Safely handles None or empty input.
    """
    if text is None or not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation and special characters
    text = re.sub(rf"[{re.escape(string.punctuation)}]", " ", text)
    
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    return text


def tokenize_text(text: str) -> list[str]:
    """
    Tokenizes text into individual words using NLTK word_tokenize with regex fallback.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return []
    
    if word_tokenize:
        try:
            return word_tokenize(cleaned)
        except Exception:
            pass
            
    # Fallback if NLTK tokenizer encounters an issue
    return cleaned.split()


def remove_stopwords(tokens: list[str]) -> list[str]:
    """
    Removes standard English stopwords from a list of tokens.
    """
    if not tokens:
        return []
    return [token for token in tokens if token not in STOPWORDS]


def preprocess(text: str, remove_stop: bool = True) -> str:
    """
    Full preprocessing pipeline:
    1. Cleans text (lowercase, punctuation removal, whitespace normalization).
    2. Tokenizes text.
    3. Filters English stopwords.
    4. Applies Porter Stemmer to handle word variations (singular/plural, verb forms).
    5. Returns space-separated string suitable for TF-IDF vectorization.
    """
    tokens = tokenize_text(text)
    if not tokens:
        return ""
    
    if remove_stop and STOPWORDS:
        filtered = remove_stopwords(tokens)
        if filtered:
            tokens = filtered

    stemmed_tokens = [stemmer.stem(token) for token in tokens]
    if not stemmed_tokens:
        return clean_text(text)
        
    return " ".join(stemmed_tokens)
