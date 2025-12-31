"""
Image Generator Module
Creates pixel-perfect question images with professional typography.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont
import textwrap

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Generates question images with precise layout and typography."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the image generator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.img_config = config['image']
        self.width = self.img_config['resolution']['width']
        self.height = self.img_config['resolution']['height']
        self.padding = self.img_config['padding']
        self.bg_color = self.img_config['background_color']
        
        # Load fonts
        self.font_path = config['paths']['font_file']
        self.active_font_path = None  # Track the actual font being used
        self._load_fonts()
    
    def _load_fonts(self) -> None:
        """Load fonts for question and options."""
        try:
            # Try to load custom font
            if Path(self.font_path).exists():
                self.active_font_path = self.font_path
                self.question_font = ImageFont.truetype(
                    self.font_path,
                    self.img_config['fonts']['question']['size']
                )
                self.options_font = ImageFont.truetype(
                    self.font_path,
                    self.img_config['fonts']['options']['size']
                )
                logger.info(f"Loaded custom font: {self.font_path}")
            else:
                # Use larger default font sizes when custom font not available
                logger.warning("Custom font not found, using default with larger sizes")
                try:
                    # Try common system fonts on Windows/Linux
                    for font_name in ['seguiemj.ttf', 'segoeui.ttf', 'calibri.ttf', 'verdana.ttf', 'arial.ttf', 'Arial.ttf', 'DejaVuSans.ttf', 'Roboto-Regular.ttf']:
                        try:
                            self.question_font = ImageFont.truetype(
                                font_name,
                                self.img_config['fonts']['question']['size']
                            )
                            self.options_font = ImageFont.truetype(
                                font_name,
                                self.img_config['fonts']['options']['size']
                            )
                            self.active_font_path = font_name
                            logger.info(f"Loaded system font: {font_name}")
                            return
                        except:
                            continue
                    raise Exception("No system fonts found")
                except:
                    # Last resort: use PIL default
                    self.question_font = ImageFont.load_default()
                    self.options_font = ImageFont.load_default()
                    logger.warning("Using PIL default font")
        except Exception as e:
            logger.error(f"Failed to load fonts: {e}")
            self.question_font = ImageFont.load_default()
            self.options_font = ImageFont.load_default()
        
    def generate(self, question_data: Dict[str, Any], output_path: str) -> str:
        """
        Generate question image with header and footer overlays.
        
        Args:
            question_data: Question dictionary
            output_path: Path to save the image
            
        Returns:
            Path to generated image
        """
        logger.info(f"Generating image for question ID: {question_data['id']}")
        
        # Create full-size canvas (1080x1920 for complete video frame)
        full_height = 1920
        img = Image.new('RGB', (self.width, full_height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Draw header overlay (top)
        # Draw header overlay (top)
        header_height = self.config['overlays']['header'].get('height', 200)
        header_bg = self.config['overlays']['header'].get('background', '#000000')
        
        # Handle color conversion if needed (support both hex and rgba strings if possible, but keeping it simple for now)
        # Using a new image for the overlay to support alpha if configured, otherwise pasting solid
        if header_bg.startswith('#'):
            header_overlay = Image.new('RGBA', (self.width, header_height), header_bg)
        else:
            # Fallback for rgba string parsing if we were using it, but config is now hex
            # For simplicity assuming hex from config update
            header_overlay = Image.new('RGBA', (self.width, header_height), (40, 53, 147, 255))

        img.paste(header_overlay, (0, 0), header_overlay)
        
        # Get header text template from config and format it
        header_template = self.config['overlays']['header']['text']
        # Default to 'Quant' if type is missing
        q_type = question_data.get('type', 'Quant')
        header_text = header_template.format(id=question_data['id'], type=q_type)
        try:
            header_font_size = self.config['overlays']['header']['font_size']
            if self.active_font_path:
                header_font = ImageFont.truetype(self.active_font_path, header_font_size)
            else:
                 header_font = ImageFont.load_default()
        except:
            header_font = ImageFont.load_default()
        
        # Center Header Text
        header_bbox = draw.textbbox((0, 0), header_text, font=header_font)
        header_text_width = header_bbox[2] - header_bbox[0]
        header_text_height = header_bbox[3] - header_bbox[1]
        
        header_x = (self.width - header_text_width) // 2
        header_y = (header_height - header_text_height) // 2 - 10 # Slight visual connection
        
        draw.text((header_x, header_y), header_text, fill='#FFFFFF', font=header_font)
        
        # Content area (centered vertically between header and footer)
        # Re-fetch heights in case they weren't defined in local scope (though header_height was)
        content_header_height = self.config['overlays']['header'].get('height', 200)
        content_footer_height = self.config['overlays']['footer'].get('height', 200)
        
        content_start_y = content_header_height + 120  # More space after header
        # subtract footer height AND the 150px safe zone margin AND the 120px padding
        content_end_y = full_height - content_footer_height - 150 - 120  
        content_center_y = (content_start_y + content_end_y) // 2
        content_width = self.width - (2 * self.padding)
        # Calculate question height first
        
        # --- Dynamic Font Sizing Start ---
        available_height = content_end_y - content_start_y
        
        # Initial font sizes from config
        base_q_size = self.img_config['fonts']['question']['size']
        base_opt_size = self.img_config['fonts']['options']['size']
        
        # Calculate optimal font sizes
        q_size, opt_size = self._calculate_optimal_font_size(
            question_data, 
            content_width, 
            available_height,
            base_q_size,
            base_opt_size
        )
        
        # Update fonts with calculated sizes
        if self.active_font_path:
            self.question_font = ImageFont.truetype(self.active_font_path, q_size)
            self.options_font = ImageFont.truetype(self.active_font_path, opt_size)
        else:
            # Fallback (won't resize, but logic is here)
            self.question_font = ImageFont.load_default()
            self.options_font = ImageFont.load_default()
            
        logger.info(f"Dynamic Sizing: Q={q_size}px (was {base_q_size}), Opt={opt_size}px (was {base_opt_size})")
        # --- Dynamic Font Sizing End ---
        question_lines = self._wrap_text(question_data['question'], content_width, self.question_font)
        question_height = len(question_lines) * 90  # Approximate height
        
        # Calculate options height
        options_height = 4 * 90  # 4 options
        
        # Total content height
        total_content_height = question_height + 250 + options_height  # 250px gap
        
        # Start position to center everything
        start_y = content_center_y - (total_content_height // 2)
        
        # Draw question
        question_y = start_y
        actual_question_height = self._draw_question(
            draw, 
            question_data['question'],
            question_y,
            content_width
        )
        
        # Draw options with more spacing
        options_y = question_y + actual_question_height + 250
        self._draw_options(
            draw,
            question_data['options'],
            options_y,
            content_width
        )
        
        # Draw footer overlay (bottom)
        # Draw footer overlay (bottom)
        footer_height = self.config['overlays']['footer'].get('height', 200)
        footer_bg = self.config['overlays']['footer'].get('background', '#000000')
        # Move footer up by 150px (Save Zone for video progress bar)
        footer_y_pos = full_height - footer_height - 150
        
        if footer_bg.startswith('#'):
            footer_overlay = Image.new('RGBA', (self.width, footer_height), footer_bg)
        else:
             footer_overlay = Image.new('RGBA', (self.width, footer_height), (40, 53, 147, 255))
            
        img.paste(footer_overlay, (0, footer_y_pos), footer_overlay)
        
        footer_text = self.config['overlays']['footer'].get('text', "⏸️ Pause & Comment Your Answer 👇")
        try:
            footer_font_size = self.config['overlays']['footer']['font_size']
            if self.active_font_path:
                footer_font = ImageFont.truetype(self.active_font_path, footer_font_size)
            else:
                footer_font = ImageFont.load_default()
        except:
            footer_font = ImageFont.load_default()
        
        # Center Footer Text
        footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
        footer_text_width = footer_bbox[2] - footer_bbox[0]
        footer_text_height = footer_bbox[3] - footer_bbox[1]
        
        footer_x = (self.width - footer_text_width) // 2
        footer_text_y = footer_y_pos + (footer_height - footer_text_height) // 2 - 10
        
        draw.text((footer_x, footer_text_y), footer_text, fill='#FFFFFF', font=footer_font, align='center')
        
        # Save image
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, format='PNG', quality=100)
        
        logger.info(f"Image saved to: {output_path}")
        return str(output_path)
    
    
    def _calculate_optimal_font_size(self, question_data: Dict[str, Any], 
                                   max_width: int, max_height: int, 
                                   start_q_size: int, start_opt_size: int) -> Tuple[int, int]:
        """
        Iteratively calculate the largest font size that fits the content.
        Maintains the ratio between question and option font sizes.
        """
        q_size = start_q_size
        opt_size = start_opt_size
        min_size = 20  # Minimum readable size
        step = 5       # Step size for reduction
        
        ratio = opt_size / q_size
        
        line_spacing = self.img_config['layout']['line_spacing']
        option_spacing = self.img_config['layout']['option_spacing']
        gap_between_q_and_opt = 150
        
        while q_size >= min_size:
            # Create temporary fonts
            try:
                if self.active_font_path:
                    temp_q_font = ImageFont.truetype(self.active_font_path, int(q_size))
                    temp_opt_font = ImageFont.truetype(self.active_font_path, int(opt_size))
                else:
                    return q_size, opt_size # Cannot resize default font
            except:
                return q_size, opt_size
            
            # 1. Measure Question Height
            q_lines = self._wrap_text(question_data['question'], max_width, temp_q_font)
            # Estimate height: (num_lines * line_height) + (num_lines-1 * spacing)
            # Using bbox for more accuracy or simple approximation
            # Simple approximation based on previous logic:
            # text_height * line_spacing is the stride. 
            # Get height of one line
            bbox = temp_q_font.getbbox("Tg") # distinct ascender/descender
            one_line_h = bbox[3] - bbox[1]
            total_q_h = len(q_lines) * (one_line_h * line_spacing)
            
            # 2. Measure Options Height
            # 4 options
            # Label + Text
            total_opt_h = 0
            labels = ['A', 'B', 'C', 'D']
            for label, opt_text in zip(labels, question_data['options']):
                # Label measurement
                # Option text measurement (wrapped)
                # Label takes some space, say 50px? 
                # Let's approximate label width + spacing as 80px
                label_w_approx = 80
                item_width = max_width - label_w_approx
                
                opt_lines = self._wrap_text(opt_text, item_width, temp_opt_font)
                
                bbox_opt = temp_opt_font.getbbox("Tg")
                opt_line_h = bbox_opt[3] - bbox_opt[1]
                
                # Height of this option block
                # Using similar drawing logic approximation: bbox + 5px per line? 
                # Drawing logic was: bbox[3]-bbox[1] + 5
                this_opt_h = len(opt_lines) * (opt_line_h + 5)
                total_opt_h += this_opt_h
            
            # Add spacing between options (3 gaps for 4 items)
            total_opt_h += (3 * option_spacing)
            
            # 3. Total Height
            total_content_height = total_q_h + gap_between_q_and_opt + total_opt_h
            
            if total_content_height <= max_height:
                return int(q_size), int(opt_size)
            
            # Reduce size
            q_size -= step
            opt_size = q_size * ratio
            
        return int(min_size), int(min_size * ratio)

    def _draw_question(self, draw: ImageDraw, text: str, y_start: int, 
                       max_width: int) -> int:
        """
        Draw question text with auto-wrapping.
        
        Returns:
            Height of the rendered text
        """
        # Wrap text
        wrapped_lines = self._wrap_text(text, max_width, self.question_font)
        
        line_spacing = self.img_config['layout']['line_spacing']
        current_y = y_start
        
        for line in wrapped_lines:
            # Get text bbox for centering
            bbox = draw.textbbox((0, 0), line, font=self.question_font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center horizontally
            x = (self.width - text_width) // 2
            
            # Draw text
            draw.text(
                (x, current_y),
                line,
                fill=self.img_config['fonts']['question']['color'],
                font=self.question_font
            )
            
            current_y += int(text_height * line_spacing)
        
        return current_y - y_start
    
    def _draw_options(self, draw: ImageDraw, options: list, y_start: int,
                      max_width: int) -> int:
        """
        Draw options with labels (A, B, C, D).
        
        Returns:
            Height of the rendered options
        """
        labels = ['A', 'B', 'C', 'D']
        option_spacing = self.img_config['layout']['option_spacing']
        label_spacing = self.img_config['layout']['label_spacing']
        
        current_y = y_start
        
        for label, option_text in zip(labels, options):
            # Get label dimensions
            label_bbox = draw.textbbox((0, 0), label + ".", font=self.options_font)
            label_width = label_bbox[2] - label_bbox[0]
            
            # Draw label
            x_label = self.padding
            draw.text(
                (x_label, current_y),
                f"{label}.",
                fill=self.img_config['fonts']['options']['color'],
                font=self.options_font
            )
            
            # Draw option text
            x_option = x_label + label_width + label_spacing
            option_max_width = max_width - label_width - label_spacing
            
            wrapped_option = self._wrap_text(
                option_text, 
                option_max_width, 
                self.options_font
            )
            
            option_y = current_y
            for line in wrapped_option:
                draw.text(
                    (x_option, option_y),
                    line,
                    fill=self.img_config['fonts']['options']['color'],
                    font=self.options_font
                )
                
                bbox = draw.textbbox((0, 0), line, font=self.options_font)
                option_y += bbox[3] - bbox[1] + 5
            
            current_y = option_y + option_spacing
        
        return current_y - y_start
    
    def _wrap_text(self, text: str, max_width: int, font: ImageFont) -> list:
        """
        Wrap text to fit within max_width.
        
        Returns:
            List of wrapped lines
        """
        # Create temporary draw to measure text
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = temp_draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines if lines else [text]
