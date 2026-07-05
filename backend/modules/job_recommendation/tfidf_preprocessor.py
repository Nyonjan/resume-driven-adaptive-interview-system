from modules.job_recommendation.corpus_builder import build_corpus

def prepare_tfidf_input(user_id):
    """
    Step 5 of Job Recommendation Module:
    1. Builds the corpus (Candidate + Eligible Jobs).
    2. Tokenizes documents by lowercasing and splitting by whitespace.
    3. Construct a unique, alphabetically sorted vocabulary.
    
    Returns:
        dict: {
            "tokenized_docs": [["word1", "word2"], ...],
            "vocabulary": ["sorted", "unique", "words", ...],
            "job_metadata": [{"job_id": 1, "title": "..."}, ...]
        }
        dict: Error if corpus build fails or no documents are found.
    """
    # STEP 5.1 — Build Corpus
    corpus_result = build_corpus(user_id)
    
    # Handle Errors from build_corpus (e.g., Resume not found, empty candidate doc)
    if isinstance(corpus_result, dict) and "error" in corpus_result:
        return corpus_result
    
    documents = corpus_result.get("documents", [])
    job_metadata = corpus_result.get("job_metadata", [])

    # Special Case: Minimal corpus check (Needs at least one document, usually handled by corpus_builder validation)
    if not documents:
        return {"error": "Corpus is empty. Ensure candidate has skills and eligible jobs exist."}

    # STEP 5.2 — Tokenize Documents
    tokenized_docs = []
    unique_words = set()
    
    for doc in documents:
        # Safety lowercase and split by whitespace
        # Multi-word skills like 'machine_learning' are already underscored
        tokens = doc.lower().split()
        tokenized_docs.append(tokens)
        
        # Collect for vocabulary
        unique_words.update(tokens)

    # STEP 5.3 — Build Vocabulary
    # Unique words sorted alphabetically for deterministic vector ordering
    vocab = sorted(list(unique_words))

    # STEP 5.4 — Return Format
    return {
        "tokenized_docs": tokenized_docs,
        "vocabulary": vocab,
        "job_metadata": job_metadata
    }
