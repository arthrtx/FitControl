# FitControl V5

FitControl é uma aplicação de gestão de academias desenvolvida em Python com CustomTkinter. O sistema permite gerir alunos, funcionários, planos, pagamentos e presenças através de uma interface moderna, com modo claro e escuro, reconhecimento facial integrado e cumprimento do RGPD.

## Funcionalidades

- Autenticação de utilizadores com níveis de acesso (administrador e funcionário) e bloqueio após 3 tentativas falhadas.
- Gestão de alunos com fotografia, filtros, pesquisa sem acentos e ficha com o histórico de mensalidades.
- Planos Diário, Mensal, Trimestral e Anual.
- Controlo de pagamentos e mensalidades em atraso, com notificações.
- Registo de presenças por Face ID ou manual.
- Dashboard com estatísticas e gráficos em tempo real.
- Relatório mensal em PDF.
- Arquivo de presenças e de alunos, com restauro e apagamento definitivo.
- Registos de administração (logins, alterações, pedidos RGPD).
- **Modo claro e modo escuro**, alternáveis no botão sol/lua do canto superior direito.
- Termos de Utilização e Política de Privacidade (RGPD) aceites no login.
- Base de dados SQLite criada automaticamente na primeira execução.

## Novidades da versão 5.0

### Interface nova
- **Redesenho completo**: menu lateral com indicador luminoso e opção de recolher, painel principal arredondado com fundo em degradê e faixa de boas-vindas com atalhos.
- **Dashboard em vidro fosco**: cartões desfocados por cima do degradê, linhas de LEDs (alunos em dia, presenças dos últimos 14 dias, receita, equipa), medidor das mensalidades, linha das entradas dos últimos 30 dias e barras da receita mensal. Passando o rato aparece o valor.
- **Gráficos desenhados pela própria aplicação** (deixou de ser preciso o matplotlib).
- **Tabelas** com linhas alternadas, ordenação ao clicar no cabeçalho e filtros (Em dia / Em atraso / Sem pagamento).
- **Pesquisa de alunos** nos pagamentos e presenças (escreve-se o nome em vez de procurar numa lista enorme).
- **Câmara dentro da aplicação**: o Face ID, a fotografia do aluno e o teste da câmara aparecem na própria janela.
- **Avisos rápidos** no canto da janela em vez de caixas de mensagem para tudo.
- Login mais pequeno e janelas sempre centradas no ecrã; os botões ajustam-se a ecrãs com escala do Windows (125%, 150%).

### Desempenho
- A troca de tema é instantânea e a janela já não pisca; a barra de título acompanha o tema.
- A página Presenças abria com 4 s de bloqueio: o reconhecimento facial passou a carregar em segundo plano.
- Corrigido um ciclo infinito de redesenho nas tabelas e gráficos ~8× mais rápidos.
- Páginas só são criadas quando se abrem e o dashboard só redesenha quando os dados mudam.

### RGPD
- **Termos de Utilização e Política de Privacidade** reescritos (arts. 13.º e 9.º do RGPD, Lei 58/2019, CNPD). Cada utilizador aceita-os no primeiro login e sempre que mudarem de versão; a aceitação fica registada.
- **Consentimento facial explícito**: a foto do aluno só é tirada com consentimento, que pode ser retirado ao editar o aluno (a foto e o modelo facial são apagados).
- **Exportar dados do aluno** (direito de acesso e portabilidade) em JSON.
- **Apagar definitivamente** um aluno do arquivo (direito ao apagamento). Os alunos com mais de 60 dias no arquivo são apagados da base de dados.
- **Palavras-passe cifradas** (PBKDF2). As contas antigas são convertidas automaticamente.
- Registos com mais de 2 anos são apagados automaticamente.

### Face ID mais fiável
- Funciona em pastas com acentos (ex.: `C:\Users\João\...`).
- A imagem já não é deformada antes do reconhecimento e a comparação é mais tolerante com webcams fracas.
- Se o DirectShow não funcionar, a câmara é aberta pelo Media Foundation, e usa a câmara e a resolução escolhidas na página Câmara.
- Só carrega os modelos de deteção e reconhecimento (mais rápido e menos memória).
- Os erros (sem câmara, sem alunos com foto, etc.) aparecem no ecrã em vez de o Face ID ficar parado em "A preparar".

### Executável e run.bat
- Executável novo em pasta (arranca muito mais rápido do que o ficheiro único da V4.2), com o modelo do Face ID e o runtime do Visual C++ incluídos.
- Os dados ficam na pasta `dados`, ao lado do executável.
- `run.bat` corrigido: fins de linha do Windows, deteção do Python 3.12+ de 64 bits, reinstalação das dependências quando o `requirements.txt` muda.

## Como executar

### Opção 1 — Executável (recomendada)

1. Vá à secção **Releases** deste repositório e descarregue **`FitControl-V5.0-Windows.zip`**.
2. Extraia o zip para qualquer pasta (ex.: Área de Trabalho ou Documentos).
3. Abra a pasta `FitControl` e faça duplo clique em **FitControl.exe**.

> Requisitos: Windows 10 ou Windows 11 (64 bits). Câmara (apenas para o Face ID).
> Não precisa de instalar Python, bibliotecas nem internet: o modelo do Face ID já vai incluído.
> Para mudar de computador, basta copiar a pasta `FitControl` inteira (os dados vão na pasta `dados`).

### Opção 2 — A partir do código-fonte

1. Instale o Python 3.12 ou superior (64 bits).
2. Num terminal, dentro da pasta do projeto:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run_gui.py
```

Também pode simplesmente executar o **`run.bat`** (instala o Python se for preciso, cria o ambiente virtual e inicia a aplicação).

### Primeiro acesso

```
Utilizador: adm
Palavra-passe: adm
```

Este é o **administrador temporário**. Após entrar, altere os dados dessa conta (menu Funcionários) ou crie outra conta de administrador — o aviso de segurança desaparece assim que o fizer.

### Reconhecimento facial (Face ID)

1. Ao criar o aluno, marque o **consentimento para reconhecimento facial** e tire a foto na janela que aparece.
2. Abra a página **Presenças** e clique em **Iniciar Face ID** (a imagem da câmara aparece na própria página).
3. Coloque o rosto em frente à câmara: quando reconhecido, a presença é registada automaticamente.
4. Para terminar, clique em **Parar** (ou mude de página).

> A partir do código-fonte, na primeira utilização é preciso internet para descarregar o modelo facial (cerca de 280 MB). No executável o modelo já vem incluído.
> Sem alunos com foto, o Face ID mostra "Sem rostos registados".

## Versões anteriores

### V4.2 — Edição Portátil
- Executável único `FitControl.exe` com todas as dependências embutidas.
- **Modo claro**: primeira versão com tema claro e escuro.
- **Relatório PDF** do mês selecionado, com resumo por plano.
- **Termos de Utilização** no primeiro login e centro de **notificações**.
- **Tirar nova foto ao editar um aluno**, com a referência facial recalculada.
- Correção do bloqueio da base de dados ao eliminar alunos (identificadores reaproveitados do arquivo) e pesquisa sem acentos nos pagamentos.

### V4.1 — Edição Portátil
- Face ID corrigido e validado de ponta a ponta, com o modelo `buffalo_l` embutido.
- Base de dados vazia criada automaticamente na primeira execução.
- Aviso do administrador temporário no primeiro login.

## Tecnologias

- Python
- CustomTkinter / Tkinter
- OpenCV
- insightface / onnxruntime
- Pillow / NumPy
- ReportLab
- SQLite
- PyInstaller (empacotamento)

## Estrutura do Projeto

```
FitControl/
│
├── interface_grafica/          # Interface (login, janela principal, diálogos, widgets, gráficos)
│   └── paginas/                # Dashboard, Alunos, Pagamentos, Presenças, Arquivos, Sistema, Câmara
├── modulos/                    # Lógica de negócio (alunos, pagamentos, presenças, privacidade...)
├── projeto_ginasio/            # Configuração, base de dados, câmara e Face ID
├── run_gui.py                  # Ponto de entrada
├── run.bat                     # Inicialização rápida no Windows
├── requirements.txt            # Dependências Python
└── README.md
```

## Autor

Arthur da Hora de Sal
