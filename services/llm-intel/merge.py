#!/usr/bin/env python3
"""
Script to merge duplicate topics in the database
Run this once to clean up existing duplicates before using the improved matcher
"""

import asyncio
import asyncpg
import structlog
from typing import List, Dict, Set, Tuple
from collections import defaultdict

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# Database configuration
DB_CONFIG = {
    "host": "postgres",
    "port": 5432,
    "database": "newsinsight_db",
    "user": "newsinsight_user",
    "password": "newsinsight_password_2024"
}

# Duplicate groups to merge (canonical_name -> list of duplicates)
DUPLICATE_GROUPS = [
    # Privacy-related
    ['privacy', 'data privacy', 'user privacy', 'digital privacy', 'personal data'],
    
    # AI-related
    ['ai', 'artificial intelligence'],
    ['machine learning', 'ml'],
    
    # Tech-related
    ['tech', 'technology'],
    
    # Photo/Image-related
    ['photo editing', 'image editing'],
    ['photo enhancement', 'image enhancement'],
    ['photo', 'photograph', 'image'],
    
    # Social media
    ['social media', 'social network'],
    
    # Mobile-related
    ['smartphone', 'mobile phone', 'mobile device'],
    ['mobile app', 'mobile application'],
    
    # Cloud-related
    ['cloud storage', 'cloud upload'],
    
    # Organization-related
    ['photo organization', 'photo library', 'image organization'],
]

class DuplicateMerger:
    """Merge duplicate topics in database"""
    
    def __init__(self):
        self.conn = None
    
    async def connect(self):
        """Connect to database"""
        self.conn = await asyncpg.connect(
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            database=DB_CONFIG["database"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        logger.info("database_connected")
    
    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
            logger.info("database_closed")
    
    async def find_topic_by_name(self, name: str) -> Dict:
        """Find topic by canonical name (case-insensitive)"""
        row = await self.conn.fetchrow("""
            SELECT id, canonical_name, display_name, searchable_terms, 
                   category, article_count, is_active
            FROM topics
            WHERE LOWER(canonical_name) = LOWER($1)
            AND is_active = TRUE
            LIMIT 1
        """, name)
        
        if row:
            return dict(row)
        return None
    
    async def find_duplicate_group(self, names: List[str]) -> List[Dict]:
        """Find all topics matching any name in the group"""
        topics = []
        for name in names:
            topic = await self.find_topic_by_name(name)
            if topic:
                topics.append(topic)
        return topics
    
    async def merge_topics(self, primary_topic_id: int, duplicate_topic_ids: List[int]):
        """
        Merge duplicate topics into primary topic
        - Update all article_topics references
        - Merge searchable_terms
        - Update article_count
        - Mark duplicates as inactive
        """
        if not duplicate_topic_ids:
            return
        
        logger.info("merging_topics",
                   primary_id=primary_topic_id,
                   duplicate_ids=duplicate_topic_ids,
                   count=len(duplicate_topic_ids))
        
        try:
            # Start transaction
            async with self.conn.transaction():
                # 1. Collect all searchable terms from duplicates
                duplicate_terms = await self.conn.fetch("""
                    SELECT DISTINCT unnest(searchable_terms) as term
                    FROM topics
                    WHERE id = ANY($1::int[])
                """, duplicate_topic_ids)
                
                all_terms = [row['term'] for row in duplicate_terms]
                
                # 2. Update article_topics - point all references to primary topic
                for dup_id in duplicate_topic_ids:
                    # Update existing mappings
                    updated = await self.conn.execute("""
                        UPDATE article_topics
                        SET topic_id = $1,
                            match_method = match_method || '_merged'
                        WHERE topic_id = $2
                        AND article_id NOT IN (
                            SELECT article_id 
                            FROM article_topics 
                            WHERE topic_id = $1
                        )
                    """, primary_topic_id, dup_id)
                    
                    # Delete duplicate mappings (same article, both topics)
                    deleted = await self.conn.execute("""
                        DELETE FROM article_topics
                        WHERE topic_id = $1
                        AND article_id IN (
                            SELECT article_id 
                            FROM article_topics 
                            WHERE topic_id = $2
                        )
                    """, dup_id, primary_topic_id)
                    
                    logger.info("article_mappings_updated",
                               duplicate_id=dup_id,
                               updated=updated,
                               deleted=deleted)
                
                # 3. Merge searchable terms into primary topic
                if all_terms:
                    await self.conn.execute("""
                        UPDATE topics
                        SET searchable_terms = array(
                            SELECT DISTINCT unnest(searchable_terms || $2::text[])
                        ),
                        updated_at = NOW()
                        WHERE id = $1
                    """, primary_topic_id, all_terms)
                    
                    logger.info("searchable_terms_merged",
                               primary_id=primary_topic_id,
                               added_terms=len(all_terms))
                
                # 4. Update article_count
                new_count = await self.conn.fetchval("""
                    SELECT COUNT(DISTINCT article_id)
                    FROM article_topics
                    WHERE topic_id = $1
                """, primary_topic_id)
                
                await self.conn.execute("""
                    UPDATE topics
                    SET article_count = $2,
                        updated_at = NOW()
                    WHERE id = $1
                """, primary_topic_id, new_count)
                
                logger.info("article_count_updated",
                           primary_id=primary_topic_id,
                           new_count=new_count)
                
                # 5. Mark duplicates as inactive
                await self.conn.execute("""
                    UPDATE topics
                    SET is_active = FALSE,
                        updated_at = NOW()
                    WHERE id = ANY($1::int[])
                """, duplicate_topic_ids)
                
                logger.info("duplicates_marked_inactive",
                           duplicate_ids=duplicate_topic_ids)
            
            logger.info("merge_completed_successfully",
                       primary_id=primary_topic_id,
                       merged_count=len(duplicate_topic_ids))
        
        except Exception as e:
            logger.error("merge_failed",
                        primary_id=primary_topic_id,
                        duplicate_ids=duplicate_topic_ids,
                        error=str(e))
            raise
    
    async def process_duplicate_groups(self):
        """Process all duplicate groups"""
        total_merged = 0
        
        for group in DUPLICATE_GROUPS:
            logger.info("processing_group", group=group)
            
            # Find all topics in this group
            topics = await self.find_duplicate_group(group)
            
            if len(topics) <= 1:
                logger.info("no_duplicates_found", group=group)
                continue
            
            # Sort by article_count (highest first) to choose primary
            topics.sort(key=lambda x: x['article_count'], reverse=True)
            
            primary = topics[0]
            duplicates = topics[1:]
            
            duplicate_ids = [t['id'] for t in duplicates]
            
            logger.info("merging_group",
                       primary_name=primary['canonical_name'],
                       primary_id=primary['id'],
                       primary_count=primary['article_count'],
                       duplicates=[t['canonical_name'] for t in duplicates],
                       duplicate_ids=duplicate_ids)
            
            # Merge duplicates into primary
            await self.merge_topics(primary['id'], duplicate_ids)
            
            total_merged += len(duplicate_ids)
        
        logger.info("all_groups_processed", total_merged=total_merged)
        return total_merged
    
    async def find_similar_topics(self) -> List[Tuple[str, str, int]]:
        """Find potentially similar topics using fuzzy matching"""
        # Get all active topics
        topics = await self.conn.fetch("""
            SELECT canonical_name, article_count
            FROM topics
            WHERE is_active = TRUE
            ORDER BY article_count DESC
        """)
        
        similar_pairs = []
        
        # Use PostgreSQL's similarity function if available
        for i, topic1 in enumerate(topics):
            for topic2 in topics[i+1:]:
                similarity_score = await self.conn.fetchval("""
                    SELECT similarity($1, $2)
                """, topic1['canonical_name'], topic2['canonical_name'])
                
                if similarity_score and similarity_score > 0.6:
                    similar_pairs.append((
                        topic1['canonical_name'],
                        topic2['canonical_name'],
                        int(similarity_score * 100)
                    ))
        
        # Sort by similarity
        similar_pairs.sort(key=lambda x: x[2], reverse=True)
        
        return similar_pairs

async def main():
    """Main execution"""
    merger = DuplicateMerger()
    
    try:
        await merger.connect()
        
        # Get initial stats
        total_topics = await merger.conn.fetchval("""
            SELECT COUNT(*) FROM topics WHERE is_active = TRUE
        """)
        
        total_mappings = await merger.conn.fetchval("""
            SELECT COUNT(*) FROM article_topics
        """)
        
        logger.info("initial_stats",
                   total_topics=total_topics,
                   total_mappings=total_mappings)
        
        print(f"\n{'='*60}")
        print(f"DUPLICATE TOPIC MERGER")
        print(f"{'='*60}")
        print(f"Active topics before: {total_topics}")
        print(f"Article-topic mappings before: {total_mappings}")
        print(f"{'='*60}\n")
        
        # Process duplicate groups
        merged_count = await merger.process_duplicate_groups()
        
        # Get final stats
        final_topics = await merger.conn.fetchval("""
            SELECT COUNT(*) FROM topics WHERE is_active = TRUE
        """)
        
        final_mappings = await merger.conn.fetchval("""
            SELECT COUNT(*) FROM article_topics
        """)
        
        logger.info("final_stats",
                   final_topics=final_topics,
                   final_mappings=final_mappings,
                   topics_merged=merged_count)
        
        print(f"\n{'='*60}")
        print(f"MERGE COMPLETED")
        print(f"{'='*60}")
        print(f"Active topics after: {final_topics}")
        print(f"Topics merged: {merged_count}")
        print(f"Topics reduced by: {total_topics - final_topics}")
        print(f"Article-topic mappings after: {final_mappings}")
        print(f"{'='*60}\n")
        
        # Find other potentially similar topics
        print("\nFinding other potentially similar topics...")
        similar = await merger.find_similar_topics()
        
        if similar:
            print(f"\nFound {len(similar)} potentially similar topic pairs:")
            print(f"(Review these manually)\n")
            for topic1, topic2, score in similar[:20]:  # Show top 20
                print(f"  {score}% - '{topic1}' <-> '{topic2}'")
        
    except Exception as e:
        logger.error("merge_failed", error=str(e))
        print(f"\n❌ Error: {e}")
    finally:
        await merger.close()

if __name__ == "__main__":
    asyncio.run(main())