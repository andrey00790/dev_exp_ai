#!/usr/bin/env python3
"""
Analytics Database Migration Script

Creates all necessary tables for analytics functionality.
"""

import sys
import os
import psycopg2
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def run_migration():
    """Run analytics database migration"""
    try:
        print("🚀 Starting analytics database migration...")
        
        # Database settings (using defaults for local development)
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'ai_assistant'),
            'user': os.getenv('DB_USER', 'ai_assistant_user'),
            'password': os.getenv('DB_PASSWORD', 'ai_assistant_password')
        }
        
        print(f"📡 Connecting to database: {db_config['database']}@{db_config['host']}:{db_config['port']}")
        
        # Connect to database
        conn = psycopg2.connect(**db_config)
        
        print("✅ Database connection established")
        
        # Read SQL migration file
        sql_file = project_root / "scripts" / "create_analytics_tables.sql"
        
        if not sql_file.exists():
            print(f"❌ SQL file not found: {sql_file}")
            return False
            
        with open(sql_file, 'r') as f:
            sql = f.read()
        
        print("📝 Executing analytics tables migration...")
        
        # Execute migration
        with conn.cursor() as cur:
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
            
            for i, statement in enumerate(statements):
                if statement:
                    print(f"  📋 Executing statement {i+1}/{len(statements)}")
                    cur.execute(statement)
        
        conn.commit()
        conn.close()
        
        print("✅ Analytics tables created successfully!")
        print("📊 Phase 4.2 Analytics infrastructure ready!")
        print("")
        print("Created tables:")
        print("  📈 usage_metrics - Track feature usage and performance")
        print("  💰 cost_metrics - Monitor LLM and service costs")
        print("  ⚡ performance_metrics - System performance monitoring")
        print("  👤 user_behavior_metrics - User interaction analytics")
        print("  📊 aggregated_metrics - Pre-computed analytics data")
        print("  💡 insight_reports - Automated insights and recommendations")
        print("")
        print("Next steps:")
        print("  1. Restart your application to load analytics endpoints")
        print("  2. Access analytics dashboard at /analytics")
        print("  3. Start collecting metrics automatically")
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        print("💡 Hint: Make sure PostgreSQL is running and database exists")
        return False
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1) 