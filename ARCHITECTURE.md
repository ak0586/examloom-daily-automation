# Educational Video Automation Pipeline - Architecture v2.0

## System Overview (Single JSON Design)

This is a fully automated pipeline that generates and publishes educational quiz videos using a **single self-contained JSON file** where each question includes ALL metadata (caption, description, hashtags).

## Key Architectural Change

**Previous Design:** Separate JSON files for questions, captions, descriptions, hashtags  
**New Design:** One unified `questions.json` with complete metadata per question

### Benefits
- ✅ **Atomic Operations** - Each question is fully self-contained
- ✅ **Easier Management** - All content for a question in one place
- ✅ **Better Organization** - Caption/hashtag variations tied to specific questions
- ✅ **Simpler Logic** - No random selection from separate pools
- ✅ **Content Consistency** - Description always matches the question

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CRON SCHEDULER (2x daily)                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  MAIN ORCHESTRATOR                           │
│                  (main.py)                                   │
└──┬──────────┬──────────┬──────────┬──────────┬────────────┘
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
┌────────┐ ┌──────┐ ┌────────┐ ┌────────┐ ┌──────┐
│Question│ │Image │ │Video   │ │Upload  │ │Notify│
│Selector│ │Gen   │ │Creator │ │Manager │ │      │
└────────┘ └──────┘ └────────┘ └────────┘ └──────┘
```

## Module Breakdown

### 1. Question Selector (`modules/question_selector.py`)
**UPDATED:** Reads single JSON, returns complete question object
- Loads `questions.json`
- Maintains `used_questions.log`
- Returns full question with caption/description/hashtags
- No external file dependencies

### 2. Image Generator (`modules/image_generator.py`)
**UNCHANGED:** Still generates images from question data
- Uses Pillow (PIL)
- Creates pixel-perfect 1080×1400 canvas
- Renders question text + options
- Auto-wrapping with precise typography

### 3. Video Creator (`modules/video_creator.py`)
**UNCHANGED:** Still creates videos with FFmpeg
- Creates 1080×1920 vertical video
- Adds header/footer overlays
- Implements zoom-in effect
- Duration: 20 seconds

### 4. Upload Manager (`modules/upload_manager.py`)
**SIMPLIFIED:** Receives all content from question object
- Facebook Reels uploader
- YouTube Shorts uploader
- No content manager dependency
- Direct use of question metadata

### 5. Telegram Notifier (`modules/telegram_notifier.py`)
**UNCHANGED:** Still sends notifications
- Sends success/failure notifications
- Includes upload details
- Timestamp tracking

## Data Flow (Updated)

```
questions.json → Question Selector → Complete Question Object
                                           ↓
                                    [question, options, answer,
                                     explanation, caption,
                                     description, hashtags]
                                           ↓
                 ┌─────────────────────────┼─────────────────────┐
                 │                         │                     │
                 ▼                         ▼                     ▼
          Image Generator          Caption & Description    Hashtags
                 │                   (from object)        (from object)
                 ▼                         │                     │
          question.png                     │                     │
                 │                         │                     │
                 ▼                         │                     │
          Video Creator                    │                     │
                 │                         │                     │
                 ▼                         │                     │
          final_video.mp4                  │                     │
                 │                         │                     │
                 └─────────────────────────┴─────────────────────┘
                                           │
                                           ▼
                                    Upload Manager
                                           │
                                           ▼
                              [Facebook, YouTube]
                                           │
                                           ▼
                                 Telegram Notifier
```

## File Structure (Updated)

```
project/
├── main.py                      # Orchestrator
├── config.yaml                  # Configuration
├── requirements.txt             # Python dependencies
├── .env                         # API keys (not committed)
│
├── data/
│   ├── questions.json           # SINGLE SOURCE OF TRUTH
│   └── used_questions.log       # Tracking file
│
├── modules/
│   ├── __init__.py
│   ├── question_selector.py    # UPDATED: Returns full object
│   ├── image_generator.py      # UNCHANGED
│   ├── video_creator.py        # UNCHANGED
│   ├── upload_manager.py       # SIMPLIFIED: No content manager
│   └── telegram_notifier.py    # UNCHANGED
│
├── assets/
│   ├── fonts/
│   │   └── Roboto-Medium.ttf
│   └── temp/                    # Temporary files
│
└── logs/
    └── automation.log           # Execution logs
```

## JSON Data Structure

### Complete Question Object

```json
{
  "id": 1,
  "difficulty": "easy",
  "question": "A train travels at 60 km/h for 5 hours. What distance does it cover?",
  "options": ["250 km", "300 km", "350 km", "400 km"],
  "answer": "B",
  "explanation": "Distance = Speed × Time = 60 × 5 = 300 km.",
  "captions": [
    "Can you solve this in 10 seconds? 👇"
  ],
  "descriptions": [
    "✅ Correct Answer: B\n\nExplanation:\nDistance = Speed × Time = 300 km.\n\nFollow for daily exam practice 💯"
  ],
  "hashtags": [
    "#competitiveexams",
    "#quantitativeaptitude",
    "#exampractice",
    "#shorts",
    "#reels"
  ]
}
```

### Field Specifications

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `id` | integer | Yes | Unique identifier |
| `difficulty` | string | Yes | Question difficulty level |
| `question` | string | Yes | Question text |
| `options` | array[string] | Yes | 4 answer choices |
| `answer` | string | Yes | Correct option (A/B/C/D) |
| `explanation` | string | Yes | Solution explanation |
| `captions` | array[string] | Yes | Video titles (1+ entries) |
| `descriptions` | array[string] | Yes | Video descriptions (1+ entries) |
| `hashtags` | array[string] | Yes | Hashtags (5-20 entries) |

## Changes from v1.0

### ✅ Removed Components
- ❌ `content_manager.py` - No longer needed
- ❌ `captions.json` - Merged into questions.json
- ❌ `descriptions.json` - Merged into questions.json
- ❌ `hashtags.json` - Merged into questions.json

### ✅ Updated Components
- ✏️ `question_selector.py` - Returns complete object
- ✏️ `upload_manager.py` - Receives metadata from question
- ✏️ `main.py` - Simplified content flow

### ✅ Unchanged Components
- ✅ `image_generator.py` - Still generates images
- ✅ `video_creator.py` - Still creates videos
- ✅ `telegram_notifier.py` - Still sends notifications

## Advantages of Single JSON Design

### 1. Content Consistency
```python
# Old: Caption might not match question context
caption = random.choice(all_captions)  # Generic
description = format_template(question)  # Generic

# New: Caption is specific to this question
caption = question['captions'][0]  # Contextual
description = question['descriptions'][0]  # Specific
```

### 2. Better Organization
```
Old Structure:
questions.json:    {id: 1, question: "..."}
captions.json:     ["Generic caption 1", ...]
descriptions.json: ["Generic template 1", ...]
hashtags.json:     ["#tag1", "#tag2", ...]

New Structure:
questions.json: {
  id: 1,
  question: "...",
  captions: ["Specific to this question"],
  descriptions: ["Includes answer and explanation"],
  hashtags: ["Relevant to this topic"]
}
```

### 3. Atomic Operations
- Each question is a complete, publishable unit
- No dependency on external content files
- Easy to add/remove/update individual questions
- Backup and restore is simpler

### 4. Simplified Logic
```python
# Old: Multiple file reads
question = select_question()
caption = random.choice(load_captions())
template = random.choice(load_descriptions())
description = template.format(answer=question['answer'])
hashtags = random.sample(load_hashtags(), 10)

# New: Single object
question = select_question()
caption = question['captions'][0]
description = question['descriptions'][0]
hashtags = ' '.join(question['hashtags'])
```

## Technology Stack (Unchanged)

- **Language**: Python 3.9+
- **Image Processing**: Pillow (PIL)
- **Video Processing**: FFmpeg
- **HTTP Requests**: requests, httpx
- **Facebook API**: facebook-sdk
- **YouTube API**: google-api-python-client
- **Telegram**: python-telegram-bot
- **Scheduling**: cron
- **Configuration**: PyYAML, python-dotenv

## Security & Best Practices (Unchanged)

### API Keys
- Stored in `.env` file
- Never committed to version control
- Loaded via `python-dotenv`

### Error Handling
- Try-catch blocks at every step
- Detailed logging
- Graceful degradation
- Automatic retry logic

## Performance Metrics (Unchanged)

- Average execution time: 45-60 seconds
- Image generation: ~2 seconds
- Video creation: ~15-20 seconds
- Upload time: ~20-30 seconds (varies by network)
- Total pipeline: <90 seconds

## Migration from v1.0

### Step 1: Convert Data Format
```python
# migration_script.py
import json

# Load old files
with open('questions.json') as f:
    questions = json.load(f)
with open('captions.json') as f:
    captions = json.load(f)
with open('descriptions.json') as f:
    descriptions = json.load(f)
with open('hashtags.json') as f:
    hashtags = json.load(f)

# Create new format
new_questions = []
for q in questions:
    new_questions.append({
        **q,
        'captions': [captions[0]],  # Assign appropriate caption
        'descriptions': [descriptions[0].format(
            answer=q['answer'],
            explanation=q['explanation']
        )],
        'hashtags': hashtags[:10]  # Select relevant hashtags
    })

# Save
with open('questions_v2.json', 'w') as f:
    json.dump(new_questions, f, indent=2)
```

### Step 2: Update Code
- Replace `content_manager.py` usage
- Update `main.py` to use question object directly
- Remove external content file references

### Step 3: Test
- Verify question object structure
- Test image generation
- Test video creation
- Test uploads

## Scalability (Enhanced)

1. **Question Management**: Easier to scale - each entry is complete
2. **Content Variations**: Multiple captions/descriptions per question
3. **Batch Operations**: Process multiple questions independently
4. **Version Control**: Track question changes more easily
5. **Export/Import**: Single file makes deployment simpler
