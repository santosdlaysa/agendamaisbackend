# Setup do Projeto Agendamento MVP

## 1. Instale as dependências do projeto

```sh
npm install
```

## 2. Configure o banco de dados PostgreSQL

- Crie um banco de dados PostgreSQL.
- No arquivo `.env`, adicione a variável:

```
DATABASE_URL=postgresql://usuario:senha@localhost:5432/nome_do_banco
```

## 3. Rode as migrations do Prisma

```sh
npx prisma migrate dev
```

## 4. Inicie o servidor de desenvolvimento

```sh
npm run dev
```

Acesse o sistema em http://localhost:3000

---

## Observações
- Para autenticação, configure o NextAuth no arquivo `src/lib/auth.ts` e as rotas em `src/app/api/auth/[...nextauth]/route.ts`.
- Para customizar estilos, edite os arquivos em `src/styles/`.
- Para criar rotas de API, utilize a pasta `src/app/api/`.
- Para adicionar novos componentes, utilize as subpastas de `src/components/`.

Se precisar migrar lógica Python para API Route, reescreva a lógica em TypeScript e coloque em `src/app/api/`.
