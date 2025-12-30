# 🎬 Educational Video Automation Pipeline v2.0

## Single JSON Design - Self-Contained Questions

Fully automated system for creating and publishing educational quiz videos using a **single, self-contained JSON file** where each question includes all metadata (caption, description, hashtags).

---

## 🆕 What's New in v2.0

### Single Source of Truth
- **One JSON file** (`questions.json`) contains everything
- Each question is **self-contained** with its own caption, description, and hashtags
- No separate files for captions, descriptions, or hashtags
- Simpler, cleaner, more maintainable

### Improved Content Management
- **Contextual captions** - Specific to each question
- **Relevant descriptions** - Include answer and explanation
- **Targeted hashtags** - Match question topic and difficulty
- **Multiple variations** - Support multiple captions/descriptions per question

### Simplified Architecture
- ❌ Removed `content_manager.py` module (no longer needed)
- ❌ Removed separate content JSON files
- ✅ Cleaner data flow
- ✅ Easier question management
- ✅ Better version control

---

## 📦 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [JSON Data Format](#json-data-format)
- [Usage](#usage)
- [Configuration](#configuration)
- [Automation](#automation)
- [Migration from v1.0](#migration-from-v10)
- [FAQ](#faq)

---

## ✨ Features

- **100% Automated** - Select, generate, upload without manual intervention
- **Self-Contained Data** - Each question is a complete unit
- **Pixel-Perfect Images** - Runtime generation with professional typography
- **FFmpeg Videos** - 20-second vertical videos with overlays
- **Multi-Platform** - Facebook Reels + YouTube Shorts
- **Smart Tracking** - Never repeats questions
- **Contextual Content** - Captions and hashtags match question topic
- **Telegram Alerts** - Real-time notifications
- **Modular & Clean** - Well-documented, extensible code

---

## 🚀 Installation

### Prerequisites

- **OS**: Linux (Ubuntu 20.04+)
- **Python**: 3.9 or higher
- **FFmpeg**: Latest version
- **API Credentials**: Facebook, YouTube, Telegram

### Quick Start

```bash
# 1. Clone/download project
cd educational-video-automation-v2

# 2. Run setup
chmod +x setup.sh
./setup.sh

# 3. Configure credentials
nano .env
# Add your API keys

# 4. Test run
source venv/bin/activate
python3 main.py

# 5. Schedule automation
crontab -e
# Add: 0 9,21 * * * cd /path && venv/bin/python3 main.py
```

---

## 📄 JSON Data Format

### Complete Question Object

Each question in `questions.json` **must** include ALL these fields:

```json
{
  "id": 1,
  "difficulty": "easy",
  "question": "A train travels at 60 km/h for 5 hours. What distance does it cover?",
  "options": ["250 km", "300 km", "350 km", "400 km"],
  "answer": "B",
  "explanation": "Distance = Speed × Time = 60 × 5 = 300 km.",
  "captions": [
    "Can you solve this in 10 seconds? 👇",
    "Quick speed-distance problem! 🚂"
  ],
  "descriptions": [
    "✅ Correct Answer: B\n\nExplanation:\nDistance = Speed × Time = 60 × 5 = 300 km.\n\nFollow for daily exam practice 💯"
  ],
  "hashtags": [
    "#competitiveexams",
    "#quantitativeaptitude",
    "#exampractice",
    "#shorts",
    "#reels",
    "#speed",
    "#distance",
    "#mathematics"
  ]
}
```

### Field Specifications

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | ✅ Yes | Unique identifier (1, 2, 3, ...) |
| `difficulty` | string | ✅ Yes | `"easy"`, `"medium"`, or `"hard"` |
| `question` | string | ✅ Yes | Question text (< 200 chars recommended) |
| `options` | array | ✅ Yes | Exactly 4 answer choices |
| `answer` | string | ✅ Yes | Correct option: `"A"`, `"B"`, `"C"`, or `"D"` |
| `explanation` | string | ✅ Yes | Solution explanation |
| `captions` | array | ✅ Yes | 1+ video captions (short, engaging) |
| `descriptions` | array | ✅ Yes | 1+ video descriptions (with answer) |
| `hashtags` | array | ✅ Yes | 5-20 hashtags (relevant to topic) |

### ⚠️ Important Rules

1. **All fields are required** - Missing fields will cause errors
2. **Arrays must not be empty** - At least 1 caption, 1 description, 5 hashtags
3. **Options must have exactly 4 items** - For A, B, C, D choices
4. **Answer must be A/B/C/D** - Not 0/1/2/3 or full text
5. **IDs must be unique** - No duplicate IDs allowed

### 📝 Best Practices

#### Good Captions
```json
"captions": [
  "Can you solve this in 10 seconds? 👇",  // Creates urgency
  "Quick math challenge! 🧠",               // Engaging
  "Pause and try this! ⏸️"                 // Call to action
]
```

#### Good Descriptions
```json
"descriptions": [
  "✅ Correct Answer: B\n\n📝 Explanation:\n[detailed solution]\n\nFollow for more! 💯"
]
```

**Include:**
- ✅ Answer clearly stated
- 📝 Step-by-step explanation
- 🎯 Call to action
- ✨ Emoji for engagement

#### Good Hashtags
```json
"hashtags": [
  "#competitiveexams",     // General
  "#quantitative",         // Category
  "#speedproblems",        // Specific
  "#shorts",               // Platform
  "#reels",                // Platform
  "#ssc",                  // Exam type
  "#banking",              // Exam type
  "#mathematics"           // Subject
]
```

**Mix:**
- 🎯 General exam hashtags
- 📚 Subject/topic tags
- 🎓 Specific exam names
- 📱 Platform tags (#shorts, #reels)

---

## 🎯 Usage

### Manual Run

```bash
# Activate environment
source venv/bin/activate

# Run pipeline
python3 main.py
```

### What Happens

1. **Selects** first unused question from JSON
2. **Validates** all required fields present
3. **Extracts** caption and description from question
4. **Generates** 1080×1400 image with question
5. **Creates** 20-second vertical video (1080×1920)
6. **Uploads** to Facebook Reels and YouTube Shorts
7. **Notifies** via Telegram
8. **Marks** question as used

### Check Logs

```bash
# Real-time monitoring
tail -f logs/automation.log

# View recent execution
tail -50 logs/automation.log

# Check for errors
grep "ERROR" logs/automation.log
```

### View Statistics

```python
from modules.question_selector import QuestionSelector

selector = QuestionSelector('data/questions.json', 'data/used_questions.log')
stats = selector.get_stats()

print(f"Total: {stats['total']}")
print(f"Used: {stats['used']}")
print(f"Remaining: {stats['remaining']}")
print(f"By difficulty: {stats['remaining_by_difficulty']}")
```

---

## ⚙️ Configuration

### config.yaml

```yaml
# Data files
data:
  questions: "data/questions.json"  # Single source of truth
  used_log: "data/used_questions.log"

# Video settings
video:
  resolution:
    width: 1080
    height: 1920
  duration: 20
  fps: 30

# Image settings
image:
  resolution:
    width: 1080
    height: 1400
  background_color: "#FFFFFF"
  padding: 80

# Upload settings
upload:
  facebook:
    enabled: true
  youtube:
    enabled: true
```

### .env

```bash
# Facebook
FACEBOOK_PAGE_ID=your_page_id
FACEBOOK_ACCESS_TOKEN=your_token

# YouTube
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_secret

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## 🤖 Automation

### Cron Setup

```bash
# Edit crontab
crontab -e

# Add line (runs at 9 AM and 9 PM)
0 9,21 * * * cd /home/user/project && /home/user/project/venv/bin/python3 main.py >> /home/user/project/logs/cron.log 2>&1
```

### Systemd Timer (Alternative)

```ini
# /etc/systemd/system/video-pipeline.timer
[Unit]
Description=Run video pipeline twice daily

[Timer]
OnCalendar=*-*-* 09,21:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable video-pipeline.timer
sudo systemctl start video-pipeline.timer
```

---

## 🔄 Migration from v1.0

If you're upgrading from the multi-file JSON design:

### Step 1: Backup Current Data

```bash
cp data/questions.json data/questions_v1_backup.json
cp data/captions.json data/captions_backup.json
cp data/descriptions.json data/descriptions_backup.json
cp data/hashtags.json data/hashtags_backup.json
```

### Step 2: Run Migration Script

```python
# migrate_to_v2.py
import json

# Load old files
with open('data/questions.json') as f:
    questions = json.load(f)
with open('data/captions.json') as f:
    captions = json.load(f)
with open('data/descriptions.json') as f:
    descriptions = json.load(f)
with open('data/hashtags.json') as f:
    hashtags = json.load(f)

# Create new format
new_questions = []
for q in questions:
    new_q = {
        'id': q['id'],
        'difficulty': 'medium',  # Add if missing
        'question': q['question'],
        'options': q['options'],
        'answer': q['answer'],
        'explanation': q['explanation'],
        'captions': [captions[0]],  # Assign relevant caption
        'descriptions': [
            descriptions[0].format(
                answer=q['answer'],
                explanation=q['explanation']
            )
        ],
        'hashtags': hashtags[:10]  # Select relevant hashtags
    }
    new_questions.append(new_q)

# Save new format
with open('data/questions_v2.json', 'w') as f:
    json.dump(new_questions, f, indent=2)

print(f"Migrated {len(new_questions)} questions to v2.0 format")
```

### Step 3: Update Code

```bash
# Replace old modules
rm modules/content_manager.py
cp modules_v2/* modules/

# Update main script
cp main_v2.py main.py

# Update questions file
mv data/questions_v2.json data/questions.json
```

### Step 4: Test

```bash
python3 main.py
```

---

## 📊 Adding New Questions

### Template

```json
{
  "id": 11,
  "difficulty": "medium",
  "question": "Your question here?",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "answer": "B",
  "explanation": "Step-by-step explanation here.",
  "captions": [
    "Engaging caption with emoji! 🎯"
  ],
  "descriptions": [
    "✅ Correct Answer: B\n\nExplanation:\n[Your explanation]\n\nFollow for more! 💯"
  ],
  "hashtags": [
    "#relevant",
    "#hashtags",
    "#for",
    "#this",
    "#question",
    "#shorts",
    "#reels"
  ]
}
```

### Validation

```bash
# Validate JSON syntax
python3 -m json.tool data/questions.json > /dev/null

# Validate question format
python3 -c "
from modules.question_selector import QuestionSelector
qs = QuestionSelector('data/questions.json', 'data/used_questions.log')
print('All questions valid!')
"
```

---

## ❓ FAQ

### Q: Can I have multiple captions per question?
**A:** Yes! Add multiple captions to the array. The system uses the first one by default.

```json
"captions": [
  "Primary caption used by default",
  "Alternative caption 1",
  "Alternative caption 2"
]
```

### Q: How do I use different captions for different uploads?
**A:** Modify `main.py` to select random or sequential caption:

```python
import random
caption = random.choice(question['captions'])
```

### Q: Can hashtags vary by question?
**A:** Yes! That's the main advantage of v2.0. Each question has its own relevant hashtags.

### Q: What if I want generic hashtags for all videos?
**A:** Include common hashtags in every question:

```json
"hashtags": [
  "#competitiveexams",  // Common to all
  "#quantitative",      // Common to all
  "#speedproblems",     // Specific to this question
  "#shorts",            // Required for all
  "#reels"              // Required for all
]
```

### Q: How do I reset and start over?
**A:** Delete the used questions log:

```bash
rm data/used_questions.log
```

All questions become available again.

### Q: Can I export unused questions?
**A:** Yes:

```python
from modules.question_selector import QuestionSelector

selector = QuestionSelector('data/questions.json', 'data/used_questions.log')
selector.export_unused_questions('unused_questions.json')
```

---

## 🐛 Troubleshooting

### "Missing required field" Error
**Solution:** Check your JSON has all required fields. Run validation:

```python
from modules.question_selector import QuestionSelector
QuestionSelector('data/questions.json', 'data/used_questions.log')
```

### "options must be array of 4 items"
**Solution:** Ensure exactly 4 options (A, B, C, D):

```json
"options": ["Option A", "Option B", "Option C", "Option D"]
```

### "answer must be A, B, C, or D"
**Solution:** Use uppercase letters only:

```json
"answer": "B"  // ✅ Correct
"answer": "b"  // ❌ Wrong
"answer": "2"  // ❌ Wrong
```

### "captions must be non-empty array"
**Solution:** Include at least one caption:

```json
"captions": ["At least one caption required"]
```

---

## 📈 Best Practices

### Question Design
- ✅ Keep questions under 150 characters
- ✅ Use clear, unambiguous wording
- ✅ Make options distinctly different
- ✅ Provide step-by-step explanations

### Caption Strategy
- ✅ Create urgency ("in 10 seconds")
- ✅ Ask questions ("Can you solve?")
- ✅ Use emojis sparingly (2-3 max)
- ✅ Keep under 60 characters

### Description Optimization
- ✅ Start with answer
- ✅ Show solution steps
- ✅ Add call-to-action
- ✅ Use formatting (\n\n for spacing)

### Hashtag Selection
- ✅ Mix general and specific tags
- ✅ Include platform tags (#shorts, #reels)
- ✅ Use 8-15 hashtags per video
- ✅ Research trending exam tags

---

## 🎉 Success Metrics

Track your video performance:

- **Engagement rate**: (Likes + Comments + Shares) / Views × 100
- **Watch time**: Average % of video watched
- **Growth**: Follower increase per week
- **Best performers**: Track which difficulty/topics perform best

---

## 📞 Support

**Documentation:**
- ARCHITECTURE_v2.md - System design
- TECHNICAL_GUIDE.md - Deep dive
- EXAMPLES.md - Customization ideas

**Logs:**
- Application: `logs/automation.log`
- Cron: `logs/cron.log`

---

## 🚀 Next Steps

1. ✅ Add 50-100 questions to `questions.json`
2. ✅ Customize captions and descriptions
3. ✅ Test with `python3 main.py`
4. ✅ Schedule automation with cron
5. ✅ Monitor logs and engagement
6. ✅ Iterate based on performance

---

**Built with ❤️ for educators**

*v2.0 - Simpler, cleaner, better!*
