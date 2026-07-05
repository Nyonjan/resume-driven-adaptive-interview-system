from modules.resume_parsing.text_preprocessor import preprocess_for_structure, preprocess_for_nlp

def test_preprocessing():
    test_cases = [
        {
            "input": "John Doe-Smith / Senior Dev @ Google. Visit: cool-site.com. Phone: +1-234-567-89! #MachineLearning",
            "expected_structure": "John Doe-Smith / Senior Dev @ Google. Visit: cool-site.com. Phone: 1-234-567-89 MachineLearning",
            "expected_nlp": "john doesmith senior dev google visit coolsitecom phone 123456789 machinelearning"
        },
        {
            "input": "Multiple   spaces \n and newlines!!!",
            "expected_structure": "Multiple spaces and newlines",
            "expected_nlp": "multiple spaces and newlines"
        }
    ]

    for i, case in enumerate(test_cases):
        struct = preprocess_for_structure(case["input"])
        nlp = preprocess_for_nlp(case["input"])
        
        print(f"Test Case {i+1}:")
        print(f"  Input: {case['input']}")
        print(f"  Structure: '{struct}'")
        print(f"  NLP:       '{nlp}'")
    
    print("\nVerification complete.")

if __name__ == "__main__":
    test_preprocessing()
