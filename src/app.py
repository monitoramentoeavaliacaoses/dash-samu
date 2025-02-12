import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
import matplotlib.pyplot as plt
import folium.plugins as plugins
import numpy as np
import ast
from matplotlib import cm
from matplotlib.colors import Normalize
from etl import fetch_and_clean_data
from maps import show_heatmap, show_circle_map_km, show_circle_map_trajeto
from streamlit_folium import st_folium
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os
from dotenv import load_dotenv
# Título da página
st.session_state['layout'] = "wide"
st.set_page_config(layout=st.session_state['layout'])
load_dotenv()
import time
config = {
    "credentials": {
        "usernames": {
            os.getenv("USERNAME_A"): {
                "email": os.getenv("EMAIL_A"),
                "logged_in": False,
                "name": os.getenv("NAME_A"),
                "password": os.getenv("PASSWORD_A"),  # Substitua pela senha criptografada, se necessário
            },
            os.getenv("USERNAME_B"): {
                "email": os.getenv("EMAIL_B"),
                "logged_in": False,
                "name": os.getenv("NAME_B"),
                "password": os.getenv("PASSWORD_B"),  # Substitua pela senha criptografada, se necessário
            },
            os.getenv("USERNAME_C"): {
                "email": os.getenv("EMAIL_C"),
                "logged_in": False,
                "name": os.getenv("NAME_C"),
                "password": os.getenv("PASSWORD_C"),  # Substitua pela senha criptografada, se necessário
            },
            os.getenv("USERNAME_D"): {
                "email": os.getenv("EMAIL_D"),
                "logged_in": False,
                "name": os.getenv("NAME_D"),
                "password": os.getenv("PASSWORD_D"),  # Substitua pela senha criptografada, se necessário
            }


        }
    },
    "cookie": {
        "expiry_days": 30,
        "key": "random_signature_key",
        "name": "random_cookie_name",
    }
}


with open("config.yml", "w") as yaml_file:
    yaml.dump(config, yaml_file, default_flow_style=False)


with open("config.yml") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

auth_status = st.session_state.get(["authentication_status"])
if auth_status == None:

    authenticator.login()

    st.markdown(
    """
    <style>
    div[data-testid="stForm"] {
        max-width: 80vw !important;
        width: 40vw !important;
        min-width: 320px !important;
        margin: auto;
    }

    div[data-testid="stAlert"] {
        max-width: 80vw !important;
        width: 40vw !important;
        min-width: 320px !important;
        margin: auto;
    }
    </style>
    """,
    unsafe_allow_html=True
)
    

if st.session_state["authentication_status"]:


    authenticator.logout()
    st.header("Dashboard das transferências do SAMU")

    tb_fat_transp = fetch_and_clean_data()

    st.markdown(
        """
    <style>
    [data-testid="stMetric"] {
        border: 1px solid
    }
    [data-testid="stMetricValue"] {
        font-size: 1.2rem
    }
    
    [data-testid="stMarkdownContainer"] {
        font-size: 0.95rem
    }

    div[data-testid="stForm"] {
        max-width: 20px !important;
        margin: auto;
        }
    
    </style>
    """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([4, 1])

    with left:

        unidades_list = tb_fat_transp['unidade_origem'].unique()

        with st.sidebar:
            unidades_escolhidas = st.multiselect("Unidade de Origem das Solicitações", sorted(unidades_list))

        if unidades_escolhidas:
            tb_fat_transp = tb_fat_transp[tb_fat_transp['unidade_origem'].isin(unidades_escolhidas)]    

        tipo_transf_list = tb_fat_transp['tipo_transf'].unique()

        with st.sidebar:
            tipo_transf_escolhidas = st.multiselect("Tipo de Transferência", sorted(tipo_transf_list))

        if tipo_transf_escolhidas:
            tb_fat_transp = tb_fat_transp[tb_fat_transp['tipo_transf'].isin(tipo_transf_escolhidas)]

        tipo_viatura_list = tb_fat_transp[~tb_fat_transp['tipo_viatura'].isna()]['tipo_viatura'].unique()

        with st.sidebar:
            tipo_viatura_escolhidas = st.multiselect("Tipo de viatura", sorted(tipo_viatura_list))

        if tipo_viatura_escolhidas:
            tb_fat_transp = tb_fat_transp[tb_fat_transp['tipo_viatura'].isin(tipo_viatura_escolhidas)]

        viaturas_list = tb_fat_transp[~tb_fat_transp['viatura'].isna()]['viatura'].unique()

        with st.sidebar:
            viaturas_escolhidas = st.multiselect("Viatura", sorted(viaturas_list))

        if viaturas_escolhidas:
            tb_fat_transp = tb_fat_transp[tb_fat_transp['viatura'].isin(viaturas_escolhidas)]

        col_0_0, col_0_1, col_0_2, col_0_3 = st.columns([1, 1, 1, 1])
        km_rodados = int(sum(tb_fat_transp["distancia_total_percorrida"]))
        with col_0_0:

            st.metric(
                label="Km rodados",
                border=True,
                value=f"{km_rodados:,}".replace(",", ".")
            )

        with col_0_1:
            km_transf_aval = int(sum(tb_fat_transp[tb_fat_transp["tipo_transf"]=="TRANSFERÊNCIAS CRU PARA AVALIAÇÃO/EXAME/CONSULTA/TOMOGRAFIA"]["distancia_total_percorrida"])) 
            st.metric(
                label="Km Transf. Avaliação",
                border=True,
                value=f"{km_transf_aval:,} ({km_transf_aval/km_rodados * 100:.2f}%)".replace(',', 'X').replace('.', ',').replace('X', '.'),
            )
        with col_0_2:

            km_transf_uti = int(sum(tb_fat_transp[tb_fat_transp["tipo_transf"]=="TRANSFERÊNCIAS CRL PARA UTI"]["distancia_total_percorrida"]))
            st.metric(
                label="Km Transf. UTI",
                border=True,
                value=f"{km_transf_uti:,} ({km_transf_uti/km_rodados * 100:.2f}%)".replace(',', 'X').replace('.', ',').replace('X', '.'),
            )

        with col_0_3:

            km_transf_enf = int(sum(tb_fat_transp[tb_fat_transp["tipo_transf"]=="TRANSFERÊNCIAS CRL PARA ENFERMARIA"]["distancia_total_percorrida"]))
            st.metric(
                label="Km Transf. Enf.",
                border=True,
                value=f"{km_transf_enf:,} ({km_transf_enf/km_rodados * 100:.2f}%)".replace(',', 'X').replace('.', ',').replace('X', '.'),
            )


        tab_heatmap, tab_circle_map_km, tab_circle_map_trajeto, tab_dist_unidade, tab_dist_tipo_transf_tipo_viatura, tab_dist_viatura  = \
            st.tabs(["Heatmap dos trajetos", "Mapa - km", "Mapa - nº de trajetos", \
                    "Dist. x Unidade", "Dist. x Tipo transf x Tipo Viatura", "Dist. x Viatura"])

        with tab_heatmap:
            st.markdown("### Heatmap sobre os trajetos das unidades móveis")
            show_heatmap(tb_fat_transp)

        with tab_circle_map_km:
            st.markdown("### Mapa de pontos da Kilometragem por Unidade de Solicitação")
            show_circle_map_km(tb_fat_transp)

        with tab_circle_map_trajeto:
            st.markdown("### Mapa de pontos do nº de Transferências por Unidade de Solicitação")
            show_circle_map_trajeto(tb_fat_transp)

        with tab_dist_unidade:
        
            df_group = tb_fat_transp.groupby(["unidade_origem"]).agg(
            distancia_total_percorrida=("distancia_total_percorrida", "sum"),
            qtd_dest_final=("qtd_dest_final", "sum")).reset_index().sort_values(by=["distancia_total_percorrida"], ascending=False)\
                .rename(columns={"unidade_origem": "Unidade de Origem", "distancia_total_percorrida": "Distância Total Percorrida (Km)", \
                "qtd_dest_final": "Transferências"})
            
            df_group["Distância (%)"] = df_group["Distância Total Percorrida (Km)"].apply(
            lambda x: round(int(x) / df_group['Distância Total Percorrida (Km)'].astype(int).sum() * 100, 1)) 

            df_group["Transferências (%)"] = df_group["Transferências"].apply(
            lambda x: round(int(x) / df_group['Transferências'].astype(int).sum() * 100, 1)) 

            df_group["Distância Total Percorrida (Km)"] = df_group["Distância Total Percorrida (Km)"].astype(str).str.replace(',', 'X').replace('.', ',').replace('X', '.').str.split(".").str.get(0)
            st.dataframe(df_group, use_container_width=True, hide_index=True)

        with tab_dist_tipo_transf_tipo_viatura:
        
            df_group = tb_fat_transp.groupby(["tipo_transf"]).agg(
            distancia_total_percorrida=("distancia_total_percorrida", "sum"),
            qtd_dest_final=("qtd_dest_final", "sum")).reset_index().sort_values(by=["distancia_total_percorrida"], ascending=False)\
                .rename(columns={"tipo_transf": "Tipo de Transferência", "distancia_total_percorrida": "Distância Total Percorrida (Km)", \
                "qtd_dest_final": "Transferências"})
            
            df_group["Distância (%)"] = df_group["Distância Total Percorrida (Km)"].apply(
            lambda x: round(int(x) / df_group['Distância Total Percorrida (Km)'].astype(int).sum() * 100, 1)) 

            df_group["Transferências (%)"] = df_group["Transferências"].apply(
            lambda x: round(int(x) / df_group['Transferências'].astype(int).sum() * 100, 1)) 

            df_group["Distância Total Percorrida (Km)"] = df_group["Distância Total Percorrida (Km)"].astype(str).str.replace(',', 'X').replace('.', ',').replace('X', '.').str.split(".").str.get(0)
            st.dataframe(df_group, use_container_width=True, hide_index=True)

            df_group = tb_fat_transp.groupby(["tipo_viatura"]).agg(
            distancia_total_percorrida=("distancia_total_percorrida", "sum"),
            qtd_dest_final=("qtd_dest_final", "sum")).reset_index().sort_values(by=["distancia_total_percorrida"], ascending=False)\
                .rename(columns={"tipo_viatura": "Tipo de Viatura", "distancia_total_percorrida": "Distância Total Percorrida (Km)", \
                "qtd_dest_final": "Transferências"})
            
            df_group["Distância (%)"] = df_group["Distância Total Percorrida (Km)"].apply(
            lambda x: round(int(x) / df_group['Distância Total Percorrida (Km)'].astype(int).sum() * 100, 1)) 

            df_group["Transferências (%)"] = df_group["Transferências"].apply(
            lambda x: round(int(x) / df_group['Transferências'].astype(int).sum() * 100, 1)) 

            df_group["Distância Total Percorrida (Km)"] = df_group["Distância Total Percorrida (Km)"].astype(str).str.replace(',', 'X').replace('.', ',').replace('X', '.').str.split(".").str.get(0)
            st.dataframe(df_group, use_container_width=True, hide_index=True)

        with tab_dist_viatura:
            df_group = tb_fat_transp.groupby(["viatura"]).agg(
            distancia_total_percorrida=("distancia_total_percorrida", "sum"),
            qtd_dest_final=("qtd_dest_final", "sum")).reset_index().sort_values(by=["distancia_total_percorrida"], ascending=False)\
                .rename(columns={"viatura": "Viatura", "distancia_total_percorrida": "Distância Total Percorrida (Km)", \
                "qtd_dest_final": "Transferências"})
            
            df_group["Distância (%)"] = df_group["Distância Total Percorrida (Km)"].apply(
            lambda x: round(int(x) / df_group['Distância Total Percorrida (Km)'].astype(int).sum() * 100, 1)) 
            

            df_group["Transferências (%)"] = df_group["Transferências"].apply(
            lambda x: round(int(x) / df_group['Transferências'].astype(int).sum() * 100, 1)) 

            df_group["Distância Total Percorrida (Km)"] = df_group["Distância Total Percorrida (Km)"].astype(str).str.replace(',', 'X').replace('.', ',').replace('X', '.').str.split(".").str.get(0)
            st.dataframe(df_group, use_container_width=True, hide_index=True)

elif st.session_state["authentication_status"] is False:

    st.error("Usuário/Senha inválido")

elif st.session_state["authentication_status"] is None:

    st.warning("Por favor, utilize seu usuário e senha")

