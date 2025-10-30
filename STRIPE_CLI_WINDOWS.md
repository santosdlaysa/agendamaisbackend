# Instalar Stripe CLI no Windows - Guia Completo

## Método 1: Instalador MSI (Recomendado) ⭐

**Mais fácil e rápido!**

### Passos:

1. **Baixe o instalador:**
   - Acesse: https://github.com/stripe/stripe-cli/releases/latest
   - Procure por: `stripe_X.X.X_windows_x86_64.msi`
   - Clique para baixar (ex: `stripe_1.19.4_windows_x86_64.msi`)

2. **Execute o instalador:**
   - Clique duas vezes no arquivo `.msi` baixado
   - Siga o assistente de instalação
   - Clique em "Next" → "Install" → "Finish"

3. **Reinicie o PowerShell**

4. **Verifique a instalação:**
   ```powershell
   stripe --version
   ```

5. **Login no Stripe:**
   ```powershell
   stripe login
   ```

6. **Inicie o webhook listener:**
   ```powershell
   stripe listen --forward-to localhost:5000/api/subscriptions/webhook
   ```

---

## Método 2: Via Scoop (Gerenciador de Pacotes)

### Passo 1: Instalar Scoop

Abra o PowerShell como **Administrador** e execute:

```powershell
# Permitir execução de scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Instalar Scoop
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
```

### Passo 2: Instalar Stripe CLI

```powershell
# Adicionar bucket do Stripe
scoop bucket add stripe https://github.com/stripe/scoop-stripe-cli.git

# Instalar Stripe CLI
scoop install stripe
```

### Passo 3: Verificar

```powershell
stripe --version
```

---

## Método 3: Download Manual (Portátil)

### Passos:

1. **Baixe o ZIP:**
   - Acesse: https://github.com/stripe/stripe-cli/releases/latest
   - Baixe: `stripe_X.X.X_windows_x86_64.zip`

2. **Extraia para uma pasta:**
   ```powershell
   # Exemplo: extrair para C:\stripe
   Expand-Archive -Path .\stripe_1.19.4_windows_x86_64.zip -DestinationPath C:\stripe
   ```

3. **Adicione ao PATH (Temporário):**
   ```powershell
   $env:Path += ";C:\stripe"
   ```

4. **Adicione ao PATH (Permanente):**
   ```powershell
   # Via PowerShell (Administrador)
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\stripe", "Machine")
   ```

   Ou manualmente:
   - Pesquisar "Variáveis de Ambiente" no menu Iniciar
   - Editar variável PATH
   - Adicionar: `C:\stripe`

5. **Teste:**
   ```powershell
   stripe --version
   ```

---

## Método 4: Sem Instalar (Para Testes)

Se você só quer testar temporariamente sem instalar, pode usar um webhook secret de teste:

```env
# .env
STRIPE_WEBHOOK_SECRET=whsec_test_temporary_secret
```

**Nota:** Isso NÃO vai funcionar com webhooks reais, apenas para desenvolvimento local sem o CLI.

---

## Usando o Stripe CLI

### Login

```powershell
stripe login
```

Isso abrirá seu navegador para autorizar.

### Iniciar Webhook Listener (Desenvolvimento)

```powershell
stripe listen --forward-to localhost:5000/api/subscriptions/webhook
```

Você verá algo como:
```
> Ready! Your webhook signing secret is whsec_1234567890abcdef (^C to quit)
```

**Copie esse secret para seu `.env`:**

```env
STRIPE_WEBHOOK_SECRET=whsec_1234567890abcdef
```

### Testar Webhooks

Em outro terminal:

```powershell
# Simular pagamento bem-sucedido
stripe trigger invoice.paid

# Simular falha no pagamento
stripe trigger invoice.payment_failed

# Simular cancelamento
stripe trigger customer.subscription.deleted
```

---

## Troubleshooting

### Erro: "stripe: The term 'stripe' is not recognized"

**Solução:**
1. Reinicie o PowerShell
2. Verifique se o PATH foi configurado
3. Tente executar o caminho completo: `C:\Program Files\Stripe\stripe.exe --version`

### Erro: "UnauthorizedAccess" ao instalar Scoop

**Solução:**
```powershell
# Execute como Administrador
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Erro: "stripe login" não abre navegador

**Solução:**
```powershell
# Use o link manualmente
stripe login
# Copie o link exibido e cole no navegador
```

### Webhook não recebe eventos

**Solução:**
1. Verifique se o servidor Flask está rodando
2. Verifique se a URL está correta
3. Certifique-se de que não há firewall bloqueando

---

## Comandos Úteis

```powershell
# Ver versão
stripe --version

# Ver ajuda
stripe help

# Listar eventos
stripe events list

# Ver logs
stripe logs tail

# Testar webhook
stripe trigger customer.subscription.created

# Ver produtos
stripe products list

# Ver preços
stripe prices list
```

---

## Alternativa: Webhook no Stripe Dashboard (Produção)

Se você não quiser usar o CLI, pode configurar webhooks diretamente:

1. Acesse: https://dashboard.stripe.com/webhooks
2. Clique em "Add endpoint"
3. URL: `https://seu-dominio.com/api/subscriptions/webhook`
4. Selecione eventos:
   - invoice.paid
   - invoice.payment_failed
   - customer.subscription.deleted
   - customer.subscription.updated
5. Copie o "Signing secret"

---

## Links Úteis

- [Stripe CLI Releases](https://github.com/stripe/stripe-cli/releases)
- [Stripe CLI Docs](https://stripe.com/docs/stripe-cli)
- [Scoop](https://scoop.sh/)

---

**Última atualização:** 2025-10-30
