# Edição Portátil (executável)

Esta pasta contém as instruções para a edição portátil do **FitControl V4** —
a aplicação pronta a executar em qualquer computador com **Windows 10/11 (64
bits)**, sem instalar Python nem qualquer dependência.

## Porque é que o executável não está nesta pasta?

O GitHub só aceita ficheiros até **100 MB** dentro de um repositório, e o
empacotamento completo do FitControl (que inclui o modelo de reconhecimento
facial `buffalo_l`, OpenCV, onnxruntime, etc.) ocupa cerca de **650 MB**. Por
isso a versão portátil é publicada como **Release** (download até 2 GB).

## Como descarregar

1. Abra a secção **Releases** deste repositório (ou utilize o link na página
   principal do projeto).
2. Descarregue o ficheiro **`FitControl-Portable-V4.zip`**.
3. Extraia para qualquer pasta (ex.: Área de Trabalho ou Documentos).
4. Faça duplo clique em **`FitControl.exe`**.

## Primeiro acesso

```
Utilizador: adm
Palavra-passe: adm
```

É o **administrador temporário**. Mude os dados dessa conta ou crie outra
conta de administrador no menu Funcionários — o aviso de segurança
desaparece assim que o fizer.

## Notas

- A primeira execução cria automaticamente a Base de Dados vazia (pasta
  `dados`), pronta a usar.
- Para o Face ID, crie um aluno com **foto** e, na página Presenças, clique
  em **Iniciar Face ID**. Sem alunos com foto, aparece "Sem embeddings
  registados".
- Fica na mesma a ser desenvolvido a partir do código-fonte (pasta raiz do
  projeto): ver `README.md` principal.