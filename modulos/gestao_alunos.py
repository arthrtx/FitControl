from datetime import datetime, timedelta
import os
import shutil

import numpy as np

from projeto_ginasio.Camara import ler_imagem
from projeto_ginasio.config import *
from projeto_ginasio.dados import alunos, alunos_excluidos
from projeto_ginasio.db_adapter import (
    save_alunos, add_aluno, update_aluno, delete_aluno,
    save_alunos_excluidos, add_aluno_excluido, remove_aluno_excluido, add_log
)

def gerar_embedding(caminho_foto):

    try:

        # usa o mesmo modelo do Face ID (carregado uma vez só e com a pasta
        # certa dos modelos, também no executável)
        from projeto_ginasio.reconhecimento.reconhecimento import carregar_modelo, maior_rosto

        ia = carregar_modelo()


        imagem = ler_imagem(caminho_foto)


        if imagem is None:
            return None


        rosto = maior_rosto(ia.get(imagem))


        if rosto is None:
            print("Nenhum rosto encontrado.")
            return None


        embedding = rosto.embedding


        embedding = embedding / np.linalg.norm(embedding)


        return embedding.tolist()


    except Exception as erro:

        print(
            f"Erro ao gerar embedding: {erro}"
        )

        return None


# fotos
# ======================================================
def guardar_foto(origem, id_aluno):

    destino = os.path.join(PASTA_FACES, f"{id_aluno}.jpg")

    if os.path.abspath(origem) != os.path.abspath(destino):
        shutil.move(origem, destino)

    return destino


def apagar_foto(caminho):

    if not caminho or caminho == "sem_foto":
        return

    try:
        if os.path.exists(caminho):
            os.remove(caminho)
    except OSError as erro:
        print(f"Não foi possível apagar a foto: {erro}")

# inicialização
# ======================================================
def inicializar():
    carregar_alunos()
    carregar_alunos_excluidos()
    limpar_alunos_expirados()


# guardar alunos
# ======================================================
def guardar_alunos():
    try:
        save_alunos(alunos)
    except Exception as erro:
        raise Exception(f"Não foi possível guardar os alunos: {erro}")


# logs
# ======================================================
def escrever_log(evento, tipo="geral"):
    try:
        add_log(evento, tipo=tipo)
    except Exception as erro:
        raise Exception(f"Não foi possível escrever no log: {erro}")


# carregar alunos
# ======================================================
def carregar_alunos():
    # Dados agora são carregados do banco de dados em dados.py
    pass


# gerar ID
# ======================================================
def gerar_id():

    ids_usados = [aluno["id"] for aluno in alunos]

    ids_usados.extend(aluno["id"] for aluno in alunos_excluidos)

    if not ids_usados:

        return 1

    return max(ids_usados) + 1

# verificar documento
# ======================================================
def documento_existe(documento):

    for aluno in alunos:
        if aluno["documento"] == documento:
            return True

    return False


# criar alunos
# ======================================================
def criar_aluno(nome, telemovel, documento, plano, foto=None):
#regras============================
    nome = nome.strip()
    telemovel = telemovel.strip()
    documento = documento.strip()

    if not nome:
        return "Erro: O nome não pode estar vazio."
    if len(nome.split()) < 2:
        return "Erro: O nome deve conter pelo menos 2 palavras (nome e sobrenome)."
        
    if not documento:
        return "Erro: O documento não pode estar vazio."
    if len(documento) > 12:
        return "Erro: O documento não pode ter mais de 12 caracteres."
        
    if not telemovel.isdigit():
        return "Erro: O telemóvel deve conter apenas dígitos numéricos."
    if len(telemovel) != 9:
        return "Erro: O telemóvel deve ter exatamente 9 dígitos."
        
        
    planos_validos = [
        "Diário",
        "Mensal",
        "Trimestral",
        "Anual"
    ]

    if plano not in planos_validos:
        return f"Erro: O plano deve ser um dos seguintes: {', '.join(planos_validos)}."


    id_aluno = gerar_id()

    if documento_existe(documento):
        return "Erro: Já existe um aluno com este documento."


    # a foto só chega aqui se o aluno deu consentimento para o Face ID
    if not foto:

        caminho_foto = "sem_foto"
        embedding = None


    else:

        caminho_foto = guardar_foto(foto, id_aluno)

        embedding = gerar_embedding(
            caminho_foto
        )

    novo_aluno = {
        "id": id_aluno,
        "nome": nome,
        "telemovel": telemovel,
        "documento": documento,
        "plano": plano,
        "foto": caminho_foto,
        "embedding": embedding
    }


    add_aluno(novo_aluno)
    alunos.append(novo_aluno)
    escrever_log(f"Aluno '{nome}' registado.", tipo="aluno")

    if foto:
        escrever_log(f"Consentimento facial dado por '{nome}'.", tipo="aluno")

    return True


# listar alunos
# ======================================================
def listar_alunos():

    return sorted(
        alunos,
        key=lambda aluno: aluno["nome"].lower()
    )


# editar alunos
# ======================================================
def editar_aluno(id_aluno, nome, telemovel, documento, plano, nova_foto=None, remover_foto=False):
#regras============================
    nome = nome.strip()
    telemovel = telemovel.strip()
    documento = documento.strip()

    if not nome:
        return "Erro: O nome não pode estar vazio."
    if len(nome.split()) < 2:
        return "Erro: O nome deve conter pelo menos 2 palavras (nome e sobrenome)."
        
    if not documento:
        return "Erro: O documento não pode estar vazio."
    if len(documento) > 12:
        return "Erro: O documento não pode ter mais de 12 caracteres."
        
    if not telemovel.isdigit():
        return "Erro: O telemóvel deve conter apenas dígitos numéricos."
    if len(telemovel) != 9:
        return "Erro: O telemóvel deve ter exatamente 9 dígitos."
        
        
    planos_validos = [
        "Diário",
        "Mensal",
        "Trimestral",
        "Anual"
    ]

    if plano not in planos_validos:
        return f"Erro: O plano deve ser um dos seguintes: {', '.join(planos_validos)}."


    for outro in alunos:

        if outro["documento"] == documento and outro["id"] != id_aluno:
            return "Erro: Já existe outro aluno com este documento."


    for aluno in alunos:

        if aluno["id"] == id_aluno:

            if nova_foto:

                caminho_foto = guardar_foto(nova_foto, id_aluno)

                embedding = gerar_embedding(
                    caminho_foto
                )

                aluno["foto"] = caminho_foto
                aluno["embedding"] = embedding

            elif remover_foto:

                # consentimento retirado: sai a foto e o modelo facial
                apagar_foto(aluno.get("foto"))

                aluno["foto"] = "sem_foto"
                aluno["embedding"] = None

                escrever_log(f"Consentimento facial retirado por '{nome}'.", tipo="aluno")


            aluno["nome"] = nome
            aluno["telemovel"] = telemovel
            aluno["documento"] = documento
            aluno["plano"] = plano

            update_aluno(aluno)

            escrever_log(f"Aluno '{nome}' editado.", tipo="aluno")

            return True

    return False


# eliminar alunos
# ======================================================
def eliminar_aluno(id_aluno):

    for aluno in alunos:

        if aluno["id"] == id_aluno:

            aluno_excluido = aluno.copy()

            aluno_excluido["data_exclusao"] = datetime.now().strftime("%d/%m/%Y")

            for arquivado in alunos_excluidos:

                if arquivado["id"] == id_aluno:

                    alunos_excluidos.remove(arquivado)

                    break

            try:

                add_aluno_excluido(aluno_excluido)
                delete_aluno(id_aluno)

            except Exception as erro:

                raise Exception(
                    f"Não foi possível mover o aluno para o arquivo: {erro}"
                )

            alunos_excluidos.append(aluno_excluido)
            alunos.remove(aluno)


            escrever_log(
                f"Aluno '{aluno['nome']}' movido para arquivo de exclusão.",
                tipo="aluno"
            )

            return True

    return False


# restaurar alunos excluidos
# ======================================================
def restaurar_aluno(id_aluno):

    for aluno in alunos_excluidos:

        if aluno["id"] == id_aluno:

            if documento_existe(aluno["documento"]):
                return False


            aluno.pop("data_exclusao", None)

            try:

                add_aluno(aluno)
                remove_aluno_excluido(id_aluno)

            except Exception as erro:

                raise Exception(
                    f"Não foi possível restaurar o aluno: {erro}"
                )

            alunos.append(aluno)
            alunos_excluidos.remove(aluno)


            escrever_log(
                f"Aluno '{aluno['nome']}' restaurado.",
                tipo="aluno"
            )

            return True

    return False


# listar alunos excluidos
# ======================================================
def listar_alunos_excluidos():

    return sorted(
        alunos_excluidos,
        key=lambda aluno: aluno["nome"].lower()
    )


# carregar alunos excluidos
# ======================================================
def carregar_alunos_excluidos():
    # Dados agora são carregados do banco de dados em dados.py
    pass


# guardar alunos excluidos
# ======================================================
def guardar_alunos_excluidos():
    try:
        save_alunos_excluidos(alunos_excluidos)
    except Exception as erro:
        raise Exception(f"Não foi possível guardar alunos excluídos: {erro}")


# apagar definitivamente (direito ao apagamento)
# ======================================================
def apagar_definitivamente(id_aluno):

    for aluno in alunos_excluidos:

        if aluno["id"] == id_aluno:

            remove_aluno_excluido(id_aluno)
            alunos_excluidos.remove(aluno)

            apagar_foto(aluno.get("foto"))

            escrever_log(
                f"Dados do aluno ID {id_aluno} apagados definitivamente.",
                tipo="aluno"
            )

            return True

    return False


# limpar alunos excluidos
# ======================================================
def limpar_alunos_expirados():

    hoje = datetime.now()

    removidos = []


    for aluno in alunos_excluidos:

        try:
            data = datetime.strptime(
                aluno["data_exclusao"],
                "%d/%m/%Y"
            )
        except (ValueError, TypeError, KeyError):
            continue


        if hoje - data >= timedelta(days=60):

            removidos.append(aluno)


    # antes só saíam da lista em memória e voltavam a aparecer ao reabrir
    for aluno in removidos:

        remove_aluno_excluido(aluno["id"])
        alunos_excluidos.remove(aluno)
        apagar_foto(aluno.get("foto"))

        escrever_log(
            f"Aluno ID {aluno['id']} eliminado definitivamente após 60 dias.",
            tipo="aluno"
        )
