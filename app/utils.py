from flask import current_app
from itsdangerous import URLSafeSerializer, BadSignature


def mascarar_id(id_valor, tipo):
    """Disfarca um ID interno num token opaco e assinado, para nao expor
    chaves primarias sequenciais nos URLs (ex: /auditoria/2 -> /auditoria/<token>).
    Reversivel a partir da SECRET_KEY — nao precisa de guardar nada.
    'tipo' isola os tokens por entidade: um token gerado para 'regra' nunca
    e valido como token de 'utilizador', mesmo que o numero coincida.
    """
    serializer = URLSafeSerializer(current_app.config['SECRET_KEY'], salt=f'id-{tipo}')
    return serializer.dumps(id_valor)


def desmascarar_id(token, tipo):
    """Devolve o ID original, ou None se o token for invalido, adulterado,
    ou nao pertencer a este tipo de entidade."""
    serializer = URLSafeSerializer(current_app.config['SECRET_KEY'], salt=f'id-{tipo}')
    try:
        return serializer.loads(token)
    except BadSignature:
        return None


def obter_por_token(model, token, tipo):
    """Resolve um token de URL para a instancia do modelo correspondente,
    ou None se o token for invalido ou o registo ja nao existir."""
    id_valor = desmascarar_id(token, tipo)
    if id_valor is None:
        return None
    return model.query.get(id_valor)
