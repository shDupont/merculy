# Merculy Backend

Backend Python para o aplicativo Merculy - plataforma de newsletters personalizadas com IA.

## 🚀 Funcionalidades

- **Autenticação**: Azure AD B2C com validação JWT
- **Curadoria Inteligente**: Integração com múltiplas APIs de notícias
- **IA Generativa**: Resumos e análise de viés político com Google Gemini
- **Newsletter Personalizada**: Compilação e envio automatizado
- **Agendamento**: Envios programados via APScheduler
- **Armazenamento**: Azure Cosmos DB (NoSQL)
- **Email**: Envio via SendGrid

## 📋 Pré-requisitos

- Python 3.12+
- Azure Account (AD B2C + Cosmos DB)
- Google Cloud Account (Gemini API)
- SendGrid Account
- APIs de notícias (NewsAPI, Guardian, Bing News)

## 🛠️ Instalação

1. Clone o repositório
```bash
git clone <repository-url>
cd merculy-backend
```

2. Crie ambiente virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale dependências
```bash
pip install -r requirements.txt
```

4. Configure variáveis de ambiente
```bash
cp .env.example .env
# Edite o arquivo .env com suas credenciais
```

## ⚙️ Configuração

### Azure AD B2C

1. Crie um tenant B2C
2. Configure user flow para sign up/sign in
3. Registre aplicação API
4. Configure claims customizadas (roles, groups)
5. Obtenha as configurações:
   - AZURE_TENANT_ID
   - AZURE_B2C_POLICY
   - AZURE_CLIENT_ID
   - AZURE_OPENID_CONFIG

### Azure Cosmos DB

1. Crie conta Cosmos DB (Core SQL API)
2. Configure throughput (recomendado: Serverless)
3. Obtenha URI e chave primária

### APIs Externas

1. **Google Gemini**: Crie projeto no Google Cloud, ative Generative AI API
2. **SendGrid**: Crie conta, obtenha API key
3. **NewsAPI**: Registre-se em newsapi.org
4. **Guardian API**: Registre-se em open-platform.theguardian.com
5. **Bing News**: Crie recurso no Azure Cognitive Services

## 🚀 Execução

### Desenvolvimento
```bash
python run.py
```

### Produção (Docker)
```bash
docker build -t merculy-backend .
docker run -p 8000:8000 --env-file .env merculy-backend
```

### Azure App Service
```bash
# Configurar deployment via Azure CLI ou GitHub Actions
az webapp up --resource-group merculy-rg --name merculy-api
```

## 📚 API Endpoints

### Autenticação
- Todos os endpoints (exceto `/health`) requerem header: `Authorization: Bearer <jwt_token>`

### Usuários
- `GET /v1/profile` - Obter perfil do usuário
- `PUT /v1/profile` - Atualizar perfil
- `PUT /v1/profile/preferences` - Atualizar preferências
- `GET /v1/profile/preferences` - Obter preferências
- `GET /v1/profile/topics` - Listar tópicos disponíveis

### Newsletters
- `GET /v1/newsletter/latest` - Última newsletter
- `GET /v1/newsletter/history` - Histórico de newsletters
- `POST /v1/newsletter/send-test` - Enviar newsletter de teste
- `POST /v1/newsletter/preview` - Visualizar prévia
- `GET /v1/newsletter/stats` - Estatísticas do usuário

### Sistema
- `GET /v1/health` - Health check básico
- `GET /v1/health/detailed` - Health check detalhado

## 🏗️ Arquitetura

```
merculy-backend/
├── app/
│   ├── __init__.py          # Flask factory
│   ├── auth/                # Autenticação Azure B2C
│   ├── models/              # Modelos Pydantic
│   ├── services/            # Lógica de negócio
│   ├── scheduler/           # Jobs agendados
│   ├── routes/              # Endpoints REST
│   └── core/                # Configurações
├── tests/                   # Testes unitários
├── requirements.txt
├── Dockerfile
└── run.py                   # Entry point
```

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Com cobertura
pytest --cov=app

# Testes específicos
pytest tests/test_auth.py
```

## 📊 Monitoramento

- **Logs**: Application Insights (Azure)
- **Métricas**: Health checks, performance counters
- **Alertas**: Configurar via Azure Monitor

## 🔧 Jobs Agendados

- **05:00**: Newsletter diária geral
- **08:00**: Newsletters matutinas
- **14:00**: Newsletters vespertinas
- **18:00**: Newsletters noturnas

## 🔒 Segurança

- JWT validation com chaves públicas Azure B2C
- Rate limiting (Flask-Limiter + Redis)
- CORS configurado para origens específicas
- Validação de entrada com Pydantic
- Secrets no Azure Key Vault

## 🚀 Deploy

### GitHub Actions
```yaml
name: Deploy to Azure
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Azure App Service
        uses: azure/webapps-deploy@v2
        with:
          app-name: merculy-api
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

## 📈 Escalabilidade

- **Horizontal**: Multiple App Service instances
- **Cache**: Redis para rate limiting e sessões
- **Database**: Cosmos DB auto-scaling
- **CDN**: Azure CDN para assets estáticos

## 🐛 Troubleshooting

### Problemas Comuns

1. **JWT Validation Failed**
   - Verificar AZURE_OPENID_CONFIG
   - Checar expiração do token
   - Validar audience

2. **Cosmos DB Connection**
   - Verificar URI e chave
   - Checar firewall rules
   - Validar throughput

3. **Newsletter Não Enviada**
   - Verificar SendGrid API key
   - Checar logs do scheduler
   - Validar user preferences

## 📝 Changelog

### v1.0.0 (2025-01-22)
- Autenticação Azure B2C
- Curadoria de notícias multi-fonte
- Análise IA com Gemini
- Sistema de newsletters
- Deploy Azure App Service

## 🤝 Contribuição

1. Fork o projeto
2. Crie feature branch (`git checkout -b feature/nova-feature`)
3. Commit mudanças (`git commit -am 'Add nova feature'`)
4. Push branch (`git push origin feature/nova-feature`)
5. Abra Pull Request

## 📄 Licença

Este projeto está sob licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👥 Equipe

- **Backend**: Python/Flask + Azure
- **Mobile**: Flutter
- **IA**: Google Gemini
- **Infraestrutura**: Azure Cloud

---

🔗 **Links Úteis**
- [Documentação Azure B2C](https://docs.microsoft.com/azure/active-directory-b2c/)
- [Cosmos DB Python SDK](https://docs.microsoft.com/azure/cosmos-db/sql/sql-api-sdk-python)
- [Google Generative AI](https://ai.google.dev/)
- [SendGrid API](https://sendgrid.com/docs/api-reference/)
