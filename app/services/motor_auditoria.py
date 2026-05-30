from app import db
from app.models.regra_auditoria import RegraAuditoria
from app.models.limiar_autorizacao import LimiarAutorizacao
from app.models.auditoria_aquisicao import AuditoriaAquisicao
from app.models.nao_conformidade import NaoConformidade
from app.models.aquisicao import Aquisicao
from app.models.colaborador import Colaborador
from app.models.orcamento import Orcamento
from decimal import Decimal

# =============================================================================
# DESCRICOES DE VIOLACAO POR REGRA
# Cada regra tem um template de descricao gerado dinamicamente
# com os dados reais da aquisicao violada.
# =============================================================================
DESCRICOES_VIOLACAO = {
    'RN01': lambda a, saldo: (
        f"Saldo orcamental insuficiente — valor da aquisicao "
        f"({a.valor} Kz) excede o saldo disponivel ({saldo} Kz) "
        f"no orcamento do centro de custo {a.id_centro}."
    ),
    'RN04': lambda a, **_: (
        f"Valor da aquisicao invalido — valor registado: {a.valor} Kz. "
        f"O valor deve ser positivo."
    ),
    'RN05': lambda a, nivel_exigido, **_: (
        f"Aprovacao hierarquica insuficiente — valor da aquisicao "
        f"({a.valor} Kz) exige aprovador de nivel minimo {nivel_exigido}, "
        f"mas o aprovador tem nivel {a.aprovador.nivel_hierarquico}."
    ),
    'RN06': lambda a, nivel_exigido, **_: (
        f"Perfil do aprovador incompativel — nivel {a.aprovador.nivel_hierarquico} "
        f"insuficiente para o valor da aquisicao ({a.valor} Kz). "
        f"Nivel minimo exigido: {nivel_exigido}."
    ),
    'RN07': lambda a, **_: (
        f"Solicitante igual ao aprovador — colaborador id {a.id_solicitante} "
        f"aparece como solicitante e aprovador na mesma aquisicao."
    ),
    'RN08': lambda a, **_: (
        f"Solicitante nao identificado — campo id_solicitante nao preenchido "
        f"na aquisicao {a.id_aquisicao}."
    ),
    'RN09': lambda a, **_: (
        f"Documentacao de suporte em falta — campo documento_referencia "
        f"nao preenchido na aquisicao {a.id_aquisicao}."
    ),
    'RN10': lambda a, **_: (
        f"Confirmacao de recepcao em falta — aquisicao {a.id_aquisicao} "
        f"com status '{a.status_aprovacao}' sem confirmacao de recepcao registada."
    ),
    'RN11': lambda a, **_: (
        f"Identificacao da aquisicao em falta — campo id_aquisicao "
        f"nao preenchido ou invalido."
    ),
    'RN12': lambda a, **_: (
        f"Inconsistencia de datas — data de aprovacao ({a.data_aprovacao}) "
        f"anterior a data de solicitacao ({a.data_solicitacao})."
    ),
    'RN13': lambda a, **_: (
        f"Registo duplicado — aquisicao com id {a.id_aquisicao} "
        f"ja existe na base de dados."
    ),
}


# =============================================================================
# FUNCOES AUXILIARES
# =============================================================================

def buscar_saldo_disponivel(aquisicao):
    """Calcula o saldo disponivel no orcamento da aquisicao."""
    orcamento = Orcamento.query.get(aquisicao.id_orcamento)
    if not orcamento:
        return None
    # Soma todas as aquisicoes ja auditadas neste orcamento
    total_executado = db.session.query(
        db.func.sum(Aquisicao.valor)
    ).filter(
        Aquisicao.id_orcamento == aquisicao.id_orcamento,
        Aquisicao.id_aquisicao != aquisicao.id_aquisicao,
        Aquisicao.status_aprovacao == 'aprovado'
    ).scalar() or Decimal('0')
    return orcamento.valor_orcado - total_executado


def buscar_limiar(id_regra, valor):
    """Busca o limiar de autorizacao aplicavel ao valor da aquisicao."""
    limiares = LimiarAutorizacao.query.filter_by(id_regra=id_regra).all()
    for limiar in limiares:
        if limiar.valor_maximo is None:
            if valor >= limiar.valor_minimo:
                return limiar
        else:
            if limiar.valor_minimo <= valor <= limiar.valor_maximo:
                return limiar
    return None


def registar_nao_conformidade(id_auditoria_aquisicao, regra, descricao):
    """Regista uma nao conformidade na base de dados."""
    nc = NaoConformidade(
        id_auditoria_aquisicao=id_auditoria_aquisicao,
        id_regra=regra.id_regra,
        descricao=descricao,
        gravidade=regra.gravidade,
        status='aberta'
    )
    db.session.add(nc)


# =============================================================================
# AVALIACAO DE CADA REGRA
# =============================================================================

def avaliar_regra(aquisicao, regra, regra_rn05):
    """
    Avalia uma aquisicao contra uma regra.
    Devolve (True, descricao) se houver violacao.
    Devolve (False, None) se estiver conforme.
    NAO regista nada — apenas avalia.
    """
    if regra.codigo == 'RN01':
        saldo = buscar_saldo_disponivel(aquisicao)
        if saldo is not None and aquisicao.valor > saldo:
            return True, DESCRICOES_VIOLACAO['RN01'](aquisicao, saldo)

    elif regra.codigo == 'RN04':
        if not aquisicao.valor or aquisicao.valor <= 0:
            return True, DESCRICOES_VIOLACAO['RN04'](aquisicao)

    elif regra.codigo in ('RN05', 'RN06'):
        if regra_rn05:
            limiar = buscar_limiar(regra_rn05.id_regra, aquisicao.valor)
            if limiar:
                aprovador = Colaborador.query.get(aquisicao.id_aprovador)
                if aprovador and aprovador.nivel_hierarquico < limiar.nivel_minimo:
                    return True, DESCRICOES_VIOLACAO[regra.codigo](
                        aquisicao, nivel_exigido=limiar.nivel_minimo
                    )

    elif regra.codigo == 'RN07':
        if aquisicao.id_solicitante == aquisicao.id_aprovador:
            return True, DESCRICOES_VIOLACAO['RN07'](aquisicao)

    elif regra.codigo == 'RN08':
        if not aquisicao.id_solicitante:
            return True, DESCRICOES_VIOLACAO['RN08'](aquisicao)

    elif regra.codigo == 'RN09':
        if not aquisicao.documento_referencia:
            return True, DESCRICOES_VIOLACAO['RN09'](aquisicao)

    elif regra.codigo == 'RN10':
        if not aquisicao.confirmacao_recepcao:
            return True, DESCRICOES_VIOLACAO['RN10'](aquisicao)

    elif regra.codigo == 'RN11':
        if not aquisicao.id_aquisicao:
            return True, DESCRICOES_VIOLACAO['RN11'](aquisicao)

    elif regra.codigo == 'RN12':
        if aquisicao.data_aprovacao and aquisicao.data_solicitacao:
            if aquisicao.data_aprovacao < aquisicao.data_solicitacao:
                return True, DESCRICOES_VIOLACAO['RN12'](aquisicao)

    return False, None


# =============================================================================
# MOTOR PRINCIPAL
# =============================================================================

def executar_auditoria(auditoria, periodo):
    """
    Executa uma sessao de auditoria completa.
    Analisa todas as aquisicoes do periodo e aplica todas as regras activas.
    """
    try:
        regras = RegraAuditoria.query.filter_by(ativa=True).all()
        regra_rn05 = RegraAuditoria.query.filter_by(codigo='RN05').first()

        aquisicoes = Aquisicao.query.join(Orcamento).filter(
            Orcamento.periodo == periodo
        ).all()

        total_transacoes = len(aquisicoes)
        total_nao_conformidades = 0

        for aquisicao in aquisicoes:
            # PASSO 1 — Avalia todas as regras e recolhe violacoes
            violacoes = []
            for regra in regras:
                houve_violacao, descricao = avaliar_regra(
                    aquisicao, regra, regra_rn05
                )
                if houve_violacao:
                    violacoes.append((regra, descricao))

            # PASSO 2 — Determina resultado e insere em auditoria_aquisicao
            resultado = 'nao_conforme' if violacoes else 'conforme'
            aa = AuditoriaAquisicao(
                id_auditoria=auditoria.id_auditoria,
                id_aquisicao=aquisicao.id_aquisicao,
                resultado=resultado
            )
            db.session.add(aa)
            db.session.flush()  # Gera o id_auditoria_aquisicao

            # PASSO 3 — Regista cada nao conformidade com o id correcto
            if violacoes:
                total_nao_conformidades += 1
                for regra, descricao in violacoes:
                    registar_nao_conformidade(
                        aa.id_auditoria_aquisicao, regra, descricao
                    )

        auditoria.total_transacoes = total_transacoes
        auditoria.total_nao_conformidades = total_nao_conformidades
        auditoria.status = 'concluida'

        db.session.commit()
        return True, "Auditoria concluida com sucesso."

    except Exception as e:
        db.session.rollback()
        auditoria.status = 'erro'
        db.session.commit()
        return False, str(e)
