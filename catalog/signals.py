"""
Signals do app catalog — limpeza automática de arquivos no R2 ao deletar.

Estratégia:
- Quando uma `Obra` é deletada, todas as imagens dela (capa + capítulos +
  páginas) estão sob `mangas/{slug}/` no R2. Apagamos esse prefix inteiro
  de uma vez (mais eficiente que apagar objeto por objeto).
- Quando um `Capitulo` é deletado isoladamente (sem deletar a obra),
  apagamos `mangas/{slug}/cap-{numero}/`.
- Quando uma `Pagina` é deletada isoladamente, apagamos só o objeto dela.

O cleanup é best-effort: falhas no R2 são logadas mas não bloqueiam o
delete do banco. Você pode ficar com arquivos órfãos em caso de falha,
mas nunca com dados inconsistentes.

Usamos `pre_delete` em vez de `post_delete` pra ter acesso ao `slug`/`numero`
antes do objeto sumir do banco. Não temos transação atômica entre Postgres e
R2 — se o delete do banco falhar depois da limpeza do R2, perdemos arquivos.
Mas como o CASCADE do Django é gerenciado pela ORM (não pelo banco), o sinal
dispara só quando o delete realmente vai acontecer.
"""
import logging
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import Obra, Capitulo, Pagina
from core import storage

log = logging.getLogger(__name__)


# Flag de processo: quando estamos apagando uma Obra inteira, ignoramos os
# pre_delete de Capitulo e Pagina pra não fazer N chamadas redundantes ao R2
# (a Obra já vai apagar tudo de uma vez com delete_prefix).
_obras_em_delete: set[int] = set()


@receiver(pre_delete, sender=Obra)
def obra_pre_delete(sender, instance: Obra, **kwargs):
    """
    Apaga `mangas/{slug}/` inteiro do R2 quando a obra é deletada.

    Uma chamada de delete_prefix lida com capa + todos capítulos + todas
    páginas de uma vez — muito mais eficiente que apagar cada objeto.
    """
    _obras_em_delete.add(instance.pk)
    if not instance.slug:
        return
    prefix = f'mangas/{instance.slug}/'
    try:
        n = storage.delete_prefix(prefix)
        log.info('R2 cleanup: obra %r — %d objetos removidos de %s',
                 instance.titulo, n, prefix)
    except Exception as e:
        # Best-effort: loga e segue. O delete do banco prossegue.
        log.warning('R2 cleanup falhou para obra %r (%s): %s',
                    instance.titulo, prefix, e)


@receiver(pre_delete, sender=Capitulo)
def capitulo_pre_delete(sender, instance: Capitulo, **kwargs):
    """
    Apaga `mangas/{slug}/cap-{numero}/` quando o capítulo é deletado.

    Skip se a obra-pai está sendo deletada — nesse caso o sinal da Obra
    já vai apagar tudo.
    """
    if instance.obra_id in _obras_em_delete:
        return
    try:
        slug = instance.obra.slug if instance.obra else None
    except Obra.DoesNotExist:
        slug = None
    if not slug:
        return
    # `numero` é DecimalField — formata sem zeros à direita pra casar com upload
    numero = instance.numero
    prefix = f'mangas/{slug}/cap-{numero}/'
    try:
        n = storage.delete_prefix(prefix)
        log.info('R2 cleanup: capítulo %s — %d objetos removidos de %s',
                 instance, n, prefix)
    except Exception as e:
        log.warning('R2 cleanup falhou para capítulo %s (%s): %s',
                    instance, prefix, e)


@receiver(pre_delete, sender=Pagina)
def pagina_pre_delete(sender, instance: Pagina, **kwargs):
    """
    Apaga só o objeto da página específica no R2.

    Skip se a obra-pai está sendo deletada — o sinal da Obra cuida.
    Quando o capítulo está sendo deletado isoladamente, o sinal do
    Capítulo já apaga o prefix inteiro, então também podemos pular.
    Mas como o sinal do Capítulo só corre na cascata da obra (e pulamos
    nesse caso) ou no delete direto do capítulo (e aí o prefix-delete
    cobre as páginas), não precisamos apagar duas vezes. Aqui só
    cuidamos do caso isolado de deletar uma Pagina sozinha.
    """
    # Se o capítulo-pai ou obra-pai está em delete, skip — eles cuidam.
    try:
        if instance.capitulo and instance.capitulo.obra_id in _obras_em_delete:
            return
    except (Capitulo.DoesNotExist, Obra.DoesNotExist):
        pass

    for url in (instance.imagem_url, instance.thumbnail_url):
        key = storage.key_from_public_url(url) if url else None
        if key:
            try:
                storage.delete_object(key)
            except Exception as e:
                log.warning('R2 cleanup falhou para página %s (%s): %s',
                            instance.pk, key, e)


# Cleanup do set quando a transação fecha — evita vazamento entre requests
from django.db.models.signals import post_delete


@receiver(post_delete, sender=Obra)
def obra_post_delete(sender, instance: Obra, **kwargs):
    _obras_em_delete.discard(instance.pk)
