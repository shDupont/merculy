## 🚀 Tutorial Atualizado: Deploy do Projeto Merculy no Azure

### 1. Instale o Azure CLI (se ainda não tiver)
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

### 2. Faça login no Azure
```bash
az login
```

### 3. Configure o repositório remoto no Git
```bash
git remote add azure https://merculy-app-hehte6a4ffc5hqeh.scm.brazilsouth-01.azurewebsites.net/merculy-app.git
```

---

### 🔑 4. Configure o Git Credential Manager
Para evitar erros de autenticação ao usar HTTPS com Azure Kudu, insira as credenciais no Git Credential Manager:

- **Username**: `$merculy-app`  
- **Password**: `60J9vYvsJnGuWd18Gz7lMWkcNhaBWbdoiqsgn6FsZlXS7ZBSF7ABbndFWf2u`

Você pode configurar de forma segura com:
```bash
git config credential.helper store
```
E depois fazer um `git push`, onde o Git solicitará usuário e senha. Após inseri-los, eles serão armazenados localmente.

---

### 5. Atualize os pacotes do projeto
```bash
pip install -r requirements.txt
git add requirements.txt
git commit -m "Add gunicorn to requirements"
```

### 6. Faça o push do branch `manus` (ou `main`) para o Azure
```bash
git push azure manus:main
```

### 7. Configure variáveis de ambiente no Azure Portal

| Nome                    | Valor Exemplo           |
|-------------------------|-------------------------|
| SECRET_KEY              | sua-chave-secreta-aqui  |
| COSMOS_ENDPOINT         | seu-endpoint            |
| COSMOS_KEY              | sua-chave               |
| GEMINI_API_KEY          | sua-chave               |
| NEWS_API_KEY            | sua-chave               |
| GOOGLE_CLIENT_ID        | seu-client-id           |
| GOOGLE_CLIENT_SECRET    | sua-client-secret       |
| FACEBOOK_CLIENT_ID      | seu-client-id           |
| FACEBOOK_CLIENT_SECRET  | seu-client-secret       |
| COSMOS_DATABASE_NAME    | merculy_db              |
| COSMOS_CONTAINER_NAME   | users                   |
| FLASK_ENV               | development             |

### 8. Verifique o status do app
```bash
az webapp show --name merculy-app --resource-group merculy-rg --query state
```

### 9. (Opcional) Reinicie o serviço
```bash
az webapp stop --name merculy-app --resource-group merculy-rg
az webapp start --name merculy-app --resource-group merculy-rg
```