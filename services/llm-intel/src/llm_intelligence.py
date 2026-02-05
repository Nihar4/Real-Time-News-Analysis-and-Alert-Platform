import json
import time
from itertools import product
from typing import Optional, Dict, Any, List, Tuple

import structlog
from cerebras.cloud.sdk import Cerebras
import google.generativeai as genai

logger = structlog.get_logger()


class LLMIntelligenceExtractor:
    """Extract structured company update intelligence using Gemini and Cerebras LLMs."""

    EMPTY_SENTINELS = {
        "",
        "null",
        "none",
        "n/a",
        "na",
        "untitled",
        "no title",
        "no description",
        "-",
        "--",
    }

    # Simple hints for big frequent companies
    COMPANY_HINTS = {
        "amazon": ["amazon", "aws", "amazon web services", "prime video"],
        "google": ["google", "alphabet", "deepmind"],
        "microsoft": ["microsoft", "azure", "github", "linkedin"],
        "meta": ["meta", "facebook", "instagram", "whatsapp"],
        "apple": ["apple", "iphone", "ipad", "macbook"],
        "nvidia": ["nvidia"],
        "openai": ["openai", "chatgpt"],
        "anthropic": ["anthropic", "claude"],
        "tesla": ["tesla", "spacex"],
    }

    def __init__(
        self,
        cerebras_api_keys: List[str],
        cerebras_models: List[str],
        gemini_api_keys: List[str],
        gemini_models: List[str],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        sleep_between_attempts: float = 0.5,
        min_content_length: int = 40,
    ):
        self.cerebras_api_keys = cerebras_api_keys
        self.cerebras_models = cerebras_models
        self.gemini_api_keys = gemini_api_keys
        self.gemini_models = gemini_models
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.sleep_between_attempts = sleep_between_attempts
        self.min_content_length = min_content_length

    # -------------------------------
    # helpers for source sanitization
    # -------------------------------

    def _clean_field(self, value: Optional[Any]) -> str:
        """Normalize title or content. Convert null like strings to empty."""
        if value is None:
            return ""
        text = str(value).strip()
        if text.lower() in self.EMPTY_SENTINELS:
            return ""
        return text

    def _sanitize_article_inputs(self, title: Optional[str], content: Optional[str]) -> Tuple[str, str]:
        clean_title = self._clean_field(title)
        clean_content = self._clean_field(content)
        return clean_title, clean_content

    def _is_effectively_empty_article(self, title: str, content: str) -> bool:
        """Decide if we should skip before calling the LLM."""
        if not title and not content:
            return True
        if not content:
            return True
        if len(content) < self.min_content_length:
            return True
        return False

    # -------------------------------
    # prompt construction
    # -------------------------------

    def _create_prompt(self, title: str, content: str) -> str:
        """Create the LLM prompt with strict JSON schema."""
        clipped_content = content[:8000]

        prompt = f"""You are an analyst for a company news and update system.

Your job:
- Detect whether an article contains any meaningful update related to a real company.
- Extract structured information about that company update.

Treat an article as a company update and set "is_business_relevant": true in all of these cases:
- The article mentions any real company, division, business unit, or product (for example amazon, aws, alphabet, google, microsoft, meta, apple, nvidia, openai, anthropic, tesla, oracle, salesforce, ibm, intel, adobe, netflix, tsmc, arm, etc.) and covers any of:
  - AI models, AI infrastructure, cloud services, chips, platforms, or software products
  - earnings, guidance, financial performance, funding, valuations, IPOs
  - mergers, acquisitions, partnerships, joint ventures, strategic alliances
  - leadership changes, new CEOs, senior hires, reorgs
  - strategy, product roadmaps, competitive positioning, CEO interviews, executive vision
  - culture, layoffs, hiring plans, workplace policies, remote work, internal memos
  - pricing changes, go to market moves, market entries or exits
  - regulations, antitrust actions, security incidents, or policy changes that directly affect a company
- Even if the article also talks about politics, society, or individuals, as long as it is anchored in what a company is doing or how a company is affected, treat it as a company update.

If the title directly mentions a well known company name, you must set primary_company:
- If the title includes "Amazon" or "AWS", set "primary_company": "amazon"
- If the title includes "Google" or "Alphabet", set "primary_company": "google"
- If the title includes "Microsoft" or "Azure", set "primary_company": "microsoft"
- If the title includes "Meta" or "Facebook", set "primary_company": "meta"
- Use a similar rule for other well known companies

Only set "is_business_relevant": false if:
- You cannot identify any real company or product from the content
- The content is so short or vague that you cannot tell what is happening

When the article is not a company update:
- set "is_business_relevant": false
- set "primary_company": null
- set "secondary_companies": []
- set all summaries and impact fields to empty strings
- set all scores to mid values such as 3
- set all list fields to []

When a field has no information or does not apply:
- For single value fields, use JSON null
- For list fields, use an empty list []
- Never use strings like "none", "n/a", "N/A", "unknown", "no company", or "null" to represent missing values

Important formatting rules:
- Use real JSON types, for example booleans true or false, numbers for scores, and null for missing values
- Do not wrap booleans, numbers, or null in quotes
- Return exactly one JSON object and no extra text before or after it

Article Title: {title or ""}

Article Content:
{clipped_content}

Return a JSON object with these EXACT fields and types:
{{
  "is_business_relevant": true or false,

  "primary_company": "lowercase canonical company name string, for example 'amazon', 'aws', 'google', 'microsoft', or null if no company can be identified",
  "secondary_companies": ["array", "of", "lowercase", "company", "names"],

  "event_type": "short snake_case label such as product_launch, acquisition, partnership, funding, leadership_change, strategy_shift, regulatory_action, security_incident, earnings, culture_update, or null if unclear",
  "event_subtype": "more specific type such as foundation_model, cloud_infrastructure, genai_platform, data_breach, layoff, hiring_push, or null",
  "category": "high level category such as technology, finance, healthcare, consumer, industrials, energy, or null",

  "headline_summary": "One sentence news headline focusing on the company update",
  "short_summary": "Two or three sentence summary of what happened",
  "detailed_summary": "Multi paragraph detailed summary in plain text",

  "strategic_insight": "Strategic implications and context for the main company",
  "impact_on_market": "Impact on the broader market or segment",
  "impact_on_products": "Impact on products or services",
  "impact_on_customers": "Impact on customers or users",
  "impact_on_competitors": "Impact on competitors and ecosystem",
  "impact_on_talent": "Impact on hiring, workforce, or talent market",
  "impact_on_regulation": "Regulatory or policy implications",

  "risk_score": integer 1 to 5,
  "opportunity_score": integer 1 to 5,
  "threat_level": "low", "medium", or "high",
  "confidence_level": "low", "medium", or "high",

  "overall_impact": integer 1 to 5,
  "importance_level": "low", "medium", or "high",
  "urgency": "low", "medium", or "high",
  "time_horizon": "short_term", "medium_term", or "long_term",

  "recommended_actions": "Recommended strategic actions for the main company and for observers",
  "sentiment": "positive", "negative", or "neutral",
  "sentiment_score": float between 0.0 and 1.0,

  "tags": ["list", "of", "relevant", "tags", "such", "as", "generative_ai", "cloud", "semiconductors"],

  "key_points": ["3-5 short bullet points with the core factual points"],
  "recommended_teams": ["teams that should care such as product, sales, marketing, leadership, security, legal, hr"],
  "affected_areas": ["areas such as product, market, customers, talent, regulation, operations"],
  "confidence_explanation": "One or two sentences explaining why you set the confidence_level"
}}

IMPORTANT. Return ONLY the JSON object, no markdown, no backticks, no explanations."""
        return prompt

    # -------------------------------
    # low level LLM calls
    # -------------------------------

    def _try_gemini_extraction(self, prompt: str, api_key: str, model_name: str) -> Optional[str]:
        """Try extraction with Gemini."""
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if not response or not getattr(response, "text", None):
                return None
            return response.text.strip()
        except Exception as e:
            logger.warning(
                "gemini_call_failed",
                model=model_name,
                error=str(e)[:200],
                error_type=type(e).__name__,
            )
            return None

    def _try_extraction(self, prompt: str, api_key: str, model: str) -> Optional[str]:
        """Try extraction with a specific Cerebras API key and model."""
        try:
            client = Cerebras(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(
                "llm_call_failed",
                model=model,
                error=str(e)[:200],
                error_type=type(e).__name__,
            )
            return None

    # -------------------------------
    # JSON cleaning and normalization
    # -------------------------------

    def _clean_and_parse_json(self, result_text: str, model: str, attempt: int) -> Optional[Dict[str, Any]]:
        raw = result_text.strip()

        # Strip code fences if present
        if raw.startswith("```"):
            parts = raw.split("```")
            if len(parts) >= 2:
                raw = parts[1].strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()

        # Fallback, grab from first { to last }
        if not raw.strip().startswith("{"):
            first = raw.find("{")
            last = raw.rfind("}")
            if first != -1 and last != -1 and first < last:
                raw = raw[first:last + 1]

        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning(
                "json_decode_error",
                model=model,
                attempt=attempt,
                error=str(e),
                response_text=raw[:200],
            )
            return None

    def _normalize_string_field(self, value: Any) -> str:
        if not isinstance(value, str):
            return ""
        v = value.strip()
        if v.lower() in self.EMPTY_SENTINELS:
            return ""
        return v

    def _normalize_list_field(self, value: Any) -> List[str]:
        if value is None:
            return []
        if not isinstance(value, list):
            value = [value]

        cleaned: List[str] = []
        for item in value:
            if not isinstance(item, str):
                item = str(item)
            s = item.strip()
            if s and s.lower() not in self.EMPTY_SENTINELS:
                cleaned.append(s)
        return cleaned

    def _infer_primary_company_from_title(self, title: str, current: str) -> str:
        """
        Heuristic fallback.
        If the model did not set primary_company, infer it from the title for big obvious companies.
        """
        if current:
            return current

        t = (title or "").lower()
        if not t:
            return current

        for canonical, patterns in self.COMPANY_HINTS.items():
            for pat in patterns:
                if pat in t:
                    return canonical

        return current

    def _normalize_intelligence(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Normalize primary_company first
        primary_company_raw = self._normalize_string_field(data.get("primary_company"))
        primary_company = primary_company_raw.lower() if primary_company_raw else ""
        data["primary_company"] = primary_company

        # Booleans
        val = data.get("is_business_relevant", False)
        if primary_company:
            data["is_business_relevant"] = True
        else:
            if isinstance(val, str):
                data["is_business_relevant"] = val.lower() == "true"
            else:
                data["is_business_relevant"] = bool(val)

        # Int fields
        for field in ["risk_score", "opportunity_score", "overall_impact"]:
            v = data.get(field, 3)
            try:
                v = int(v)
            except (TypeError, ValueError):
                v = 3
            data[field] = max(1, min(5, v))

        # Float field
        v = data.get("sentiment_score", 0.5)
        try:
            v = float(v)
        except (TypeError, ValueError):
            v = 0.5
        data["sentiment_score"] = max(0.0, min(1.0, v))

        # Required string fields
        required_strings = [
            "primary_company",
            "event_type",
            "category",
            "headline_summary",
            "short_summary",
            "detailed_summary",
            "strategic_insight",
            "sentiment",
            "threat_level",
            "confidence_level",
            "recommended_actions",
            "importance_level",
            "urgency",
            "time_horizon",
            "confidence_explanation",
        ]
        for field in required_strings:
            data[field] = self._normalize_string_field(data.get(field))

        # List style fields
        list_fields = [
            "secondary_companies",
            "tags",
            "key_points",
            "recommended_teams",
            "affected_areas",
        ]
        for field in list_fields:
            data[field] = self._normalize_list_field(data.get(field))

        # basic enum normalization for threat_level, confidence_level, sentiment etc
        def _normalize_enum(value: Any, allowed: List[str], default: str) -> str:
            v = self._normalize_string_field(value).lower()
            return v if v in allowed else default

        data["threat_level"] = _normalize_enum(
            data.get("threat_level", "medium"),
            ["low", "medium", "high"],
            "medium",
        )

        data["confidence_level"] = _normalize_enum(
            data.get("confidence_level", "medium"),
            ["low", "medium", "high"],
            "medium",
        )

        data["sentiment"] = _normalize_enum(
            data.get("sentiment", "neutral"),
            ["positive", "negative", "neutral"],
            "neutral",
        )

        data["importance_level"] = _normalize_enum(
            data.get("importance_level", "medium"),
            ["low", "medium", "high"],
            "medium",
        )

        data["urgency"] = _normalize_enum(
            data.get("urgency", "medium"),
            ["low", "medium", "high"],
            "medium",
        )

        data["time_horizon"] = _normalize_enum(
            data.get("time_horizon", "short_term"),
            ["short_term", "medium_term", "long_term"],
            "short_term",
        )

        return data

    def _validate_intelligence(self, intelligence: Dict[str, Any], title: str, model: str) -> tuple[bool, bool]:
        """
        Validation for company updates.
        Returns (is_valid, should_retry):
        - (True, False): Valid intelligence, use it
        - (False, False): Successfully determined no company/summary, don't retry
        - (False, True): Parsing/validation failed, should retry
        """

        # 1. Try to infer primary company from title if missing
        p_comp = intelligence.get("primary_company", "").lower().strip()
        inferred = self._infer_primary_company_from_title(title, p_comp)
        if inferred and not p_comp:
            intelligence["primary_company"] = inferred
            p_comp = inferred

        # 2. Primary company must be present and not a placeholder
        if not p_comp or p_comp in ["null", "none", "n/a", "unknown"]:
            logger.info(
                "discarding_no_company",
                title=title[:80],
                model=model,
            )
            return (False, False)  # Successfully determined no company, don't retry

        # 3. Summary should be non trivial
        summary = intelligence.get("short_summary", "").strip()
        if not summary or len(summary) < 10:
            logger.info(
                "discarding_no_summary",
                title=title[:80],
                model=model,
            )
            return (False, False)  # Successfully determined no good summary, don't retry

        logger.info(
            "llm_extraction_successful",
            model=model,
            primary_company=intelligence.get("primary_company"),
            event_type=intelligence.get("event_type"),
            tags_count=len(intelligence.get("tags", [])),
        )
        return (True, False)  # Valid intelligence

    # -------------------------------
    # public API
    # -------------------------------

    def extract(self, title: Optional[str], content: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Extract company update intelligence from article with retry logic.

        Contract.
        - Returns a fully validated intelligence dict when the article contains a usable company update.
        - Returns None when there is no clear company, or all model calls fail or produce invalid JSON.
        """
        clean_title, clean_content = self._sanitize_article_inputs(title, content)

        if self._is_effectively_empty_article(clean_title, clean_content):
            logger.info(
                "skipping_empty_article",
                raw_title=(title or "")[:50],
                raw_content_len=len(content or ""),
            )
            return None

        prompt = self._create_prompt(clean_title, clean_content)

        # 1. Try Gemini first (iterate models then keys)
        gemini_pairs = [(m, k) for m, k in product(self.gemini_models, self.gemini_api_keys)]

        for attempt, (model_name, api_key) in enumerate(gemini_pairs, start=1):
            logger.info(
                "calling_llm_gemini",
                model=model_name,
                attempt=attempt,
                title=clean_title[:50],
            )

            result_text = self._try_gemini_extraction(prompt, api_key, model_name)
            if not result_text:
                time.sleep(self.sleep_between_attempts)
                continue

            intelligence = self._clean_and_parse_json(result_text, model_name, attempt)
            if intelligence is None:
                time.sleep(self.sleep_between_attempts)
                continue

            intelligence = self._normalize_intelligence(intelligence)

            is_valid, should_retry = self._validate_intelligence(intelligence, clean_title, model_name)
            if is_valid:
                return intelligence

            if not should_retry:
                # Successfully determined no company/summary, don't waste API calls
                return None

            time.sleep(self.sleep_between_attempts)

        # 2. Fallback to Cerebras
        logger.info("gemini_failed_falling_back_to_cerebras", title=clean_title[:50])

        pairs = [(k, m) for k, m in product(self.cerebras_api_keys, self.cerebras_models)]
        max_attempts = len(pairs)

        for attempt, (api_key, model) in enumerate(pairs, start=1):
            logger.info(
                "calling_llm_cerebras",
                model=model,
                attempt=attempt,
                max_attempts=max_attempts,
                title=clean_title[:50],
            )

            result_text = self._try_extraction(prompt, api_key, model)
            if not result_text:
                time.sleep(self.sleep_between_attempts)
                continue

            intelligence = self._clean_and_parse_json(result_text, model, attempt)
            if intelligence is None:
                time.sleep(self.sleep_between_attempts)
                continue

            intelligence = self._normalize_intelligence(intelligence)

            is_valid, should_retry = self._validate_intelligence(intelligence, clean_title, model)
            if is_valid:
                return intelligence

            if not should_retry:
                # Successfully determined no company/summary, don't waste API calls
                return None

            time.sleep(self.sleep_between_attempts)

        logger.error(
            "all_llm_attempts_failed",
            title=clean_title[:50],
            total_attempts=max_attempts,
        )
        return None
