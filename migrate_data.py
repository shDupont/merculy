# Data Migration Script for SQLite to Cosmos DB

import sqlite3
import json
from datetime import datetime
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(__file__))

from src.services.user_service import user_service
from src.services.cosmos_service import cosmos_service

def check_cosmos_connection():
    """Check if Cosmos DB is available"""
    if not cosmos_service.is_available():
        print("❌ Cosmos DB is not available. Please check your configuration.")
        print("Required environment variables:")
        print("  - COSMOS_ENDPOINT")
        print("  - COSMOS_KEY")
        print("  - COSMOS_DATABASE_NAME")
        return False
    print("✅ Cosmos DB connection successful")
    return True

def check_sqlite_database():
    """Check if SQLite database exists"""
    db_path = 'src/database/app.db'
    if not os.path.exists(db_path):
        print(f"❌ SQLite database not found: {db_path}")
        return False
    print("✅ SQLite database found")
    return True

def migrate_users():
    """Migrate users from SQLite to Cosmos DB"""
    print("🔄 Starting user migration...")
    
    try:
        # Connect to SQLite
        conn = sqlite3.connect('src/database/app.db')
        cursor = conn.cursor()
        
        # Check if user table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        if not cursor.fetchone():
            print("ℹ️  No user table found in SQLite database")
            conn.close()
            return 0
        
        # Get all users from SQLite
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()
        
        if not users:
            print("ℹ️  No users found in SQLite database")
            conn.close()
            return 0
        
        # Get column names
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        migrated_count = 0
        failed_count = 0
        
        for user_row in users:
            user_data = dict(zip(columns, user_row))
            
            try:
                # Convert interests and delivery_frequency from JSON strings
                interests = []
                if user_data.get('interests'):
                    try:
                        interests = json.loads(user_data['interests'])
                    except json.JSONDecodeError:
                        interests = []
                
                delivery_schedule = {
                    'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
                    'time': '08:00'
                }
                if user_data.get('delivery_frequency'):
                    try:
                        delivery_schedule = json.loads(user_data['delivery_frequency'])
                    except json.JSONDecodeError:
                        pass
                
                # Check if user already exists in Cosmos DB
                existing_user = user_service.get_user_by_email(user_data['email'])
                if existing_user:
                    print(f"⚠️  User already exists: {user_data['email']}")
                    continue
                
                # Create user in Cosmos DB
                cosmos_user = user_service.create_user(
                    email=user_data['email'],
                    name=user_data['name'],
                    google_id=user_data.get('google_id'),
                    facebook_id=user_data.get('facebook_id'),
                    interests=interests,
                    newsletter_format=user_data.get('newsletter_format', 'single'),
                    delivery_schedule=delivery_schedule,
                    is_active=bool(user_data.get('is_active', True))
                )
                
                if cosmos_user:
                    # Update password hash if it exists
                    updates = {}
                    if user_data.get('password_hash'):
                        updates['password_hash'] = user_data['password_hash']
                    
                    # Update timestamps
                    if user_data.get('created_at'):
                        updates['created_at'] = user_data['created_at']
                    if user_data.get('last_login'):
                        updates['last_login'] = user_data['last_login']
                    
                    if updates:
                        user_service.update_user(cosmos_user.id, **updates)
                    
                    migrated_count += 1
                    print(f"✅ Migrated user: {user_data['email']}")
                else:
                    failed_count += 1
                    print(f"❌ Failed to migrate user: {user_data['email']}")
                    
            except Exception as e:
                failed_count += 1
                print(f"❌ Error migrating user {user_data.get('email', 'unknown')}: {str(e)}")
        
        conn.close()
        
        print(f"\n📊 Migration Summary:")
        print(f"   ✅ Successfully migrated: {migrated_count} users")
        print(f"   ❌ Failed migrations: {failed_count} users")
        print(f"   📋 Total processed: {len(users)} users")
        
        return migrated_count
        
    except Exception as e:
        print(f"❌ Error during user migration: {str(e)}")
        return 0

def migrate_newsletters():
    """Migrate newsletters from SQLite to Cosmos DB"""
    print("\n🔄 Starting newsletter migration...")
    
    try:
        # Connect to SQLite
        conn = sqlite3.connect('src/database/app.db')
        cursor = conn.cursor()
        
        # Check if newsletter table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='newsletter'")
        if not cursor.fetchone():
            print("ℹ️  No newsletter table found in SQLite database")
            conn.close()
            return 0
        
        # Get all newsletters from SQLite
        cursor.execute("SELECT * FROM newsletter")
        newsletters = cursor.fetchall()
        
        if not newsletters:
            print("ℹ️  No newsletters found in SQLite database")
            conn.close()
            return 0
        
        # Get column names
        cursor.execute("PRAGMA table_info(newsletter)")
        columns = [column[1] for column in cursor.fetchall()]
        
        migrated_count = 0
        failed_count = 0
        
        for newsletter_row in newsletters:
            newsletter_data = dict(zip(columns, newsletter_row))
            
            try:
                # Create newsletter document for Cosmos DB
                newsletter_doc = {
                    'user_id': str(newsletter_data['user_id']),
                    'title': newsletter_data['title'],
                    'content': newsletter_data['content'],
                    'topic': newsletter_data.get('topic'),
                    'created_at': newsletter_data.get('created_at', datetime.utcnow().isoformat()),
                    'sent_at': newsletter_data.get('sent_at'),
                    'is_saved': bool(newsletter_data.get('is_saved', False))
                }
                
                # Save to Cosmos DB
                result = cosmos_service.create_newsletter(newsletter_doc)
                
                if result:
                    migrated_count += 1
                    print(f"✅ Migrated newsletter: {newsletter_data['title'][:50]}...")
                else:
                    failed_count += 1
                    print(f"❌ Failed to migrate newsletter: {newsletter_data['title'][:50]}...")
                    
            except Exception as e:
                failed_count += 1
                print(f"❌ Error migrating newsletter: {str(e)}")
        
        conn.close()
        
        print(f"\n📊 Newsletter Migration Summary:")
        print(f"   ✅ Successfully migrated: {migrated_count} newsletters")
        print(f"   ❌ Failed migrations: {failed_count} newsletters")
        print(f"   📋 Total processed: {len(newsletters)} newsletters")
        
        return migrated_count
        
    except Exception as e:
        print(f"❌ Error during newsletter migration: {str(e)}")
        return 0

def verify_migration():
    """Verify the migration was successful"""
    print("\n🔍 Verifying migration...")
    
    try:
        users = user_service.get_all_users()
        print(f"📊 Total users in Cosmos DB: {len(users)}")
        
        if users:
            print("\n👥 Sample users:")
            for user in users[:3]:  # Show first 3 users
                print(f"   • {user.email} (Interests: {len(user.get_interests())} topics)")
        
        # Check newsletters if cosmos service has the method
        try:
            newsletters = cosmos_service.get_user_newsletters("sample", limit=1)
            print(f"📰 Newsletters accessible: ✅")
        except Exception:
            print(f"📰 Newsletters accessible: ⚠️  (may not have data)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during verification: {str(e)}")
        return False

def main():
    """Main migration function"""
    print("🚀 Starting Merculy SQLite to Cosmos DB Migration")
    print("=" * 60)
    
    # Check prerequisites
    if not check_cosmos_connection():
        return False
    
    if not check_sqlite_database():
        return False
    
    # Perform migration
    user_count = migrate_users()
    newsletter_count = migrate_newsletters()
    
    # Verify migration
    verification_success = verify_migration()
    
    print("\n" + "=" * 60)
    print("🎉 Migration completed!")
    print(f"📊 Summary:")
    print(f"   👥 Users migrated: {user_count}")
    print(f"   📰 Newsletters migrated: {newsletter_count}")
    print(f"   ✅ Verification: {'Passed' if verification_success else 'Failed'}")
    
    if user_count > 0 or newsletter_count > 0:
        print("\n📋 Next steps:")
        print("   1. Test your application: python src/main.py")
        print("   2. Verify API endpoints work correctly")
        print("   3. Consider backing up old SQLite database")
        
    return True

if __name__ == "__main__":
    main()
