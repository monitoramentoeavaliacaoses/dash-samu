import pandas as pd
import numpy as np
import streamlit as st

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import os
import json
from dotenv import load_dotenv
import time
from loguru import logger
load_dotenv()
@st.cache_data
def get_sheet(worksheet_name: str):
    file_path = 'google-api-credentials.json'
    if not os.path.exists(file_path):

        credentials = {  
            'type': os.getenv("GOOGLE_TYPE"),
            'project_id': os.getenv("GOOGLE_PROJECT_ID"),
            'private_key_id': os.getenv("GOOGLE_PRIVATE_KEY_ID"),
            'private_key': os.getenv("GOOGLE_PRIVATE_KEY").replace("__NEWLINE__", "\n"),
            'client_email': os.getenv("GOOGLE_CLIENT_EMAIL"),
            'client_id': os.getenv("GOOGLE_CLIENT_ID"),
            'auth_uri': os.getenv("GOOGLE_AUTH_URI"),
            'token_uri': os.getenv("GOOGLE_TOKEN_URI"),
            'auth_provider_x509_cert_url': os.getenv("GOOGLE_AUTH_PROVIDER_X509_CERT_URL"),
            'client_x509_cert_url': os.getenv('GOOGLE_CLIENT_X509_CERT_URL'),
            'universe_domain': os.getenv("GOOGLE_UNIVERSE_DOMAIN")
        }

        with open('google-api-credentials.json', 'w') as f:
            json.dump(credentials, f, indent=2)

    gc = gspread.service_account("google-api-credentials.json")
    url_sheet = os.getenv("URL_SHEET")
    sheet = gc.open_by_url(url_sheet)
    worksheet = sheet.worksheet(worksheet_name)
    return pd.DataFrame(worksheet.get_all_records())

@st.cache_data
def fetch_and_clean_data():
    
    dim_dist_min_hosp = pd.read_parquet(r"data/dim_dist_min_hosp.parquet")
    dim_dist_min_hosp[["cnes_Origem", "cnes_Destino"]] = dim_dist_min_hosp[["cnes_Origem", "cnes_Destino"]].apply(lambda x: x.astype(str).str.zfill(7))
    dim_dist_min_hosp["cnes_origem_destino"] = dim_dist_min_hosp["cnes_Origem"] + dim_dist_min_hosp["cnes_Destino"]
    distance_between_units_dict = dict(zip(dim_dist_min_hosp["cnes_origem_destino"], dim_dist_min_hosp["Distância (km)"]))
    rota_between_units_dict = dict(zip(dim_dist_min_hosp["cnes_origem_destino"], dim_dist_min_hosp["rota_coords"]))
    
    tb_fat_transp = get_sheet("fatTransf").astype({"cnes_unidade_origem": str, "cnes_unidade_exame": str, "cnes_unidade_dest_final": str})
    
    #tb_fat_transp = pd.read_csv(r"data\Plan_Transf_SAMU_v2 - fatTransf.csv", dtype={"cnes_unidade_origem": str, "cnes_unidade_exame": str, "cnes_unidade_dest_final": str})
    # Aplicando zfill apenas nas células com valores válidos
    tb_fat_transp[["cnes_unidade_origem", "cnes_unidade_exame", "cnes_unidade_dest_final"]] = tb_fat_transp[
        ["cnes_unidade_origem", "cnes_unidade_exame", "cnes_unidade_dest_final"]
    ].apply(lambda col: col.where(col.isna(), col.astype(str).str.zfill(7)))
    
    # Função para verificar valores válidos e concatenar
    def concat_if_valid_origem_exame(row):
        if pd.notna(row["cnes_unidade_origem"]) and pd.notna(row["cnes_unidade_exame"]):
            return str(row["cnes_unidade_origem"]) + str(row["cnes_unidade_exame"])
        return None  # Retorna None se qualquer valor for inválido

    # Aplicando a função para criar a nova coluna
    tb_fat_transp["cnes_origem_exame"] = tb_fat_transp.apply(concat_if_valid_origem_exame, axis=1)

    # Função para verificar valores válidos e concatenar
    def concat_if_valid_exame_dest_final(row):
        if pd.notna(row["cnes_unidade_exame"]) and pd.notna(row["cnes_unidade_dest_final"]):
            return str(row["cnes_unidade_exame"]) + str(row["cnes_unidade_dest_final"])
        return None  # Retorna None se qualquer valor for inválido

    # Aplicando a função para criar a nova coluna
    tb_fat_transp["cnes_exame_dest_final"] = tb_fat_transp.apply(concat_if_valid_exame_dest_final, axis=1)

    # Função para verificar valores válidos e concatenar
    def concat_if_valid_origem_dest_final(row):
        if pd.notna(row["cnes_unidade_origem"]) and pd.notna(row["cnes_unidade_dest_final"]):
            return str(row["cnes_unidade_origem"]) + str(row["cnes_unidade_dest_final"])
        return None  # Retorna None se qualquer valor for inválido

    # Aplicando a função para criar a nova coluna
    tb_fat_transp["cnes_origem_dest_final"] = tb_fat_transp.apply(concat_if_valid_origem_dest_final, axis=1)

    tb_fat_transp["distancia_origem_exame"] = tb_fat_transp["cnes_origem_exame"].map(distance_between_units_dict)
    tb_fat_transp["rota_origem_exame"] = tb_fat_transp["cnes_origem_exame"].map(rota_between_units_dict)

    tb_fat_transp["distancia_exame_dest_final"] = tb_fat_transp["cnes_exame_dest_final"].map(distance_between_units_dict)
    tb_fat_transp["rota_exame_dest_final"] = tb_fat_transp["cnes_exame_dest_final"].map(rota_between_units_dict)

    tb_fat_transp["distancia_origem_dest_final"] = tb_fat_transp["cnes_origem_dest_final"].map(distance_between_units_dict)
    tb_fat_transp["rota_origem_dest_final"] = tb_fat_transp["cnes_origem_dest_final"].map(rota_between_units_dict)
    tb_fat_transp.replace("0000000", np.nan, inplace=True) #
# Definindo condições
    condicoes = [
        ((tb_fat_transp['cnes_unidade_exame'].isna()) & (tb_fat_transp["cnes_unidade_origem"] == tb_fat_transp["cnes_unidade_dest_final"])),  # Primeira condição
        (tb_fat_transp['cnes_unidade_exame'] == tb_fat_transp["cnes_unidade_dest_final"]),  # Primeira condição
        ((tb_fat_transp['cnes_unidade_exame'].isna()))   # Segunda condição
    ]

    # Definindo os valores para cada condição
    valores = [
        0,
        tb_fat_transp['distancia_origem_exame'] * tb_fat_transp['qtd_dest_final'],  # Resultado para a primeira condição
        tb_fat_transp['distancia_origem_dest_final'] * tb_fat_transp['qtd_dest_final']   # Resultado para a segunda condição
    ]

    # A função np.select aplica as condições e valores
    tb_fat_transp['distancia_total_percorrida'] = np.select(condicoes, valores, default=(tb_fat_transp['distancia_origem_exame'] + tb_fat_transp['distancia_exame_dest_final']) * tb_fat_transp['qtd_dest_final'])  # default é 0 quando nenhuma condição é atendida

    
    return tb_fat_transp