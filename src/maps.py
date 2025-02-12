from folium.plugins import HeatMap
import folium
import ast
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

# Função
def pct_rank_qcut(series, n):

    # Cria uma série de valores limite para os quantis, dividindo o intervalo [0, 1] em n partes iguais
    edges = pd.Series([float(i) / n for i in range(n + 1)])

    # Define uma função que encontra o índice do primeiro valor na série de limites que é maior ou igual a x
    f = lambda x: (edges >= x).values.argmax()

    # Classifica a série de entrada como uma porcentagem (de 0 a 1)
    # e então aplica a função f para mapear cada valor para seu respectivo quantil
    return series.rank(pct = 1).apply(f)
@st.cache_data
def show_heatmap(df):
    
    # Criando o mapa centralizado na localização desejada
    mapa = folium.Map(location=[-10.526485623243966, -37.372524582987405], zoom_start=8.8)
    marker_hospitais = folium.FeatureGroup(name='Hospitais')
    # Lista para armazenar todos os pontos processados
    all_points = []
    
    # Iterando sobre o DataFrame para processar os pontos
    for idx, row in df.iterrows():
        # Obtém a quantidade de destinos finais
        qtd = row['qtd_dest_final']

        df_group = df.loc[df["unidade_origem"] == row['unidade_origem']].groupby("unidade_origem").agg(
        distancia_total_percorrida=("distancia_total_percorrida", "sum"),
        coord_origem=("coord_origem", "first"),
        qtd_dest_final=("qtd_dest_final", "sum")
        ).reset_index()

        marker = folium.Marker(location=row['coord_origem'].split(","),
                            unidade=f"{row['unidade_origem']}",
                            tooltip = f"""
        <div style="display:flex">
        <div style="font-size: 11px; padding: 1rem;background-color: #0F5745; color: #CEDEDC;">
            <div style="font-size: 13px;"><strong>Unidade de Origem:</strong> {row['unidade_origem']}<br></div>
            <div style="font-size: 13px;"><strong>Transferências:</strong> {df_group['qtd_dest_final'].sum()}<br></div>
            <div style="font-size: 13px;"><strong>Km rodados:</strong> {int(round(df_group['distancia_total_percorrida'].sum(), 0))}<br></div>
        </div>

        </div>
        """,
        icon=folium.features.CustomIcon(r'assets/hospital.png', icon_size=(15,15)))
        marker.add_to(marker_hospitais)
        # Verifica se a quantidade é válida, numérica e maior que zero
        if pd.notna(qtd) and isinstance(qtd, (int, float)) and qtd > 0:
            # Caso onde a unidade de exame é igual à unidade de destino final
            if row['cnes_unidade_exame'] == row['cnes_unidade_dest_final']:
                try:
                    # Converte a string da rota de origem para lista e multiplica pelo número de ocorrências
                    all_points.extend(ast.literal_eval(row['rota_origem_exame']) * int(qtd))
                except (ValueError, SyntaxError):
                    pass  # Ignora erros na conversão de rota inválida

            # Caso onde a unidade de exame é nula
            elif pd.isna(row['cnes_unidade_exame']):
                try:
                    # Converte a string da rota de destino final para lista e multiplica pelo número de ocorrências
                    all_points.extend(ast.literal_eval(row['rota_origem_dest_final']) * int(qtd))
                except (ValueError, SyntaxError):
                    pass  # Ignora erros na conversão de rota inválida

            # Caso padrão onde unidades de origem e destino são diferentes
            else:
                try:
                    # Concatena as rotas de origem e destino, ajustando pela quantidade
                    all_points.extend((
                        ast.literal_eval(row['rota_origem_exame']) +
                        ast.literal_eval(row['rota_exame_dest_final'])) * int(qtd)
                    )
                except (ValueError, SyntaxError):
                    pass  # Ignora erros na conversão de rota inválida

    mapa.add_child(marker_hospitais)
    # Criando um DataFrame com os pontos processados e contando as ocorrências de cada ponto
    points_df = pd.DataFrame(all_points, columns=["lat", "lon"])
    points_count = points_df.groupby(["lat", "lon"]).size().reset_index(name="count")

    # Obtendo o valor máximo de ocorrências para normalização das cores
    max_count = points_count["count"].max()

    # Adicionando marcadores circulares ao mapa com cores e tooltip indicando ocorrências
    for _, row in points_count.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],  # Localização do marcador
            radius=10,  # Tamanho do marcador
            color="transparent",  # Sem borda visível
            fill_opacity=0.01,  # Transparência do preenchimento
        ).add_to(mapa)

    # Adicionando o HeatMap com a intensidade baseada nas ocorrências
    heat_data = points_count[["lat", "lon", "count"]].values.tolist()

    # O valor de 'count' será usado como a intensidade do calor (não apenas a posição)
    HeatMap(heat_data, min_opacity=0.2).add_to(mapa)

    st.components.v1.html(folium.Figure().add_child(mapa).render(), height=700, width=1000)

def show_circle_map_km(df):

        # Criando o mapa centralizado na localização desejada
    mapa = folium.Map(location=[-10.526485623243966, -37.372524582987405], zoom_start=8.8)
    marker_hospitais = folium.FeatureGroup(name='Hospitais')

    # Agrupando por coord_origem e somando as distâncias totais
    df_group = df.groupby("unidade_origem").agg(
        distancia_total_percorrida=("distancia_total_percorrida", "sum"),
        coord_origem=("coord_origem", "first"),
        qtd_dest_final=("qtd_dest_final", "sum")
    ).reset_index()
    print(df_group.columns)
    dict_radius = {i: i * 3 for i in range(1, 15)}
    df_group['km_normalizado'] = pct_rank_qcut(df_group['distancia_total_percorrida'], 10)
    df_group['km_radius'] = df_group['km_normalizado'].map(dict_radius)

    for idx, row in df_group.iterrows():

        coord_origem = tuple(map(float, row['coord_origem'].split(",")))  # Convertendo coordenadas para tuple

        # Adiciona o marcador do hospital
        folium.Marker(
            location=coord_origem,
            tooltip=f"""
            <div style="display:flex">
                <div style="font-size: 11px; padding: 1rem;background-color: #0F5745; color: #CEDEDC;">
                    <div style="font-size: 13px;"><strong>Unidade de Origem:</strong> {row['unidade_origem']}<br></div>
                    <div style="font-size: 13px;"><strong>Transferências:</strong> {row['qtd_dest_final']}<br></div>
                    <div style="font-size: 13px;"><strong>Km rodados:</strong> {int(round(row['distancia_total_percorrida'], 0))}<br></div>
                </div>
            </div>
            """,
            icon=folium.features.CustomIcon(
                r'assets/hospital.png', icon_size=(15, 15)
            )
        ).add_to(marker_hospitais)

        folium.CircleMarker(
            location=coord_origem,
            radius=row['km_radius'],  # Tamanho do marcador
            color="#5B1401",
            fill=True,
            fill_color="#f4562a",
            fill_opacity=0.6,
            tooltip=f"""
            <div style="display:flex">
                <div style="font-size: 11px; padding: 1rem;background-color: #0F5745; color: #CEDEDC;">
                    <div style="font-size: 13px;"><strong>Unidade de Origem:</strong> {row['unidade_origem']}<br></div>
                    <div style="font-size: 13px;"><strong>Transferências:</strong> {row['qtd_dest_final']}<br></div>
                    <div style="font-size: 13px;"><strong>Km rodados:</strong> {int(round(row['distancia_total_percorrida'], 0))}<br></div>
                </div>
            </div>
            """  # Texto exibido ao passar o mouse
        ).add_to(mapa)


    # Adicionando camada de hospitais
    mapa.add_child(marker_hospitais)

    # Exibindo o mapa no Jupyter Notebook ou salvando como arquivo HTML
    st_folium(mapa, width=1200)


    
def show_circle_map_trajeto(df):

            # Criando o mapa centralizado na localização desejada
    # Criando o mapa centralizado na localização desejada
    mapa = folium.Map(location=[-10.526485623243966, -37.372524582987405], zoom_start=8.8)
    marker_hospitais = folium.FeatureGroup(name='Hospitais')

    # Agrupando por coord_origem e somando as distâncias totais
    df_group = df.groupby("unidade_origem").agg(
        distancia_total_percorrida=("distancia_total_percorrida", "sum"),
        coord_origem=("coord_origem", "first"),
        qtd_dest_final=("qtd_dest_final", "sum")
    ).reset_index()
    print(df_group.columns)
    dict_radius = {i: i * 3 for i in range(1, 11)}
    df_group['qtd_dest_final_normalizado'] = pct_rank_qcut(df_group['qtd_dest_final'], 10)
    df_group['qtd_dest_final_radius'] = df_group['qtd_dest_final_normalizado'].map(dict_radius)

    for idx, row in df_group.iterrows():

        coord_origem = tuple(map(float, row['coord_origem'].split(",")))  # Convertendo coordenadas para tuple

        # Adiciona o marcador do hospital
        folium.Marker(
            location=coord_origem,
            tooltip=f"""
            <div style="display:flex">
                <div style="font-size: 11px; padding: 1rem;background-color: #0F5745; color: #CEDEDC;">
                    <div style="font-size: 13px;"><strong>Unidade de Origem:</strong> {row['unidade_origem']}<br></div>
                    <div style="font-size: 13px;"><strong>Transferências:</strong> {row['qtd_dest_final']}<br></div>
                    <div style="font-size: 13px;"><strong>Km rodados:</strong> {int(round(row['distancia_total_percorrida'], 0))}<br></div> 
                </div>
            </div>
            """,
            icon=folium.features.CustomIcon(
                r'assets/hospital.png', icon_size=(15, 15)
            )
        ).add_to(marker_hospitais)

        folium.CircleMarker(
            location=coord_origem,
            radius=row['qtd_dest_final_radius'],  # Tamanho do marcador
    
            fill=True,
            fill_color="#8B1E3F",
            color="#430F1E",
            fill_opacity=0.7,
            tooltip=f"""
            <div style="display:flex">
                <div style="font-size: 11px; padding: 1rem;background-color: #0F5745; color: #CEDEDC;">
                    <div style="font-size: 13px;"><strong>Unidade de Origem:</strong> {row['unidade_origem']}<br></div>
                    <div style="font-size: 13px;"><strong>Transferências:</strong> {row['qtd_dest_final']}<br></div>
                    <div style="font-size: 13px;"><strong>Km rodados:</strong> {int(round(row['distancia_total_percorrida'], 0))}<br></div>
                </div>
            </div>
            """  # Texto exibido ao passar o mouse
        ).add_to(mapa)


    # Adicionando camada de hospitais
    mapa.add_child(marker_hospitais)

    # Exibindo o mapa no Jupyter Notebook ou salvando como arquivo HTML
    st_folium(mapa, width=1200)