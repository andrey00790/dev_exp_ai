#!/usr/bin/env python3
"""
Test script for Qdrant integration - memory mode
"""

import os
import sys
import asyncio
from typing import List

# Add project root to path
sys.path.insert(0, '/Users/a.kotenev/PycharmProjects/dev_exp_ai')

from vectorstore.qdrant_client import get_qdrant_client
from vectorstore.collections import get_collection_manager, CollectionType, DocumentMetadata
from vectorstore.embeddings import get_embeddings_service

async def test_qdrant_integration():
    """Test Qdrant integration with collections and embeddings."""
    print("🚀 Testing Qdrant Integration...")
    
    # Force memory mode
    os.environ["QDRANT_USE_MEMORY"] = "true"
    
    # 1. Test Qdrant client
    print("\n1️⃣ Testing Qdrant Client")
    client = get_qdrant_client()
    health = client.health_check()
    print(f"   Health: {health}")
    
    if health['status'] != 'healthy':
        print("❌ Qdrant client unhealthy, aborting")
        return False
    
    # 2. Test collection creation
    print("\n2️⃣ Testing Collection Creation")
    collection_manager = get_collection_manager()
    
    # Initialize collections
    init_results = await collection_manager.initialize_collections()
    print(f"   Collections initialized: {init_results}")
    
    # 3. Test embeddings service
    print("\n3️⃣ Testing Embeddings Service")
    embeddings_service = get_embeddings_service()
    
    # Test text embedding
    test_text = "This is a test document about artificial intelligence and machine learning."
    embedding_result = await embeddings_service.embed_text(test_text)
    
    if embedding_result:
        print(f"   ✅ Generated embedding: {len(embedding_result.vector)} dimensions")
        print(f"   Token count: {embedding_result.token_count}")
        print(f"   Cost estimate: ${embedding_result.cost_estimate:.6f}")
    else:
        print("   ❌ Failed to generate embedding")
        return False
    
    # 4. Test document indexing
    print("\n4️⃣ Testing Document Indexing")
    
    # Create test document metadata
    test_metadata = DocumentMetadata(
        doc_id="test_doc_001",
        title="Test AI Document",
        source="test_system",
        source_type=CollectionType.DOCUMENTS,
        author="test_user",
        content_type="text/markdown",
        tags=["ai", "ml", "test"]
    )
    
    # Index document
    index_success = await collection_manager.index_document(
        text=test_text,
        metadata=test_metadata,
        collection_type=CollectionType.DOCUMENTS
    )
    
    print(f"   Document indexing: {'✅ SUCCESS' if index_success else '❌ FAILED'}")
    
    # 5. Test document search
    print("\n5️⃣ Testing Document Search")
    
    search_query = "artificial intelligence machine learning"
    search_results = await collection_manager.search_documents(
        query=search_query,
        collection_types=[CollectionType.DOCUMENTS],
        limit=5
    )
    
    print(f"   Search results count: {len(search_results)}")
    
    if search_results:
        for i, result in enumerate(search_results[:2], 1):
            print(f"   Result {i}:")
            print(f"      Score: {result['score']:.4f}")
            print(f"      Doc ID: {result['payload'].get('doc_id', 'N/A')}")
            print(f"      Title: {result['payload'].get('title', 'N/A')}")
    
    # 6. Test collection stats
    print("\n6️⃣ Testing Collection Stats")
    stats = collection_manager.get_collection_stats()
    print("   Collection statistics:")
    for collection_name, stat in stats.items():
        print(f"      {collection_name}: {stat}")
    
    # 7. Test multiple document types
    print("\n7️⃣ Testing Multiple Document Types")
    
    test_documents = [
        {
            "text": "Confluence page about project documentation and wiki management.",
            "metadata": DocumentMetadata(
                doc_id="confluence_001",
                title="Project Documentation",
                source="confluence",
                source_type=CollectionType.CONFLUENCE,
                tags=["docs", "wiki"]
            )
        },
        {
            "text": "JIRA issue about bug fix in authentication system.",
            "metadata": DocumentMetadata(
                doc_id="jira_001", 
                title="Auth Bug Fix",
                source="jira",
                source_type=CollectionType.JIRA,
                tags=["bug", "auth"]
            )
        },
        {
            "text": "GitLab repository with Python code for data processing.",
            "metadata": DocumentMetadata(
                doc_id="gitlab_001",
                title="Data Processing Service",
                source="gitlab",
                source_type=CollectionType.GITLAB,
                tags=["python", "data"]
            )
        }
    ]
    
    for doc in test_documents:
        success = await collection_manager.index_document(
            text=doc["text"],
            metadata=doc["metadata"],
            collection_type=doc["metadata"].source_type
        )
        print(f"   Indexed {doc['metadata'].source_type.value}: {'✅' if success else '❌'}")
    
    # 8. Test cross-collection search
    print("\n8️⃣ Testing Cross-Collection Search")
    
    search_query = "documentation python data"
    all_results = await collection_manager.search_documents(
        query=search_query,
        collection_types=None,  # Search all collections
        limit=3
    )
    
    print(f"   Cross-collection search results: {len(all_results)}")
    
    for i, result in enumerate(all_results, 1):
        print(f"   Result {i}:")
        print(f"      Collection: {result['collection_type']}")
        print(f"      Score: {result['score']:.4f}")
        print(f"      Title: {result['payload'].get('title', 'N/A')}")
    
    print("\n🎉 Qdrant Integration Test Complete!")
    return True

def main():
    """Run the Qdrant integration test."""
    print("=" * 60)
    print("🔍 QDRANT INTEGRATION TEST")
    print("=" * 60)
    
    try:
        success = asyncio.run(test_qdrant_integration())
        
        if success:
            print("\n✅ ALL TESTS PASSED!")
            print("🚀 Qdrant integration is working correctly")
        else:
            print("\n❌ SOME TESTS FAILED!")
            print("🔧 Check the errors above")
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 