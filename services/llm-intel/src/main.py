#!/usr/bin/env python3
"""
Service 3: LLM Intelligence Service
Analyzes cleaned articles and extracts comprehensive business intelligence
Consumes: news.cleaned
Produces: news.enriched
"""
import asyncio
import structlog
import psycopg2
import json
from datetime import datetime
from typing import Optional

from src.config import settings
from src.kafka_handler import KafkaHandler
from src.llm_intelligence import LLMIntelligenceExtractor

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()


class LLMIntelligenceService:
    """
    Service 3: LLM Intelligence
    
    Processes cleaned articles:
    1. Calls LLM with retry logic across multiple API keys and models
    2. Extracts company-centric intelligence
    3. Publishes enriched articles to Kafka
    """
    
    def __init__(self):
        # Initialize Kafka handler
        self.kafka = KafkaHandler(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            consumer_group=settings.kafka_consumer_group,
            input_topic=settings.kafka_topic_input,
            output_topic=settings.kafka_topic_output
        )
        
        # Initialize LLM extractor with multiple API keys and models
        self.llm_extractor = LLMIntelligenceExtractor(
            cerebras_api_keys=settings.cerebras_api_keys,
            cerebras_models=settings.cerebras_models,
            gemini_api_keys=settings.gemini_api_keys,
            gemini_models=settings.gemini_models,
            max_tokens=settings.cerebras_max_tokens,
            temperature=settings.cerebras_temperature
        )
        
        logger.info("llm_intelligence_service_initialized", 
                   api_keys_count=len(settings.cerebras_api_keys),
                   models_count=len(settings.cerebras_models))
    
    def enrich_article(self, cleaned_article: dict) -> Optional[dict]:
        """Enrich a single article with LLM intelligence"""
        try:
            article_id = cleaned_article.get("article_id", "")
            title = cleaned_article.get("title", "")
            content = cleaned_article.get("content", "")
            
            if not content:
                logger.warning("no_content_found", article_id=article_id)
                return None
            
            logger.info("enriching_article", article_id=article_id, title=title[:50])
            
            # Extract intelligence using LLM with retry logic
            intelligence = self.llm_extractor.extract(title, content)
            
            if not intelligence:
                logger.warning("intelligence_extraction_failed_all_attempts", article_id=article_id)
                return None
            
            # Check if article is business-relevant
            is_business_relevant = intelligence.get("is_business_relevant", False)
            if not is_business_relevant:
                logger.info("article_not_business_relevant_skipping",
                           article_id=article_id,
                           title=title[:50])
                return None
            
            # Check if primary company is identified
            primary_company = intelligence.get("primary_company", "")
            if not primary_company or primary_company.lower() in ["null", "none", "", "unknown"]:
                logger.info("article_no_company_identified_skipping",
                           article_id=article_id,
                           title=title[:50],
                           primary_company=primary_company)
                return None
            
            # Check confidence level - skip if too low
            confidence_level = intelligence.get("confidence_level", "low")
            if confidence_level == "low":
                logger.info("article_low_confidence_skipping",
                           article_id=article_id,
                           title=title[:50],
                           confidence_level=confidence_level)
                return None
            
            # Create enriched article (original fields + intelligence)
            enriched_article = {
                # Original fields
                "article_id": article_id,
                "url": cleaned_article.get("url", ""),
                "title": title,
                "content": content,
                "source": cleaned_article.get("source", ""),
                "publish_time": cleaned_article.get("publish_time", ""),
                "fetched_at": cleaned_article.get("fetched_at", ""),
                "processed_at": cleaned_article.get("processed_at", ""),
                "word_count": cleaned_article.get("word_count", 0),
                
                # LLM Intelligence fields (per spec)
                "is_business_relevant": intelligence.get("is_business_relevant", True),
                "primary_company": intelligence.get("primary_company", ""),
                "secondary_companies": intelligence.get("secondary_companies", []),
                "event_type": intelligence.get("event_type", ""),
                "event_subtype": intelligence.get("event_subtype", ""),
                "category": intelligence.get("category", ""),
                
                "headline_summary": intelligence.get("headline_summary", ""),
                "short_summary": intelligence.get("short_summary", ""),
                "detailed_summary": intelligence.get("detailed_summary", ""),
                
                "strategic_insight": intelligence.get("strategic_insight", ""),
                "impact_on_market": intelligence.get("impact_on_market", ""),
                "impact_on_products": intelligence.get("impact_on_products", ""),
                "impact_on_customers": intelligence.get("impact_on_customers", ""),
                "impact_on_competitors": intelligence.get("impact_on_competitors", ""),
                "impact_on_talent": intelligence.get("impact_on_talent", ""),
                "impact_on_regulation": intelligence.get("impact_on_regulation", ""),
                
                "risk_score": intelligence.get("risk_score", 3),
                "opportunity_score": intelligence.get("opportunity_score", 3),
                "threat_level": intelligence.get("threat_level", "medium"),
                "confidence_level": intelligence.get("confidence_level", "medium"),
                
                "recommended_actions": intelligence.get("recommended_actions", ""),
                "sentiment": intelligence.get("sentiment", "neutral"),
                "sentiment_score": intelligence.get("sentiment_score", 0.5),
                "tags": intelligence.get("tags", []),
                
                # Metadata
                "enriched_at": datetime.utcnow().isoformat()
            }
            
            # Write to DB
            try:
                conn = psycopg2.connect(
                    host=settings.db_host,
                    port=settings.db_port,
                    dbname=settings.db_name,
                    user=settings.db_user,
                    password=settings.db_password
                )
                with conn.cursor() as cur:
                    # 1. Ensure Company Exists
                    slug = primary_company.lower().replace(" ", "-").replace(".", "") # Simple slugify
                    cur.execute("""
                        INSERT INTO companies (slug, display_name)
                        VALUES (%s, %s)
                        ON CONFLICT (slug) DO UPDATE SET display_name = EXCLUDED.display_name
                        RETURNING id
                    """, (slug, primary_company))
                    company_id = cur.fetchone()[0]
                    
                    # 2. Insert Event
                    cur.execute("""
                        INSERT INTO events (
                            article_id, primary_company_id, event_type, event_subtype, category,
                            headline_summary, short_summary, detailed_summary,
                            strategic_insight, impact_on_market, impact_on_products, impact_on_customers,
                            impact_on_competitors, impact_on_talent, impact_on_regulation,
                            risk_score, opportunity_score, threat_level, confidence_level,
                            recommended_actions, sentiment, sentiment_score, tags,
                            overall_impact, importance_level, urgency, time_horizon,
                            key_points, recommended_teams, affected_areas, confidence_explanation
                        ) VALUES (
                            %s, %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s, %s,
                            %s, %s, %s, %s
                        ) RETURNING id
                    """, (
                        article_id, company_id, 
                        enriched_article["event_type"], enriched_article["event_subtype"], enriched_article["category"],
                        enriched_article["headline_summary"], enriched_article["short_summary"], enriched_article["detailed_summary"],
                        enriched_article["strategic_insight"], enriched_article["impact_on_market"], enriched_article["impact_on_products"], enriched_article["impact_on_customers"],
                        enriched_article["impact_on_competitors"], enriched_article["impact_on_talent"], enriched_article["impact_on_regulation"],
                        enriched_article["risk_score"], enriched_article["opportunity_score"], enriched_article["threat_level"], enriched_article["confidence_level"],
                        enriched_article["recommended_actions"], enriched_article["sentiment"], enriched_article["sentiment_score"], json.dumps(enriched_article["tags"]),
                        enriched_article.get("overall_impact", 3), enriched_article.get("importance_level", "medium"), enriched_article.get("urgency", "medium"), enriched_article.get("time_horizon", "short_term"),
                        json.dumps(enriched_article.get("key_points", [])), json.dumps(enriched_article.get("recommended_teams", [])), json.dumps(enriched_article.get("affected_areas", [])), enriched_article.get("confidence_explanation", "")
                    ))
                    event_id = cur.fetchone()[0]
                    enriched_article["event_id"] = str(event_id)
                    enriched_article["primary_company_slug"] = slug # Pass slug for downstream if needed
                    
                    conn.commit()
                conn.close()
                
            except Exception as e:
                logger.error("db_write_failed", article_id=article_id, error=str(e))
                # If DB write fails, we should probably not publish to Kafka because downstream expects event_id
                return None

            logger.info("article_enriched_successfully",
                       article_id=article_id,
                       primary_company=enriched_article["primary_company"],
                       event_type=enriched_article["event_type"],
                       risk_score=enriched_article["risk_score"],
                       sentiment=enriched_article["sentiment"],
                       event_id=enriched_article.get("event_id"))
            
            return enriched_article
            
        except Exception as e:
            article_id = cleaned_article.get('article_id', 'unknown')
            logger.error("article_enrichment_error",
                        article_id=article_id,
                        error=str(e),
                        error_type=type(e).__name__)
            return None
    
    async def run(self):
        """Run the service continuously"""
        logger.info("llm_intelligence_service_started")
        
        processed_count = 0
        failed_count = 0
        
        try:
            async for cleaned_article in self.kafka.consume_messages():
                try:
                    # Enrich article
                    enriched_article = self.enrich_article(cleaned_article)
                    
                    if enriched_article:
                        # Publish to Kafka
                        await self.kafka.publish_message(enriched_article)
                        processed_count += 1
                    else:
                        failed_count += 1
                    
                    # Log stats every 5 articles
                    if (processed_count + failed_count) % 5 == 0:
                        success_rate = (processed_count / (processed_count + failed_count)) * 100
                        logger.info("processing_stats",
                                   processed=processed_count,
                                   failed=failed_count,
                                   success_rate=f"{success_rate:.2f}%")
                
                except Exception as e:
                    logger.error("message_processing_error",
                                error=str(e),
                                error_type=type(e).__name__)
                    failed_count += 1
                    continue
        
        except KeyboardInterrupt:
            logger.info("shutting_down",
                       total_processed=processed_count,
                       total_failed=failed_count)
        finally:
            await self.kafka.stop()


async def main():
    """Main entry point"""
    # Validate we have API keys
    if not settings.cerebras_api_keys:
        logger.error("no_cerebras_api_keys_configured")
        print("❌ ERROR: No Cerebras API keys configured!")
        return
    
    service = LLMIntelligenceService()
    await service.kafka.start()
    
    try:
        await service.run()
    finally:
        await service.kafka.stop()


if __name__ == "__main__":
    # Use uvloop for better async performance (optional)
    try:
        import uvloop
        uvloop.install()
        logger.info("uvloop_enabled")
    except ImportError:
        logger.info("uvloop_not_available_using_default_event_loop")
    
    # Run the service
    asyncio.run(main())
