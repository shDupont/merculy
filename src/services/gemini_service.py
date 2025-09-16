import requests
import json
import threading
from typing import List, Dict, Optional
from src.config import Config

class GeminiService:
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent"
    
    def is_available(self):
        """Check if Gemini API is available"""
        return self.api_key is not None
    
    def _make_request(self, prompt: str) -> Optional[str]:
        """Make request to Gemini API"""
        if not self.is_available():
            return None
        
        try:
            headers = {
                'Content-Type': 'application/json',
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }]
            }
            
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    return result['candidates'][0]['content']['parts'][0]['text']
            
            print(f"Gemini API error: {response.status_code} - {response.text}")
            return None
            
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return None
    
    def summarize_article(self, title: str, content: str) -> Optional[str]:
        """Generate a summary of a news article (max 3 lines)"""
        prompt = f"""
        Resuma o seguinte artigo de notícias em no máximo 3 linhas, mantendo as informações mais importantes:

        Título: {title}
        Conteúdo: {content}

        Resumo:
        """
        
        return self._make_request(prompt)
    
    def generate_bullet_point_highlights(self, title: str, content: str) -> Optional[List[str]]:
        """Generate bullet point highlights for a news article"""
        prompt = f"""
        Crie exatamente 3 frases destacando os principais aspectos do seguinte artigo de notícias.
        Cada bullet point deve ser uma frase concisa e informativa.
        
        Título: {title}
        Conteúdo: {content}
        
        Responda APENAS com os 3 frases, uma por linha, sem marcação de lista:
        """
        
        result = self._make_request(prompt)
        if result:
            # Parse the bullet points from the response
            lines = [line.strip() for line in result.split('\n') if line.strip()]
            bullet_points = []
            
            for line in lines:
                # Ensure it starts with bullet point
                if line.startswith('• ') or line.startswith('- ') or line.startswith('* '):
                    bullet_points.append(line[2:])
                elif line:
                    bullet_points.append(line)
            
            # Return exactly 3 bullet points
            return bullet_points[:3] if len(bullet_points) >= 3 else bullet_points
        
        return None
    
    def analyze_political_bias(self, title: str, content: str) -> Optional[str]:
        """Analyze political bias of a news article"""
        prompt = f"""
        Analise o viés político do seguinte artigo de notícias e classifique como 'esquerda', 'centro' ou 'direita'.
        Considere apenas o conteúdo e a linguagem utilizada, não a fonte.

        Título: {title}
        Conteúdo: {content}

        Responda apenas com uma das três opções: esquerda, centro, direita
        """
        
        result = self._make_request(prompt)
        if result:
            result = result.lower().strip()
            if 'esquerda' in result:
                return 'esquerda'
            elif 'direita' in result:
                return 'direita'
            else:
                return 'centro'
        return 'centro'  # Default fallback
    
    def analyze_comprehensive_bias(self, article_obj):
        """
        Perform comprehensive political bias analysis by searching for related articles
        and analyzing their bias. This function runs asynchronously.
        
        Args:
            article_obj: CosmosNewsArticle object
        """
        def _async_analysis():
            try:
                from src.services.news_service import news_service
                from src.models.cosmos_models import related_source_service
                from src.services.cosmos_service import cosmos_service
                
                print(f"[BIAS ANALYSIS] Starting analysis for article: {article_obj.id}")
                
                # Update status to generating
                cosmos_service.update_article_bias_status(article_obj.id, 'generating')
                
                # Search for related articles using the first 4 words of the title
                title_words = article_obj.title.split()[:4]
                search_query = ' '.join(title_words)
                print(f"[BIAS ANALYSIS] Search query: '{search_query}' (from title: '{article_obj.title}')")
                related_articles = news_service.search_news(search_query, limit=3)
                
                if not related_articles:
                    print(f"[BIAS ANALYSIS] No related articles found for: {article_obj.title}")
                    cosmos_service.update_article_bias_status(article_obj.id, 'error')
                    return
                
                # Filter out articles from the same source to ensure diversity
                diverse_articles = []
                for article in related_articles:
                    if article.get('source', '').lower() != article_obj.source.lower():
                        diverse_articles.append(article)
                    if len(diverse_articles) >= 8:  # Limit to 8 diverse sources
                        break
                
                if not diverse_articles:
                    print(f"[BIAS ANALYSIS] No diverse sources found for: {article_obj.title}")
                    cosmos_service.update_article_bias_status(article_obj.id, 'error')
                    return
                
                # Analyze each related article for political bias
                related_sources_created = 0
                for related_article in diverse_articles:
                    try:
                        # Get the first paragraph as news quote
                        content = related_article.get('content', '')
                        paragraphs = content.split('\n')
                        news_quote = paragraphs[0] if paragraphs else content[:200]
                        
                        # Analyze political bias
                        bias = self.analyze_political_bias(
                            related_article.get('title', ''),
                            content[:400]
                        )
                        
                        # Create related source record
                        related_source = related_source_service.create_related_source(
                            article_id=article_obj.id,
                            title=related_article.get('title', ''),
                            political_bias=bias,
                            published_at=related_article.get('published_at', ''),
                            news_quote=news_quote,
                            source=related_article.get('source', '')
                        )
                        
                        if related_source:
                            related_sources_created += 1
                            print(f"[BIAS ANALYSIS] Created related source {related_sources_created}: {bias}")
                            
                    except Exception as e:
                        print(f"[BIAS ANALYSIS] Error processing related article: {e}")
                        continue
                
                # Update status based on results
                if related_sources_created > 0:
                    cosmos_service.update_article_bias_status(article_obj.id, 'available')
                    print(f"[BIAS ANALYSIS] Completed analysis for article: {article_obj.id} with {related_sources_created} sources")
                else:
                    cosmos_service.update_article_bias_status(article_obj.id, 'error')
                    print(f"[BIAS ANALYSIS] Failed to create any related sources for: {article_obj.id}")
                
            except Exception as e:
                print(f"[BIAS ANALYSIS] Error in comprehensive analysis: {e}")
                try:
                    cosmos_service.update_article_bias_status(article_obj.id, 'error')
                except:
                    pass
        
        # Run the analysis in a separate thread (async)
        thread = threading.Thread(target=_async_analysis)
        thread.daemon = True
        thread.start()
        print(f"[BIAS ANALYSIS] Started async analysis thread for article: {article_obj.id}")

    def generate_newsletter_content(self, user_interests: List[str], articles: List[Dict]) -> Optional[str]:
        """Generate personalized newsletter content based on user interests and articles"""
        if not articles:
            return None
        
        interests_text = ", ".join(user_interests) if user_interests else "notícias gerais"
        
        articles_text = ""
        for i, article in enumerate(articles[:10], 1):  # Limit to 10 articles
            articles_text += f"""
            {i}. Título: {article.get('title', '')}
               Resumo: {article.get('summary', article.get('content', '')[:200])}
               Fonte: {article.get('source', '')}
               Tópico: {article.get('topic', '')}
            """
        
        prompt = f"""
        Crie uma newsletter personalizada em português brasileiro com base nos seguintes interesses do usuário: {interests_text}

        Artigos disponíveis:
        {articles_text}

        Instruções:
        1. Organize o conteúdo de forma atrativa e profissional
        2. Priorize artigos relacionados aos interesses do usuário
        3. Inclua um título chamativo para a newsletter
        4. Agrupe artigos por tópicos quando possível
        5. Mantenha um tom informativo mas envolvente
        6. Inclua uma breve introdução e conclusão
        7. Formate em HTML simples para melhor apresentação

        Newsletter:
        """
        
        return self._make_request(prompt)
    
    def generate_newsletter_by_topic(self, topic: str, articles: List[Dict]) -> Optional[str]:
        """Generate newsletter content focused on a specific topic"""
        if not articles:
            return None
        
        articles_text = ""
        for i, article in enumerate(articles[:8], 1):  # Limit to 8 articles per topic
            articles_text += f"""
            {i}. Título: {article.get('title', '')}
               Resumo: {article.get('summary', article.get('content', '')[:200])}
               Fonte: {article.get('source', '')}
            """
        
        prompt = f"""
        Crie uma seção de newsletter focada no tópico "{topic}" em português brasileiro.

        Artigos sobre {topic}:
        {articles_text}

        Instruções:
        1. Crie um título atrativo para a seção
        2. Organize os artigos de forma lógica
        3. Inclua uma breve introdução sobre o tópico
        4. Mantenha um tom informativo e profissional
        5. Formate em HTML simples
        6. Destaque as notícias mais relevantes

        Seção da Newsletter:
        """
        
        return self._make_request(prompt)
    
    def detect_fake_news(self, title: str, content: str) -> Dict[str, any]:
        """Analyze article for potential fake news indicators"""
        prompt = f"""
        Analise o seguinte artigo de notícias para detectar possíveis indicadores de fake news.
        Considere fatores como: linguagem sensacionalista, falta de fontes, informações contraditórias, etc.

        Título: {title}
        Conteúdo: {content}

        Responda no formato JSON com:
        - "score": número de 0 a 10 (0 = muito confiável, 10 = muito suspeito)
        - "indicators": lista de indicadores encontrados
        - "recommendation": "approve", "review" ou "reject"

        Resposta:
        """
        
        result = self._make_request(prompt)
        if result:
            try:
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
        
        # Fallback response
        return {
            "score": 5,
            "indicators": ["Análise não disponível"],
            "recommendation": "review"
        }
    
    def generate_topic_suggestions(self, user_history: List[str]) -> List[str]:
        """Generate topic suggestions based on user reading history"""
        if not user_history:
            return Config.AVAILABLE_TOPICS[:5]  # Return default topics
        
        history_text = "\n".join(user_history[-20:])  # Last 20 articles
        
        prompt = f"""
        Com base no histórico de leitura do usuário, sugira 5 tópicos de interesse em português:

        Histórico de artigos lidos:
        {history_text}

        Tópicos disponíveis: {', '.join(Config.AVAILABLE_TOPICS)}

        Responda apenas com uma lista de 5 tópicos separados por vírgula, escolhidos da lista disponível.
        """
        
        result = self._make_request(prompt)
        if result:
            topics = [topic.strip() for topic in result.split(',')]
            # Filter to only include available topics
            valid_topics = [topic for topic in topics if topic.lower() in [t.lower() for t in Config.AVAILABLE_TOPICS]]
            return valid_topics[:5] if valid_topics else Config.AVAILABLE_TOPICS[:5]
        
        return Config.AVAILABLE_TOPICS[:5]

# Global instance
gemini_service = GeminiService()

