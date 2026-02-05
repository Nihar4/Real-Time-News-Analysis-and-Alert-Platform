import structlog
from typing import Optional, List
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from datetime import datetime

logger = structlog.get_logger()

class MetadataExtractor:
    """Extract additional metadata from articles"""
    
    def extract_publish_date(self, html: str, extracted_date: Optional[str]) -> Optional[str]:
        """Extract publish date from HTML or use extracted date"""
        # If extraction method already got the date, use it
        if extracted_date:
            try:
                parsed = date_parser.parse(extracted_date)
                return parsed.isoformat()
            except:
                pass
        
        # Try to extract from HTML meta tags
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Common meta tag patterns for publish date
            date_tags = [
                {'property': 'article:published_time'},
                {'property': 'og:published_time'},
                {'name': 'publication_date'},
                {'name': 'publishdate'},
                {'name': 'date'},
                {'itemprop': 'datePublished'}
            ]
            
            for tag in date_tags:
                meta = soup.find('meta', tag)
                if meta and meta.get('content'):
                    try:
                        parsed = date_parser.parse(meta['content'])
                        return parsed.isoformat()
                    except:
                        continue
            
            # Try time tags
            time_tag = soup.find('time')
            if time_tag:
                datetime_attr = time_tag.get('datetime')
                if datetime_attr:
                    try:
                        parsed = date_parser.parse(datetime_attr)
                        return parsed.isoformat()
                    except:
                        pass
        
        except Exception as e:
            logger.debug("date_extraction_failed", error=str(e))
        
        return None
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Simple keyword extraction using word frequency
        (Will be improved in Topic Classification service)
        """
        try:
            # Common stop words to ignore
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
                'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was',
                'are', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 
                'does', 'did', 'will', 'would', 'could', 'should', 'may',
                'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
                'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who',
                'when', 'where', 'why', 'how', 'said', 'says', 'more', 'new',
                'about', 'into', 'through', 'during', 'before', 'after'
            }
            
            # Clean and split text
            words = text.lower().split()
            
            # Count word frequencies
            word_freq = {}
            for word in words:
                # Remove punctuation and keep only alphanumeric
                word = ''.join(c for c in word if c.isalnum())
                
                # Filter: length > 3 and not a stop word
                if len(word) > 3 and word not in stop_words:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Sort by frequency and get top keywords
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            keywords = [word for word, freq in sorted_words[:max_keywords]]
            
            return keywords
        
        except Exception as e:
            logger.debug("keyword_extraction_failed", error=str(e))
            return []