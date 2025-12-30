"""
Video Creator Module
Creates vertical videos using FFmpeg with overlays and effects.
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class VideoCreator:
    """Creates short-form vertical videos using FFmpeg."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the video creator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.video_config = config['video']
        self.overlay_config = config['overlays']
    
    def create_video(self, image_path: str, question_id: int, 
                     output_path: str) -> str:
        """
        Create video from question image.
        
        Args:
            image_path: Path to question image
            question_id: Question ID for header text
            output_path: Path to save video
            
        Returns:
            Path to generated video
        """
        logger.info(f"Creating video for question ID: {question_id}")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build FFmpeg command
        cmd = self._build_ffmpeg_command(image_path, question_id, str(output_path))
        
        try:
            # Run FFmpeg
            logger.debug(f"FFmpeg command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Video created successfully: {output_path}")
            return str(output_path)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed: {e.stderr}")
            raise
    
    def _build_ffmpeg_command(self, image_path: str, question_id: int,
                            output_path: str) -> list:
        """
        Build FFmpeg command with zoom effect only (no overlays).
        
        Returns:
            List of command arguments
        """
        width = self.video_config['resolution']['width']
        height = self.video_config['resolution']['height']
        duration = self.video_config['duration']
        fps = self.video_config['fps']
        
        # Zoom effect parameters
        zoom_start = self.overlay_config['zoom']['start_scale']
        zoom_end = self.overlay_config['zoom']['end_scale']
        
        # Build filter - ONLY zoom, no text overlays
        filter_complex = (
            # Input image, loop for duration, set frame rate
            f"[0:v]loop=loop={duration * fps}:size=1:start=0,"
            f"setpts=N/{fps}/TB,"
            # Image already at correct size (1080x1920), no scaling needed
            # Zoom effect
            f"zoompan=z='if(lte(zoom,1.0),{zoom_start},{zoom_start}+"
            f"(on/{duration * fps})*({zoom_end}-{zoom_start}))':d={duration * fps}:s={width}x{height}"
        )
        
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-loop', '1',  # Loop input image
            '-i', image_path,  # Input image
            '-filter_complex', filter_complex,
            '-t', str(duration),  # Duration
            '-r', str(fps),  # Frame rate
            '-c:v', self.video_config['codec'],  # Video codec
            '-preset', self.video_config['preset'],  # Encoding preset
            '-crf', str(self.video_config['crf']),  # Quality
            '-pix_fmt', 'yuv420p',  # Pixel format (for compatibility)
            '-movflags', '+faststart',  # Optimize for streaming
            output_path
        ]
        
        return cmd
        
    def verify_video(self, video_path: str) -> bool:
        """
        Verify that video was created successfully.
        
        Args:
            video_path: Path to video file
            
        Returns:
            True if valid, False otherwise
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-select_streams', 'v:0',
                '-count_packets',
                '-show_entries', 'stream=nb_read_packets,duration',
                '-of', 'csv=p=0',
                video_path
            ]
            
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            
            logger.info(f"Video verification: {result.stdout.strip()}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Video verification failed: {e}")
            return False
