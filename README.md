# Atualizações do Projeto FitControl

## Versão Atual 3.0

Nesta atualização foram adicionadas melhorias na segurança, organização do sistema e gestão de utilizadores, tornando o FitControl mais completo e preparado para diferentes níveis de acesso.

---

## Principais Atualizações

### 1. Estatísticas melhoradas
- Dashboard com mais informações do sistema.
- Adição de novos indicadores de funcionamento.
- Melhor visualização dos dados da academia.
- Contadores de alunos, pagamentos, presenças e outros dados relevantes.

---

### 2. Novo sistema de autenticação
- Implementado sistema de login com validação de utilizadores.
- Gestão de sessões ativas.
- Registo de tentativas falhadas.
- Bloqueio temporário após várias tentativas incorretas.
- Registo de eventos de autenticação através de logs.

---

### 3. Sistema de acessos
- Adicionado controlo de permissões.
- Separação das funcionalidades disponíveis para cada tipo de utilizador.
- Validação de acesso antes de executar determinadas ações.

---

### 4. Nova interface de login
- Criada interface gráfica própria para autenticação.
- Ligação entre login e sistema principal.
- Melhor organização do fluxo de entrada no programa.

---

### 5. Login inicial do sistema
- Criado utilizador administrador temporário inicial:


Utilizador: adm
Senha: adm


- Conta criada automaticamente na primeira execução.
- Utilizada apenas para configuração inicial do sistema.

---

### 6. Módulo de gestão de funcionários
- Criado sistema completo de gestão de funcionários.
- Possibilidade de:
  - Criar funcionários.
  - Editar dados.
  - Alterar permissões.
  - Remover funcionários.
  - Consultar funcionários existentes.

---

### 7. Funcionário inicial temporário
- Implementado administrador temporário de segurança.
- Obriga a alteração dos dados após configuração inicial.
- Após edição, a conta deixa de ser temporária.

---

### 8. Separação entre Administrador e Funcionário
- Criados diferentes níveis de acesso:
  - Administrador
  - Funcionário

- O administrador possui acesso total ao sistema.
- O funcionário possui acesso limitado às funcionalidades permitidas.

---

### 9. Dashboard melhorado
- Adicionadas mais informações importantes:
  - Total de alunos.
  - Estado das mensalidades.
  - Presenças.
  - Distribuição por planos.
  - Resumo geral da academia.

---

## Melhorias Técnicas

- Melhor organização dos módulos.
- Separação entre autenticação, permissões e gestão de funcionários.
- Estrutura preparada para novos níveis de acesso.
- Melhor controlo dos dados guardados em JSON.
- Sistema de logs para acompanhar ações importantes.

---

## Próximos passos

Possíveis melhorias futuras:
- Encriptação de palavras-passe.
- Recuperação de conta.
- Mais níveis de permissões.
- Relatórios avançados.
- Exportação de dados.