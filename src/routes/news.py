from flask import Blueprint, request, jsonify
from datetime import datetime
import json

from src.models.cosmos_models import newsletter_service, news_article_service
from src.services.news_service import news_service

from src.services.article_scraper_service import article_scraper
from src.services.gemini_service import gemini_service
from src.services.cosmos_service import cosmos_service
from src.services.jwt_service import jwt_required
from src.config import Config

news_bp = Blueprint('news', __name__)

@news_bp.route('/articles/scrape', methods=['POST'])
def scrape_article_content():
    """Scrape and return the full article content from a given URL."""
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'Missing url in request body'}), 400
    url = data['url']
    try:
        content = article_scraper.scrape_article_content(url)
        if not content:
            return jsonify({'error': 'Could not extract article content'}), 422
        return jsonify({'url': url, 'content': content}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

news_bp = Blueprint('news', __name__)

@news_bp.route('/topics', methods=['GET'])
def get_available_topics():
    """Get list of available news topics from Cosmos DB"""
    try:
        # Get topics from Cosmos DB
        cosmos_topics = cosmos_service.get_available_topics()
        
        if cosmos_topics:
            topics = [topic['id'] for topic in cosmos_topics if topic.get('isActive', True)]
        else:
            # Fallback to config topics if Cosmos DB is not available
            topics = Config.AVAILABLE_TOPICS
        
        # Get sources from Cosmos DB through news_service
        sources = news_service.get_available_sources()
        
        return jsonify({
            'topics': topics,
            'sources': sources
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/sources', methods=['GET'])
def get_available_sources():
    """Get list of available news sources from Cosmos DB"""
    try:
        sources = news_service.get_available_sources()
        return jsonify({
            'sources': sources,
            'count': len(sources)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/topics/detailed', methods=['GET'])
def get_detailed_topics():
    """Get detailed information about available topics from Cosmos DB"""
    try:
        cosmos_topics = cosmos_service.get_available_topics()
        
        if cosmos_topics:
            topics = [
                {
                    'id': topic['id'],
                    'name': topic['name'],
                    'isActive': topic.get('isActive', True),
                    'icon': topic.get('icon', ''),
                    'primary-color': topic.get('primary-color', ''),
                    'secondary-color': topic.get('secondary-color', '')
                }
                for topic in cosmos_topics if topic.get('isActive', True)
            ]
        else:
            # Fallback to config topics if Cosmos DB is not available
            topics = [
                {'id': topic, 'name': topic.title(), 'isActive': True}
                for topic in Config.AVAILABLE_TOPICS
            ]
        
        return jsonify({
            'topics': topics,
            'count': len(topics)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/news/<topic>', methods=['GET'])
@jwt_required
def get_news_by_topic(current_user, topic):
    """Get news articles by topic with user's channel preferences"""
    try:
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 100)  # Max 100 articles
        
        print(f"🔍 [NEWS DEBUG] Getting news for topic '{topic}' for user {current_user.email}")
        
        # Get user's followed channels
        user_channels = current_user.get_followed_channels()
        
        # Convert channel IDs to domains if necessary
        if user_channels:
            # Get all available channels from Cosmos DB
            all_channels = cosmos_service.get_available_channels()
            channel_domains = []
            
            for channel_id in user_channels:
                # Find the corresponding domain for each channel ID
                for channel in all_channels:
                    if channel.get('id') == channel_id and channel.get('isActive', True):
                        channel_domains.append(channel.get('domain'))
                        break
            
            user_channels = channel_domains if channel_domains else None
        
        articles = news_service.get_news_by_topic(topic, limit, user_channels)
        
        # Process articles with AI if available
        processed_articles = []
        for article in articles:
            # Generate summary with Gemini
            if gemini_service.is_available():
                summary = gemini_service.summarize_article(article['title'], article['content'])
                if summary:
                    article['summary'] = summary
                
                # Generate bullet point highlights
                bullet_highlights = gemini_service.generate_bullet_point_highlights(article['title'], article['content'])
                if bullet_highlights:
                    article['bullet_point_highlights'] = bullet_highlights
                
                # Analyze political bias
                bias = gemini_service.analyze_political_bias(article['title'], article['content'])
                article['political_bias'] = bias
            
            processed_articles.append(article)
            
            # Save to Cosmos DB and get the created article with ID
            try:
                created_article = news_article_service.create_article(
                    title=article['title'],
                    content=article['content'],
                    source=article['source'],
                    url=article['url'],
                    topic=topic,
                    image_url=article.get('image_url'),
                    summary=article.get('summary'),
                    bullet_point_highlights=article.get('bullet_point_highlights'),
                    political_bias=article.get('political_bias'),
                    published_at=article['published_at']
                )
                
                # Add the article ID to the response if creation was successful
                if created_article and created_article.id:
                    article['id'] = created_article.id
                    
            except Exception as e:
                print(f"Error saving article to Cosmos DB: {e}")
        
        return jsonify({
            'topic': topic,
            'articles': processed_articles,
            'count': len(processed_articles),
            'sources_used': len(user_channels) if user_channels else 'all_brazilian_sources'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/news/multiple-topics', methods=['POST'])
@jwt_required
def get_news_by_multiple_topics(current_user):
    """Get news articles by multiple topics with intelligent distribution"""
    try:
        data = request.get_json()
        if not data or 'topics' not in data:
            return jsonify({'error': 'Topics list is required in request body'}), 400
        
        topics = data.get('topics', [])
        limit = data.get('limit', 20)
        limit = min(limit, 40)  # Max 100 articles
        
        if not topics or not isinstance(topics, list):
            return jsonify({'error': 'Topics must be a non-empty list'}), 400
        
        print(f"🔍 [NEWS DEBUG] Getting news for multiple topics {topics} for user {current_user.email}")
        
        # Get user's followed channels
        user_channels = current_user.get_followed_channels()
        
        # Convert channel IDs to domains if necessary
        if user_channels:
            # Get all available channels from Cosmos DB
            all_channels = cosmos_service.get_available_channels()
            channel_domains = []
            
            for channel_id in user_channels:
                # Find the corresponding domain for each channel ID
                for channel in all_channels:
                    if channel.get('id') == channel_id and channel.get('isActive', True):
                        channel_domains.append(channel.get('domain'))
                        break
            
            user_channels = channel_domains if channel_domains else None
        
        # Get news by multiple topics
        news_by_topic = news_service.get_news_by_multiple_topics(topics, limit, user_channels)
        
        # Process articles with AI if available
        processed_news_by_topic = {}
        total_articles = 0
        
        for topic, articles in news_by_topic.items():
            processed_articles = []
            
            for article in articles:
                # Generate summary with Gemini
                if gemini_service.is_available():
                    summary = gemini_service.summarize_article(article['title'], article['content'])
                    if summary:
                        article['summary'] = summary
                    
                    # Generate bullet point highlights
                    bullet_highlights = gemini_service.generate_bullet_point_highlights(article['title'], article['content'])
                    if bullet_highlights:
                        article['bullet_point_highlights'] = bullet_highlights
                    
                    # Analyze political bias
                    bias = gemini_service.analyze_political_bias(article['title'], article['content'])
                    article['political_bias'] = bias
                
                processed_articles.append(article)
                
                # Save to Cosmos DB and get the created article with ID
                try:
                    created_article = news_article_service.create_article(
                        title=article['title'],
                        content=article['content'],
                        source=article['source'],
                        url=article['url'],
                        topic=topic,
                        image_url=article.get('image_url'),
                        summary=article.get('summary'),
                        bullet_point_highlights=article.get('bullet_point_highlights'),
                        political_bias=article.get('political_bias'),
                        published_at=article['published_at']
                    )
                    
                    # Add the article ID to the response if creation was successful
                    if created_article and created_article.id:
                        article['id'] = created_article.id
                        
                except Exception as e:
                    print(f"Error saving article to Cosmos DB: {e}")
            
            processed_news_by_topic[topic] = processed_articles
            total_articles += len(processed_articles)
        
        return jsonify({
            'topics': list(processed_news_by_topic.keys()),
            'news_by_topic': processed_news_by_topic,
            'total_articles': total_articles,
            'sources_used': len(user_channels) if user_channels else 'all_brazilian_sources',
            'distribution_info': {
                'requested_topics': len(topics),
                'topics_with_news': len(processed_news_by_topic),
                'requested_limit': limit,
                'actual_total': total_articles
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/news/user-interests', methods=['GET'])
@jwt_required
def get_news_by_user_interests(current_user):
    """Get news based on current user's interests with intelligent distribution"""
    try:
        # Get limit parameter (default 20)
        limit = request.args.get('limit', 20, type=int)
        
        # Debug: Check user interests
        user_interests = current_user.get_interests()
        print(f"[DEBUG] User {current_user.id} interests: {user_interests}")
        print(f"[DEBUG] Is List of Interests {'yes' if isinstance(user_interests, list) else 'no'}")
        
        # Debug: Check user channels
        user_channels = None
        if hasattr(current_user, 'get_followed_channels'):
            user_channels = current_user.get_followed_channels()
            print(f"[DEBUG] User {current_user.id} channels: {user_channels}")
        
        # Get news for current user's interests automatically
        result = news_service.get_news_by_interests(current_user, limit=limit)
        
        print(f"[DEBUG] Result: {result}")
        print(f"[DEBUG] Result type: {type(result)}")
        print(f"[DEBUG] Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict) and 'error' in result:
            return jsonify({
                'error': result['error'],
                'details': result.get('details', ''),
                'debug_info': {
                    'user_interests': user_interests,
                    'user_channels': user_channels,
                    'limit': limit
                }
            }), 400
            
        return jsonify({
            'success': True,
            'data': result,
            'user_id': current_user.id,
            'timestamp': datetime.now().isoformat(),
            'debug_info': {
                'user_interests': user_interests,
                'user_channels': user_channels,
                'limit': limit,
                'data_keys': list(result.keys()) if isinstance(result, dict) else [],
                'total_articles': sum(len(articles) for articles in result.values()) if isinstance(result, dict) else 0
            }
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Exception in get_news_by_user_interests: {str(e)}")
        return jsonify({
            'error': str(e),
            'debug_info': {
                'user_id': getattr(current_user, 'id', 'unknown'),
                'user_interests': getattr(current_user, 'interests', 'unknown'),
                'limit': limit
            }
        }), 500

@news_bp.route('/trending', methods=['GET'])
@jwt_required
def get_trending_news(current_user):
    """Get trending news"""
    try:
        limit = request.args.get('limit', 20, type=int)
        articles = news_service.get_trending_news(limit)
        
        return jsonify({
            'articles': articles,
            'count': len(articles)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/search', methods=['GET'])
@jwt_required
def search_news(current_user):
    """Search for news articles"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        limit = request.args.get('limit', 20, type=int)
        articles = news_service.search_news(query, limit)
        
        return jsonify({
            'query': query,
            'articles': articles,
            'count': len(articles)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/newsletter/generate', methods=['POST'])
@jwt_required
def generate_newsletter(current_user):
    """Generate personalized newsletter for current user based on article references"""
    try:        
        # Get user interests
        user_interests = current_user.get_interests()
        if not user_interests:
            user_interests = ['tecnologia', 'política', 'economia']  # Default interests
        
        # Get user's followed channels
        user_channels = current_user.get_followed_channels()
        
        # Convert channel IDs to domains if necessary
        if user_channels:
            # Get all available channels from Cosmos DB
            all_channels = cosmos_service.get_available_channels()
            channel_domains = []
            
            for channel_id in user_channels:
                # Find the corresponding domain for each channel ID
                for channel in all_channels:
                    if channel.get('id') == channel_id and channel.get('isActive', True):
                        channel_domains.append(channel.get('domain'))
                        break
            
            user_channels = channel_domains if channel_domains else None
        
        # Get news for user interests using the updated method
        news_by_topic = news_service.get_news_by_interests(current_user, limit=25)
        
        if not news_by_topic:
            return jsonify({'error': 'No news articles found for user interests'}), 404
        
        if current_user.newsletter_format == 'single':
            # Generate single newsletter with all topics
            all_articles = []
            article_ids = []
            
            # Process articles and collect IDs
            for topic_articles in news_by_topic.values():
                for article in topic_articles:
                    # Process article with AI if available
                    if gemini_service.is_available():
                        summary = gemini_service.summarize_article(article['title'], article['content'])
                        if summary:
                            article['summary'] = summary
                        
                        # Generate bullet point highlights
                        bullet_highlights = gemini_service.generate_bullet_point_highlights(article['title'], article['content'])
                        if bullet_highlights:
                            article['bullet_point_highlights'] = bullet_highlights
                        
                        # Analyze political bias
                        bias = gemini_service.analyze_political_bias(article['title'], article['content'])
                        article['political_bias'] = bias
                    
                    all_articles.append(article)
                    
                    # Save to Cosmos DB and collect article ID
                    try:
                        created_article = news_article_service.create_article(
                            title=article['title'],
                            content=article['content'],
                            source=article['source'],
                            url=article['url'],
                            topic=article.get('topic', 'geral'),
                            image_url=article.get('image_url', ''),
                            summary=article.get('summary'),
                            bullet_point_highlights=article.get('bullet_point_highlights'),
                            political_bias=article.get('political_bias'),
                            published_at=article.get('published_at')
                        )
                        
                        if created_article and created_article.id:
                            article_ids.append(created_article.id)
                            
                    except Exception as e:
                        print(f"Error saving article to Cosmos DB: {e}")
            
            # Create newsletter using the new model
            newsletter = newsletter_service.create_newsletter(
                user_id=current_user.id,
                title=f"Newsletter Personalizada - {datetime.now().strftime('%d/%m/%Y')}",
                topic='personalizada',
                articles=article_ids
            )
            
            if not newsletter:
                return jsonify({'error': 'Failed to create newsletter'}), 500
            
            return jsonify({
                'message': 'Newsletter generated successfully',
                'newsletter_id': newsletter.id,
                'newsletter': newsletter.to_dict(),
                'format': 'single'
            }), 201
            
        else:
            # Generate newsletter by topic
            newsletters = []
            for topic, articles in news_by_topic.items():
                article_ids = []
                
                # Process articles and collect IDs for this topic
                for article in articles:
                    # Process article with AI if available
                    if gemini_service.is_available():
                        summary = gemini_service.summarize_article(article['title'], article['content'])
                        if summary:
                            article['summary'] = summary
                        
                        # Generate bullet point highlights
                        bullet_highlights = gemini_service.generate_bullet_point_highlights(article['title'], article['content'])
                        if bullet_highlights:
                            article['bullet_point_highlights'] = bullet_highlights
                        
                        # Analyze political bias
                        bias = gemini_service.analyze_political_bias(article['title'], article['content'])
                        article['political_bias'] = bias
                    
                    # Save to Cosmos DB and collect article ID
                    try:
                        created_article = news_article_service.create_article(
                            title=article['title'],
                            content=article['content'],
                            source=article['source'],
                            url=article['url'],
                            topic=topic,
                            image_url=article.get('image_url', ''),
                            summary=article.get('summary'),
                            bullet_point_highlights=article.get('bullet_point_highlights'),
                            political_bias=article.get('political_bias'),
                            published_at=article.get('published_at')
                        )
                        
                        if created_article and created_article.id:
                            article_ids.append(created_article.id)
                            
                    except Exception as e:
                        print(f"Error saving article to Cosmos DB: {e}")
                
                # Create newsletter for this topic
                newsletter = newsletter_service.create_newsletter(
                    user_id=current_user.id,
                    title=f"Newsletter {topic.title()} - {datetime.now().strftime('%d/%m/%Y')}",
                    topic=topic,
                    articles=article_ids
                )
                
                if newsletter:
                    newsletters.append(newsletter)
            
            return jsonify({
                'message': 'Newsletters generated successfully',
                'newsletters': [{'id': n.id, 'data': n.to_dict()} for n in newsletters],
                'format': 'by_topic'
            }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/newsletters', methods=['GET'])
@jwt_required
def get_user_newsletters(current_user):
    """Get user's newsletters"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        topic = request.args.get('topic')
        
        # Calculate offset for pagination
        limit = per_page
        all_newsletters = newsletter_service.get_user_newsletters(current_user.id, limit=100)

        all_returned_newsletters = []
        for current_news in all_newsletters:
            newsletter_data = newsletter_service.get_newsletter_with_articles(current_news.id, current_user.id)
            
            newsletter = newsletter_data['newsletter']
            articles = newsletter_data['articles']
            all_returned_newsletters.append({
                "newsletter": newsletter.to_dict(),
                "articles": [article.to_dict() for article in articles]
            })
        
        # Filter by topic if specified
        if topic:
            all_newsletters = [n for n in all_newsletters if n.topic == topic]
        
        # Calculate pagination
        total = len(all_newsletters)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        newsletters = all_newsletters
        
        total_pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'newsletters': all_returned_newsletters,
            'total': total,
            'pages': total_pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/newsletters/<newsletter_id>/save', methods=['POST'])
@jwt_required
def save_newsletter(newsletter_id):
    """Save/unsave a newsletter - Deprecated: New model doesn't use save functionality"""
    try:
        # This endpoint is deprecated with the new newsletter model
        # Newsletters are now article reference collections, not saved content
        return jsonify({
            'message': 'Save functionality deprecated with new newsletter model',
            'newsletter_id': newsletter_id,
            'note': 'Newsletters are now article reference collections'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/newsletters/<newsletter_id>', methods=['GET'])
@jwt_required
def get_newsletter_details(current_user, newsletter_id):
    """Get newsletter details with populated articles"""
    try:
        newsletter_data = newsletter_service.get_newsletter_with_articles(newsletter_id, current_user.id)
        
        if not newsletter_data:
            return jsonify({'error': 'Newsletter not found'}), 404
        
        newsletter = newsletter_data['newsletter']
        articles = newsletter_data['articles']
        
        return jsonify({
            'newsletter': newsletter.to_dict(),
            'articles': [article.to_dict() for article in articles],
            'article_count': len(articles)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/newsletters/<newsletter_id>', methods=['DELETE'])
@jwt_required
def delete_newsletter(current_user, newsletter_id):
    """Delete a newsletter"""
    try:
        success = newsletter_service.delete_newsletter(newsletter_id, current_user.id)
        
        if not success:
            return jsonify({'error': 'Newsletter not found or deletion failed'}), 404
        
        return jsonify({
            'message': 'Newsletter deleted successfully',
            'newsletter_id': newsletter_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/newsletters/saved', methods=['GET'])
@jwt_required
def get_saved_newsletters(current_user):
    """Get user's newsletters - 'Saved' concept deprecated with new model"""
    try:
        # With the new model, all newsletters are simply user's newsletters
        # The concept of 'saved' vs 'unsaved' is no longer relevant
        newsletters = newsletter_service.get_user_newsletters(current_user.id)
        
        return jsonify({
            'newsletters': [n.to_dict() for n in newsletters],
            'count': len(newsletters),
            'note': 'All newsletters are now persistent article collections'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/preferences/topics', methods=['GET'])
@jwt_required
def get_topic_suggestions(current_user):
    """Get topic suggestions based on user history"""
    try:
        # Get user's reading history
        newsletters = newsletter_service.get_user_newsletters(current_user.id, limit=20)
        history = [n.title for n in newsletters]
        
        if gemini_service.is_available():
            suggestions = gemini_service.generate_topic_suggestions(history)
        else:
            # Get available topics from Cosmos DB
            cosmos_topics = cosmos_service.get_available_topics()
            if cosmos_topics:
                active_topics = [topic['id'] for topic in cosmos_topics if topic.get('isActive', True)]
                suggestions = active_topics[:5]
            else:
                suggestions = Config.AVAILABLE_TOPICS[:5]
        
        # Get all available topics from Cosmos DB
        cosmos_topics = cosmos_service.get_available_topics()
        if cosmos_topics:
            all_topics = [topic['id'] for topic in cosmos_topics if topic.get('isActive', True)]
        else:
            all_topics = Config.AVAILABLE_TOPICS
        
        return jsonify({
            'suggested_topics': suggestions,
            'all_topics': all_topics
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/articles/<article_id>/analyze', methods=['POST'])
@jwt_required
def analyze_article(article_id):
    """Analyze article for fake news detection"""
    try:
        # Get article from Cosmos DB
        articles = news_article_service.get_articles_by_topic("", limit=1)  # This needs improvement
        article = None
        
        # Find article by ID (this is a simplified approach)
        if cosmos_service.is_available():
            try:
                container = cosmos_service.database.get_container_client('news_articles')
                article_doc = container.read_item(item=article_id, partition_key=None)
                if article_doc:
                    article = {
                        'title': article_doc.get('title'),
                        'content': article_doc.get('content')
                    }
            except:
                pass
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        if gemini_service.is_available():
            analysis = gemini_service.detect_fake_news(article['title'], article['content'])
        else:
            analysis = {
                "score": 5,
                "indicators": ["Análise não disponível"],
                "recommendation": "review"
            }
        
        return jsonify({
            'article_id': article_id,
            'analysis': analysis
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

