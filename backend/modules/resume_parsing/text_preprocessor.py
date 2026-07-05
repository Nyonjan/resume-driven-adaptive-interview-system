import re

def preprocess_for_structure(text: str) -> str:
    """
    Minimal cleaning to preserve structural elements like letters, numbers, and common symbols.
    """
    if not text:
        return ""
    
    # Preserve specified characters and normalize whitespace
    cleaned_text = re.sub(r'[^a-zA-Z0-9\s\-\/\.\@]', '', text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text

def preprocess_for_nlp(text: str) -> str:
    """
    Aggressive cleaning (lowercase, removal of special characters) for NLP processing.
    """
    if not text:
        return ""
    
    text = text.lower()
    cleaned_text = re.sub(r'[^a-z0-9\s]', '', text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text

if __name__ == "__main__":
    sample_text = "John Doe-Smith / Senior Dev @ Google. Visit: cool-site.com. Phone: +1-234-567-89! #MachineLearning"
    print("Structure:", preprocess_for_structure(sample_text))
    print("NLP:", preprocess_for_nlp(sample_text))
