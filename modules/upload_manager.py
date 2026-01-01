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

# Suppress harmless Google API warning
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

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
        
        # Append CTA and music license
        cta_text = "\n\n👉 Please Subscribe & Follow for more! ❤️"
        music_license = (
            "\n\nMusic: Life of Riley – Kevin MacLeod\n"
            "Licensed under Creative Commons: Attribution 3.0\n"
            "http://creativecommons.org/licenses/by/3.0/"
        )
        full_description = description + cta_text + music_license
        
        # Upload to Facebook & Instagram (Independent but shared config)
        if self.fb_config['enabled']:
            # 1. Upload to Facebook
            results['facebook'] = self._upload_facebook(
                video_path, caption, full_description
            )
            
            # 2. Upload to Instagram (Check for linked account)
            access_token = self.fb_config['access_token']
            page_id = self.fb_config['page_id']
            
            ig_user_id = self._get_instagram_account_id(page_id, access_token)
            
            if ig_user_id:
                logger.info(f"Found linked Instagram account: {ig_user_id}")
                results['instagram'] = self._upload_instagram(
                    video_path, full_description, access_token, ig_user_id
                )
            else:
                logger.info("No linked Instagram account found for crossposting")
        
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
                'url': f"https://www.facebook.com/reel/{video_id}",
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

    def _get_instagram_account_id(self, page_id: str, access_token: str) -> Optional[str]:
        """
        Get the Instagram Business Account ID linked to the Facebook Page.
        """
        try:
            url = f"https://graph.facebook.com/v18.0/{page_id}"
            params = {
                'fields': 'instagram_business_account',
                'access_token': access_token
            }
            response = requests.get(url, params=params)
            data = response.json()
            
            if 'instagram_business_account' in data:
                return data['instagram_business_account']['id']
            return None
        except Exception as e:
            logger.warning(f"Could not get linked Instagram account: {e}")
            return None

    def _upload_instagram(self, video_path: str, caption: str, access_token: str, ig_user_id: str) -> Dict[str, Any]:
        """
        Upload video to Instagram via the Graph API using Resumable Upload (Binary).
        """
        logger.info("Uploading to Instagram Reels (Binary)...")
        
        try:
            # Step 1: Initialize Upload Session
            init_url = f"https://graph.facebook.com/v18.0/{ig_user_id}/media"
            init_data = {
                'media_type': 'REELS',
                'upload_type': 'resumable',
                'caption': caption,
                'share_to_feed': 'true',
                'access_token': access_token
            }
            
            init_response = requests.post(init_url, data=init_data)
            init_response.raise_for_status()
            init_result = init_response.json()
            
            uri = init_result.get('uri')
            video_id = init_result.get('id') # This is actually the container ID used for status checks? No, documentation says 'id' is container ID.
            
            if not uri or not video_id:
                raise Exception("Failed to initialize Instagram upload session")

            logger.info(f"Instagram upload session initialized: {video_id}")

            # Step 2: Upload Binary
            file_size = os.path.getsize(video_path)
            
            with open(video_path, 'rb') as video_file:
                headers = {
                    'Authorization': f'OAuth {access_token}',
                    'offset': '0',
                    'file_size': str(file_size),
                    'Content-Type': 'application/octet-stream'
                }
                
                upload_response = requests.post(
                    uri,
                    data=video_file,
                    headers=headers
                )
                
                if not upload_response.ok:
                    logger.error(f"Instagram binary upload failed: {upload_response.text}")
                upload_response.raise_for_status()
            
            logger.info("Instagram video binary uploaded")

            # Step 3: Publish Media
            publish_url = f"https://graph.facebook.com/v18.0/{ig_user_id}/media_publish"
            publish_data = {
                'creation_id': video_id, 
                'access_token': access_token
            }
            
            publish_response = requests.post(publish_url, data=publish_data)
            publish_response.raise_for_status()
            publish_result = publish_response.json()
            ig_media_id = publish_result.get('id')
            
            logger.info(f"Instagram publish request sent: {ig_media_id}")

            # Step 4: Wait for processing status (Optional but good for confirmation)
            # Check status of the CONTAINER (video_id), not the media_id
            status_url = f"https://graph.facebook.com/v18.0/{video_id}"
            status_params = {
                'fields': 'status_code,status',
                'access_token': access_token
            }
            
            for i in range(10): 
                time.sleep(5)
                status_response = requests.get(status_url, params=status_params)
                status_data = status_response.json()
                
                status_code = status_data.get('status_code')
                if status_code == 'FINISHED':
                    logger.info("Instagram processing FINISHED")
                    break
                elif status_code == 'ERROR':
                    logger.error(f"Instagram processing ERROR: {status_data}")
                    # Don't throw here, passing back the ID might still be useful
                    break
                
                logger.debug(f"Instagram status: {status_code}")
                
            # Step 5: Get Permalink
            permalink = None
            try:
                # Need to query the media ID (ig_media_id) not the container ID
                media_url = f"https://graph.facebook.com/v18.0/{ig_media_id}"
                media_params = {
                    'fields': 'permalink,shortcode',
                    'access_token': access_token
                }
                media_response = requests.get(media_url, params=media_params)
                if media_response.ok:
                    media_data = media_response.json()
                    permalink = media_data.get('permalink')
                    logger.info(f"Instagram permalink: {permalink}")
            except Exception as e:
                logger.warning(f"Could not fetch Instagram permalink: {e}")

            return {
                'success': True,
                'id': ig_media_id,
                'container_id': video_id,
                'url': permalink or f"https://www.instagram.com/reel/{ig_media_id}/", # Fallback
                'response': publish_result
            }

        except Exception as e:
            logger.error(f"Instagram upload failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
