-- =============================================================================
-- 03_seed.sql
-- Dados iniciais obrigatórios do sistema
-- Empresa NS Aplicação — Sistema de Auditoria de Conformidade
-- =============================================================================

USE sistema_auditoria;

-- =============================================================================
-- UTILIZADORES INICIAIS
-- =============================================================================
INSERT INTO utilizador (nome, email, perfil, ativo) VALUES
('Administrador do Sistema', 'admin@ns-aplicacao.ao',    'administrador', TRUE),
('Auditor Chefe',            'auditor@ns-aplicacao.ao',  'auditor',        TRUE);



-- =============================================================================
-- REGRAS DE AUDITORIA
-- 16 regras pré-carregadas correspondentes às regras de negócio definidas.
-- valor_referencia = NULL para regras sem limiar numérico.
-- O administrador pode ajustar valor_referencia e ativa via interface.
-- =============================================================================

INSERT INTO regra_auditoria
    (codigo, nome, descricao, campo, operador, valor_referencia, tipo_regra, gravidade)
VALUES

-- ============================================================================
-- REGRAS ORÇAMENTAIS
-- ============================================================================

('RN01', 'Saldo orçamental insuficiente',
 'Nenhum processo de aquisição pode ser executado quando o valor solicitado ultrapassar o saldo disponível no orçamento aprovado para o respectivo centro de custo.',
 'valor', 'maior', NULL, 'orcamental', 'critica'),

('RN02', 'Centro de custo inválido ou inactivo',
 'Toda solicitação de aquisição deve estar obrigatoriamente associada a um centro de custo válido e activo.',
 'id_centro', 'nao_nulo', NULL, 'orcamental', 'critica'),

('RN03', 'Período orçamental não definido',
 'Toda aquisição deve estar vinculada a um período orçamental previamente definido.',
 'id_orcamento', 'nao_nulo', NULL, 'orcamental', 'alta'),

('RN04', 'Dados obrigatórios em falta',
 'Toda solicitação de aquisição deve possuir valor monetário positivo, data válida e descrição do objecto da aquisição.',
 'valor', 'maior', 0.00, 'orcamental', 'critica'),

-- ============================================================================
-- REGRAS DE AUTORIZAÇÃO
-- ============================================================================

('RN05', 'Aprovação hierárquica insuficiente',
 'Toda aquisição acima do limite financeiro definido deve possuir aprovação formal de um responsável hierárquico autorizado.',
 'valor', 'maior', NULL, 'autorizacao', 'critica'),

('RN06', 'Perfil de aprovador incompatível',
 'O aprovador da aquisição deve possuir perfil funcional compatível com o nível de autorização exigido.',
 'nivel_hierarquico_aprovador', 'maior_igual', NULL, 'autorizacao', 'alta'),

('RN07', 'Solicitante igual ao aprovador',
 'O utilizador responsável pela solicitação da aquisição não pode ser o mesmo responsável pela sua aprovação final.',
 'id_solicitante', 'igual_campos', NULL, 'autorizacao', 'critica'),

-- ============================================================================
-- REGRAS PROCEDIMENTAIS
-- ============================================================================

('RN08', 'Solicitante não identificado',
 'Toda aquisição deve possuir um responsável solicitante devidamente identificado no sistema.',
 'id_solicitante', 'nao_nulo', NULL, 'procedimental', 'alta'),

('RN09', 'Documentação de suporte em falta',
 'Toda aquisição deve possuir documentação de suporte obrigatória.',
 'documento_referencia', 'nao_nulo', NULL, 'procedimental', 'alta'),

('RN10', 'Pagamento sem confirmação de recepção',
 'Nenhuma aquisição pode prosseguir para pagamento sem confirmação prévia da recepção do bem ou serviço contratado.',
 'confirmacao_recepcao', 'igual', NULL, 'procedimental', 'alta'),

-- ============================================================================
-- REGRAS DE INTEGRIDADE
-- ============================================================================

('RN11', 'Identificação única em falta',
 'Todo processo de aquisição deve possuir identificação única e rastreável.',
 'id_aquisicao', 'nao_nulo', NULL, 'integridade', 'critica'),

('RN12', 'Inconsistência de datas',
 'Toda aquisição deve possuir datas consistentes entre solicitação e aprovação.',
 'data_aprovacao', 'maior_igual', NULL, 'integridade', 'alta'),

('RN13', 'Registo duplicado detectado',
 'Nenhum registo pode ser duplicado para o mesmo processo de aquisição.',
 'id_aquisicao', 'igual', NULL, 'integridade', 'critica'),

-- ============================================================================
-- REGRAS DE AUDITORIA
-- ============================================================================

('RN14', 'Classificação automática de não conformidade',
 'Processos que violem qualquer regra de negócio devem ser automaticamente classificados como não conformes.',
 'resultado', 'igual', NULL, 'integridade', 'critica'),

('RN15', 'Registo de não conformidade incompleto',
 'Toda não conformidade identificada deve ser registada com descrição da irregularidade, data da detecção e responsável associado.',
 'descricao', 'nao_nulo', NULL, 'integridade', 'alta'),

('RN16', 'Relatório de auditoria indisponível',
 'O sistema deve permitir a geração de relatórios contendo as não conformidades detectadas e respectivas evidências.',
 'relatorio', 'nao_nulo', NULL, 'integridade', 'media');
 
