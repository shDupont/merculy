"""
Merculy Backend - Google Gemini AI Service
"""
import google.generativeai as genai
from typing import Dict, Optional
from flask import current_app
from ..models.user import Article, BiasType
from ..core.config import Config
import json
import time

class GeminiService:
    def __init__(self):
        self.config = Config()
        self.model = None
        self._initialize()

    def _initialize(self):
        """Initialize Gemini client"""
        try:
            genai.configure(api_key=self.config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            current_app.logger.error(f"Gemini initialization error: {str(e)}")
            raise

    def summarize_and_analyze_bias(self, article: Article) -> Dict:
        """Summarize article and analyze political bias"""
        try:
            content_to_analyze = f"""
            Título: {article.title}
            Resumo: {article.excerpt}
            Conteúdo: {article.content[:1000] if article.content else ''}
            Fonte: {article.source}
            """

            prompt = f"""
            Analise o seguinte artigo de notícia e faça:

            1. Um resumo em até 3 linhas (máximo 300 caracteres)
            2. Classifique o viés político em: esquerda, centro ou direita
            3. Atribua um score de confiança (0.0 a 1.0) para a classificação

            Responda APENAS em formato JSON válido:
            {{
                "summary": "resumo da notícia aqui",
                "bias": "esquerda|centro|direita",
                "confidence_score": 0.85
            }}

            Artigo para análise:
            {content_to_analyze}
            """

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=500
                )
            )

            # Parse JSON response
            result = json.loads(response.text.strip())

            # Validate response
            if not all(key in result for key in ['summary', 'bias', 'confidence_score']):
                raise ValueError("Incomplete response from Gemini")

            # Validate bias value
            if result['bias'] not in ['esquerda', 'centro', 'direita']:
                result['bias'] = 'centro'  # Default fallback

            # Ensure confidence score is between 0 and 1
            result['confidence_score'] = max(0.0, min(1.0, float(result['confidence_score'])))

            return result

        except json.JSONDecodeError as e:
            current_app.logger.error(f"JSON decode error in Gemini response: {str(e)}")
            return self._fallback_response()
        except Exception as e:
            current_app.logger.error(f"Gemini analysis error: {str(e)}")
            return self._fallback_response()

    def _fallback_response(self) -> Dict:
        """Fallback response when AI analysis fails"""
        return {
            "summary": "Resumo não disponível no momento",
            "bias": "centro",
            "confidence_score": 0.0
        }

    def enhance_articles(self, articles: list[Article]) -> list[Article]:
        """Enhance articles with AI analysis"""
        enhanced_articles = []

        for article in articles:
            try:
                # Add small delay to avoid rate limits
                time.sleep(0.5)

                # Get AI analysis
                analysis = self.summarize_and_analyze_bias(article)

                # Update article with AI insights
                article.summary = analysis['summary']
                article.bias = BiasType(analysis['bias'])
                article.confidence_score = analysis['confidence_score']

                enhanced_articles.append(article)

            except Exception as e:
                current_app.logger.warning(f"Error enhancing article {article.title}: {str(e)}")
                # Add article without AI enhancement
                article.summary = article.excerpt[:200] if article.excerpt else "Sem resumo"
                article.bias = BiasType.CENTRO
                article.confidence_score = 0.0
                enhanced_articles.append(article)

        return enhanced_articles

    def generate_newsletter_intro(self, user_name: str, articles_count: int, topics: list[str]) -> str:
        """Generate personalized newsletter introduction"""
        try:
            prompt = f"""
            Crie uma introdução personalizada e amigável para uma newsletter diária.

            Informações:
            - Nome do usuário: {user_name}
            - Número de artigos: {articles_count}
            - Tópicos de interesse: {', '.join(topics)}

            A introdução deve:
            - Ser calorosa e pessoal
            - Mencionar os tópicos principais
            - Ter tom jornalístico mas acessível
            - Máximo 150 palavras
            - Em português brasileiro

            Responda apenas com o texto da introdução, sem formatação markdown.
            """

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=300
                )
            )

            return response.text.strip()

        except Exception as e:
            current_app.logger.error(f"Error generating intro: {str(e)}")
            return f"Olá {user_name}, aqui está sua newsletter personalizada com {articles_count} notícias selecionadas para você."

# Global service instance
gemini_service = GeminiService()
