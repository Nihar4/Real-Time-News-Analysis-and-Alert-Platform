import json
import random
import re
import time
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlsplit, urlunsplit

import requests
import structlog
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Optional dependencies — degrade gracefully if missing
try:
    import httpx  # HTTP/2 capable
except Exception:
    httpx = None

try:
    import cloudscraper  # Handles many Cloudflare anti-bot flows
except Exception:
    cloudscraper = None

try:
    import trafilatura
except Exception:
    trafilatura = None

try:
    from newspaper import Article as NewspaperArticle
except Exception:
    NewspaperArticle = None

try:
    from readability import Document
except Exception:
    Document = None

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None

logger = structlog.get_logger()

# --------------------------------------------------------------------------------------
# Utilities
# --------------------------------------------------------------------------------------
DEFAULT_UAS: List[str] = [
    # Fresh-ish Chrome on major desktops
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    # A couple of Firefox variants
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
]

def jitter(base: float, spread: float = 0.6) -> float:
    lo = max(0, base - spread)
    hi = base + spread
    return random.uniform(lo, hi)

def looks_like_cloudflare(resp: requests.Response) -> bool:
    if not resp:
        return False
    server = (resp.headers.get("Server") or "").lower()
    if "cloudflare" in server:
        return True
    # Typical interstitial titles or tokens
    if re.search(r"attention required|cloudflare|just a moment", resp.text[:2000], re.I):
        return True
    return False

def merge_headers(base: Dict[str, str], extra: Dict[str, str]) -> Dict[str, str]:
    out = dict(base)
    out.update({k: v for k, v in extra.items() if v is not None})
    return out


# --------------------------------------------------------------------------------------
# Main extractor
# --------------------------------------------------------------------------------------
class TextExtractor:
    """
    Multi-method text extraction with a resilient fetcher.
    Tries 4 methods in order of reliability:
      1. Trafilatura
      2. Newspaper3k
      3. Readability
      4. BeautifulSoup
    """

    def __init__(
        self,
        user_agent: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        proxies: Optional[Dict[str, str]] = None,
        user_agents_pool: Optional[List[str]] = None,
        respect_robots: bool = False,  # keep False; enable if you want robots.txt checks
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.proxies = proxies
        self.respect_robots = respect_robots

        self.user_agents_pool = user_agents_pool or DEFAULT_UAS
        self.user_agent = user_agent or random.choice(self.user_agents_pool)

        # "Default" headers; we'll build per-request variants
        self.base_headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
            # A more realistic modern Chrome fingerprint:
            "sec-ch-ua": '"Chromium";v="126", "Not(A:Brand";v="24", "Google Chrome";v="126"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }

        # Prepare a robust requests session
        self.session = self._build_session()

    # ------------------------------------------------------------------
    # HTTP plumbing
    # ------------------------------------------------------------------
    def _build_session(self) -> requests.Session:
        session = requests.Session()

        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset(["HEAD", "GET", "OPTIONS"]),
            backoff_factor=self.backoff_factor,
            raise_on_status=False,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=20, pool_maxsize=20)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        if self.proxies:
            session.proxies.update(self.proxies)

        return session

    def _normalized_url(self, url: str) -> str:
        parts = urlsplit(url)
        return urlunsplit((parts.scheme or "https", parts.netloc, parts.path, parts.query, ""))

    def _build_headers(self, url: str, referer: Optional[str] = None, ua: Optional[str] = None) -> Dict[str, str]:
        parts = urlsplit(url)
        default_ref = f"{parts.scheme}://{parts.netloc}/" if parts.netloc else None
        headers = merge_headers(
            self.base_headers,
            {
                "User-Agent": ua or random.choice(self.user_agents_pool),
                "Referer": referer or default_ref,
                "Origin": f"{parts.scheme}://{parts.netloc}" if parts.netloc else None,
            },
        )
        return headers

    def _warm_up(self, url: str, headers: Dict[str, str]) -> None:
        """
        Light warm-up to collect cookies/redirects before the main GET.
        """
        try:
            # HEAD isn't always allowed; if 405, do a light GET to root.
            head = self.session.head(url, headers=headers, timeout=self.timeout, allow_redirects=True)
            if head.status_code == 405:
                parts = urlsplit(url)
                root = f"{parts.scheme}://{parts.netloc}/"
                self.session.get(root, headers=headers, timeout=self.timeout, allow_redirects=True)
        except Exception:
            # Warm-up is best-effort
            pass

    def _requests_fetch(self, url: str, attempt: int) -> Tuple[Optional[str], Optional[int], Optional[requests.Response]]:
        headers = self._build_headers(url)
        self._warm_up(url, headers)

        # Random human-like delay
        time.sleep(jitter(0.7))

        resp = self.session.get(
            url,
            headers=headers,
            timeout=self.timeout,
            allow_redirects=True,
        )

        # Reject non-HTML content-types
        ctype = (resp.headers.get("Content-Type") or "").lower()
        if "text/html" not in ctype and "application/xhtml+xml" not in ctype:
            # "Maybe" still HTML — if it looks like it
            if "<html" not in resp.text[:2000].lower():
                return None, resp.status_code, resp

        text = resp.text if resp and len(resp.text) >= 100 else None
        return text, resp.status_code, resp

    def _httpx_fetch(self, url: str, attempt: int) -> Tuple[Optional[str], Optional[int]]:
        if httpx is None:
            return None, None

        headers = self._build_headers(url)
        time.sleep(jitter(0.9))

        # A fresh client per attempt can change TLS fingerprints slightly
        with httpx.Client(http2=True, timeout=self.timeout, follow_redirects=True, headers=headers, proxies=self.proxies) as client:
            r = client.get(url)
            ctype = (r.headers.get("Content-Type") or "").lower()
            if "text/html" not in ctype and "application/xhtml+xml" not in ctype:
                if "<html" not in r.text[:2000].lower():
                    return None, r.status_code
            text = r.text if r and len(r.text) >= 100 else None
            return text, r.status_code

    def _cloudscraper_fetch(self, url: str, attempt: int) -> Tuple[Optional[str], Optional[int]]:
        if cloudscraper is None:
            return None, None

        scraper = cloudscraper.create_scraper(browser={"browser": "chrome", "platform": "windows", "mobile": False})
        headers = self._build_headers(url)
        time.sleep(jitter(1.2))
        r = scraper.get(url, headers=headers, timeout=self.timeout, allow_redirects=True)
        ctype = (r.headers.get("Content-Type") or "").lower()
        if "text/html" not in ctype and "application/xhtml+xml" not in ctype:
            if "<html" not in r.text[:2000].lower():
                return None, r.status_code
        text = r.text if r and len(r.text) >= 100 else None
        return text, r.status_code

    def fetch_html(self, url: str) -> Optional[str]:
        """
        Robust HTML fetch with:
          - Rotating UAs/headers
          - Warm-up cookie collection
          - Requests (HTTP/1.1) → httpx (HTTP/2) → cloudscraper fallback
          - Backoff with jitter
        """
        normalized = self._normalized_url(url)
        logger.info("fetching_url", url=normalized)

        # Try a few attempts, rotate UA every time
        for attempt in range(1, self.max_retries + 1):
            # Rotate UA for each attempt
            self.user_agent = random.choice(self.user_agents_pool)
            self.base_headers["User-Agent"] = self.user_agent

            # 1) requests
            try:
                text, status, resp = self._requests_fetch(normalized, attempt)
                if text and status and status < 400:
                    logger.info("fetch_successful", method="requests", attempt=attempt, status=status)
                    return text

                # If explicitly blocked and looks like Cloudflare, try cloudscraper early:
                if status == 403 and looks_like_cloudflare(resp):
                    logger.info("detected_cloudflare_interstitial")
                    text2, status2 = self._cloudscraper_fetch(normalized, attempt)
                    if text2 and status2 and status2 < 400:
                        logger.info("fetch_successful", method="cloudscraper", attempt=attempt, status=status2)
                        return text2
            except requests.exceptions.Timeout:
                logger.warning("requests_timeout", attempt=attempt)
            except requests.exceptions.RequestException as e:
                logger.warning("requests_error", attempt=attempt, error=str(e))

            # 2) httpx with HTTP/2 (often fixes 403s due to TLS/ALPN fingerprint)
            try:
                text_h2, status_h2 = self._httpx_fetch(normalized, attempt)
                if text_h2 and status_h2 and status_h2 < 400:
                    logger.info("fetch_successful", method="httpx", attempt=attempt, status=status_h2)
                    return text_h2
            except Exception as e:
                logger.debug("httpx_error", attempt=attempt, error=str(e))

            # 3) cloudscraper fallback (if not already tried)
            try:
                text_cs, status_cs = self._cloudscraper_fetch(normalized, attempt)
                if text_cs and status_cs and status_cs < 400:
                    logger.info("fetch_successful", method="cloudscraper", attempt=attempt, status=status_cs)
                    return text_cs
            except Exception as e:
                logger.debug("cloudscraper_error", attempt=attempt, error=str(e))

            # Backoff with jitter
            sleep_s = jitter(self.backoff_factor * attempt)
            logger.info("retry_backoff", sleep=f"{sleep_s:.2f}s", attempt=attempt)
            time.sleep(sleep_s)

        logger.error("all_fetch_attempts_failed", url=url)
        return None

    # ------------------------------------------------------------------
    # Extraction methods
    # ------------------------------------------------------------------
    def extract_with_trafilatura(self, url: str, html: str) -> Optional[Dict]:
        """Method 1: Trafilatura (BEST - specialized for news/articles)"""
        if trafilatura is None:
            logger.info("extraction_method_unavailable", method="trafilatura", reason="trafilatura_not_installed")
            return None

        def _run_trafilatura(favor_precision: bool) -> Optional[Dict]:
            try:
                extracted = trafilatura.extract(
                    html,
                    include_comments=False,
                    include_tables=True,
                    include_images=False,
                    output_format="json",
                    url=url,
                    favor_precision=favor_precision,
                )
                logger.debug(
                    "trafilatura_extract_returned",
                    favor_precision=favor_precision,
                    extracted_type=type(extracted).__name__,
                    extracted_is_none=extracted is None,
                )
                if not extracted:
                    return None

                data = json.loads(extracted)
                title = data.get("title") or ""
                content = (data.get("text") or "").strip()
                if content and len(content) > 100:
                    logger.info(
                        "extraction_success",
                        method="trafilatura",
                        favor_precision=favor_precision,
                        length=len(content),
                    )
                    return {
                        "title": title,
                        "content": content,
                        "author": data.get("author"),
                        "date": data.get("date"),
                        "description": data.get("description", ""),
                        "image_url": data.get("image"),
                        "keywords": [],
                        "method": "trafilatura",
                    }
                else:
                    logger.info(
                        "extraction_too_short",
                        method="trafilatura",
                        favor_precision=favor_precision,
                        length=len(content) if content else 0,
                        url=url,
                    )
                    return None
            except Exception as e:
                logger.warning(
                    "trafilatura_failed",
                    error=str(e),
                    favor_precision=favor_precision,
                    url=url,
                )
                return None

        # First try high precision
        result = _run_trafilatura(favor_precision=True)
        if result:
            return result

        # If that gives None, fall back to recall mode
        logger.info("trafilatura_retry_with_lower_precision", url=url)
        return _run_trafilatura(favor_precision=False)

    def extract_with_newspaper(self, url: str, html: str) -> Optional[Dict]:
        """Method 2: Newspaper3k (GOOD - widely used, reliable)"""
        if NewspaperArticle is None:
            logger.info("extraction_method_unavailable", method="newspaper3k", reason="newspaper3k_not_installed")
            return None
        try:
            article = NewspaperArticle(url)
            article.set_html(html)
            article.parse()
            text = (article.text or "").strip()
            if text and len(text) > 100:
                logger.info("extraction_success", method="newspaper3k", length=len(text))
                return {
                    "title": article.title,
                    "content": text,
                    "author": ", ".join(article.authors) if getattr(article, "authors", None) else None,
                    "date": article.publish_date.isoformat() if getattr(article, "publish_date", None) else None,
                    "description": getattr(article, "meta_description", None),
                    "image_url": getattr(article, "top_image", None),
                    "keywords": (article.keywords[:10] if getattr(article, "keywords", None) else []),
                    "method": "newspaper3k",
                }
            else:
                logger.info(
                    "extraction_too_short",
                    method="newspaper3k",
                    length=len(text) if text else 0,
                    url=url,
                )
        except Exception as e:
            logger.warning("newspaper_failed", error=str(e), url=url)
        return None

    def extract_with_readability(self, html: str) -> Optional[Dict]:
        """Method 3: Readability (DECENT - Mozilla's algorithm)"""
        if Document is None or BeautifulSoup is None:
            logger.info(
                "extraction_method_unavailable",
                method="readability",
                reason="document_or_bs4_not_installed",
            )
            return None
        try:
            doc = Document(html)
            soup = BeautifulSoup(doc.summary(), "lxml")

            # Dust tags
            for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript", "iframe"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            title = (doc.title() or "").strip()

            if text and len(text) > 100:
                logger.info("extraction_success", method="readability", length=len(text))
                return {
                    "title": title,
                    "content": text,
                    "author": None,
                    "date": None,
                    "description": None,
                    "image_url": None,
                    "keywords": [],
                    "method": "readability",
                }
            else:
                logger.info(
                    "extraction_too_short",
                    method="readability",
                    length=len(text) if text else 0,
                )
        except Exception as e:
            logger.warning("readability_failed", error=str(e))
        return None

    def extract_with_beautifulsoup(self, html: str) -> Optional[Dict]:
        """Method 4: BeautifulSoup (FALLBACK - basic extraction)"""
        if BeautifulSoup is None:
            logger.info("extraction_method_unavailable", method="beautifulsoup", reason="beautifulsoup_not_installed")
            return None
        try:
            soup = BeautifulSoup(html, "lxml")

            # Remove unwanted elements
            for tag in soup(["script", "style", "nav", "header", "footer", "aside", "iframe", "noscript"]):
                tag.decompose()

            # Title
            title = ""
            h1 = soup.find("h1")
            if h1 and h1.get_text(strip=True):
                title = h1.get_text(strip=True)
            elif soup.title and soup.title.get_text(strip=True):
                title = soup.title.get_text(strip=True)

            # Main content
            main = soup.find(["article", "main"])
            content = ""
            if main:
                content = main.get_text(separator="\n", strip=True)
            else:
                # Smart-ish content div
                content_div = soup.find(
                    "div",
                    class_=lambda x: x
                    and any(w in x.lower() for w in ["content", "article", "post", "story", "text", "body"])
                )
                if content_div:
                    content = content_div.get_text(separator="\n", strip=True)
                else:
                    # All paragraphs fallback
                    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
                    content = "\n".join(p for p in paragraphs if p)

            content = "\n".join(line.strip() for line in content.split("\n") if line.strip())

            if content and len(content) > 100:
                logger.info("extraction_success", method="beautifulsoup", length=len(content))
                return {
                    "title": title,
                    "content": content,
                    "author": None,
                    "date": None,
                    "description": None,
                    "image_url": None,
                    "keywords": [],
                    "method": "beautifulsoup",
                }
            else:
                logger.info(
                    "extraction_too_short",
                    method="beautifulsoup",
                    length=len(content) if content else 0,
                )
        except Exception as e:
            logger.warning("beautifulsoup_failed", error=str(e))
        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def extract(self, url: str) -> Optional[Dict]:
        """
        Main extraction method - tries all 4 methods in order
        Returns first successful extraction
        """
        html = self.fetch_html(url)
        if not html:
            logger.error("no_html_downloaded", url=url)
            return None

        methods = [
            ("trafilatura", lambda: self.extract_with_trafilatura(url, html)),
            ("newspaper3k", lambda: self.extract_with_newspaper(url, html)),
            ("readability", lambda: self.extract_with_readability(html)),
            ("beautifulsoup", lambda: self.extract_with_beautifulsoup(html)),
        ]

        for name, fn in methods:
            logger.info("extraction_method_attempt", method=name, url=url)
            try:
                result = fn()
                if result and result.get("content"):
                    logger.info(
                        "extraction_method_succeeded",
                        method=name,
                        length=len(result["content"]),
                        url=url,
                    )
                    return result
                else:
                    logger.info(
                        "extraction_method_no_content",
                        method=name,
                        url=url,
                    )
            except Exception as e:
                logger.warning(
                    "extraction_method_exception",
                    method=name,
                    url=url,
                    error=str(e),
                )
                continue

        logger.warning("all_extraction_methods_failed", url=url)
        return None
