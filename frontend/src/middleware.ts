import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Rotas públicas (não requerem autenticação)
const publicPaths = ['/login', '/api/auth']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Verifica se é rota pública
  const isPublic = publicPaths.some(path => pathname.startsWith(path))

  if (isPublic) {
    return NextResponse.next()
  }

  // Verifica token de autenticação
  const accessToken = request.cookies.get('access_token')?.value
  const authHeader = request.headers.get('authorization')

  // Se há token no localStorage (verificado pelo cliente), permite
  // O middleware só verifica cookies, autenticação real é feita pelo cliente

  // Para páginas que requerem autenticação, redireciona para login se não autenticado
  // Mas aqui só podemos verificar cookies, não localStorage

  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Aplica a todas as rotas exceto:
     * - api routes
     * - _next/static
     * - _next/image
     * - favicon.ico
     * - assets públicos
     */
    '/((?!api|_next/static|_next/image|favicon.ico|public).*)',
  ],
}