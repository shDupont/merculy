# Guia de Deployment - Merculy Backend

Este guia fornece instruções detalhadas para fazer o deploy do Merculy Backend em diferentes ambientes.

## Pré-requisitos

### 1. Contas e Serviços Necessários

- **Azure Account**: Para Cosmos DB e App Service
- **Google Cloud Console**: Para OAuth Google
- **Facebook Developers**: Para OAuth Facebook  
- **Google AI Studio**: Para API Gemini
- **NewsAPI**: Para API de notícias

### 2. Configuração das APIs Externas

#### Google OAuth Setup

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione existente
3. Ative a Google+ API
4. Vá para "Credentials" > "Create Credentials" > "OAuth 2.0 Client ID"
5. Configure:
   - Application type: Web application
   - Authorized redirect URIs: `https://seu-dominio.com/api/auth/google-callback`
6. Anote o Client ID e Client Secret

#### Facebook OAuth Setup

1. Acesse [Facebook Developers](https://developers.facebook.com/)
2. Crie um novo app
3. Adicione "Facebook Login" product
4. Configure Valid OAuth Redirect URIs: `https://seu-dominio.com/api/auth/facebook-callback`
5. Anote o App ID e App Secret

#### Gemini API Setup

1. Acesse [Google AI Studio](https://makersuite.google.com/)
2. Crie uma nova API key
3. Configure as permissões necessárias
4. Anote a API key

#### NewsAPI Setup

1. Acesse [NewsAPI](https://newsapi.org/)
2. Registre-se para uma conta gratuita
3. Anote sua API key

## Deployment no Azure App Service

### 1. Preparação do Ambiente Azure

```bash
# Instalar Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login no Azure
az login

# Criar resource group
az group create --name merculy-rg --location "Brazil South"

# Criar App Service Plan
az appservice plan create \
  --name merculy-plan \
  --resource-group merculy-rg \
  --sku B1 \
  --is-linux
```

### 2. Configuração do Cosmos DB

```bash
# Criar conta Cosmos DB
az cosmosdb create \
  --name merculy-cosmos \
  --resource-group merculy-rg \
  --kind GlobalDocumentDB \
  --locations regionName="Brazil South" failoverPriority=0 isZoneRedundant=False

# Obter connection string
az cosmosdb keys list \
  --name merculy-cosmos \
  --resource-group merculy-rg \
  --type connection-strings
```

### 3. Deploy da Aplicação

```bash
# Criar Web App
az webapp create \
  --resource-group merculy-rg \
  --plan merculy-plan \
  --name merculy-backend \
  --runtime "PYTHON|3.11" \
  --deployment-local-git

# Configurar variáveis de ambiente
az webapp config appsettings set \
  --resource-group merculy-rg \
  --name merculy-backend \
  --settings \
    SECRET_KEY="sua-chave-secreta-forte" \
    COSMOS_ENDPOINT="https://merculy-cosmos.documents.azure.com:443/" \
    COSMOS_KEY="sua-cosmos-key" \
    COSMOS_DATABASE_NAME="merculy_db" \
    COSMOS_CONTAINER_NAME="users" \
    GOOGLE_CLIENT_ID="seu-google-client-id" \
    GOOGLE_CLIENT_SECRET="seu-google-client-secret" \
    FACEBOOK_CLIENT_ID="seu-facebook-client-id" \
    FACEBOOK_CLIENT_SECRET="seu-facebook-client-secret" \
    GEMINI_API_KEY="sua-gemini-api-key" \
    NEWS_API_KEY="sua-news-api-key"

# Deploy via Git
git remote add azure https://merculy-backend.scm.azurewebsites.net/merculy-backend.git
git push azure main
```

### 4. Configuração de Startup

Crie o arquivo `startup.sh`:

```bash
#!/bin/bash
cd /home/site/wwwroot
pip install -r requirements.txt
gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 src.main:app
```

Configure no Azure:

```bash
az webapp config set \
  --resource-group merculy-rg \
  --name merculy-backend \
  --startup-file startup.sh
```

## Deployment com Docker

### 1. Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY src/ ./src/
COPY .env .

# Expor porta
EXPOSE 5000

# Comando de inicialização
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "src.main:app"]
```

### 2. Docker Compose

```yaml
version: '3.8'

services:
  merculy-backend:
    build: .
    ports:
      - "5000:5000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - COSMOS_ENDPOINT=${COSMOS_ENDPOINT}
      - COSMOS_KEY=${COSMOS_KEY}
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
      - FACEBOOK_CLIENT_ID=${FACEBOOK_CLIENT_ID}
      - FACEBOOK_CLIENT_SECRET=${FACEBOOK_CLIENT_SECRET}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - NEWS_API_KEY=${NEWS_API_KEY}
    volumes:
      - ./src/database:/app/src/database
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - merculy-backend
    restart: unless-stopped
```

### 3. Build e Deploy

```bash
# Build da imagem
docker build -t merculy-backend .

# Run local
docker-compose up -d

# Deploy para registry
docker tag merculy-backend:latest seu-registry/merculy-backend:latest
docker push seu-registry/merculy-backend:latest
```

## Deployment no Heroku

### 1. Preparação

```bash
# Instalar Heroku CLI
curl https://cli-assets.heroku.com/install.sh | sh

# Login
heroku login

# Criar app
heroku create merculy-backend
```

### 2. Configuração

```bash
# Configurar variáveis de ambiente
heroku config:set SECRET_KEY="sua-chave-secreta"
heroku config:set COSMOS_ENDPOINT="seu-cosmos-endpoint"
heroku config:set COSMOS_KEY="sua-cosmos-key"
heroku config:set GOOGLE_CLIENT_ID="seu-google-client-id"
heroku config:set GOOGLE_CLIENT_SECRET="seu-google-client-secret"
heroku config:set FACEBOOK_CLIENT_ID="seu-facebook-client-id"
heroku config:set FACEBOOK_CLIENT_SECRET="seu-facebook-client-secret"
heroku config:set GEMINI_API_KEY="sua-gemini-api-key"
heroku config:set NEWS_API_KEY="sua-news-api-key"
```

### 3. Procfile

```
web: gunicorn --bind 0.0.0.0:$PORT --workers 4 src.main:app
```

### 4. Deploy

```bash
# Deploy
git push heroku main

# Verificar logs
heroku logs --tail
```

## Configuração de SSL/HTTPS

### 1. Certificado Let's Encrypt

```bash
# Instalar certbot
sudo apt install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d seu-dominio.com

# Renovação automática
sudo crontab -e
# Adicionar: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. Configuração Nginx

```nginx
server {
    listen 80;
    server_name seu-dominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com;

    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoramento e Logs

### 1. Application Insights (Azure)

```bash
# Adicionar Application Insights
az extension add --name application-insights

# Criar recurso
az monitor app-insights component create \
  --app merculy-insights \
  --location "Brazil South" \
  --resource-group merculy-rg
```

### 2. Configuração de Logs

```python
import logging
from azure.monitor.opentelemetry.exporter import AzureMonitorLogExporter

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure Monitor
exporter = AzureMonitorLogExporter(
    connection_string="InstrumentationKey=sua-key"
)
```

### 3. Health Checks

```python
@app.route('/health')
def health_check():
    checks = {
        'database': check_database(),
        'cosmos_db': check_cosmos_db(),
        'gemini_api': check_gemini_api(),
        'news_api': check_news_api()
    }
    
    status = 'healthy' if all(checks.values()) else 'unhealthy'
    
    return {
        'status': status,
        'checks': checks,
        'timestamp': datetime.utcnow().isoformat()
    }
```

## Backup e Recuperação

### 1. Backup do Cosmos DB

```bash
# Backup automático (configurado no Azure)
az cosmosdb sql database throughput migrate \
  --account-name merculy-cosmos \
  --resource-group merculy-rg \
  --name merculy_db \
  --throughput 400
```

### 2. Backup de Configurações

```bash
# Exportar configurações do App Service
az webapp config appsettings list \
  --name merculy-backend \
  --resource-group merculy-rg \
  --output json > backup-config.json
```

## Troubleshooting

### 1. Problemas Comuns

#### Erro de CORS
```python
# Verificar configuração CORS
CORS(app, origins=["https://seu-frontend.com"], supports_credentials=True)
```

#### Timeout de API
```python
# Aumentar timeout
requests.get(url, timeout=30)
```

#### Erro de Memória
```bash
# Aumentar workers no Gunicorn
gunicorn --workers 2 --max-requests 1000 src.main:app
```

### 2. Logs de Debug

```bash
# Azure App Service
az webapp log tail --name merculy-backend --resource-group merculy-rg

# Docker
docker logs -f container-name

# Heroku
heroku logs --tail --app merculy-backend
```

### 3. Performance Tuning

```python
# Cache de respostas
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.cached(timeout=300)
def get_news_cached(topic):
    return news_service.get_news_by_topic(topic)
```

## Segurança

### 1. Variáveis de Ambiente

```bash
# Nunca commitar .env
echo ".env" >> .gitignore

# Usar Azure Key Vault em produção
az keyvault create \
  --name merculy-keyvault \
  --resource-group merculy-rg \
  --location "Brazil South"
```

### 2. Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

### 3. Validação de Input

```python
from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    email = fields.Email(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    password = fields.Str(required=True, validate=validate.Length(min=8))
```

## Checklist de Deploy

- [ ] Configurar todas as variáveis de ambiente
- [ ] Testar conexões com APIs externas
- [ ] Configurar CORS para domínio de produção
- [ ] Configurar SSL/HTTPS
- [ ] Configurar monitoramento e logs
- [ ] Testar health checks
- [ ] Configurar backup automático
- [ ] Testar recuperação de desastres
- [ ] Configurar rate limiting
- [ ] Revisar configurações de segurança
- [ ] Documentar URLs e credenciais
- [ ] Testar integração com frontend

## Contatos de Suporte

- **Azure Support**: https://azure.microsoft.com/support/
- **Heroku Support**: https://help.heroku.com/
- **Google Cloud Support**: https://cloud.google.com/support/
- **Documentação do Projeto**: README.md

