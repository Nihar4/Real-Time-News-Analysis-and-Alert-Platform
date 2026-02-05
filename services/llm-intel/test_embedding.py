#!/usr/bin/env python3
"""
Test script for the new embedding model
Tests Qwen/Qwen3-Embedding-0.6B with 1024 dimensions
"""

import sys
import os
sys.path.append('src')

from sentence_transformers import SentenceTransformer
import numpy as np

def test_embedding_model():
    """Test the new embedding model"""
    print("🧪 Testing Qwen/Qwen3-Embedding-0.6B embedding model...")
    
    try:
        # Load the model
        model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")
        print("✅ Model loaded successfully")
        
        # Test texts
        test_texts = [
            "artificial intelligence",
            "AI",
            "machine learning",
            "ML",
            "technology",
            "tech"
        ]
        
        print(f"\n📝 Testing with {len(test_texts)} sample texts...")
        
        # Generate embeddings
        embeddings = model.encode(test_texts, convert_to_numpy=True)
        
        print(f"✅ Generated embeddings: {embeddings.shape}")
        print(f"   - Dimension: {embeddings.shape[1]}")
        print(f"   - Number of texts: {embeddings.shape[0]}")
        
        # Test similarity between related terms
        print("\n🔍 Testing similarity between related terms:")
        
        # AI vs artificial intelligence
        ai_emb = embeddings[0:1]  # artificial intelligence (keep as array)
        ai_short_emb = embeddings[1:2]  # AI (keep as array)
        similarity_ai = model.similarity(ai_emb, ai_short_emb)[0][0]
        print(f"   - 'artificial intelligence' vs 'AI': {similarity_ai:.4f}")
        
        # ML vs machine learning
        ml_emb = embeddings[2:3]  # machine learning (keep as array)
        ml_short_emb = embeddings[3:4]  # ML (keep as array)
        similarity_ml = model.similarity(ml_emb, ml_short_emb)[0][0]
        print(f"   - 'machine learning' vs 'ML': {similarity_ml:.4f}")
        
        # Tech vs technology
        tech_emb = embeddings[4:5]  # technology (keep as array)
        tech_short_emb = embeddings[5:6]  # tech (keep as array)
        similarity_tech = model.similarity(tech_emb, tech_short_emb)[0][0]
        print(f"   - 'technology' vs 'tech': {similarity_tech:.4f}")
        
        # Cross-similarity (should be lower)
        ai_ml_sim = model.similarity(ai_emb, ml_emb)[0][0]
        print(f"   - 'artificial intelligence' vs 'machine learning': {ai_ml_sim:.4f}")
        
        print("\n✅ Embedding model test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing embedding model: {e}")
        return False

if __name__ == "__main__":
    success = test_embedding_model()
    sys.exit(0 if success else 1)
