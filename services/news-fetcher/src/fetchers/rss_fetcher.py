import asyncio
import aiohttp
import feedparser
from typing import AsyncGenerator, Tuple, Dict, Any, List
from urllib.parse import urljoin, urlparse
from datetime import datetime
from ..utils.app_logger import get_logger
from ..utils.state_store import FeedHTTPState

log = get_logger("rss_fetcher")

class RSSFetcher:
    def __init__(self, timeout: int = 15, http_state: FeedHTTPState = None, rate_limit_delay: float = 1.0):
        self.timeout = timeout
        self.http_state = http_state or FeedHTTPState("")
        self.rate_limit_delay = rate_limit_delay
        self.failed_feeds: List[Dict[str, str]] = []

    async def fetch_feed(self, session: aiohttp.ClientSession, url: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Fetch a single RSS feed and return feed title and entries."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; NewsFetcher/1.0)',
                'Accept': 'application/rss+xml, application/xml, text/xml, */*'
            }
            
            # Add If-Modified-Since header if we have state
            last_modified = self.http_state.get_last_modified(url)
            if last_modified:
                headers['If-Modified-Since'] = last_modified

            async with session.get(url, headers=headers, timeout=self.timeout) as response:
                if response.status == 304:
                    log.info(f"Feed {url} not modified since last fetch")
                    return "", []
                
                if response.status != 200:
                    log.warning(f"HTTP {response.status} for {url}")
                    return "", []

                content_type = response.headers.get('content-type', '').lower()
                if 'xml' not in content_type and 'rss' not in content_type:
                    log.warning(f"Non-RSS content type for {url}: {content_type}")
                    return "", []

                # Update last modified
                last_modified = response.headers.get('last-modified', '')
                if last_modified:
                    self.http_state.set_last_modified(url, last_modified)

                content = await response.text()
                feed = feedparser.parse(content)
                
                if not feed.entries:
                    log.warning(f"No entries found in feed: {url}")
                    return "", []

                feed_title = feed.feed.get('title', 'Unknown Feed')
                log.info(f"Processing {len(feed.entries)} entries from {feed_title}")
                
                return feed_title, feed.entries

        except asyncio.TimeoutError:
            log.warning(f"Timeout fetching {url}")
            return "", []
        except Exception as e:
            log.warning(f"Fetch failed for {url}: {e}")
            return "", []

    async def stream_entries(self, urls: List[str], dedupe_store) -> AsyncGenerator[Tuple[str, Dict[str, Any]], None]:
        """Stream entries from multiple RSS feeds."""
        self.failed_feeds = []
        
        async with aiohttp.ClientSession() as session:
            for i, url in enumerate(urls, 1):
                log.info(f"Fetching feed {i}/{len(urls)}: {url}")
                
                feed_title, entries = await self.fetch_feed(session, url)
                
                if not entries:
                    self.failed_feeds.append({
                        'url': url,
                        'error': 'No entries found in feed'
                    })
                    continue

                for entry in entries:
                    # Create a unique ID for deduplication
                    entry_id = entry.get('id') or entry.get('guid') or entry.get('link', '')
                    if not entry_id:
                        # Generate ID from title and link
                        title = entry.get('title', '')
                        link = entry.get('link', '')
                        entry_id = f"{title}_{link}".replace(' ', '_')[:100]
                    
                    # Check if we've seen this entry before
                    if dedupe_store.seen(entry_id):
                        continue
                    
                    # Prepare entry data for Kafka
                    entry_data = {
                        'id': entry_id,
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'summary': entry.get('summary', ''),
                        'published': entry.get('published', ''),
                        'updated': entry.get('updated', ''),
                        'authors': entry.get('authors', []),
                        'tags': [tag.get('term', '') for tag in entry.get('tags', [])],
                        'feed_title': feed_title,
                        'feed_url': url,
                        'fetched_at': datetime.now().isoformat(),
                        'raw_entry': entry  # Store the complete raw entry
                    }
                    
                    yield feed_title, entry_data
                
                # Rate limiting
                if i < len(urls):
                    await asyncio.sleep(self.rate_limit_delay)
        
        # Log failed feeds summary
        if self.failed_feeds:
            log.error("=" * 60)
            log.error("FAILED RSS FEEDS SUMMARY:")
            log.error("=" * 60)
            for i, failed in enumerate(self.failed_feeds, 1):
                log.error(f"{i}. URL: {failed['url']}")
                log.error(f"   Error: {failed['error']}")
                log.error("-" * 40)
            log.error(f"Total failed feeds: {len(self.failed_feeds)}")
            log.error("=" * 60)
