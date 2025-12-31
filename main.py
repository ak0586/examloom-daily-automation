#!/usr/bin/env python3
"""
Educational Video Automation Pipeline v2.0 (Single JSON Design)
Main orchestrator that runs the complete workflow.
"""

import os
import sys
import logging
from pathlib import Path
import yaml
from datetime import datetime
from dotenv import load_dotenv

# Import modules
from modules.question_selector import QuestionSelector
from modules.image_generator import ImageGenerator
from modules.video_creator import VideoCreator
from modules.upload_manager import UploadManager
from modules.telegram_notifier import TelegramNotifier


def setup_logging(config):
    """Configure logging."""
    log_config = config['logging']
    log_dir = Path(log_config['file']).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_config['level']),
        format=log_config['format'],
        handlers=[
            logging.FileHandler(log_config['file'], encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Force stdout to use UTF-8 to handle emojis validation on Windows consoles
    if sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            # Python < 3.7 doesn't support reconfigure, but we are on 3.13 so this is fine
            pass

    return logging.getLogger(__name__)


def load_config():
    """Load configuration from YAML file."""
    with open('config.yaml', 'r',encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Replace environment variables in config
    config = _replace_env_vars(config)
    
    return config


def _replace_env_vars(obj):
    """Recursively replace ${VAR} with environment variables."""
    if isinstance(obj, dict):
        return {k: _replace_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_replace_env_vars(item) for item in obj]
    elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
        var_name = obj[2:-1]
        return os.getenv(var_name, obj)
    return obj


def cleanup_temp_files(temp_dir):
    """Clean up temporary files."""
    temp_path = Path(temp_dir)
    if temp_path.exists():
        for file in temp_path.glob('*'):
            try:
                file.unlink()
            except Exception as e:
                logging.warning(f"Could not delete {file}: {e}")


def prune_logs(log_file, max_sessions):
    """
    Keep only the last N sessions in the log file.
    A session is defined by the start marker "Educational Video Automation Pipeline".
    """
    if not os.path.exists(log_file):
        return

    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Split by the session start marker
        marker = "Educational Video Automation Pipeline"
        # The split will create empty string at start if file starts with marker
        # We look for the marker to count sessions
        
        # Find all start occurrences
        starts = [i for i in range(len(content)) if content.startswith(marker, i)]
        
        # If we have more sessions than allowed (minus 1 for the current new one)
        # We want to keep (max_sessions - 1) previous sessions so the new one makes it max_sessions
        keep_count = max(0, max_sessions - 1)
        
        if len(starts) > keep_count:
            # The cut point is the start index of the session we want to keep
            # If we want to keep last 9, we need the 9th from last start index
            cut_index = starts[-keep_count] if keep_count > 0 else len(content)
            
            # If we are pruning, write back only the kept content
            if cut_index > 0:
                new_content = content[cut_index:]
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Pruned logs: Kept last {keep_count} sessions")

    except Exception as e:
        print(f"Failed to prune logs: {e}")


def main():
    """Main execution function."""
    # Load environment variables
    load_dotenv()
    
    # Load configuration
    config = load_config()
    
    # Prune logs before setting up new logging
    # We use backup_count from config as the number of sessions to keep
    log_file = config['logging']['file']
    max_sessions = config['logging'].get('backup_count', 5)
    prune_logs(log_file, max_sessions)
    
    # Setup logging
    logger = setup_logging(config)
    logger.info("=" * 60)
    logger.info("Educational Video Automation Pipeline v2.0")
    logger.info("Single JSON Design - Self-Contained Questions")
    logger.info("=" * 60)
    
    try:
        # Initialize modules
        logger.info("Initializing modules...")
        
        question_selector = QuestionSelector(
            config['data']['questions'],
            config['data']['used_log']
        )
        
        image_generator = ImageGenerator(config)
        video_creator = VideoCreator(config)
        upload_manager = UploadManager(config)
        telegram_notifier = TelegramNotifier(config)
        
        # Get usage statistics
        # Get usage statistics
        stats = question_selector.get_stats()
        logger.info(f"Question bank stats: {stats['used']}/{stats['total']} used "
                   f"({stats['percentage_used']}%)")
        logger.info(f"Remaining by difficulty: {stats['remaining_by_difficulty']}")
        
        # Check Facebook Token Expiry
        days_remaining = upload_manager.verify_facebook_token()
        if days_remaining is not None:
            logger.info(f"Facebook Token Status: {days_remaining} days remaining")
            if days_remaining <= 5:
                logger.warning(f"Facebook token expires in {days_remaining} days!")
                telegram_notifier.send_alert(
                    "Facebook Token Expiring Soon",
                    f"⚠️ Your Facebook Access Token will expire in {days_remaining} days.\n"
                    "Please regenerate it to avoid upload failures."
                )
        
        # Step 1: Select question (with all metadata)
        logger.info("\n[Step 1/6] Selecting question with metadata...")
        question = question_selector.get_next_question()
        
        if not question:
            logger.error("No unused questions available!")
            telegram_notifier.send_error_alert("No unused questions available")
            return 1
        
        logger.info(f"Selected: Question ID {question['id']}")
        logger.info(f"Difficulty: {question['difficulty']}")
        logger.info(f"Question: {question['question'][:50]}...")
        
        # Step 2: Extract caption and description from question object
        logger.info("\n[Step 2/6] Extracting caption and description...")
        caption = question_selector.get_caption(question)
        description = question_selector.get_description(question)
        
        logger.info(f"Caption: {caption}")
        logger.info(f"Description length: {len(description)} chars")
        logger.info(f"Hashtags count: {len(question['hashtags'])}")
        
        # Step 3: Generate image
        logger.info("\n[Step 3/6] Generating question image...")
        temp_dir = config['paths']['temp_dir']
        Path(temp_dir).mkdir(parents=True, exist_ok=True)
        
        image_path = f"{temp_dir}/question_{question['id']}.png"
        image_generator.generate(question, image_path)
        logger.info(f"Image created: {image_path}")
        
        # # Step 4: Create video
        # logger.info("\n[Step 4/6] Creating video...")
        # video_path = f"{temp_dir}/video_{question['id']}.mp4"
        # video_creator.create_video(image_path, question['id'], video_path)
        
        # # Verify video
        # if not video_creator.verify_video(video_path):
        #     raise Exception("Video verification failed")
        
        # logger.info(f"Video created: {video_path}")
        

        # Step 4: Create video
        logger.info("\n[Step 4/6] Creating video...")
        video_dir = "video"
        Path(video_dir).mkdir(parents=True, exist_ok=True)
        video_path = f"{video_dir}/video_{question['id']}.mp4"
        video_creator.create_video(image_path, question['id'], video_path)
        
        # Verify video
        if not video_creator.verify_video(video_path):
            raise Exception("Video verification failed")
        
        logger.info(f"Video created: {video_path}")
        '''
        # Step 5: Upload to platforms
        logger.info("\n[Step 5/6] Uploading to social media...")
        logger.info(f"Using caption: {caption}")
        logger.info(f"Using description with {len(question['hashtags'])} hashtags")
        
        upload_results = upload_manager.upload_all(
            video_path,
            caption,
            description
        )
        
        # Log upload results
        for platform, result in upload_results.items():
            status = "✅ Success" if result['success'] else "❌ Failed"
            logger.info(f"{platform.capitalize()}: {status}")
            if not result['success']:
                logger.error(f"Error: {result.get('error')}")
        
        # Step 6: Send notification
        logger.info("\n[Step 6/6] Sending Telegram notification...")
        telegram_notifier.send_notification(question['id'], upload_results)
        
        # Mark question as used only if at least one upload succeeded
        if any(r['success'] for r in upload_results.values()):
            question_selector.mark_as_used(question['id'])
            logger.info(f"Question {question['id']} marked as used")
        else:
            logger.warning("All uploads failed - question not marked as used")
        '''        
        # Clean up temporary files
        logger.info("\nCleaning up temporary files...")
        cleanup_temp_files(temp_dir)
        
        logger.info("\n" + "=" * 60)
        logger.info("Pipeline execution completed successfully!")
        logger.info(f"Question ID: {question['id']}")
        logger.info(f"Difficulty: {question['difficulty']}")
        logger.info(f"Caption used: {caption[:30]}...")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"\n❌ Pipeline failed: {e}", exc_info=True)
        
        # Send error notification
        try:
            telegram_notifier.send_error_alert(str(e))
        except:
            pass
        
        return 1


if __name__ == "__main__":
    sys.exit(main())