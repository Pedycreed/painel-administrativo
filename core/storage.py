"""
Cliente de storage pra Cloudflare R2 (compatível com S3 via boto3).

Variáveis de ambiente esperadas:
    R2_ACCOUNT_ID         - ID da conta Cloudflare
    R2_ACCESS_KEY_ID      - Access key do API token do R2
    R2_SECRET_ACCESS_KEY  - Secret key do API token do R2
    R2_BUCKET             - Nome do bucket (ex: 'mangapanel')
    R2_PUBLIC_URL         - URL pública do bucket (ex: 'https://pub-xxxx.r2.dev'
                            ou 'https://cdn.seudominio.com'). SEM barra no final.

Estrutura de pastas dentro do bucket:
    mangas/{slug}/capa.{ext}                -> capa da obra
    mangas/{slug}/cap-{numero}/p-{NN}.{ext}  -> páginas de um capítulo
"""
import os
from functools import lru_cache
from typing import Optional

import boto3
import certifi
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError

# Python 3.13 no Windows não vem com CA bundle do sistema. Setamos as envs
# que tanto o ssl quanto o requests/urllib3 honram pra encontrar o bundle do
# certifi automaticamente. Idempotente — só seta se não existir.
_CERTIFI_BUNDLE = certifi.where()
os.environ.setdefault('SSL_CERT_FILE', _CERTIFI_BUNDLE)
os.environ.setdefault('REQUESTS_CA_BUNDLE', _CERTIFI_BUNDLE)
os.environ.setdefault('AWS_CA_BUNDLE', _CERTIFI_BUNDLE)


class R2ConfigError(RuntimeError):
    """Variáveis de ambiente do R2 não estão configuradas."""


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise R2ConfigError(
            f'Variável de ambiente {name} não configurada. '
            f'Veja .env.example pra as credenciais necessárias.'
        )
    return value


@lru_cache(maxsize=1)
def get_client():
    """
    Retorna o cliente boto3 configurado pro R2.

    Cacheado: criar cliente boto3 não é gratuito, e ele é thread-safe.
    """
    account_id = _require_env('R2_ACCOUNT_ID')
    access_key = _require_env('R2_ACCESS_KEY_ID')
    secret_key = _require_env('R2_SECRET_ACCESS_KEY')

    endpoint_url = f'https://{account_id}.r2.cloudflarestorage.com'

    # Workaround pra Python 3.13 no Windows que não acha CA bundle do sistema.
    # Se R2_SKIP_TLS_VERIFY=1, desliga a verificação (APENAS DEV LOCAL!).
    # Caso contrário usa o bundle do certifi.
    skip_verify = os.environ.get('R2_SKIP_TLS_VERIFY', '').strip() in ('1', 'true', 'True')
    if skip_verify:
        import logging
        import urllib3
        logging.getLogger(__name__).warning(
            'R2_SKIP_TLS_VERIFY=1 — verificação TLS DESLIGADA. '
            'NUNCA use isso em produção!'
        )
        # Silencia o warning ruidoso do urllib3 sobre TLS desligado
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        verify_param: bool | str = False
    else:
        verify_param = certifi.where()

    return boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        # R2 não usa região mas o boto3 exige algum valor
        region_name='auto',
        verify=verify_param,
        config=Config(
            signature_version='s3v4',
            # Retries automáticos pra falhas transientes de rede
            retries={'max_attempts': 3, 'mode': 'standard'},
        ),
    )


def get_bucket() -> str:
    return _require_env('R2_BUCKET')


def get_public_url(key: str) -> str:
    """Monta a URL pública absoluta pra um objeto do bucket."""
    base = _require_env('R2_PUBLIC_URL').rstrip('/')
    return f'{base}/{key.lstrip("/")}'


def upload_bytes(
    key: str,
    data: bytes,
    content_type: Optional[str] = None,
) -> str:
    """
    Sobe bytes pro R2 e devolve a URL pública.

    - `key`: caminho dentro do bucket (ex: 'mangas/solo/capa.jpg')
    - `data`: conteúdo binário
    - `content_type`: MIME type. Se None, R2 deduz pela extensão.

    Sobrescreve se já existir (mesmo comportamento de upsert).
    """
    client = get_client()
    bucket = get_bucket()

    extra: dict = {}
    if content_type:
        extra['ContentType'] = content_type

    try:
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=data,
            **extra,
        )
    except (BotoCoreError, ClientError) as e:
        raise RuntimeError(f'Falha ao subir {key} pro R2: {e}') from e

    return get_public_url(key)


def delete_object(key: str) -> None:
    """Deleta um objeto. Não erra se não existir."""
    client = get_client()
    bucket = get_bucket()
    try:
        client.delete_object(Bucket=bucket, Key=key)
    except (BotoCoreError, ClientError) as e:
        # Não relança — delete é best-effort, não queremos quebrar fluxos
        # que dependem da limpeza opcional.
        import logging
        logging.getLogger(__name__).warning(
            'Falha ao deletar %s do R2: %s', key, e
        )


def delete_prefix(prefix: str) -> int:
    """
    Deleta TODOS os objetos do bucket que começam com `prefix`.

    Útil pra apagar uma "pasta" inteira (R2/S3 não tem pastas reais, mas
    `mangas/{slug}/` agrupa tudo de uma obra). Usa list+bulk-delete em lotes
    de 1000 (limite da API).

    Retorna o número de objetos deletados. Não erra se a "pasta" não existir.
    Best-effort: loga falhas e segue.
    """
    if not prefix:
        return 0

    client = get_client()
    bucket = get_bucket()
    import logging
    log = logging.getLogger(__name__)

    deleted = 0
    continuation_token: Optional[str] = None

    while True:
        list_kwargs = {'Bucket': bucket, 'Prefix': prefix, 'MaxKeys': 1000}
        if continuation_token:
            list_kwargs['ContinuationToken'] = continuation_token

        try:
            resp = client.list_objects_v2(**list_kwargs)
        except (BotoCoreError, ClientError) as e:
            log.warning('Falha ao listar prefix %s no R2: %s', prefix, e)
            return deleted

        contents = resp.get('Contents', [])
        if not contents:
            return deleted

        # Bulk delete (até 1000 por chamada)
        objects = [{'Key': obj['Key']} for obj in contents]
        try:
            client.delete_objects(
                Bucket=bucket,
                Delete={'Objects': objects, 'Quiet': True},
            )
            deleted += len(objects)
        except (BotoCoreError, ClientError) as e:
            log.warning(
                'Falha ao deletar lote de %s objetos com prefix %s: %s',
                len(objects), prefix, e,
            )

        if not resp.get('IsTruncated'):
            return deleted
        continuation_token = resp.get('NextContinuationToken')


def key_from_public_url(url: str) -> Optional[str]:
    """
    Extrai o key (caminho dentro do bucket) de uma URL pública do R2.

    Ex: 'https://pub-xxx.r2.dev/mangas/solo/capa.jpg' -> 'mangas/solo/capa.jpg'
    Retorna None se a URL estiver vazia ou não bater com R2_PUBLIC_URL.
    """
    if not url:
        return None
    base = os.environ.get('R2_PUBLIC_URL', '').rstrip('/')
    if base and url.startswith(base + '/'):
        return url[len(base) + 1:]
    # Fallback: se a URL é absoluta mas não casa com R2_PUBLIC_URL, retorna None
    if url.startswith('http://') or url.startswith('https://'):
        return None
    # URL já parece ser só a key relativa
    return url.lstrip('/')
