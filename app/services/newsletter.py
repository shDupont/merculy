"""
Merculy Backend - Newsletter Compilation and Sending Service
"""
from jinja2 import Template
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from typing import List
from datetime import datetime
from flask import current_app
from ..models.user import User, Article, Newsletter, NewsletterFormat
from ..core.config import Config
from .gemini import gemini_service

class NewsletterService:
    def __init__(self):
        self.config = Config()
        self.sendgrid_client = SendGridAPIClient(api_key=self.config.SENDGRID_API_KEY)

    def compile_newsletter_html(self, user: User, articles: List[Article]) -> str:
        """Compile newsletter HTML based on user preferences"""

        # Generate personalized intro
        intro = gemini_service.generate_newsletter_intro(
            user.name,
            len(articles),
            user.preferences.topics
        )

        if user.preferences.newsletter_format == NewsletterFormat.UNICA:
            return self._compile_single_format(user, articles, intro)
        else:
            return self._compile_by_topic_format(user, articles, intro)

    def _compile_single_format(self, user: User, articles: List[Article], intro: str) -> str:
        """Compile newsletter in single format"""
        template = Template('''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Merculy - Sua Newsletter Personalizada</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; border-bottom: 3px solid #007bff; padding-bottom: 20px; margin-bottom: 20px; }
        .intro { color: #666; line-height: 1.6; margin-bottom: 30px; }
        .article { margin-bottom: 25px; padding: 15px; border-left: 4px solid #007bff; background-color: #f8f9fa; }
        .article-title { font-size: 18px; font-weight: bold; color: #333; margin-bottom: 8px; }
        .article-summary { color: #666; line-height: 1.5; margin-bottom: 10px; }
        .article-meta { font-size: 12px; color: #999; }
        .bias-esquerda { border-left-color: #dc3545; }
        .bias-centro { border-left-color: #ffc107; }
        .bias-direita { border-left-color: #28a745; }
        .footer { text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 12px; }
        .read-more { color: #007bff; text-decoration: none; font-weight: bold; }
        .read-more:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="color: #007bff; margin: 0;">📰 Merculy</h1>
            <p style="color: #666; margin: 5px 0 0 0;">{{ date.strftime('%d de %B de %Y') }}</p>
        </div>

        <div class="intro">
            <p>{{ intro }}</p>
        </div>

        {% for article in articles %}
        <div class="article {% if article.bias %}bias-{{ article.bias.value }}{% endif %}">
            <div class="article-title">{{ article.title }}</div>
            <div class="article-summary">{{ article.summary or article.excerpt }}</div>
            <div class="article-meta">
                📰 {{ article.source }} | 🏛️ {{ article.bias.value.title() if article.bias else 'Centro' }} | ⏰ {{ article.published_at.strftime('%H:%M') }}
                <br><a href="{{ article.url }}" class="read-more" target="_blank">Leia mais →</a>
            </div>
        </div>
        {% endfor %}

        <div class="footer">
            <p>Newsletter gerada por Merculy AI</p>
            <p>Você está recebendo este e-mail porque se cadastrou no Merculy.</p>
        </div>
    </div>
</body>
</html>
        ''')

        return template.render(
            user=user,
            articles=articles,
            intro=intro,
            date=datetime.now()
        )

    def _compile_by_topic_format(self, user: User, articles: List[Article], intro: str) -> str:
        """Compile newsletter organized by topics"""
        # Group articles by topic
        articles_by_topic = {}
        for article in articles:
            topic = article.topic
            if topic not in articles_by_topic:
                articles_by_topic[topic] = []
            articles_by_topic[topic].append(article)

        template = Template('''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Merculy - Sua Newsletter por Tópicos</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; border-bottom: 3px solid #007bff; padding-bottom: 20px; margin-bottom: 20px; }
        .intro { color: #666; line-height: 1.6; margin-bottom: 30px; }
        .topic-section { margin-bottom: 35px; }
        .topic-title { font-size: 20px; font-weight: bold; color: #007bff; margin-bottom: 15px; border-bottom: 2px solid #007bff; padding-bottom: 5px; }
        .article { margin-bottom: 20px; padding: 15px; border-left: 4px solid #007bff; background-color: #f8f9fa; }
        .article-title { font-size: 16px; font-weight: bold; color: #333; margin-bottom: 8px; }
        .article-summary { color: #666; line-height: 1.5; margin-bottom: 10px; }
        .article-meta { font-size: 12px; color: #999; }
        .bias-esquerda { border-left-color: #dc3545; }
        .bias-centro { border-left-color: #ffc107; }
        .bias-direita { border-left-color: #28a745; }
        .footer { text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 12px; }
        .read-more { color: #007bff; text-decoration: none; font-weight: bold; }
        .read-more:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="color: #007bff; margin: 0;">📰 Merculy</h1>
            <p style="color: #666; margin: 5px 0 0 0;">{{ date.strftime('%d de %B de %Y') }}</p>
        </div>

        <div class="intro">
            <p>{{ intro }}</p>
        </div>

        {% for topic, topic_articles in articles_by_topic.items() %}
        <div class="topic-section">
            <div class="topic-title">📋 {{ topic }}</div>
            {% for article in topic_articles %}
            <div class="article {% if article.bias %}bias-{{ article.bias.value }}{% endif %}">
                <div class="article-title">{{ article.title }}</div>
                <div class="article-summary">{{ article.summary or article.excerpt }}</div>
                <div class="article-meta">
                    📰 {{ article.source }} | 🏛️ {{ article.bias.value.title() if article.bias else 'Centro' }} | ⏰ {{ article.published_at.strftime('%H:%M') }}
                    <br><a href="{{ article.url }}" class="read-more" target="_blank">Leia mais →</a>
                </div>
            </div>
            {% endfor %}
        </div>
        {% endfor %}

        <div class="footer">
            <p>Newsletter gerada por Merculy AI</p>
            <p>Você está recebendo este e-mail porque se cadastrou no Merculy.</p>
        </div>
    </div>
</body>
</html>
        ''')

        return template.render(
            user=user,
            articles_by_topic=articles_by_topic,
            intro=intro,
            date=datetime.now()
        )

    def send_newsletter(self, user: User, html_content: str, subject: str = None) -> bool:
        """Send newsletter via SendGrid"""
        try:
            if not subject:
                subject = f"📰 Sua Newsletter Merculy - {datetime.now().strftime('%d/%m/%Y')}"

            message = Mail(
                from_email=Email(self.config.SENDGRID_FROM_EMAIL, "Merculy"),
                to_emails=To(user.email, user.name),
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            response = self.sendgrid_client.send(message)

            if response.status_code in [200, 202]:
                current_app.logger.info(f"Newsletter sent successfully to {user.email}")
                return True
            else:
                current_app.logger.error(f"SendGrid error: {response.status_code} - {response.body}")
                return False

        except Exception as e:
            current_app.logger.error(f"Error sending newsletter to {user.email}: {str(e)}")
            return False

    def create_newsletter_record(self, user: User, articles: List[Article], html_content: str) -> Newsletter:
        """Create newsletter record"""
        return Newsletter(
            user_id=user.user_id,
            date=datetime.now(),
            format=user.preferences.newsletter_format,
            articles=articles,
            html_content=html_content,
            sent_at=datetime.now()
        )

# Global service instance
newsletter_service = NewsletterService()
