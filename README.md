# Agendamento MVP

Projeto estruturado conforme especificação Next.js 14 + TypeScript + Tailwind + Prisma + NextAuth.

## Como rodar

1. Instale as dependências:
   ```sh
   npm install
   ```
2. Configure o banco de dados PostgreSQL e a variável de ambiente `DATABASE_URL`.
3. Rode as migrations:
   ```sh
   npx prisma migrate dev
   ```
4. Rode o projeto:
   ```sh
   npm run dev
   ```

Acesse em http://localhost:3000
