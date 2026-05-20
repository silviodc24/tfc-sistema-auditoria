use sistema_auditoria;

create table utilizador (
    id_utilizador  INT          NOT NULL AUTO_INCREMENT,
    nome           VARCHAR(100) NOT NULL,
    email          VARCHAR(150) NOT NULL,
    perfil         ENUM('auditor','administrador') NOT NULL DEFAULT 'auditor',
    ativo          BOOLEAN      NOT NULL DEFAULT TRUE,

    CONSTRAINT pk_utilizador PRIMARY KEY (id_utilizador),
    CONSTRAINT uq_utilizador_email UNIQUE (email)
);

CREATE TABLE colaborador (
    id_colaborador    INT          NOT NULL AUTO_INCREMENT,
    nome              VARCHAR(100) NOT NULL,
    email             VARCHAR(150) NOT NULL,
    nivel_hierarquico INT          NOT NULL,
    ativo             BOOLEAN      NOT NULL DEFAULT TRUE,

    CONSTRAINT pk_colaborador PRIMARY KEY (id_colaborador),
    CONSTRAINT uq_colaborador_email UNIQUE (email),
    CONSTRAINT ck_colaborador_nivel CHECK (nivel_hierarquico BETWEEN 1 AND 6)
);

CREATE TABLE centro_custo (
    id_centro      INT          NOT NULL AUTO_INCREMENT,
    nome           VARCHAR(100) NOT NULL,
    departamento   VARCHAR(100) NOT NULL,
    id_responsavel INT          NOT NULL,
    ativo          BOOLEAN      NOT NULL DEFAULT TRUE,

    CONSTRAINT pk_centro_custo PRIMARY KEY (id_centro),
    CONSTRAINT fk_centro_responsavel
        FOREIGN KEY (id_responsavel) REFERENCES colaborador(id_colaborador)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE orcamento (
    id_orcamento     INT           NOT NULL AUTO_INCREMENT,
    id_centro        INT           NOT NULL,
    periodo          VARCHAR(20)   NOT NULL,
    valor_orcado     DECIMAL(15,2) NOT NULL,
    valor_executado  DECIMAL(15,2) NOT NULL DEFAULT 0.00,

    CONSTRAINT pk_orcamento PRIMARY KEY (id_orcamento),
    CONSTRAINT fk_orcamento_centro
        FOREIGN KEY (id_centro) REFERENCES centro_custo(id_centro)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT ck_orcamento_valor_orcado CHECK (valor_orcado > 0),
    CONSTRAINT ck_orcamento_valor_executado CHECK (valor_executado >= 0),
    CONSTRAINT uq_orcamento_centro_periodo UNIQUE (id_centro, periodo)
);

CREATE TABLE aquisicao (
    id_aquisicao         INT           NOT NULL AUTO_INCREMENT,
    id_centro            INT           NOT NULL,
    id_orcamento         INT           NOT NULL,
    id_solicitante       INT           NOT NULL,
    id_aprovador         INT           NOT NULL,
    data_solicitacao     DATE          NOT NULL,
    data_aprovacao       DATE          NULL,
    valor                DECIMAL(15,2) NOT NULL,
    descricao            VARCHAR(255)  NOT NULL,
    tipo_aquisicao       ENUM('bem','servico') NOT NULL,
    documento_referencia VARCHAR(100)  NULL,
    status_aprovacao     ENUM('aprovado','pendente','rejeitado') NOT NULL DEFAULT 'pendente',
    origem_dado          ENUM('csv','erp','manual') NOT NULL DEFAULT 'csv',
    confirmacao_recepcao BOOLEAN       NOT NULL DEFAULT FALSE,

    CONSTRAINT pk_aquisicao PRIMARY KEY (id_aquisicao),
    CONSTRAINT fk_aquisicao_centro
        FOREIGN KEY (id_centro) REFERENCES centro_custo(id_centro)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_aquisicao_orcamento
        FOREIGN KEY (id_orcamento) REFERENCES orcamento(id_orcamento)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_aquisicao_solicitante
        FOREIGN KEY (id_solicitante) REFERENCES colaborador(id_colaborador)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_aquisicao_aprovador
        FOREIGN KEY (id_aprovador) REFERENCES colaborador(id_colaborador)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT ck_aquisicao_valor CHECK (valor > 0)
);


CREATE TABLE regra_auditoria (
    id_regra         INT           NOT NULL AUTO_INCREMENT,
    codigo           VARCHAR(10)   NOT NULL,
    nome             VARCHAR(100)  NOT NULL,
    descricao        TEXT          NOT NULL,
    campo            VARCHAR(80)   NOT NULL,
    operador         ENUM('igual','diferente','maior','maior_igual','menor','menor_igual','nulo','nao_nulo','igual_campos') NOT NULL,
    valor_referencia DECIMAL(15,2) NULL,
    tipo_regra       ENUM('orcamental','autorizacao','procedimental','integridade') NOT NULL,
    gravidade        ENUM('baixa','media','alta','critica') NOT NULL DEFAULT 'alta',
    ativa            BOOLEAN       NOT NULL DEFAULT TRUE,

    CONSTRAINT pk_regra_auditoria PRIMARY KEY (id_regra),
    CONSTRAINT uq_regra_codigo UNIQUE (codigo)
);

CREATE TABLE limiar_autorizacao (
    id_limiar    INT           NOT NULL AUTO_INCREMENT,
    id_regra     INT           NOT NULL,
    valor_minimo DECIMAL(15,2) NOT NULL,
    valor_maximo DECIMAL(15,2) NULL,
    nivel_minimo INT           NOT NULL,

    CONSTRAINT pk_limiar_autorizacao PRIMARY KEY (id_limiar),
    CONSTRAINT fk_limiar_regra
        FOREIGN KEY (id_regra) REFERENCES regra_auditoria(id_regra)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT ck_limiar_valor_minimo CHECK (valor_minimo >= 0),
    CONSTRAINT ck_limiar_nivel CHECK (nivel_minimo BETWEEN 1 AND 6),
    CONSTRAINT ck_limiar_intervalo CHECK (
        valor_maximo IS NULL OR valor_maximo > valor_minimo
    )
);

CREATE TABLE auditoria (
    id_auditoria            INT          NOT NULL AUTO_INCREMENT,
    id_utilizador           INT          NOT NULL,
    data_execucao           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    periodo_analisado       VARCHAR(20)  NOT NULL,
    total_transacoes        INT          NOT NULL DEFAULT 0,
    total_nao_conformidades INT          NOT NULL DEFAULT 0,
    status                  ENUM('em_curso','concluida','erro') NOT NULL DEFAULT 'em_curso',

    CONSTRAINT pk_auditoria PRIMARY KEY (id_auditoria),
    CONSTRAINT fk_auditoria_utilizador
        FOREIGN KEY (id_utilizador) REFERENCES utilizador(id_utilizador)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

CREATE TABLE auditoria_aquisicao (
    id_auditoria_aquisicao INT  NOT NULL AUTO_INCREMENT,
    id_auditoria           INT  NOT NULL,
    id_aquisicao           INT  NOT NULL,
    resultado              ENUM('conforme','nao_conforme','inconclusivo') NOT NULL,

    CONSTRAINT pk_auditoria_aquisicao PRIMARY KEY (id_auditoria_aquisicao),
    CONSTRAINT fk_aa_auditoria
        FOREIGN KEY (id_auditoria) REFERENCES auditoria(id_auditoria)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_aa_aquisicao
        FOREIGN KEY (id_aquisicao) REFERENCES aquisicao(id_aquisicao)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT uq_aa_auditoria_aquisicao
        UNIQUE (id_auditoria, id_aquisicao)
);

CREATE TABLE nao_conformidade (
    id_nao_conformidade    INT      NOT NULL AUTO_INCREMENT,
    id_auditoria_aquisicao INT      NOT NULL,
    id_regra               INT      NOT NULL,
    descricao              TEXT     NOT NULL,
    gravidade              ENUM('baixa','media','alta','critica') NOT NULL,
    data_registo           DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status                 ENUM('aberta','em_analise','resolvida','ignorada') NOT NULL DEFAULT 'aberta',
    comentario_auditor     TEXT     NULL,

    CONSTRAINT pk_nao_conformidade PRIMARY KEY (id_nao_conformidade),
    CONSTRAINT fk_nc_auditoria_aquisicao
        FOREIGN KEY (id_auditoria_aquisicao) REFERENCES auditoria_aquisicao(id_auditoria_aquisicao)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_nc_regra
        FOREIGN KEY (id_regra) REFERENCES regra_auditoria(id_regra)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- Índices da tabela aquisicao
CREATE INDEX idx_aquisicao_centro       ON aquisicao(id_centro);
CREATE INDEX idx_aquisicao_orcamento    ON aquisicao(id_orcamento);
CREATE INDEX idx_aquisicao_solicitante  ON aquisicao(id_solicitante);
CREATE INDEX idx_aquisicao_aprovador    ON aquisicao(id_aprovador);
CREATE INDEX idx_aquisicao_data         ON aquisicao(data_solicitacao);

-- Índices da tabela nao_conformidade
CREATE INDEX idx_nc_gravidade           ON nao_conformidade(gravidade);
CREATE INDEX idx_nc_status              ON nao_conformidade(status);
CREATE INDEX idx_nc_regra               ON nao_conformidade(id_regra);
CREATE INDEX idx_nc_data                ON nao_conformidade(data_registo);

-- Índices da tabela auditoria
CREATE INDEX idx_auditoria_periodo      ON auditoria(periodo_analisado);
CREATE INDEX idx_auditoria_status       ON auditoria(status);

-- Índices da tabela auditoria_aquisicao
CREATE INDEX idx_aa_resultado           ON auditoria_aquisicao(resultado);
