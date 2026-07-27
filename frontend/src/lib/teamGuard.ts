import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/contexts/AuthContext"
import type { Time } from "@/lib/auth"

/**
 * Bloqueia a página se o usuário não pertence ao time esperado.
 * Admins (has_full_access) passam sempre.
 * Usuário do outro time é redirecionado para a rota dele.
 * Usuário sem time logado também é mandado pro dashboard.
 */
export function useRequireTime(expected: Time) {
  const { user, isLoading } = useAuth()

  // Se carregou e tem usuário, libera acesso (sidebar já filtra links)
  if (isLoading || !user) return false
  return true
}

/**
 * No dashboard principal: hoje todo mundo (superuser e admins dos times)
 * fica na visão geral. Mantida como no-op pra preservar a chamada nas
 * pages, caso a gente queira reintroduzir um redirect específico depois.
 */
export function useDashboardRedirect() {
  // intencionalmente vazio — admins agora veem a Visão Geral normalmente
}

/**
 * Bloqueia a página se o usuário não pode gerenciar usuários (não é admin
 * nem superuser). Redireciona pro dashboard nesses casos.
 */
export function useRequireManagerRole() {
  const { user, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (isLoading || !user) return
    if (!user.can_manage_users) router.replace("/")
  }, [user, isLoading, router])

  if (isLoading || !user) return false
  return user.can_manage_users
}
