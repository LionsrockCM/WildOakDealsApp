
import os
import time
import requests

def ask_grok(prompt):
    api_key = os.getenv('XAI_API_KEY')
    if not api_key:
        raise ValueError("XAI_API_KEY not found in environment variables")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'grok-2-latest',
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 150
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(
                'https://api.x.ai/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=10
            )
            break
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed, retrying...")
            time.sleep(1)
    
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code} - {response.text}"

def main():
    try:
        response = ask_grok("Write a simple Python function to calculate fibonacci numbers")
        print("Grok's response:", response)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
