#!/usr/bin/env python3
"""
Script to update all @login_required routes to @jwt_required in news.py
"""

def update_news_routes():
    """Update news.py routes to use JWT authentication"""
    
    file_path = r"c:\Users\ghnun\Projects\merculy-bak\merculy\src\routes\news.py"
    
    # Read the current file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace @login_required with @jwt_required
    content = content.replace('@login_required', '@jwt_required')
    
    # Replace function definitions to include current_user parameter
    # This is a simplified replacement - more complex functions may need manual updates
    
    replacements = [
        # Update function signatures that don't have parameters
        ('def get_news_by_user_interests():', 'def get_news_by_user_interests(current_user):'),
        ('def get_trending_news():', 'def get_trending_news(current_user):'),
        ('def search_news():', 'def search_news(current_user):'),
        ('def generate_newsletter():', 'def generate_newsletter(current_user):'),
        ('def get_user_newsletters():', 'def get_user_newsletters(current_user):'),
        ('def get_newsletter_details(newsletter_id):', 'def get_newsletter_details(current_user, newsletter_id):'),
        ('def delete_newsletter(newsletter_id):', 'def delete_newsletter(current_user, newsletter_id):'),
        ('def get_saved_newsletters():', 'def get_saved_newsletters(current_user):'),
        ('def get_topic_suggestions():', 'def get_topic_suggestions(current_user):'),
    ]
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    # Write the updated content back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Updated {file_path} with JWT authentication")
    print("🔧 Manual updates still needed for complex function signatures and current_user usage")

if __name__ == "__main__":
    update_news_routes()
