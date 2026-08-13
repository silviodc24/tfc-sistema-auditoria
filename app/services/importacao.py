import csv
import io
from app import db
from app.models.colaborador import Colaborador
from app.models.centro_custo import CentroCusto
from app.models.orcamento import Orcamento
from app.models.aquisicao import Aquisicao
from datetime import datetime
from decimal import Decimal


# =============================================================================
# FUNCOES AUXILIARES
# =============================================================================

def ler_csv(ficheiro):
    """Le um ficheiro CSV enviado via form e devolve lista de dicionarios."""
    conteudo = ficheiro.read().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(conteudo))
    return list(reader)


def parse_bool(valor):
    """Converte string para booleano."""
    return str(valor).strip().upper() in ('1', 'TRUE', 'SIM', 'YES')


def parse_decimal(valor):
    """Converte string para Decimal."""
    try:
        return Decimal(str(valor).strip().replace(',', '.'))
    except Exception:
        return None


def parse_data(valor):
    """Converte string para date."""
    valor = str(valor).strip()
    if not valor:
        return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
        try:
            return datetime.strptime(valor, fmt).date()
        except ValueError:
            continue
    return None


# =============================================================================
# IMPORTACAO DE COLABORADORES
# =============================================================================

def importar_colaboradores(ficheiro):
    """
    Importa colaboradores a partir de um ficheiro CSV.
    Actualiza o registo se o email ja existir.
    Devolve (sucesso, mensagem, total_importados, erros).
    """
    erros = []
    total = 0

    try:
        linhas = ler_csv(ficheiro)

        for i, linha in enumerate(linhas, start=2):
            try:
                nome = linha.get('nome', '').strip()
                email = linha.get('email', '').strip()
                nivel = linha.get('nivel_hierarquico', '').strip()
                ativo = parse_bool(linha.get('ativo', '1'))

                if not nome or not email or not nivel:
                    erros.append(f"Linha {i}: campos obrigatórios em falta.")
                    continue

                nivel_int = int(nivel)
                if nivel_int not in range(1, 7):
                    erros.append(f"Linha {i}: nível hierárquico inválido — {nivel}.")
                    continue

                existente = Colaborador.query.filter_by(email=email).first()
                if existente:
                    existente.nome = nome
                    existente.nivel_hierarquico = nivel_int
                    existente.ativo = ativo
                else:
                    c = Colaborador(
                        nome=nome,
                        email=email,
                        nivel_hierarquico=nivel_int,
                        ativo=ativo
                    )
                    db.session.add(c)

                total += 1

            except Exception as e:
                erros.append(f"Linha {i}: erro — {str(e)}")

        db.session.commit()
        return True, f"{total} colaborador(es) importado(s) com sucesso.", total, erros

    except Exception as e:
        db.session.rollback()
        return False, f"Erro ao processar ficheiro: {str(e)}", 0, erros


# =============================================================================
# IMPORTACAO DE CENTROS DE CUSTO
# =============================================================================

def importar_centros_custo(ficheiro):
    """
    Importa centros de custo a partir de um ficheiro CSV.
    O id_responsavel deve corresponder a um colaborador existente.
    """
    erros = []
    total = 0

    try:
        linhas = ler_csv(ficheiro)

        for i, linha in enumerate(linhas, start=2):
            try:
                nome = linha.get('nome', '').strip()
                departamento = linha.get('departamento', '').strip()
                responsavel_id = linha.get('responsavel_id', '').strip()
                ativo = parse_bool(linha.get('ativo', '1'))

                if not nome or not departamento or not responsavel_id:
                    erros.append(f"Linha {i}: campos obrigatórios em falta.")
                    continue

                responsavel = Colaborador.query.get(int(responsavel_id))
                if not responsavel:
                    erros.append(f"Linha {i}: colaborador responsável id={responsavel_id} não encontrado.")
                    continue

                existente = CentroCusto.query.filter_by(nome=nome).first()
                if existente:
                    existente.departamento = departamento
                    existente.id_responsavel = responsavel.id_colaborador
                    existente.ativo = ativo
                else:
                    cc = CentroCusto(
                        nome=nome,
                        departamento=departamento,
                        id_responsavel=responsavel.id_colaborador,
                        ativo=ativo
                    )
                    db.session.add(cc)

                total += 1

            except Exception as e:
                erros.append(f"Linha {i}: erro — {str(e)}")

        db.session.commit()
        return True, f"{total} centro(s) de custo importado(s) com sucesso.", total, erros

    except Exception as e:
        db.session.rollback()
        return False, f"Erro ao processar ficheiro: {str(e)}", 0, erros


# =============================================================================
# IMPORTACAO DE ORCAMENTOS
# =============================================================================

def importar_orcamentos(ficheiro):
    """
    Importa orçamentos a partir de um ficheiro CSV.
    O id_centro deve corresponder a um centro de custo existente.
    """
    erros = []
    total = 0

    try:
        linhas = ler_csv(ficheiro)

        for i, linha in enumerate(linhas, start=2):
            try:
                id_centro = linha.get('id_centro', '').strip()
                periodo = linha.get('periodo', '').strip()
                valor_orcado = parse_decimal(linha.get('valor_orcado', ''))
                valor_executado = parse_decimal(linha.get('valor_executado', '0'))

                if not id_centro or not periodo or not valor_orcado:
                    erros.append(f"Linha {i}: campos obrigatórios em falta.")
                    continue

                centro = CentroCusto.query.get(int(id_centro))
                if not centro:
                    erros.append(f"Linha {i}: centro de custo id={id_centro} não encontrado.")
                    continue

                if valor_orcado <= 0:
                    erros.append(f"Linha {i}: valor orçado deve ser positivo.")
                    continue

                existente = Orcamento.query.filter_by(
                    id_centro=centro.id_centro,
                    periodo=periodo
                ).first()

                if existente:
                    existente.valor_orcado = valor_orcado

                    # valor_executado representa despesa historica anterior a
                    # este sistema (ex: ERP). Uma vez que o orcamento ja tem
                    # aquisicoes registadas aqui, reescreve-lo causaria dupla
                    # contagem no calculo de saldo da RN01 — essa despesa
                    # ficaria contada tanto em valor_executado como na soma
                    # das aquisicoes. So aceita a alteracao enquanto o
                    # orcamento ainda nao tiver aquisicoes associadas.
                    tem_aquisicoes = Aquisicao.query.filter_by(
                        id_orcamento=existente.id_orcamento
                    ).first() is not None

                    if tem_aquisicoes:
                        novo_valor_executado = valor_executado or Decimal('0')
                        if novo_valor_executado != existente.valor_executado:
                            erros.append(
                                f"Linha {i}: valor_executado não foi actualizado — o orçamento "
                                f"id={existente.id_orcamento} já tem aquisições registadas; "
                                f"alterá-lo causaria dupla contagem no saldo (RN01). "
                                f"Valor mantido: {existente.valor_executado}."
                            )
                    else:
                        existente.valor_executado = valor_executado or Decimal('0')
                else:
                    o = Orcamento(
                        id_centro=centro.id_centro,
                        periodo=periodo,
                        valor_orcado=valor_orcado,
                        valor_executado=valor_executado or Decimal('0')
                    )
                    db.session.add(o)

                total += 1

            except Exception as e:
                erros.append(f"Linha {i}: erro — {str(e)}")

        db.session.commit()
        return True, f"{total} orçamento(s) importado(s) com sucesso.", total, erros

    except Exception as e:
        db.session.rollback()
        return False, f"Erro ao processar ficheiro: {str(e)}", 0, erros


# =============================================================================
# IMPORTACAO DE AQUISICOES
# =============================================================================

def importar_aquisicoes(ficheiro):
    """
    Importa aquisições a partir de um ficheiro CSV.
    Valida referências a colaboradores, centros de custo e orçamentos.
    """
    erros = []
    total = 0

    try:
        linhas = ler_csv(ficheiro)

        for i, linha in enumerate(linhas, start=2):
            try:
                id_centro = linha.get('id_centro', '').strip()
                id_orcamento = linha.get('id_orcamento', '').strip()
                id_solicitante = linha.get('id_solicitante', '').strip()
                id_aprovador = linha.get('id_aprovador', '').strip()
                data_solicitacao = parse_data(linha.get('data_solicitacao', ''))
                data_aprovacao = parse_data(linha.get('data_aprovacao', ''))
                valor = parse_decimal(linha.get('valor', ''))
                descricao = linha.get('descricao', '').strip()
                tipo_aquisicao = linha.get('tipo_aquisicao', '').strip().lower()
                documento_referencia = linha.get('documento_referencia', '').strip() or None
                status_aprovacao = linha.get('status_aprovacao', 'pendente').strip().lower()
                origem_dado = linha.get('origem_dado', 'csv').strip().lower()
                confirmacao_recepcao = parse_bool(linha.get('confirmacao_recepcao', '0'))

                # Validacoes obrigatorias
                if not all([id_centro, id_orcamento, id_solicitante,
                            id_aprovador, data_solicitacao, valor, descricao]):
                    erros.append(f"Linha {i}: campos obrigatórios em falta.")
                    continue

                if valor <= 0:
                    erros.append(f"Linha {i}: valor deve ser positivo.")
                    continue

                if tipo_aquisicao not in ('bem', 'servico'):
                    erros.append(f"Linha {i}: tipo_aquisicao inválido — use 'bem' ou 'servico'.")
                    continue

                # Validacao de referencias
                centro = CentroCusto.query.get(int(id_centro))
                if not centro:
                    erros.append(f"Linha {i}: centro de custo id={id_centro} não encontrado.")
                    continue

                orcamento = Orcamento.query.get(int(id_orcamento))
                if not orcamento:
                    erros.append(f"Linha {i}: orçamento id={id_orcamento} não encontrado.")
                    continue

                solicitante = Colaborador.query.get(int(id_solicitante))
                if not solicitante:
                    erros.append(f"Linha {i}: solicitante id={id_solicitante} não encontrado.")
                    continue

                aprovador = Colaborador.query.get(int(id_aprovador))
                if not aprovador:
                    erros.append(f"Linha {i}: aprovador id={id_aprovador} não encontrado.")
                    continue

                # documento_referencia identifica univocamente o documento de
                # origem (ex: numero de factura/nota de encomenda). Quando
                # presente, reimportar a mesma referencia actualiza o registo
                # existente em vez de criar um duplicado — sem isso, cada
                # reimportacao do mesmo CSV duplicava a aquisicao e inflacionava
                # a despesa considerada no saldo da RN01.
                existente = None
                if documento_referencia:
                    existente = Aquisicao.query.filter_by(
                        documento_referencia=documento_referencia
                    ).first()

                if existente:
                    existente.id_centro = centro.id_centro
                    existente.id_orcamento = orcamento.id_orcamento
                    existente.id_solicitante = solicitante.id_colaborador
                    existente.id_aprovador = aprovador.id_colaborador
                    existente.data_solicitacao = data_solicitacao
                    existente.data_aprovacao = data_aprovacao
                    existente.valor = valor
                    existente.descricao = descricao
                    existente.tipo_aquisicao = tipo_aquisicao
                    existente.status_aprovacao = status_aprovacao
                    existente.origem_dado = origem_dado
                    existente.confirmacao_recepcao = confirmacao_recepcao
                else:
                    a = Aquisicao(
                        id_centro=centro.id_centro,
                        id_orcamento=orcamento.id_orcamento,
                        id_solicitante=solicitante.id_colaborador,
                        id_aprovador=aprovador.id_colaborador,
                        data_solicitacao=data_solicitacao,
                        data_aprovacao=data_aprovacao,
                        valor=valor,
                        descricao=descricao,
                        tipo_aquisicao=tipo_aquisicao,
                        documento_referencia=documento_referencia,
                        status_aprovacao=status_aprovacao,
                        origem_dado=origem_dado,
                        confirmacao_recepcao=confirmacao_recepcao
                    )
                    db.session.add(a)

                total += 1

            except Exception as e:
                erros.append(f"Linha {i}: erro — {str(e)}")

        db.session.commit()
        return True, f"{total} aquisição(ões) importada(s) com sucesso.", total, erros

    except Exception as e:
        db.session.rollback()
        return False, f"Erro ao processar ficheiro: {str(e)}", 0, erros