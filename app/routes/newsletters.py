"""
Merculy Backend - Newsletter Management Routes
"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from ..auth.decorators import requires_auth, requires_role
from ..services.cosmos import cosmos_service
from ..services.news import news_service
from ..services.gemini import gemini_service
from ..services.newsletter import newsletter_service
from ..models.user import NewsletterRequest
from pydantic import ValidationError

newsletters_bp = Blueprint('newsletters', __name__)

@newsletters_bp.route('/newsletter/latest', methods=['GET'])
@requires_auth
def get_latest_newsletter():
    """Get user's latest newsletter"""
    try:
        newsletters = cosmos_service.get_user_newsletters(g.current_user['user_id'], limit=1)

        if not newsletters:
            return jsonify({'message': 'No newsletters found'}), 404

        latest = newsletters[0]
        return jsonify({
            'id': latest.id,
            'date': latest.date.isoformat(),
            'format': latest.format.value,
            'articles_count': len(latest.articles),
            'sent_at': latest.sent_at.isoformat() if latest.sent_at else None
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@newsletters_bp.route('/newsletter/history', methods=['GET'])
@requires_auth
def get_newsletter_history():
    """Get user's newsletter history"""
    try:
        limit = request.args.get('limit', 10, type=int)
        limit = min(limit, 50)  # Max 50 newsletters

        newsletters = cosmos_service.get_user_newsletters(g.current_user['user_id'], limit=limit)

        newsletters_data = []
        for newsletter in newsletters:
            newsletters_data.append({
                'id': newsletter.id,
                'date': newsletter.date.isoformat(),
                'format': newsletter.format.value,
                'articles_count': len(newsletter.articles),
                'sent_at': newsletter.sent_at.isoformat() if newsletter.sent_at else None,
                'articles': [
                    {
                        'title': article.title,
                        'source': article.source,
                        'topic': article.topic,
                        'bias': article.bias.value if article.bias else None,
                        'url': article.url
                    }
                    for article in newsletter.articles
                ]
            })

        return jsonify({
            'newsletters': newsletters_data,
            'total': len(newsletters_data)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@newsletters_bp.route('/newsletter/send-test', methods=['POST'])
@requires_auth
def send_test_newsletter():
    """Send a test newsletter immediately"""
    try:
        data = request.get_json() or {}

        # Validate request
        try:
            newsletter_request = NewsletterRequest(**data)
        except ValidationError as e:
            return jsonify({'error': 'Validation error', 'details': e.errors()}), 400

        # Get user
        user = cosmos_service.get_user(g.current_user['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Fetch and curate news
        articles = news_service.fetch_curated_news(
            user.preferences.topics + user.preferences.custom_topics,
            days_back=2  # Get more articles for testing
        )

        if not articles:
            return jsonify({'error': 'No articles found for your topics'}), 404

        # Enhance with AI
        enhanced_articles = gemini_service.enhance_articles(articles[:10])  # Limit for testing

        # Compile newsletter HTML
        html_content = newsletter_service.compile_newsletter_html(user, enhanced_articles)

        # Send newsletter if requested
        if newsletter_request.immediate_send:
            subject = f"🧪 Test Newsletter - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            success = newsletter_service.send_newsletter(user, html_content, subject)

            if success:
                # Save newsletter record
                newsletter_record = newsletter_service.create_newsletter_record(
                    user, enhanced_articles, html_content
                )
                cosmos_service.save_newsletter(newsletter_record)

                return jsonify({
                    'message': 'Test newsletter sent successfully',
                    'articles_count': len(enhanced_articles),
                    'sent_at': datetime.now().isoformat()
                })
            else:
                return jsonify({'error': 'Failed to send newsletter'}), 500
        else:
            # Just return the preview
            return jsonify({
                'message': 'Test newsletter compiled successfully',
                'articles_count': len(enhanced_articles),
                'preview': html_content[:500] + '...',  # First 500 chars as preview
                'articles': [
                    {
                        'title': article.title,
                        'source': article.source,
                        'topic': article.topic,
                        'bias': article.bias.value if article.bias else None,
                        'summary': article.summary
                    }
                    for article in enhanced_articles
                ]
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@newsletters_bp.route('/newsletter/preview', methods=['POST'])
@requires_auth
def preview_newsletter():
    """Generate newsletter preview without sending"""
    try:
        # Get user
        user = cosmos_service.get_user(g.current_user['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Get topics from request or user preferences
        data = request.get_json() or {}
        topics = data.get('topics', user.preferences.topics + user.preferences.custom_topics)

        if not topics:
            return jsonify({'error': 'No topics specified'}), 400

        # Fetch articles
        articles = news_service.fetch_curated_news(topics, days_back=1)

        if not articles:
            return jsonify({'error': 'No articles found for specified topics'}), 404

        # Enhance first 5 articles for preview
        preview_articles = gemini_service.enhance_articles(articles[:5])

        return jsonify({
            'articles_count': len(preview_articles),
            'topics_covered': list(set(article.topic for article in preview_articles)),
            'articles': [
                {
                    'title': article.title,
                    'source': article.source,
                    'topic': article.topic,
                    'bias': article.bias.value if article.bias else None,
                    'summary': article.summary,
                    'confidence_score': article.confidence_score,
                    'published_at': article.published_at.isoformat(),
                    'url': article.url
                }
                for article in preview_articles
            ]
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@newsletters_bp.route('/newsletter/stats', methods=['GET'])
@requires_auth
def get_newsletter_stats():
    """Get newsletter statistics for user"""
    try:
        # Get last 30 days of newsletters
        newsletters = cosmos_service.get_user_newsletters(g.current_user['user_id'], limit=30)

        if not newsletters:
            return jsonify({
                'total_newsletters': 0,
                'last_30_days': 0,
                'topics_distribution': {},
                'average_articles_per_newsletter': 0
            })

        # Calculate stats
        last_30_days = datetime.now() - timedelta(days=30)
        recent_newsletters = [n for n in newsletters if n.date >= last_30_days]

        # Topics distribution
        topics_count = {}
        total_articles = 0

        for newsletter in newsletters:
            for article in newsletter.articles:
                topic = article.topic
                topics_count[topic] = topics_count.get(topic, 0) + 1
                total_articles += 1

        return jsonify({
            'total_newsletters': len(newsletters),
            'last_30_days': len(recent_newsletters),
            'topics_distribution': topics_count,
            'average_articles_per_newsletter': round(total_articles / len(newsletters), 1) if newsletters else 0,
            'last_newsletter': newsletters[0].date.isoformat() if newsletters else None
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
