"""
Telegram Notifier Module
Sends notifications after video uploads.
"""

import logging
from datetime import datetime
from typing import Dict, Any
import requests

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Sends Telegram notifications for upload status."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Telegram notifier.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config['telegram']
        self.enabled = self.config['enabled']
        self.bot_token = self.config.get('bot_token')
        self.chat_id = self.config.get('chat_id')
        
        if self.enabled and (not self.bot_token or not self.chat_id):
            logger.warning("Telegram enabled but credentials missing")
            self.enabled = False
    
    def send_notification(self, question_id: int, 
                         upload_results: Dict[str, Any]) -> bool:
        """
        Send upload notification.
        
        Args:
            question_id: ID of the uploaded question
            upload_results: Upload results from all platforms
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.info("Telegram notifications disabled")
            return False
        
        try:
            message = self._format_message(question_id, upload_results)
            return self._send_message(message)
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    def _format_message(self, question_id: int,
                        upload_results: Dict[str, Any]) -> str:
        """
        Format notification message.
        
        Returns:
            Formatted message string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check upload status
        fb_status = "✅ Success" if upload_results.get('facebook', {}).get('success') else "❌ Failed"
        yt_status = "✅ Success" if upload_results.get('youtube', {}).get('success') else "❌ Failed"
        
        # Build message
        message = (
            "🎬 *Video Upload Report*\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 Question ID: `{question_id}`\n"
            f"📘 Facebook: {fb_status}\n"
            f"▶️ YouTube: {yt_status}\n"
            f"🕒 Time: {timestamp}\n\n"
        )
        
        # Add video links if available
        if upload_results.get('youtube', {}).get('success'):
            yt_url = upload_results['youtube'].get('url', 'N/A')
            message += f"🔗 YouTube: {yt_url}\n"
        
        if upload_results.get('facebook', {}).get('success'):
            fb_video_id = upload_results['facebook'].get('video_id', 'N/A')
            message += f"🔗 Facebook Video ID: `{fb_video_id}`\n"
        
        # Add error info if any failed
        errors = []
        if not upload_results.get('facebook', {}).get('success'):
            fb_error = upload_results.get('facebook', {}).get('error', 'Unknown error')
            errors.append(f"Facebook: {fb_error}")
        
        if not upload_results.get('youtube', {}).get('success'):
            yt_error = upload_results.get('youtube', {}).get('error', 'Unknown error')
            errors.append(f"YouTube: {yt_error}")
        
        if errors:
            message += "\n⚠️ *Errors:*\n"
            for error in errors:
                message += f"• {error}\n"
        
        return message
    
    def _send_message(self, message: str) -> bool:
        """
        Send message via Telegram API.
        
        Returns:
            True if successful, False otherwise
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                
                data = {
                    'chat_id': self.chat_id,
                    'text': message,
                    # 'parse_mode': 'Markdown',  # Disabled to prevent 400 Bad Request errors
                    'disable_web_page_preview': True
                }
                
                response = requests.post(url, data=data, timeout=10)
                response.raise_for_status()
                
                logger.info("Telegram notification sent successfully")
                return True
                
            except Exception as e:
                # Redact token from error message to prevent leaks
                error_msg = str(e).replace(self.bot_token, "[REDACTED]")
                
                if attempt < max_retries - 1:
                    logger.warning(f"Telegram send failed (attempt {attempt + 1}/{max_retries}): {error_msg}. Retrying...")
                    import time
                    time.sleep(2)
                else:
                    logger.error(f"Failed to send Telegram message after {max_retries} attempts: {error_msg}")
                    return False
    
    def send_alert(self, title: str, message: str) -> bool:
        """
        Send a generic alert message.
        
        Args:
            title: Alert title
            message: Alert content
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        formatted_msg = (
            f"⚠️ *{title}*\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"{message}\n\n"
            f"🕒 Time: {timestamp}"
        )
        
        return self._send_message(formatted_msg)

    def send_error_alert(self, error_message: str) -> bool:
        """
        Send error alert.
        
        Args:
            error_message: Error description
            
        Returns:
            True if sent successfully
        """
        if not self.enabled:
            return False
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        message = (
            "🚨 *Pipeline Error Alert*\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"❌ Error: {error_message}\n"
            f"🕒 Time: {timestamp}\n\n"
            "Please check the logs for details."
        )
        
        return self._send_message(message)
