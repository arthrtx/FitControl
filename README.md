# FitControl V4

FitControl V4 é uma aplicação de gestão de academias desenvolvida em Python com CustomTkinter. O sistema permite gerir alunos, funcionários, planos, pagamentos e presenças através de uma interface moderna e intuitiva, com reconhecimento facial integrado.

## Funcionalidades

- Autenticação de utilizadores com diferentes níveis de acesso.
- Gestão de alunos e funcionários.
- Registo e gestão de planos.
- Controlo de pagamentos e mensalidades.
- Registo de presenças.
- Dashboard com estatísticas e gráficos em tempo real.
- Sistema de histórico e arquivo de dados.
- Reconhecimento facial (Face ID) com modelo embutido (funciona offline).
- Base de dados SQLite (auto-criada e vazia na primeira execução).

## Novidades

### Atualização de etiquetas e PDF

- **Relatório PDF redesenhado**: cabeçalho, cartões de resumo, tabelas, paginação e rodapé reorganizados para leitura mais clara. O botão **Gerar Relatório PDF** passou a usar o estilo primário da aplicação.
- **Relatórios agrupados por plano**: para além do total de alunos, o PDF apresenta agora o valor médio pago por plano.
- **Pesquisa de pagamentos apenas por nome**: o campo **Pesquisar aluno pelo nome...** filtra somente pelo nome do aluno. O documento, telemóvel e ID deixaram de ser usados na pesquisa.

### Melhorias de interface

- **Atualização manual do dashboard**: o botão `↻` entre o relógio e o botão de tema permite recarregar cartões e gráficos sem recarregar a aplicação.
- **Dashboard mais completo**: 7 cartões de indicadores e 4 gráficos.

### Alunos e fotografia

- **Atualização de foto na edição**: ao editar um aluno é possível marcar a caixa **📷 Tirar nova foto ao guardar** para capturar uma nova fotografia pela câmera. A referência facial é recalculada e guardada automaticamente.
- **Cancelamento sem perda**: se cancelar a captura da câmera, a foto existente é mantida e a edição continua normalmente.
- **Foto apenas na edição**: criar um mantém o comportamento atual (tirar foto ao criar); a opção de troca de foto existe apenas no formulário de edição.

### Correções de estabilidade

- **Eliminação de alunos corrigida**: eliminar um aluno e movê-lo para o arquivo de exclusão já não bloqueia a aplicação. A causa era a reutilização de identificadores entre alunos ativos e arquivados, que gerava um conflito na base de dados e deixava a base bloqueada em todas as escritas seguintes.
- **Identificadores únicos garantidos**: os novos alunos já não reaproveitam o número de um aluno que está no arquivo de exclusão.
- **Erros visíveis**: se a eliminação falhar, é apresentada uma mensagem de erro em vez de a aplicação ficar aparentemente congelada.

## Novidades desta versão (Edição Portátil)

- **Versão portátil pronta a usar**: o executável e todas as dependências (Python, OpenCV, modelo facial e bibliotecas) vêm já empacotados na pasta `_internal`. Basta extrair e executar `FitControl.exe` — **não requer instalação nem internet**.
- **Face ID corrigido e validado de ponta a ponta**: o modelo de reconhecimento (insightface `buffalo_l`) e os dados auxiliares do insightface ficam embutidos no executável, eliminando os erros que impediam o Face ID de funcionar fora do ambiente de desenvolvimento.
- **Base de Dados começa vazia**: a primeira execução cria automaticamente uma base de dados limpa (estado de fábrica), pronta para registar a sua academia.
- **Aviso do administrador temporário**: no primeiro login é alertado para alterar os dados da conta temporária ou criar outra conta de administrador; o aviso desaparece assim que o fizer.
- Executável gerado com o **PyInstaller (onedir)** e testado: login, painel principal e reconhecimento facial validados no executável final.

## Como executar

### Opção 1 — Versão portátil (recomendada)

1. Vá à secção **Releases** deste repositório e descarregue `FitControl-Portable-V4.zip`.
2. Extraia para qualquer pasta (ex.: Área de Trabalho ou Documentos).
3. Abra a pasta e faça duplo clique em **FitControl.exe**.

> Requisitos: Windows 10 ou Windows 11 (64 bits). Câmera (apenas para o Face ID).
> Não precisa de instalar Python nem qualquer biblioteca.

### Opção 2 — A partir do código-fonte

1. Instale o Python 3.11 ou superior (64 bits).
2. Num terminal, dentro da pasta do projeto:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run_gui.py
```

Também pode simplesmente executar o **`run.bat`** (usa/cria o ambiente virtual e inicia a aplicação).

### Primeiro acesso

```
Utilizador: adm
Palavra-passe: adm
```

Este é o **administrador temporário**. Após entrar, altere os dados dessa conta (menu Funcionários) ou crie outra conta de administrador — o aviso de segurança desaparece assim que o fizer.

### Reconhecimento facial (Face ID)

1. Crie um aluno e associe uma **foto** (o sistema gera a referência facial).
2. Abra a página **Presenças** e clique em **Iniciar Face ID**.
3. Coloque o rosto em frente à câmera: quando reconhecido, a presença é registada automaticamente.
4. Para terminar, pressione **Q** na janela do Face ID (ou feche a janela).

> Sem alunos com foto cadastrados, o Face ID mostra "Sem embeddings registados".

## Tecnologias

- Python
- CustomTkinter / Tkinter
- OpenCV
- insightface / onnxruntime
- Matplotlib
- Pillow
- SQLite
- PyInstaller (empacotamento)

## Estrutura do Projeto

```
FitControl/
│
├── interface_grafica/          # Interface (login, app, dialogs, widgets)
├── modulos/                    # Lógica de negócio (alunos, pagamentos, presenças...)
├── projeto_ginasio/            # Configuração, Base de Dados, câmera e Face ID
├── portable/                   # Instruções da edição portátil
├── run_gui.py                  # Ponto de entrada
├── run.bat                     # Inicialização rápida no Windows
├── requirements.txt            # Dependências Python
└── README.md
```

## Autor

Arthur da Hora de Sal
