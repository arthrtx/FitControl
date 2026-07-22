# FitControl

Sistema de gestão de academia desenvolvido em Python com interface gráfica.

## Versão atual
v3.0.0

## Funcionalidades

### Gestão de alunos
- Registo e edição de alunos.
- Gestão de planos.
- Pagamentos.
- Controlo de presenças.
- Sistema de lixeira e restauração de alunos excluídos.

### Segurança e autenticação
- Sistema de login.
- Gestão de sessões.
- Registo de tentativas falhadas.
- Bloqueio temporário após erros de autenticação.
- Sistema de logs.

### Gestão de funcionários
- Criação de funcionários.
- Edição de dados.
- Alteração de permissões.
- Remoção de funcionários.
- Diferentes níveis de acesso.

### Permissões

Administrador:
- Acesso total ao sistema.
- Gestão de funcionários.
- Configurações.

Funcionário:
- Acesso limitado às funcionalidades permitidas.

### Dashboard
- Total de alunos.
- Pagamentos.
- Presenças.
- Distribuição por planos.
- Resumo geral da academia.

## Melhorias da versão 3.0

- Novo sistema de autenticação.
- Nova interface de login.
- Sistema de acessos e permissões.
- Administrador temporário inicial.
- Melhor organização dos módulos.
- Separação entre lógica, interface e segurança.

## Execução

Windows:
run.bat
ou:
python run_gui.py

## Histórico

### v3.0.0
- Segurança e gestão de utilizadores adicionadas.

### v2.0.0
- Nova arquitetura modular.
- Nova interface gráfica.
- Separação entre módulos e interface.

### v1.0.0
- Primeira versão funcional.
