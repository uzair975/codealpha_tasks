"""
FAQ Chatbot Logic Module
Handles FAQ dataset loading, dual TF-IDF vectorization, and accurate cosine similarity matching.
"""

import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from preprocessing import preprocess

# Default similarity threshold to reject unrelated questions
DEFAULT_SIMILARITY_THRESHOLD = 0.25
FALLBACK_RESPONSE = "Sorry, I couldn't find a relevant answer to that question."


def load_faqs(csv_path: str) -> pd.DataFrame:
    """
    Loads and validates the FAQ dataset from a CSV file.
    Expects 'Question' and 'Answer' columns (case-insensitive).
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"FAQ dataset file not found at: {csv_path}")
        
    df = pd.read_csv(csv_path)
    
    if df.empty:
        raise ValueError("The FAQ dataset is empty.")
    
    # Normalize column names to find question and answer columns
    col_map = {col.strip().lower(): col for col in df.columns}
    
    if "question" not in col_map or "answer" not in col_map:
        raise ValueError(
            f"CSV file must contain 'Question' and 'Answer' columns. "
            f"Found columns: {list(df.columns)}"
        )
        
    q_col = col_map["question"]
    a_col = col_map["answer"]
    
    # Clean dataset by dropping null entries in Question/Answer
    faq_df = df[[q_col, a_col]].dropna().copy()
    faq_df.columns = ["Question", "Answer"]
    
    # Retain Category column if present
    if "category" in col_map:
        faq_df["Category"] = df[col_map["category"]].fillna("")
    else:
        faq_df["Category"] = ""
    
    if faq_df.empty:
        raise ValueError("No valid Question-Answer pairs found in the dataset.")
        
    return faq_df.reset_index(drop=True)


def initialize_chatbot(csv_path: str):
    """
    Initializes the chatbot once by loading data, preprocessing questions and answers,
    and fitting dual TF-IDF vectorizers.
    Returns: ((q_vectorizer, a_vectorizer), (q_matrix, a_matrix, q_corpus), faq_df)
    """
    faq_df = load_faqs(csv_path)
    
    # Preprocess questions and answers separately
    q_corpus = [preprocess(str(q)) for q in faq_df["Question"]]
    a_corpus = [preprocess(str(a)) for a in faq_df["Answer"]]
    
    # Fit TF-IDF Vectorizers with unigrams and bigrams
    q_vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
    q_matrix = q_vectorizer.fit_transform(q_corpus)
    
    a_vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
    a_matrix = a_vectorizer.fit_transform(a_corpus)
    
    vectorizers = (q_vectorizer, a_vectorizer)
    matrices = (q_matrix, a_matrix, q_corpus)
    
    return vectorizers, matrices, faq_df


def get_faq_response(
    user_query: str,
    vectorizers,
    matrices,
    faq_df: pd.DataFrame,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD
) -> tuple[str, float]:
    """
    Finds the best matching FAQ answer for a user query using dual cosine similarity.
    Returns: (response_text, similarity_score)
    """
    if not user_query or not user_query.strip():
        return "Please enter a valid question.", 0.0
        
    # Preprocess user query
    processed_query = preprocess(user_query)
    if not processed_query:
        return FALLBACK_RESPONSE, 0.0
        
    q_vec, a_vec = vectorizers
    q_mat, a_mat, q_corpus = matrices
    
    query_tokens = set(processed_query.split())
    
    # Compute similarity against FAQ questions and answers
    sim_q = cosine_similarity(q_vec.transform([processed_query]), q_mat).flatten()
    sim_a = cosine_similarity(a_vec.transform([processed_query]), a_mat).flatten()
    
    # Weighted combined similarity: 75% Question match + 25% Answer match
    combined_scores = 0.75 * sim_q + 0.25 * sim_a
    
    # Boost for direct question keyword overlap
    for i, doc in enumerate(q_corpus):
        doc_tokens = set(doc.split())
        overlap = len(query_tokens.intersection(doc_tokens))
        if overlap > 0:
            combined_scores[i] += 0.04 * overlap
    
    best_match_idx = int(combined_scores.argmax())
    best_score = float(combined_scores[best_match_idx])
    
    # Check against similarity threshold
    if best_score >= threshold:
        matched_answer = faq_df.iloc[best_match_idx]["Answer"]
        return matched_answer, best_score
    else:
        return FALLBACK_RESPONSE, best_score


# Alias for backward compatibility
get_response = get_faq_response


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "data", "faqs.csv")
    if not os.path.exists(data_path):
        data_path = os.path.join(base_dir, "GIKI_FAQ_Dataset.csv")
        
    print(f"Loading FAQ dataset from: {data_path}...")
    try:
        vecs, mats, faqs = initialize_chatbot(data_path)
        print(f"Chatbot initialized successfully with {len(faqs)} FAQs.\n")
        print("Type 'exit' or 'quit' to stop.\n" + "-" * 50)
        
        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
                
            answer, score = get_response(user_input, vecs, mats, faqs)
            print(f"Bot: {answer}")
            
    except Exception as e:
        print(f"Error initializing chatbot: {e}")
