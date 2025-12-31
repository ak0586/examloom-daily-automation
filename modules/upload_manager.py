"""
Upload Manager Module
Handles uploads to Facebook Reels and YouTube Shorts.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
import requests
import os

logger = logging.getLogger(__name__)


class UploadManager:
    """Manages video uploads to social media platforms."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the upload manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.fb_config = config['upload']['facebook']
        self.yt_config = config['upload']['youtube']
    
    def upload_all(self, video_path: str, caption: str, 
                   description: str) -> Dict[str, Any]:
        """
        Upload video to all enabled platforms.
        
        Args:
            video_path: Path to video file
            caption: Video caption/title
            description: Video description
            
        Returns:
            Dictionary with upload results
        """
        results = {}
        
        # Append music license
        music_license = (
            "\n\nMusic: Life of Riley – Kevin MacLeod\n"
            "Licensed under Creative Commons: Attribution 3.0\n"
            "http://creativecommons.org/licenses/by/3.0/"
        )
        full_description = description + music_license
        
        # Upload to Facebook
        if self.fb_config['enabled']:
            results['facebook'] = self._upload_facebook(
                video_path, caption, full_description
            )
        
        # Upload to YouTube
        if self.yt_config['enabled']:
            results['youtube'] = self._upload_youtube(
                video_path, caption, full_description
            )
        
        return results
    
    def verify_facebook_token(self) -> Optional[int]:
        """
        Check Facebook Access Token expiration.
        
        Returns:
            Days remaining until expiration, or None if check fails/infinite.
        """
        if not self.fb_config['enabled']:
            return None
            
        try:
            access_token = self.fb_config['access_token']
            
            # Use debug_token endpoint
            url = "https://graph.facebook.com/debug_token"
            params = {
                'input_token': access_token,
                'access_token': access_token 
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'data' in data and 'expires_at' in data['data']:
                expires_at = data['data']['expires_at']
                
                # expires_at = 0 means never expires
                if expires_at == 0:
                    return 9999
                
                # Calculate days remaining
                from datetime import datetime
                expiry_date = datetime.fromtimestamp(expires_at)
                days_remaining = (expiry_date - datetime.now()).days
                return days_remaining
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not verify Facebook token expiry: {e}")
            return None

    def _upload_facebook(self, video_path: str, caption: str,
                         description: str) -> Dict[str, Any]:
        """
        Upload video to Facebook Reels.
        
        Returns:
            Upload result dictionary
        """
        logger.info("Uploading to Facebook Reels...")
        
        try:
            # Initialize upload session
            page_id = self.fb_config['page_id']
            access_token = self.fb_config['access_token']
            
            # Step 1: Initialize upload
            init_url = f"https://graph.facebook.com/v18.0/{page_id}/video_reels"
            
            init_data = {
                'upload_phase': 'start',
                'access_token': access_token
            }
            
            init_response = requests.post(init_url, data=init_data)
            init_response.raise_for_status()
            init_result = init_response.json()
            
            video_id = init_result.get('video_id')
            upload_url = init_result.get('upload_url')
            
            if not video_id or not upload_url:
                raise Exception("Failed to initialize upload session")
            
            logger.info(f"Upload session initialized: {video_id}")
            
            # Step 2: Upload video file
            file_size = os.path.getsize(video_path)
            
            with open(video_path, 'rb') as video_file:
                # Facebook requires raw binary upload with offset header
                headers = {
                    'Authorization': f'OAuth {access_token}',
                    'offset': '0',
                    'file_size': str(file_size)
                }
                upload_response = requests.post(
                    upload_url, 
                    data=video_file,
                    headers=headers
                )
                upload_response.raise_for_status()
            
            logger.info("Video file uploaded")
            
            # Step 3: Finish upload and publish
            finish_data = {
                'upload_phase': 'finish',
                'video_id': video_id,
                'description': description,
                'title': caption,
                'access_token': access_token,
                'video_state': 'PUBLISHED'
            }
            
            finish_response = requests.post(init_url, data=finish_data)
            finish_response.raise_for_status()
            finish_result = finish_response.json()
            
            logger.info(f"Facebook upload response: {finish_result}")
            logger.info("Facebook upload successful")
            
            return {
                'success': True,
                'video_id': video_id,
                'response': finish_result
            }
            
        except Exception as e:
            logger.error(f"Facebook upload failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _upload_youtube(self, video_path: str, title: str,
                        description: str) -> Dict[str, Any]:
        """
        Upload video to YouTube Shorts.
        
        Returns:
            Upload result dictionary
        """
        logger.info("Uploading to YouTube Shorts...")
        
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            from google.auth.transport.requests import Request
            import pickle
            import os
            
            SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
            
            creds = None
            token_file = self.yt_config['credentials_file']
            
            # Load credentials
            if os.path.exists(token_file):
                with open(token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.yt_config['client_secrets_file'], SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save credentials
                with open(token_file, 'wb') as token:
                    pickle.dump(creds, token)
            
            # Build YouTube service
            youtube = build('youtube', 'v3', credentials=creds)
            
            # Prepare video metadata
            # Sanitize description (YouTube doesn't allow < or >)
            # Replace with full-width unicode equivalents to preserve meaning
            safe_description = description.replace('<', '＜').replace('>', '＞')
            
            # Note: Adding #Shorts in title/description makes it a Short
            body = {
                'snippet': {
                    'title': title,
                    'description': safe_description + '\n\n#Shorts',
                    'tags': ['shorts', 'education', 'quiz'],
                    'categoryId': self.yt_config['category_id']
                },
                'status': {
                    'privacyStatus': self.yt_config['privacy_status'],
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # Upload video
            media = MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True,
                mimetype='video/mp4'
            )
            
            request = youtube.videos().insert(
                part='snippet,status',
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"Upload progress: {int(status.progress() * 100)}%")
            
            video_id = response['id']
            logger.info(f"YouTube upload successful: {video_id}")
            
            return {
                'success': True,
                'video_id': video_id,
                'url': f"https://youtube.com/shorts/{video_id}",
                'response': response
            }
            
        except Exception as e:
            logger.error(f"YouTube upload failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _retry_upload(self, upload_func, *args, **kwargs) -> Dict[str, Any]:
        """
        Retry upload with exponential backoff.
        
        Returns:
            Upload result
        """
        max_attempts = 3
        base_delay = 5
        
        for attempt in range(max_attempts):
            result = upload_func(*args, **kwargs)
            
            if result['success']:
                return result
            
            if attempt < max_attempts - 1:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Upload attempt {attempt + 1} failed, "
                             f"retrying in {delay}s...")
                time.sleep(delay)
        
        return result
