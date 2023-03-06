import requests
import json
import pandas as pd
from datetime import datetime, time, timedelta, date
import streamlit as st
import aiohttp
import asyncio
from time import sleep
from openpyxl import Workbook
from collections import Counter


def token(login, password):
    """
    login = email informado na primeira caixa de código. É preenchido automaticamente
    password = senha informada na primeira caixa de código. É preenchida automaticamente
    """
    url = "https://lora.nlt-iot.com/token"  # Link gerado pela API LoRa
    payload = json.dumps({  # corpo exigido para poder fazer o Post na API
        "email": f"{login}",
        "password": f"{password}"
    })
    headers = {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTI3LCJleHAiOjE2NzE3MzQ0NDZ9.9Lmo2xCpVBoBZ3btPiQwvSoudeaJ8nE9ehrJNlI2lH4',
        'Content-Type': 'application/json'
    }
    # resposta obtida pela API
    resposta = requests.request("POST", url, headers=headers, data=payload)
    hora_atual = datetime.now()  # ajuste de fuso horário
    # adição de 30 minutos na expiração do token
    hora_limite = hora_atual + timedelta(minutes=30)
    if "200" in str(resposta):
        st.success("Token criado com sucesso")
        return resposta.json()["access_token"], resposta
    else:
        st.error(
            f"Não foi possível criar o token. Verifique se o email e senha informados estão corretos", icon="⚠️")
        return resposta.json()["detail"], resposta


async def token_assinc(session, url, login, password):
    payload = json.dumps({  # corpo exigido para poder fazer o Post na API
        "email": f"{login}",
        "password": f"{password}"
    })
    headers = {
        'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MTI3LCJleHAiOjE2NzE3MzQ0NDZ9.9Lmo2xCpVBoBZ3btPiQwvSoudeaJ8nE9ehrJNlI2lH4',
        'Content-Type': 'application/json'}
    try:
        async with session.post(url, headers=headers, data=payload):
            url = f"{url}"  # Link gerado pela API LoRa
            # resposta obtida pela API
            resposta = requests.request(
                "POST", url, headers=headers, data=payload)
            hora_atual = datetime.now()  # ajuste de fuso horário
            # adição de 30 minutos na expiração do token
            hora_limite = hora_atual + timedelta(minutes=30)
            if "200" in str(resposta):
                st.success("Token criado com sucesso")
                return resposta.json()["access_token"], resposta
            else:
                st.error(
                    f"Não foi possível criar o token. Verifique se o email e senha informados estão corretos", icon="⚠️")
    except:
        pass


async def mensagem(session, url, tok):
    headers = {'Authorization': f'Bearer {tok}'}

    async with session.get(url, headers=headers) as response:
        mensagem = await response.json()
        return mensagem


async def ativo(session, url, tok):
    headers = {'Authorization': f'Bearer {tok}'}

    async with session.get(url, headers=headers) as response:
        atividade = await response.json()
        return atividade


async def main(arq_orig, token, login, password):
    try:
        lista_geral_tags = list()
        lista_msg = list()
        geral = list()
        async with aiohttp.ClientSession() as session:
            counter = Counter()
            lista_deveui = [dev for dev in arq_orig["DevEUI"]]
            cont_dev = 0
            tempo_inicial = datetime.now()
            novo_arquivo = "planilha_teste.xlsx"
            wb = Workbook()
            ws = wb.active
            ws.append(["DevEUI", "Status", "Atividade", "Porta"])
            url_token = "https://lora.nlt-iot.com/token"
            barra = st.progress(0)
            data_atual = str(date.today())
            for deveui in lista_deveui:
                total = len(lista_deveui)
                cont_dev += (100 / total) / 100
                barra.progress(cont_dev)
                sleep(0.3)
                url_msg = f"https://lora.nlt-iot.com/messages/{deveui}?message_type=uplink&limit=1&final_date={data_atual}%2023%3A59"
                url_ativo = f"https://lora.nlt-iot.com/devices/{deveui}/activation"
                url_tag = f"https://lora.nlt-iot.com/devices/{deveui}"
                tag_dev = await tag(session, url_tag, tokn)
                mensagens = await mensagem(session, url_msg, token)
                atividades = await ativo(session, url_ativo, token)
                tempo_atual = datetime.now()
                if "credentials" in str(mensagens.values()):
                    break
                for chave, valor in atividades.items():
                    if valor == True:
                        # adiciona na lista o dev eui, e seu respectivo dicionário com mensagem, todos eles em uma única lista
                        lista_msg.append([deveui, mensagens, "Ativo"])
                    else:
                        lista_msg.append([deveui, mensagens, "Não ativo"])
                for listas in lista_msg:
                    if "not found" in str(listas[1].values()):
                        geral.append([listas[0], "Fora da NLT",
                                     listas[2], "Porta desconhecida", "Desconhecida"])
                        lista_geral_tags.extend(["Desconhecida"])
                    else:
                        lista_geral_tags.extend(tag_dev)
                        tag_formatada = ", ".join(map(str, tag_dev))
                        if "[]" in str(listas[1].values()):
                            geral.append(
                                [listas[0], "Na NLT", listas[2], "Porta desconhecida", tag_formatada])
                        else:
                            for chave, valor in listas[1].items():
                                if chave == "messages" and valor != []:
                                    for dic in valor:
                                        for chaves, valores in dic.items():
                                            if chaves == "params":
                                                porta = valores["port"]
                                                geral.append(
                                                    [listas[0], "Na NLT", listas[2], f"Porta {porta}"], tag_formatada)
                # for linha in geral:
                #     ws.append(linha)
                # wb.save(novo_arquivo)
                lista_msg.clear()
                if (tempo_atual - tempo_inicial) >= timedelta(minutes=10):
                    tokn = await token_assinc(session, url_token, login, password)
                    tempo_inicial = tempo_atual
                df = pd.DataFrame(
                    geral, columns=["DevEUI", "Status", "Atividade", "Porta"])
    except:
        pass
    return df


async def tag(session, url, token):
    headers = {"Authorization": f"Bearer {token}"}
    async with session.get(url, headers=headers) as resposta:
        tag = await resposta.json()
        for chaves, valores in tag.items():
            if chaves == "tags":
                return valores
