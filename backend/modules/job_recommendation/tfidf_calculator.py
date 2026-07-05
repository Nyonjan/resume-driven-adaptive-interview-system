import math
from modules.job_recommendation.tfidf_preprocessor import prepare_tfidf_input

def compute_tf(user_id):
    """
    Step 6 of Job Recommendation Module:
    Computes the Term Frequency (TF) vector for each document in the corpus.
    Formula: TF(w, d) = (count of word w in document d) / (total words in document d)
    
    Returns:
        dict: {
            "tf_vectors": [[0.5, 0.2, ...], [doc2_vector], ...],
            "vocabulary": ["sorted", "unique", "words", ...],
            "job_metadata": [...]
        }
        dict: Error if preprocessing fails.
    """
    # STEP 6.1 — Get Tokenized Docs + Vocabulary
    tfidf_input = prepare_tfidf_input(user_id)
    
    # Handle Errors from prepare_tfidf_input
    if isinstance(tfidf_input, dict) and "error" in tfidf_input:
        return tfidf_input
    
    tokenized_docs = tfidf_input.get("tokenized_docs", [])
    vocabulary = tfidf_input.get("vocabulary", [])
    job_metadata = tfidf_input.get("job_metadata", [])

    # STEP 6.2 — Compute TF For Each Document
    tf_vectors = []
    
    for doc in tokenized_docs:
        total_words = len(doc)
        
        # Initialize TF vector with 0s matching vocabulary length
        tf_vector = []
        
        if total_words == 0:
            # Handle empty document case
            tf_vector = [0.0] * len(vocabulary)
        else:
            # Optimization: Pre-count word frequencies in this document
            word_counts = {}
            for word in doc:
                word_counts[word] = word_counts.get(word, 0) + 1
            
            # For each word in vocabulary, compute its TF
            for word in vocabulary:
                count = word_counts.get(word, 0)
                tf_val = count / total_words
                tf_vector.append(tf_val) 

        tf_vectors.append(tf_vector)

    return {
        "tf_vectors": tf_vectors,
        "vocabulary": vocabulary,
        "job_metadata": job_metadata
    }

def compute_idf(user_id):
    """
    Step 7 of Job Recommendation Module:
    Computes the Inverse Document Frequency (IDF) for each word in the vocabulary.
    Formula: IDF(w) = log(N / DF)
    where N is total documents and DF is the number of documents containing word w.
    
    Returns:
        dict: {
            "idf_vector": [idf1, idf2, ...],
            "vocabulary": [...],
            "job_metadata": [...]
        }
        dict: Error if preprocessing fails.
    """
    # STEP 7.1 — Get Tokenized Docs + Vocabulary
    tfidf_input = prepare_tfidf_input(user_id)
    
    # Handle Errors from prepare_tfidf_input
    if isinstance(tfidf_input, dict) and "error" in tfidf_input:
        return tfidf_input
    
    tokenized_docs = tfidf_input.get("tokenized_docs", [])
    vocabulary = tfidf_input.get("vocabulary", [])
    job_metadata = tfidf_input.get("job_metadata", [])

    N = len(tokenized_docs)
    idf_vector = []

    # Pre-calculate presence sets for each document for faster DF calculation
    doc_sets = [set(doc) for doc in tokenized_docs]

    # STEP 7.2 — Calculate Document Frequency (DF) and STEP 7.3 — Compute IDF
    for word in vocabulary:
        df = 0
        for doc_set in doc_sets:
            if word in doc_set:
                df += 1
        
        # Compute IDF using natural log
        if df == 0:
            idf = 0.0
        else:
            idf = math.log(N / df)
            
        idf_vector.append(idf)

    return {
        "idf_vector": idf_vector,
        "vocabulary": vocabulary,
        "job_metadata": job_metadata
    }

def compute_tfidf(user_id):
    """
    Step 8 of Job Recommendation Module:
    Computes the final TF-IDF vectors by multiplying TF and IDF.
    Formula: TF-IDF(w, d) = TF(w, d) * IDF(w)
    
    Returns:
        dict: {
            "tfidf_vectors": [[val1, val2, ...], ...],
            "vocabulary": [...],
            "job_metadata": [...]
        }
    """
    # 8.1 Fetch TF
    tf_result = compute_tf(user_id)
    if isinstance(tf_result, dict) and "error" in tf_result:
        return tf_result
        
    tf_vectors = tf_result["tf_vectors"]
    vocabulary = tf_result["vocabulary"]
    job_metadata = tf_result["job_metadata"]
    
    # 8.2 Fetch IDF
    idf_result = compute_idf(user_id)
    if isinstance(idf_result, dict) and "error" in idf_result:
        # This shouldn't happen if tf_result succeeded, but for safety:
        return idf_result
        
    idf_vector = idf_result["idf_vector"]
    
    # 8.3 Multiply TF x IDF
    tfidf_vectors = []
    for tf_vec in tf_vectors:
        tfidf_vec = []
        for i in range(len(tf_vec)):
            val = tf_vec[i] * idf_vector[i]
            tfidf_vec.append(val)
        tfidf_vectors.append(tfidf_vec)
        
    return {
        "tfidf_vectors": tfidf_vectors,
        "vocabulary": vocabulary,
        "job_metadata": job_metadata
    }
