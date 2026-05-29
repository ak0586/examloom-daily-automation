# 🎬 Educational Video Automation Pipeline

A fully automated system for creating and publishing shorts/reels. It generates video content from a JSON data source, creates pixel-perfect visuals, edits them into videos with FFmpeg, and uploads them to YouTube and Facebook.

## ✨ Features
- **Zero-Touch Automation**: Runs purely on code (GitHub Actions or Local Cron).
- **Single Source of Truth**: All data (captions, hashtags, questions) lives in `questions.json`.
- **Cross-Platform**: Supports Windows and Linux.
- **Smart Tracking**: Never repeats questions; tracks history in `used_questions.log`.

---

## 📦 Table of Contents

- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running Locally](#-running-locally)
- [GitHub Actions Automation](#-github-actions-automation)
- [Data Format](#-data-format)
- [Troubleshooting](#-troubleshooting)

---

## 🛠 Prerequisites

- **Python**: 3.10 or higher
- **FFmpeg**: Must be installed and added to your system PATH.
  - *Windows*: `winget install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org/).
  - *Linux*: `sudo apt install ffmpeg`
- **API Credentials**:
  - Google/YouTube Data API (OAuth 2.0 Client ID)
  - Facebook Graph API (Page Access Token)
  - Telegram Bot API (Token & Chat ID)

---

## 🚀 Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/educational-video-automation.git
cd educational-video-automation
```

### 2. Set up Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## ⚙ Configuration

### 1. Environment Variables (`.env`)
Create a `.env` file in the root directory:

```ini
# Facebook
FACEBOOK_PAGE_ID=your_page_id
FACEBOOK_ACCESS_TOKEN=your_token

# YouTube (Client ID/Secret needed for local auth flow)
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_secret

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 2. Audio Configuration (Optional)
To add background music to your videos:
1.  Place an MP3 file in the `assets/music/` directory.
2.  The system will automatically detect the first `.mp3` file found and loop it as background music.
    - Effect: The audio loops infinitely to match the video duration.
    - **Attribution**: The system automatically appends the required Creative Commons license to the video description.
    - Note: If no file is found, the video will be created without background music.

### 3. YouTube Authentication (Local Run)
The first time you run the script locally, it will open a browser to authenticate with YouTube. This generates `client_secrets.json` (input) and `youtube_credentials.json` (output session).

---

## 🏃 Running Locally

To run the pipeline manually:

```bash
# Ensure venv is active
python main.py
```

### Workflow
1.  **Selects Question**: Picks the first unused question from `data/questions.json`.
2.  **Generates Assets**: Creates images (`assets/temp/`) and video.
3.  **Uploads**: Pushes to YouTube Shorts and Facebook Reels.
4.  **Notifies**: Sends a Telegram message with status.
5.  **Updates Log**: Marks question as used in `data/used_questions.log`.

---

## 🤖 GitHub Actions Automation

This project includes a workflow (`.github/workflows/daily_video.yml`) to run the pipeline automatically twice a day (Manual trigger also available).

### Setup Secrets for GitHub

Since GitHub Actions cannot open a browser for YouTube login, you must encode your local credential files and save them as Secrets.

1.  **Run the Secret Generator**:
    ```bash
    # Run this locally after you have successfully authenticated once
    python generate_secrets.py
    ```
2.  **Copy the Output**: The script will print Base64 strings for your files.
3.  **Add to GitHub Repository Secrets** (Settings > Secrets and variables > Actions):
    - `CLIENT_SECRETS_BASE64`: (Content from generate_secrets.py)
    - `YOUTUBE_CREDENTIALS_BASE64`: (Content from generate_secrets.py)
    - `FACEBOOK_PAGE_ID`
    - `FACEBOOK_ACCESS_TOKEN`
    - `TELEGRAM_BOT_TOKEN`
    - `TELEGRAM_CHAT_ID`
  
4.  # Generate Facebook Access Token for Automation

Follow these steps to generate a **Facebook Page Access Token** for the automation system.

## 1. Open Graph API Explorer

* Go to: https://developers.facebook.com/tools/explorer/
* Log in with the Facebook account that manages the page.

## 2. Select the Meta App

* In the **Meta App** dropdown, select **Business Store**.

## 3. Choose Token Type

* In **User or Page**, select **User Token**.

## 4. Generate Access Token

* Click **Generate Access Token**.

## 5. Select Required Permissions

Enable the following permissions:

```
business_management
pages_show_list
pages_manage_metadata
pages_manage_posts
pages_manage_engagement
pages_read_engagement
pages_read_user_content
instagram_basic
instagram_content_publish
```

Then confirm the permissions.

## 6. Get Page Access Token

* In the API endpoint field, run:

```
GET /me/accounts
```

* Click **Submit**.

The response will include the **Page Access Token** for each page.

Example response:

```json
{
  "data": [
    {
      "name": "Page Name",
      "id": "PAGE_ID",
      "access_token": "PAGE_ACCESS_TOKEN"
    }
  ]
}
```

## 7. Copy the Page Access Token

Copy the **access_token** corresponding to the page used for automation.

## 8. Update Environment Variables

Paste the token into your `.env` file:

```
FACEBOOK_ACCESS_TOKEN=PAGE_ACCESS_TOKEN
FACEBOOK_PAGE_ID=YOUR_PAGE_ID
```

## 9. Verify Instagram Connection (Optional but Recommended)

Run:

```
GET /{PAGE_ID}?fields=instagram_business_account
```

Expected response:

```json
{
  "instagram_business_account": {
    "id": "INSTAGRAM_BUSINESS_ID"
  }
}
```

If this field is present, Instagram cross-posting will work correctly.

## 10. Security Note

* Never commit access tokens to the repository.
* Store tokens only in **environment variables** or **secret managers**.


---

## 📄 Data Format (`questions.json`)

The system relies on `data/questions.json`. Each entry is self-contained.

```json
[
  {
    "id": 1001,
    "difficulty": "Easy",
    "question": "What is the capital of France?",
    "options": ["Berlin", "Madrid", "Paris", "Rome"],
    "answer": "C",
    "explanation": "Paris is the capital and most populous city of France.",
    "captions": ["Generic Caption 1 🇫🇷", "Test Your Knowledge! 👇"],
    "descriptions": ["Answer: C\n\nExplanation: Paris is the capital..."],
    "hashtags": ["#geography", "#quiz", "#shorts"]
  }
]
```

---

## 🐛 Troubleshooting

### Common Errors

**1. `ffmpeg not found` or `ImageMagick` errors**
- Ensure FFmpeg is installed and accessible in your system PATH.
- Run `ffmpeg -version` to verify.

**2. YouTube Upload Fails (400/401)**
- Your `youtube_credentials.json` might be expired.
- Delete `youtube_credentials.json`, run `python main.py` locally to re-authenticate, then update your GitHub Secrets.

**3. "Invalid video description"**
- Ensure your `descriptions` field in JSON doesn't contain forbidden characters (like `<` or `>`).

---

## 🔄 Migration History (v1.0 to v2.0)

*Legacy Note: If you are upgrading from the older multi-file version.*

Version 2.0 replaces the scattered `captions.json`, `hashtags.json`, etc., with a single `questions.json`.
- **Old Structure**: Separate files for every metadata type.
- **New Structure**: Everything lives inside the Question object.

To migrate, use the included scripts or manually merge your data into the new JSON format shown above.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Developer

Developed by **Ankit** (or your name/organization).
- **GitHub**: [Ankit Kumar](https://github.com/ak0586)
- **LinkedIn**: [ankit59](https://www.linkedin.com/in/ankit59/)

## 📬 Contact

For support, questions, or collaboration:
- **Email**: ankitkumar81919895@gmail.com
- **Issues**: [GitHub Issues](https://github.com/ak0586/educational-video-automation/issues)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
