"""
Unit / Integration Test Suite for FAQ Chatbot
Tests preprocessing, dataset loading, vectorization, and threshold logic.
"""

import os
import pandas as pd
from preprocessing import clean_text, tokenize_text, remove_stopwords, preprocess
from chatbot import load_faqs, initialize_chatbot, get_response, FALLBACK_RESPONSE, DEFAULT_SIMILARITY_THRESHOLD


def test_preprocessing():
    print("Testing Preprocessing...")
    assert clean_text(None) == ""
    assert clean_text("") == ""
    assert clean_text("  HELLO   World!  ") == "hello world"
    assert clean_text("What is GIKI's location???") == "what is giki s location"
    
    tokens = tokenize_text("Undergraduate Admissions in 2026!")
    assert isinstance(tokens, list)
    assert len(tokens) > 0
    
    # Preprocess pipeline with stemming
    processed = preprocess("How do I apply for undergraduate admissions?")
    assert "appli" in processed or "apply" in processed
    assert "undergradu" in processed or "undergraduate" in processed
    assert "admiss" in processed or "admissions" in processed
    print("[PASS] Preprocessing tests passed.")


def test_matching_logic():
    print("\nTesting Chatbot Matching Logic...")
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "faqs.csv")
    vectorizers, matrices, df = initialize_chatbot(data_path)
    
    # 1. User's query: requirement to apply for undergraduate scholarship
    q_scholarship = "what is the requirement to apply for the undergraduate scholarship"
    ans_s, score_s = get_response(q_scholarship, vectorizers, matrices, df)
    assert score_s >= DEFAULT_SIMILARITY_THRESHOLD
    # Verify accurate match (scholarship / financial aid, NOT attendance or MS admission)
    assert "scholarship" in ans_s.lower() or "financial" in ans_s.lower() or "cmeef" in ans_s.lower()
    assert "80%" not in ans_s and "16 years of education" not in ans_s
    print(f"[PASS] Scholarship query accurately matched (score: {score_s:.3f}) -> {ans_s[:70]}...")

    # 2. Exact match query
    q1 = "How do I apply for GIKI undergraduate admissions?"
    ans1, score1 = get_response(q1, vectorizers, matrices, df)
    assert score1 >= DEFAULT_SIMILARITY_THRESHOLD
    assert "Admissions Portal" in ans1
    print(f"[PASS] Exact query matched (score: {score1:.3f})")

    # 3. Location query
    q3 = "What is the location of GIKI?"
    ans3, score3 = get_response(q3, vectorizers, matrices, df)
    assert score3 >= DEFAULT_SIMILARITY_THRESHOLD
    assert "Tarbela" in ans3
    print(f"[PASS] Location query matched (score: {score3:.3f})")

    # 4. Completely unrelated query (should reject)
    q4 = "What is the recipe for baking chocolate cake with strawberries?"
    ans4, score4 = get_response(q4, vectorizers, matrices, df)
    assert ans4 == FALLBACK_RESPONSE
    print(f"[PASS] Unrelated query rejected (score: {score4:.3f}) -> Fallback message returned.")

    # 5. Empty query handling
    ans5, score5 = get_response("", vectorizers, matrices, df)
    assert ans5 == "Please enter a valid question."
    print("[PASS] Empty query handled correctly.")


if __name__ == "__main__":
    test_preprocessing()
    test_matching_logic()
    print("\nAll automated tests completed successfully!")
