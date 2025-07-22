"""
Merculy Backend - Scheduled Jobs
"""
from datetime import datetime, time
import pytz
from flask import current_app
from ..services.cosmos import cosmos_service
from ..services.news import news_service
from ..services.gemini import gemini_service
from ..services.newsletter import newsletter_service

def register_jobs(scheduler):
    """Register all scheduled jobs"""

    @scheduler.task('cron', id='daily_newsletters', hour=5, minute=0)
    def send_daily_newsletters():
        """Send daily newsletters to all active users"""
        with scheduler.app.app_context():
            try:
                current_app.logger.info("Starting daily newsletter job")

                # Initialize Cosmos DB
                if not cosmos_service.client:
                    cosmos_service.initialize()

                # Get all active users
                users = cosmos_service.list_active_users()
                current_app.logger.info(f"Found {len(users)} active users")

                success_count = 0
                error_count = 0

                for user in users:
                    try:
                        # Check if user should receive newsletter today
                        if should_send_newsletter_today(user):
                            # Fetch and curate news for user
                            articles = news_service.fetch_curated_news(
                                user.preferences.topics + user.preferences.custom_topics
                            )

                            if not articles:
                                current_app.logger.warning(f"No articles found for user {user.email}")
                                continue

                            # Enhance articles with AI analysis
                            enhanced_articles = gemini_service.enhance_articles(articles)

                            # Compile newsletter HTML
                            html_content = newsletter_service.compile_newsletter_html(
                                user, enhanced_articles
                            )

                            # Send newsletter
                            if newsletter_service.send_newsletter(user, html_content):
                                # Save newsletter record
                                newsletter_record = newsletter_service.create_newsletter_record(
                                    user, enhanced_articles, html_content
                                )
                                cosmos_service.save_newsletter(newsletter_record)
                                success_count += 1
                            else:
                                error_count += 1

                    except Exception as e:
                        current_app.logger.error(f"Error processing user {user.email}: {str(e)}")
                        error_count += 1
                        continue

                current_app.logger.info(
                    f"Daily newsletter job completed. Success: {success_count}, Errors: {error_count}"
                )

            except Exception as e:
                current_app.logger.error(f"Fatal error in daily newsletter job: {str(e)}")

    @scheduler.task('cron', id='morning_newsletters', hour=8, minute=0)
    def send_morning_newsletters():
        """Send morning newsletters (8AM)"""
        send_newsletters_by_hour(8)

    @scheduler.task('cron', id='afternoon_newsletters', hour=14, minute=0)
    def send_afternoon_newsletters():
        """Send afternoon newsletters (2PM)"""
        send_newsletters_by_hour(14)

    @scheduler.task('cron', id='evening_newsletters', hour=18, minute=0)
    def send_evening_newsletters():
        """Send evening newsletters (6PM)"""
        send_newsletters_by_hour(18)

def send_newsletters_by_hour(target_hour: int):
    """Send newsletters to users configured for specific hour"""
    with current_app.app_context():
        try:
            current_app.logger.info(f"Starting newsletter job for hour {target_hour}")

            # Initialize Cosmos DB
            if not cosmos_service.client:
                cosmos_service.initialize()

            # Get users configured for this hour
            users = cosmos_service.list_active_users()
            target_users = [
                user for user in users 
                if user.preferences.delivery_hour == target_hour and should_send_newsletter_today(user)
            ]

            current_app.logger.info(f"Found {len(target_users)} users for hour {target_hour}")

            success_count = 0
            error_count = 0

            for user in target_users:
                try:
                    # Fetch and curate news
                    articles = news_service.fetch_curated_news(
                        user.preferences.topics + user.preferences.custom_topics
                    )

                    if not articles:
                        continue

                    # Enhance with AI
                    enhanced_articles = gemini_service.enhance_articles(articles)

                    # Compile and send
                    html_content = newsletter_service.compile_newsletter_html(
                        user, enhanced_articles
                    )

                    if newsletter_service.send_newsletter(user, html_content):
                        newsletter_record = newsletter_service.create_newsletter_record(
                            user, enhanced_articles, html_content
                        )
                        cosmos_service.save_newsletter(newsletter_record)
                        success_count += 1
                    else:
                        error_count += 1

                except Exception as e:
                    current_app.logger.error(f"Error processing user {user.email}: {str(e)}")
                    error_count += 1
                    continue

            current_app.logger.info(
                f"Newsletter job for hour {target_hour} completed. Success: {success_count}, Errors: {error_count}"
            )

        except Exception as e:
            current_app.logger.error(f"Fatal error in newsletter job for hour {target_hour}: {str(e)}")

def should_send_newsletter_today(user) -> bool:
    """Check if user should receive newsletter today"""
    try:
        # Get current day in user's timezone
        user_tz = pytz.timezone(user.preferences.delivery_timezone)
        now = datetime.now(user_tz)
        current_day = now.strftime('%A').lower()

        # Map English days to user's configured days
        day_mapping = {
            'monday': 'monday',
            'tuesday': 'tuesday', 
            'wednesday': 'wednesday',
            'thursday': 'thursday',
            'friday': 'friday',
            'saturday': 'saturday',
            'sunday': 'sunday'
        }

        # Check if current day is in user's configured days
        return current_day in [day_mapping.get(day, day) for day in user.preferences.frequency_days]

    except Exception as e:
        current_app.logger.error(f"Error checking schedule for user {user.email}: {str(e)}")
        return False
