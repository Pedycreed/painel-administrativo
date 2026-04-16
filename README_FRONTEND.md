# Instruções para Configurar o Frontend

## O que foi feito:

### Backend (Django)
✅ JWT configurado com `djangorestframework-simplejwt`
✅ Rotas de autenticação: `/api/token/` e `/api/token/refresh/`
✅ ViewSets filtrados por fonte: `/api/scan/obras/` e `/api/agregador/obras/`
✅ Usuário admin criado: `admin` / `admin123`

### Frontend (Next.js) - Arquivos Criados
A estrutura do frontend está em `/workspace/frontend/` com:
- `src/lib/api.ts` - Configuração da API com axios e interceptors JWT
- `src/context/AuthContext.tsx` - Contexto de autenticação
- `src/app/login/page.tsx` - Página de login
- `src/app/dashboard/page.tsx` - Dashboard com cards Scan/Agregador
- `src/app/scan/page.tsx` - Lista de obras da Scan
- `src/app/agregador/page.tsx` - Lista de obras do Agregador
- `src/app/layout.tsx` - Layout principal com AuthProvider
- `src/app/page.tsx` - Redirecionamento inicial
- `.env.local` - Variáveis de ambiente

## Como usar no SEU computador:

### 1. Copie os arquivos do frontend

No seu projeto local, crie a pasta `frontend` e copie estes arquivos:

```bash
# No seu computador, na raiz do projeto:
mkdir -p frontend/src/app/login frontend/src/app/dashboard frontend/src/app/scan frontend/src/app/agregador frontend/src/lib frontend/src/context
```

Copie o conteúdo de cada arquivo que criei aqui para os correspondentes no seu PC.

### 2. Instale as dependências do frontend

```bash
cd frontend
npm install
```

### 3. Configure o .env.local

Crie um arquivo `.env.local` na pasta `frontend` com:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### 4. Rode o backend

```bash
# Na raiz do projeto Django:
python manage.py runserver
```

### 5. Rode o frontend

```bash
# Na pasta frontend:
npm run dev
```

### 6. Acesse

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api
- Admin Django: http://localhost:8000/admin

### 7. Login

Use as credenciais:
- Usuário: `admin`
- Senha: `admin123`

## Próximos passos recomendados:

1. **Testar o fluxo completo**: Login → Dashboard → Scan/Agregador
2. **Criar formulário de nova obra**: Para adicionar obras em cada módulo
3. **Implementar upload de imagens**: Integrar com S3 ou Supabase Storage
4. **Adicionar página de detalhes da obra**: Ver capítulos, páginas, etc.
5. **Migrar para PostgreSQL**: Para produção

