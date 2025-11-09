#!/usr/bin/env python
"""
Script to create MongoDB text indexes for product search functionality.
This script should be run once to set up the necessary indexes for optimal search performance.

Usage:
    python setup_search_indexes.py
"""

import os
import sys
import django
from pymongo import TEXT, ASCENDING

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from products.models import Product, Brand


def create_product_search_indexes():
    """
    Create text indexes for Product model to enable full-text search.
    
    Text indexes will be created on:
    - name.vi, name.en, name.ja
    - description.vi, description.en, description.ja
    - tags
    """
    print("Creating text indexes for Product collection...")
    
    try:
        # Get the MongoDB collection
        collection = Product._get_collection()
        
        # Drop existing text index if it exists
        try:
            existing_indexes = collection.index_information()
            for index_name, index_info in existing_indexes.items():
                # Check if it's a text index
                if any(field[1] == 'text' for field in index_info.get('key', [])):
                    print(f"Dropping existing text index: {index_name}")
                    collection.drop_index(index_name)
        except Exception as e:
            print(f"Note: Could not drop existing text index: {e}")
        
        # Create new text index
        # MongoDB text indexes support multilingual fields
        index_spec = [
            ("name.vi", TEXT),
            ("name.en", TEXT),
            ("name.ja", TEXT),
            ("description.vi", TEXT),
            ("description.en", TEXT),
            ("description.ja", TEXT),
            ("tags", TEXT)
        ]
        
        # Create the index with specific weights to prioritize name over description
        result = collection.create_index(
            index_spec,
            name="product_search_text_index",
            weights={
                "name.vi": 10,
                "name.en": 10,
                "name.ja": 10,
                "description.vi": 5,
                "description.en": 5,
                "description.ja": 5,
                "tags": 7
            },
            default_language="none"  # Disable language-specific stemming
        )
        
        print(f"✓ Text index created successfully: {result}")
        
        # Also ensure we have regular indexes for filtering
        print("\nEnsuring additional indexes for filtering...")
        
        # Index for brand filtering
        if "brand_1" not in collection.index_information():
            collection.create_index([("brand", ASCENDING)], name="brand_1")
            print("✓ Brand index created")
        
        # Index for category filtering
        if "category_1" not in collection.index_information():
            collection.create_index([("category", ASCENDING)], name="category_1")
            print("✓ Category index created")
        
        # Index for status filtering
        if "status_1" not in collection.index_information():
            collection.create_index([("status", ASCENDING)], name="status_1")
            print("✓ Status index created")
        
        # Index for stock filtering
        if "stock_1" not in collection.index_information():
            collection.create_index([("stock", ASCENDING)], name="stock_1")
            print("✓ Stock index created")
        
        # Compound index for common queries (status + stock)
        if "status_1_stock_1" not in collection.index_information():
            collection.create_index(
                [("status", ASCENDING), ("stock", ASCENDING)],
                name="status_1_stock_1"
            )
            print("✓ Status + Stock compound index created")
        
        print("\n✓ All indexes created successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Error creating indexes: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_brand_search_indexes():
    """
    Create text indexes for Brand model to enable autocomplete on brands.
    """
    print("\nCreating text indexes for Brand collection...")
    
    try:
        # Get the MongoDB collection
        collection = Brand._get_collection()
        
        # Drop existing text index if it exists
        try:
            existing_indexes = collection.index_information()
            for index_name, index_info in existing_indexes.items():
                if any(field[1] == 'text' for field in index_info.get('key', [])):
                    print(f"Dropping existing text index: {index_name}")
                    collection.drop_index(index_name)
        except Exception as e:
            print(f"Note: Could not drop existing text index: {e}")
        
        # Create text index on brand names
        index_spec = [
            ("name.vi", TEXT),
            ("name.en", TEXT),
            ("name.ja", TEXT)
        ]
        
        result = collection.create_index(
            index_spec,
            name="brand_search_text_index",
            weights={
                "name.vi": 10,
                "name.en": 10,
                "name.ja": 10
            },
            default_language="none"
        )
        
        print(f"✓ Brand text index created successfully: {result}")
        return True
        
    except Exception as e:
        print(f"✗ Error creating brand indexes: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_indexes():
    """
    Verify that all indexes were created successfully.
    """
    print("\n" + "="*60)
    print("VERIFYING INDEXES")
    print("="*60)
    
    try:
        # Verify Product indexes
        product_collection = Product._get_collection()
        product_indexes = product_collection.index_information()
        
        print("\nProduct Collection Indexes:")
        for index_name, index_info in product_indexes.items():
            print(f"  - {index_name}: {index_info.get('key', [])}")
        
        # Verify Brand indexes
        brand_collection = Brand._get_collection()
        brand_indexes = brand_collection.index_information()
        
        print("\nBrand Collection Indexes:")
        for index_name, index_info in brand_indexes.items():
            print(f"  - {index_name}: {index_info.get('key', [])}")
        
        print("\n✓ Index verification complete!")
        
    except Exception as e:
        print(f"✗ Error verifying indexes: {e}")


def main():
    """
    Main function to set up all search indexes.
    """
    print("="*60)
    print("MONGODB SEARCH INDEX SETUP")
    print("="*60)
    print("\nThis script will create text indexes for:")
    print("  - Product collection (name, description, tags)")
    print("  - Brand collection (name)")
    print("\nThese indexes will improve search performance significantly.")
    print("-"*60)
    
    # Create Product indexes
    product_success = create_product_search_indexes()
    
    # Create Brand indexes
    brand_success = create_brand_search_indexes()
    
    # Verify all indexes
    verify_indexes()
    
    # Final summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    if product_success and brand_success:
        print("✓ All indexes created successfully!")
        print("\nYour search functionality is now optimized.")
        print("\nAPI Endpoints ready:")
        print("  - GET /api/products/autocomplete?q=<query>")
        print("  - GET /api/products/search?q=<query>")
    else:
        print("✗ Some indexes failed to create. Please check the errors above.")
        sys.exit(1)
    
    print("="*60)


if __name__ == "__main__":
    main()

