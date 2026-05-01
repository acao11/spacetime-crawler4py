import re
from collections import Counter

# Standard English stop words
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "as", "at", 
    "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can", "could", 
    "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", "further", "had", "has", 
    "have", "having", "he", "her", "here", "hers", "herself", "him", "himself", "his", "how", "i", "if", 
    "in", "into", "is", "it", "its", "itself", "just", "me", "more", "most", "my", "myself", "no", "nor", 
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", 
    "over", "own", "same", "she", "should", "so", "some", "such", "than", "that", "the", "their", "theirs", 
    "them", "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too", 
    "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", 
    "whom", "why", "with", "would", "you", "your", "yours", "yourself", "yourselves"
}

def tokenize(text: str) -> list:
    """
    Tokenizes a string into a list of alphanumeric tokens.
    Filters out tokens that are shorter than 2 characters (optional but usually helpful).
    """
    # Use regex to find all alphanumeric sequences
    tokens = re.findall(r'[a-zA-Z0-9]+', text.lower())
    # Filter for ASCII and non-stop words
    return [t for t in tokens if len(t) > 1 and t not in STOP_WORDS]

def computeWordFrequencies(tokens: list) -> dict:
    return dict(Counter(tokens))
