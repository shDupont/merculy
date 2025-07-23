from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import json

from src.models.user import db, Newsletter, NewsArticle
from src.services.news_service import news_service
from src.services.gemini_service import gemini_service
from src.services.cosmos_service import cosmos_service
from src.config import Config

news_bp = Blueprint('news', __name__)

@news_bp.route('/topics', methods=['GET'])
def get_available_topics():
    """Get list of available news topics"""
    return jsonify({
        'topics': Config.AVAILABLE_TOPICS,
        'sources': news_service.get_available_sources()
    }), 200

@news_bp.route('/news/<topic>', methods=['GET'])
@login_required
def get_news_by_topic(topic):
    """Get news articles by topic"""
    try:
        limit = request.args.get('limit', 20, type=int)
        limit = min(limit, 100)  # Max 100 articles
        
        articles = news_service.get_news_by_topic(topic, limit)
        
        # Process articles with AI if available
        processed_articles = []
        for article in articles:
            # Generate summary with Gemini
            if gemini_service.is_available():
                summary = gemini_service.summarize_article(article['title'], article['content'])
                if summary:
                    article['summary'] = summary
                
                # Analyze political bias
                bias = gemini_service.analyze_political_bias(article['title'], article['content'])
                article['political_bias'] = bias
            
            processed_articles.append(article)
            
            # Save to database
            news_article = NewsArticle(
                title=article['title'],
                content=article['content'],
                summary=article.get('summary', ''),
                source=article['source'],
                url=article['url'],
                topic=topic,
                political_bias=article.get('political_bias'),
                published_at=datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
            )
            
            try:
                db.session.add(news_article)
                db.session.commit()
            except:
                db.session.rollback()
            
            # Also save to Cosmos DB if available
            if cosmos_service.is_available():
                cosmos_service.create_news_article(article)
        
        return jsonify({
            'topic': topic,
            'articles': processed_articles,
            'count': len(processed_articles)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/trending', methods=['GET'])
@login_required
def get_trending_news():
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
@login_required
def search_news():
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
@login_required
def generate_newsletter():
    """Generate personalized newsletter for current user"""
    try:
        data = request.get_json() or {}
        
        # Get user interests
        user_interests = current_user.get_interests()
        if not user_interests:
            user_interests = ['tecnologia', 'política', 'economia']  # Default interests
        
        # Get news for user interests
        news_by_topic = news_service.get_news_by_interests(user_interests, limit_per_topic=5)
        
        if not news_by_topic:
            return jsonify({'error': 'No news articles found for user interests'}), 404
        
        newsletter_content = ""
        
        if current_user.newsletter_format == 'single':
            # Generate single newsletter with all topics
            all_articles = []
            for topic_articles in news_by_topic.values():
                all_articles.extend(topic_articles)
            
            if gemini_service.is_available():
                newsletter_content = gemini_service.generate_newsletter_content(user_interests, all_articles)
            
            if not newsletter_content:
                # Fallback content generation
                newsletter_content = f"<h1>Newsletter Personalizada - {datetime.now().strftime('%d/%m/%Y')}</h1>"
                for topic, articles in news_by_topic.items():
                    newsletter_content += f"<h2>{topic.title()}</h2>"
                    for article in articles[:3]:
                        newsletter_content += f"""
                        <div style="margin-bottom: 20px;">
                            <h3>{article['title']}</h3>
                            <p>{article['summary']}</p>
                            <p><small>Fonte: {article['source']}</small></p>
                        </div>
                        """
            
            # Save newsletter
            newsletter = Newsletter(
                user_id=current_user.id,
                title=f"Newsletter Personalizada - {datetime.now().strftime('%d/%m/%Y')}",
                content=newsletter_content,
                topic='personalizada'
            )
            
        else:
            # Generate newsletter by topic
            newsletters = []
            for topic, articles in news_by_topic.items():
                if gemini_service.is_available():
                    topic_content = gemini_service.generate_newsletter_by_topic(topic, articles)
                else:
                    # Fallback content
                    topic_content = f"<h2>{topic.title()}</h2>"
                    for article in articles:
                        topic_content += f"""
                        <div style="margin-bottom: 15px;">
                            <h3>{article['title']}</h3>
                            <p>{article['summary']}</p>
                            <p><small>Fonte: {article['source']}</small></p>
                        </div>
                        """
                
                newsletter = Newsletter(
                    user_id=current_user.id,
                    title=f"Newsletter {topic.title()} - {datetime.now().strftime('%d/%m/%Y')}",
                    content=topic_content,
                    topic=topic
                )
                newsletters.append(newsletter)
            
            # Save all newsletters
            for newsletter in newsletters:
                db.session.add(newsletter)
            
            db.session.commit()
            
            return jsonify({
                'message': 'Newsletters generated successfully',
                'newsletters': [n.to_dict() for n in newsletters],
                'format': 'by_topic'
            }), 201
        
        db.session.add(newsletter)
        db.session.commit()
        
        # Also save to Cosmos DB if available
        if cosmos_service.is_available():
            cosmos_service.create_newsletter({
                'user_id': current_user.id,
                'title': newsletter.title,
                'content': newsletter.content,
                'topic': newsletter.topic
            })
        
        return jsonify({
            'message': 'Newsletter generated successfully',
            'newsletter': newsletter.to_dict(),
            'format': 'single'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@news_bp.route('/newsletters', methods=['GET'])
@login_required
def get_user_newsletters():
    """Get user's newsletters"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        topic = request.args.get('topic')
        
        query = Newsletter.query.filter_by(user_id=current_user.id)
        
        if topic:
            query = query.filter_by(topic=topic)
        
        newsletters = query.order_by(Newsletter.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'newsletters': [n.to_dict() for n in newsletters.items],
            'total': newsletters.total,
            'pages': newsletters.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/newsletters/<int:newsletter_id>/save', methods=['POST'])
@login_required
def save_newsletter(newsletter_id):
    """Save/unsave a newsletter"""
    try:
        newsletter = Newsletter.query.filter_by(
            id=newsletter_id, 
            user_id=current_user.id
        ).first()
        
        if not newsletter:
            return jsonify({'error': 'Newsletter not found'}), 404
        
        newsletter.is_saved = not newsletter.is_saved
        db.session.commit()
        
        # Also update in Cosmos DB if available
        if cosmos_service.is_available():
            cosmos_service.save_newsletter(str(newsletter_id), current_user.id)
        
        return jsonify({
            'message': f"Newsletter {'saved' if newsletter.is_saved else 'unsaved'} successfully",
            'newsletter': newsletter.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@news_bp.route('/newsletters/saved', methods=['GET'])
@login_required
def get_saved_newsletters():
    """Get user's saved newsletters"""
    try:
        newsletters = Newsletter.query.filter_by(
            user_id=current_user.id,
            is_saved=True
        ).order_by(Newsletter.created_at.desc()).all()
        
        return jsonify({
            'newsletters': [n.to_dict() for n in newsletters],
            'count': len(newsletters)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/preferences/topics', methods=['GET'])
@login_required
def get_topic_suggestions():
    """Get topic suggestions based on user history"""
    try:
        # Get user's reading history
        newsletters = Newsletter.query.filter_by(user_id=current_user.id).limit(20).all()
        history = [n.title for n in newsletters]
        
        if gemini_service.is_available():
            suggestions = gemini_service.generate_topic_suggestions(history)
        else:
            suggestions = Config.AVAILABLE_TOPICS[:5]
        
        return jsonify({
            'suggested_topics': suggestions,
            'all_topics': Config.AVAILABLE_TOPICS
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@news_bp.route('/articles/<int:article_id>/analyze', methods=['POST'])
@login_required
def analyze_article(article_id):
    """Analyze article for fake news detection"""
    try:
        article = NewsArticle.query.get(article_id)
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        if gemini_service.is_available():
            analysis = gemini_service.detect_fake_news(article.title, article.content)
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

