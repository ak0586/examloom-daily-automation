import base64
import os

def encode_file(file_path):
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None
    
    with open(file_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return encoded

def main():
    print("="*60)
    print("GitHub Secrets Generator")
    print("="*60)
    print("Copy the output below and paste it into GitHub Repository Secrets.\n")

    # 1. Client Secrets
    print("🔹 Secret Name: CLIENT_SECRETS_BASE64")
    secret = encode_file("client_secrets.json")
    if secret:
        print(secret)
    print("\n" + "-"*60 + "\n")

    # 2. YouTube Credentials (Token)
    print("🔹 Secret Name: YOUTUBE_CREDENTIALS_BASE64")
    secret = encode_file("youtube_credentials.json")
    if secret:
        print(secret)
    else:
        print("⚠️ youtube_credentials.json not found. Run main.py locally first to login!")
    
    print("\n" + "="*60)
    print("\nAlso add these normal secrets:")
    print("- FACEBOOK_PAGE_ID")
    print("- FACEBOOK_ACCESS_TOKEN")
    print("- TELEGRAM_BOT_TOKEN")
    print("- TELEGRAM_CHAT_ID")

if __name__ == "__main__":
    main()
