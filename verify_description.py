
from modules.question_selector import QuestionSelector
import os
import yaml

def load_config():
    with open('config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    config = load_config()
    qs = QuestionSelector(config['data']['questions'], config['data']['used_log'])
    
    # Get a question (any question)
    question = qs.get_question_by_id(1)
    if not question:
        print("Question 1 not found.")
        return

    description = qs.get_description(question)
    with open('verification_result.txt', 'w', encoding='utf-8') as f:
        f.write("Generated Description:\n")
        f.write("-" * 40 + "\n")
        f.write(description + "\n")
        f.write("-" * 40 + "\n")
        
        sol_pos = description.find("Solution:")
        ans_pos = description.find("Correct Answer:")
        
        if sol_pos != -1 and ans_pos != -1 and ans_pos > sol_pos:
            f.write("\n✅ Verification PASSED: Answer is AFTER Solution.\n")
        else:
            f.write("\n❌ Verification FAILED: Order is incorrect.\n")

if __name__ == "__main__":
    main()
