import structlog
from typing import Optional
from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator

logger = structlog.get_logger()

class Translator:
    """Handle language detection and translation"""
    
    def detect_language(self, text: str) -> str:
        """
        Detect language of text
        Returns language code (e.g., 'en', 'es', 'fr', 'de', 'hi', etc.)
        """
        try:
            if len(text) > 50:
                lang = detect(text)
                logger.debug("language_detected", language=lang)
                return lang
        except LangDetectException as e:
            logger.debug("language_detection_failed", error=str(e))
        
        # Default to English if detection fails
        return 'en'
    
    def translate_to_english(self, text: str, source_lang: Optional[str] = None) -> Optional[str]:
        """
        Translate text to English
        
        Args:
            text: Text to translate
            source_lang: Source language code (auto-detected if None)
        
        Returns:
            Translated text or None if translation fails
        """
        try:
            # Detect source language if not provided
            if not source_lang:
                source_lang = self.detect_language(text)
            
            # No translation needed if already English
            if source_lang == 'en':
                return None
            
            # Translate
            logger.info("translating_text", 
                       source_lang=source_lang,
                       text_length=len(text))
            
            translator = GoogleTranslator(source=source_lang, target='en')
            
            # Handle long text (split if needed)
            max_length = 4500  # Google Translate limit per request
            if len(text) <= max_length:
                translated = translator.translate(text)
            else:
                # Split text into chunks
                chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
                translated_chunks = []
                
                for chunk in chunks:
                    translated_chunk = translator.translate(chunk)
                    translated_chunks.append(translated_chunk)
                
                translated = ' '.join(translated_chunks)
            
            logger.info("translation_successful",
                       source_lang=source_lang,
                       original_length=len(text),
                       translated_length=len(translated))
            
            return translated
            
        except Exception as e:
            logger.error("translation_failed", 
                        source_lang=source_lang,
                        error=str(e))
            return None