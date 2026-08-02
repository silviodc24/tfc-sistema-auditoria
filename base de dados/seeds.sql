-- =============================================================================
-- 03_seed.sql
-- Dados iniciais obrigatórios do sistema
-- Empresa NS Aplicação — Sistema de Auditoria de Conformidade
-- =============================================================================

USE sistema_auditoria;

-- =============================================================================
-- UTILIZADORES INICIAIS
-- =============================================================================
INSERT INTO utilizador (nome, email, password_hash, perfil, ativo) VALUES
('Administrador do Sistema', 'admin@ns-aplicacao.ao', 'scrypt:32768:8:1$PLLgkShWo4EFH4X2$a0ec7bc4b3c0213ab2e935bf3b0e9374ab5775d0c0f56582d98c2eab8e8bfc84c5266fa999755c06053cb750e8e527fce92c9783ac23bd585113bcbf72e33889', 'administrador', TRUE),
('Auditor Chefe', 'auditor@ns-aplicacao.ao', 'scrypt:32768:8:1$PLLgkShWo4EFH4X2$a0ec7bc4b3c0213ab2e935bf3b0e9374ab5775d0c0f56582d98c2eab8e8bfc84c5266fa999755c06053cb750e8e527fce92c9783ac23bd585113bcbf72e33889', 'auditor', TRUE);



-- =============================================================================
-- REGRAS DE AUDITORIA
-- 13 regras pré-carregadas correspondentes às regras de negócio definidas.
-- valor_referencia = NULL para regras sem limiar numérico.
-- O administrador pode ajustar valor_referencia e ativa via interface.
-- =============================================================================

INSERT INTO regra_auditoria
    (codigo, nome, descricao, campo, operador, valor_referencia, tipo_regra, gravidade)
VALUES

('RN01', 'Saldo orçamental insuficiente',
 'Saldo orçamental disponível deve ser suficiente para cobrir o valor da aquisição.',
 'valor', 'maior', NULL, 'orcamental', 'critica'),

('RN02', 'Centro de custo inválido ou inactivo',
 'Centro de custo deve ser válido e activo.',
 'id_centro', 'nao_nulo', NULL, 'integridade', 'critica'),

('RN03', 'Período orçamental não definido',
 'O período orçamental deve estar definido.',
 'id_orcamento', 'nao_nulo', NULL, 'orcamental', 'alta'),

('RN04', 'Dados obrigatórios em falta',
 'Dados obrigatórios devem estar preenchidos.',
 'valor', 'maior', 0.00, 'integridade', 'critica'),

('RN05', 'Aprovação hierárquica insuficiente',
 'O nível hierárquico do aprovador deve ser compatível com o valor da aquisição.',
 'valor', 'maior', NULL, 'autorizacao', 'critica'),

('RN06', 'Perfil de aprovador incompatível',
 'O perfil do aprovador deve ser compatível com o valor da aquisição.',
 'nivel_hierarquico_aprovador', 'maior_igual', NULL, 'autorizacao', 'alta'),

('RN07', 'Solicitante igual ao aprovador',
 'O solicitante não pode ser o mesmo colaborador que o aprovador.',
 'id_solicitante', 'igual_campos', NULL, 'integridade', 'critica'),

('RN08', 'Solicitante não identificado',
 'O solicitante deve estar identificado na aquisição.',
 'id_solicitante', 'nao_nulo', NULL, 'procedimental', 'alta'),

('RN09', 'Documentação de suporte em falta',
 'A aquisição deve ter documentação de suporte registada.',
 'documento_referencia', 'nao_nulo', NULL, 'procedimental', 'alta'),

('RN10', 'Pagamento sem confirmação de recepção',
 'A aquisição deve ter confirmação de recepção registada.',
 'confirmacao_recepcao', 'igual', NULL, 'procedimental', 'alta'),

('RN11', 'Identificação única em falta',
 'A aquisição deve ter identificação válida e preenchida.',
 'id_aquisicao', 'nao_nulo', NULL, 'integridade', 'critica'),

('RN12', 'Inconsistência de datas',
 'A data de aprovação deve ser posterior à data de solicitação.',
 'data_aprovacao', 'maior_igual', NULL, 'integridade', 'alta'),

('RN13', 'Registo duplicado detectado',
 'Não podem existir registos duplicados de aquisição.',
 'id_aquisicao', 'igual', NULL, 'integridade', 'critica');


 -- =============================================================================
-- LIMIARES DE AUTORIZAÇÃO
-- Configuração inicial para RN05 e RN06.
-- Valores fictícios para a Empresa NS Aplicação.
-- Ajustáveis pelo administrador via interface.
-- =============================================================================
INSERT INTO limiar_autorizacao (id_regra, valor_minimo, valor_maximo, nivel_minimo)
SELECT id_regra, 0.00, 499999.99, 2
FROM regra_auditoria WHERE codigo = 'RN05'
UNION ALL
SELECT id_regra, 500000.00, 999999.99, 3
FROM regra_auditoria WHERE codigo = 'RN05'
UNION ALL
SELECT id_regra, 1000000.00, 4999999.99, 4
FROM regra_auditoria WHERE codigo = 'RN05'
UNION ALL
SELECT id_regra, 5000000.00, NULL, 5
FROM regra_auditoria WHERE codigo = 'RN05';
