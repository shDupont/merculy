# Merculy Backend API

Backend completo para o aplicativo Merculy - uma plataforma de newsletters personalizadas com IA.

## Visão Geral

O Merculy Backend é uma API REST desenvolvida em Flask que oferece:

- **Autenticação completa**: Login via email/senha, Google OAuth e Facebook OAuth
- **Integração com Azure Cosmos DB**: Banco de dados NoSQL para escalabilidade
- **IA com Gemini**: Geração de resumos, análise de viés político e criação de newsletters personalizadas
- **API de Notícias**: Integração com NewsAPI para notícias em português
- **Sistema de Newsletters**: Geração automática de conteúdo personalizado
- **Moderação de Conteúdo**: Detecção de fake news com IA

## Arquitetura

```
┌─────────────────────────────┐
│ Flutter App (Merculy)       │
└────────────┬────────────────┘
             │ HTTP/JSON
             ↓
┌─────────────────────────────┐
│ Flask Backend API           │
├─────────────────────────────┤
│ • Autenticação (Flask-Login)│
│ • Rotas REST                │
│ • Middleware CORS           │
└────┬──────────────┬─────────┘
     │              │
     ↓              ↓
┌─────────────┐ ┌─────────────┐
│ SQLite      │ │ Azure       │
│ (Local)     │ │ Cosmos DB   │
└─────────────┘ └─────────────┘
     │              │
     └──────┬───────┘
            ↓
┌─────────────────────────────┐
│ Serviços Externos           │
├─────────────────────────────┤
│ • Google OAuth              │
│ • Facebook OAuth            │
│ • Gemini AI API             │
│ • NewsAPI                   │
└─────────────────────────────┘
```

## Funcionalidades Principais

### 1. Sistema de Autenticação

- **Registro e Login**: Email/senha com hash seguro
- **OAuth Social**: Google e Facebook integrados
- **Gerenciamento de Sessão**: Flask-Login para controle de estado
- **Perfil de Usuário**: Atualização de dados e preferências

### 2. Curadoria de Conteúdo com IA

- **Busca Inteligente**: Filtragem por tópicos de interesse
- **Resumos Automáticos**: Gemini gera resumos de até 3 linhas
- **Análise de Viés**: Classificação política (esquerda/centro/direita)
- **Detecção de Fake News**: Análise de credibilidade com IA

### 3. Sistema de Newsletters

- **Geração Personalizada**: Baseada nos interesses do usuário
- **Múltiplos Formatos**: Newsletter única ou por assunto
- **Agendamento**: Configuração de dias e horários
- **Histórico**: Salvamento e organização de newsletters

### 4. Integração com Dados

- **Banco Híbrido**: SQLite local + Azure Cosmos DB
- **APIs de Notícias**: NewsAPI com fontes brasileiras
- **Cache Inteligente**: Otimização de performance
- **Sincronização**: Dados consistentes entre plataformas

## Instalação e Configuração

### Pré-requisitos

- Python 3.11+
- Conta Azure (para Cosmos DB)
- Chaves de API (Google, Facebook, Gemini, NewsAPI)

### 1. Configuração do Ambiente

```bash
# Clone o projeto
cd merculy-backend

# Ative o ambiente virtual
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### 2. Configuração das Variáveis de Ambiente

Edite o arquivo `.env`:

```env
# Flask Configuration
SECRET_KEY=sua-chave-secreta-aqui
FLASK_ENV=development

# Google OAuth Configuration
GOOGLE_CLIENT_ID=seu-google-client-id
GOOGLE_CLIENT_SECRET=seu-google-client-secret

# Facebook OAuth Configuration
FACEBOOK_CLIENT_ID=seu-facebook-client-id
FACEBOOK_CLIENT_SECRET=seu-facebook-client-secret

# Azure Cosmos DB Configuration
COSMOS_ENDPOINT=seu-cosmos-endpoint
COSMOS_KEY=sua-cosmos-key
COSMOS_DATABASE_NAME=merculy_db
COSMOS_CONTAINER_NAME=users

# Gemini API Configuration
GEMINI_API_KEY=sua-gemini-api-key

# News API Configuration
NEWS_API_KEY=sua-news-api-key
NEWS_API_URL=https://newsapi.org/v2/everything
```

### 3. Execução

```bash
# Desenvolvimento
python src/main.py

# Produção
gunicorn -w 4 -b 0.0.0.0:5000 src.main:app
```

## Endpoints da API

### Autenticação (`/api/auth`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/register` | Registrar novo usuário |
| POST | `/login` | Login com email/senha |
| POST | `/google-login` | Login com Google |
| POST | `/facebook-login` | Login com Facebook |
| POST | `/logout` | Logout do usuário |
| GET | `/me` | Informações do usuário atual |
| PUT | `/update-profile` | Atualizar perfil |
| PUT | `/change-password` | Alterar senha |

### Notícias e Newsletters (`/api`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/topics` | Tópicos disponíveis |
| GET | `/news/<topic>` | Notícias por tópico |
| GET | `/trending` | Notícias em alta |
| GET | `/search` | Buscar notícias |
| POST | `/newsletter/generate` | Gerar newsletter |
| GET | `/newsletters` | Newsletters do usuário |
| POST | `/newsletters/<id>/save` | Salvar newsletter |
| GET | `/newsletters/saved` | Newsletters salvas |
| GET | `/preferences/topics` | Sugestões de tópicos |
| POST | `/articles/<id>/analyze` | Analisar fake news |

## Exemplos de Uso

### 1. Registro de Usuário

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "João Silva",
    "email": "joao@email.com",
    "password": "senha123",
    "interests": ["tecnologia", "política"],
    "newsletter_format": "single",
    "delivery_schedule": {
      "days": ["monday", "wednesday", "friday"],
      "time": "08:00"
    }
  }'
```

### 2. Login com Google

```bash
curl -X POST http://localhost:5000/api/auth/google-login \
  -H "Content-Type: application/json" \
  -d '{
    "token": "google-oauth-token-aqui"
  }'
```

### 3. Buscar Notícias por Tópico

```bash
curl -X GET "http://localhost:5000/api/news/tecnologia?limit=10" \
  -H "Authorization: Bearer seu-token-aqui"
```

### 4. Gerar Newsletter Personalizada

```bash
curl -X POST http://localhost:5000/api/newsletter/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer seu-token-aqui"
```

## Estrutura do Projeto

```
merculy-backend/
├── src/
│   ├── models/
│   │   └── user.py              # Modelos de dados
│   ├── routes/
│   │   ├── auth.py              # Rotas de autenticação
│   │   ├── news.py              # Rotas de notícias
│   │   └── user.py              # Rotas de usuários
│   ├── services/
│   │   ├── cosmos_service.py    # Serviço Azure Cosmos DB
│   │   ├── gemini_service.py    # Serviço Gemini AI
│   │   └── news_service.py      # Serviço de notícias
│   ├── static/                  # Arquivos estáticos
│   ├── database/                # Banco SQLite local
│   ├── config.py                # Configurações
│   └── main.py                  # Aplicação principal
├── venv/                        # Ambiente virtual
├── requirements.txt             # Dependências
├── .env                         # Variáveis de ambiente
└── README.md                    # Documentação
```

## Modelos de Dados

### User
```python
{
  "id": int,
  "email": str,
  "name": str,
  "interests": [str],
  "newsletter_format": "single" | "by_topic",
  "delivery_schedule": {
    "days": [str],
    "time": str
  },
  "created_at": datetime,
  "last_login": datetime
}
```

### Newsletter
```python
{
  "id": int,
  "user_id": int,
  "title": str,
  "content": str,
  "topic": str,
  "created_at": datetime,
  "is_saved": bool
}
```

### NewsArticle
```python
{
  "id": int,
  "title": str,
  "content": str,
  "summary": str,
  "source": str,
  "url": str,
  "topic": str,
  "political_bias": "esquerda" | "centro" | "direita",
  "published_at": datetime
}
```

## Configuração de Produção

### 1. Azure App Service

```bash
# Deploy para Azure
az webapp up --name merculy-backend --resource-group merculy-rg
```

### 2. Variáveis de Ambiente de Produção

Configure no Azure Portal:
- `SECRET_KEY`: Chave secreta forte
- `COSMOS_ENDPOINT`: Endpoint do Cosmos DB
- `COSMOS_KEY`: Chave de acesso do Cosmos DB
- `GEMINI_API_KEY`: Chave da API Gemini
- `NEWS_API_KEY`: Chave da NewsAPI

### 3. CORS e Segurança

```python
# Configuração para produção
CORS(app, origins=["https://merculy.app"], supports_credentials=True)
```

## Monitoramento e Logs

### Health Check

```bash
curl http://localhost:5000/health
```

### Logs de Aplicação

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Testes

### Executar Testes

```bash
# Testes unitários
python -m pytest tests/

# Testes de integração
python -m pytest tests/integration/
```

### Cobertura de Código

```bash
coverage run -m pytest
coverage report
```

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## Suporte

Para suporte técnico:
- Email: suporte@merculy.app
- Documentação: https://docs.merculy.app
- Issues: https://github.com/merculy/backend/issues

## Changelog

### v1.0.0 (2025-01-23)
- ✅ Sistema de autenticação completo
- ✅ Integração com Azure Cosmos DB
- ✅ Serviços de IA com Gemini
- ✅ API de notícias em português
- ✅ Geração de newsletters personalizadas
- ✅ Sistema de moderação de conteúdo

