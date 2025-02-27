# s6_validacao_de_consistencia_interna_rel_micro_muni.py
import pandas as pd
import numpy as np
import pickle
import os
import matplotlib.pyplot as plt
import seaborn as sns
import sys

# Verificar se unidecode está instalado e instalar se necessário
try:
    import unidecode
except ImportError:
    print("Instalando pacote unidecode...")
    import subprocess
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "unidecode"])
    import unidecode


def normalizar_texto(texto):
    """Normaliza texto removendo acentos e convertendo para minúsculas"""
    if pd.isna(texto):
        return texto
    try:
        return unidecode.unidecode(str(texto).lower().strip())
    except:
        return str(texto).lower().strip()


def validar_consistencia_interna(df_gold_micro, df_gold_municipio, df_silver):
    """
    Verifica a consistência interna entre os arquivos da pasta gold
    e sua relação com a pasta silver
    """
    print("Executando validação de consistência interna...")

    # Preparar dataframes
    df_gold_micro = df_gold_micro.copy()
    df_gold_municipio = df_gold_municipio.copy()
    df_silver = df_silver.copy()

    # Normalizar nomes para facilitar o join
    df_gold_micro['microrregiao_norm'] = df_gold_micro['microrregiao'].apply(
        normalizar_texto)
    df_gold_municipio['municipio_norm'] = df_gold_municipio['municipio'].apply(
        normalizar_texto)
    df_silver['microrregiao_norm'] = df_silver['microrregiao'].apply(
        normalizar_texto)
    df_silver['municipio_norm'] = df_silver['municipio'].apply(
        normalizar_texto)

    # Verificar quais municípios no gold_municipio estão no silver
    municipios_matched = pd.merge(
        df_gold_municipio,
        df_silver[['municipio_norm', 'microrregiao_norm']],
        on='municipio_norm',
        how='left'
    )

    # Verificar municípios sem correspondência
    municipios_sem_match = municipios_matched[municipios_matched['microrregiao_norm'].isna(
    )]

    # Agrupar municípios por microrregião e somar quantidades
    if 'microrregiao_norm' in municipios_matched.columns:
        soma_por_micro = municipios_matched.groupby('microrregiao_norm')[
            'nu_quantidade'].sum().reset_index()
        soma_por_micro.columns = ['microrregiao_norm', 'quantidade_calculada']

        # Comparar com os valores diretos de microrregião
        comparacao_micro = pd.merge(
            soma_por_micro,
            df_gold_micro[['microrregiao_norm', 'nu_quantidade']],
            on='microrregiao_norm',
            how='outer'
        )

        # Renomear para clareza
        comparacao_micro = comparacao_micro.rename(
            columns={'nu_quantidade': 'quantidade_declarada'})

        # Calcular diferenças
        comparacao_micro['diferenca'] = comparacao_micro['quantidade_calculada'] - \
            comparacao_micro['quantidade_declarada']
        comparacao_micro['percentual_diferenca'] = (
            comparacao_micro['diferenca'] / comparacao_micro['quantidade_declarada'] * 100).round(2)
        comparacao_micro['status'] = np.where(comparacao_micro['diferenca'].abs() < 0.01, '✓',
                                              np.where(comparacao_micro['diferenca'].abs() <= comparacao_micro['quantidade_declarada'] * 0.01, '⚠️', '❌'))
    else:
        print(
            "AVISO: Não foi possível estabelecer relação entre municípios e microrregiões!")
        comparacao_micro = pd.DataFrame()

    # Verificar possíveis duplicações
    municipios_duplicados = df_gold_municipio['municipio_norm'].value_counts()
    municipios_duplicados = municipios_duplicados[municipios_duplicados > 1]

    # Criar visualização das discrepâncias
    if not comparacao_micro.empty:
        plt.figure(figsize=(12, 8))
        df_plot = comparacao_micro[comparacao_micro['diferenca'].abs() > 0].sort_values(
            by='diferenca', key=abs, ascending=False).head(10)
        if not df_plot.empty:
            sns.barplot(x='microrregiao_norm', y='diferenca', data=df_plot)
            plt.xticks(rotation=45, ha='right')
            plt.title(
                'Top 10 Microrregiões com Discrepâncias entre Valor Direto e Calculado')
            plt.ylabel('Diferença (Calculado - Declarado)')
            plt.tight_layout()
            plt.savefig('discrepancias_consistencia.png')
        plt.close()

    resultados = {
        'comparacao_micro': comparacao_micro,
        'municipios_sem_match': municipios_sem_match,
        'municipios_duplicados': municipios_duplicados,
        'total_inconsistencias': len(comparacao_micro[comparacao_micro['diferenca'].abs() > 0]) if not comparacao_micro.empty else 0
    }

    # Imprimir resultados
    print("\n=== Validação de Consistência Interna ===")
    print(
        f"Total de microrregiões analisadas: {len(comparacao_micro) if not comparacao_micro.empty else 0}")
    print(
        f"Total de inconsistências encontradas: {resultados['total_inconsistencias']}")

    print("\nMicrorregiões com inconsistências entre valor calculado e declarado:")
    if not comparacao_micro.empty:
        inconsistencias = comparacao_micro[comparacao_micro['diferenca'].abs(
        ) > 0]
        if not inconsistencias.empty:
            print(inconsistencias[['microrregiao_norm', 'quantidade_calculada',
                  'quantidade_declarada', 'diferenca', 'percentual_diferenca', 'status']])
        else:
            print("Nenhuma inconsistência encontrada!")

    print(
        f"\nMunicípios sem correspondência na tabela silver: {len(municipios_sem_match)}")
    if not municipios_sem_match.empty:
        print(municipios_sem_match[['municipio', 'nu_quantidade']].head(10))

    print(
        f"\nMunicípios duplicados na base Gold: {len(municipios_duplicados)}")
    if not municipios_duplicados.empty:
        for municipio, count in municipios_duplicados.items():
            print(f"  - {municipio}: {count} ocorrências")
            print(df_gold_municipio[df_gold_municipio['municipio_norm'] == municipio][[
                  'municipio', 'nu_quantidade']])

    return resultados


if __name__ == "__main__":
    # Carregar dataframes processados
    try:
        with open('dataframes_processados.pkl', 'rb') as f:
            dataframes = pickle.load(f)
    except:
        with open('dataframes.pkl', 'rb') as f:
            dataframes = pickle.load(f)

    # Executar validação de consistência interna
    resultados_consistencia = validar_consistencia_interna(
        dataframes['gold_micro'],
        dataframes['gold_municipio'],
        dataframes['silver']
    )

    # Salvar resultados
    with open('resultados_consistencia.pkl', 'wb') as f:
        pickle.dump(resultados_consistencia, f)

    print("\nResultados da validação de consistência interna salvos com sucesso.")
