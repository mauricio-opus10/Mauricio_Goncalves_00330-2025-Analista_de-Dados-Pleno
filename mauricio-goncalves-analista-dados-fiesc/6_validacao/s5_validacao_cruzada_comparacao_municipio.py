# s5_validacao_cruzada_comparacao_municipio.py
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


def extrair_codigo_nome(texto):
    """Extrai código e nome de uma string no formato '420005 ABDON BATISTA'"""
    if pd.isna(texto):
        return None, texto

    partes = str(texto).strip().split(' ', 1)
    if len(partes) == 2 and partes[0].isdigit():
        codigo = partes[0]
        nome = partes[1]
        return codigo, nome
    return None, texto


def validar_por_municipio(df_gold_municipio, df_tabnet_municipio):
    """
    Compara os dados por município entre as bases gold e tabnet
    """
    print("Executando validação por município...")

    # Preparar dataframe Gold
    df_gold = df_gold_municipio.copy()
    df_gold.columns = ['municipio', 'quantidade_gold']

    # Preparar dataframe TABNET
    df_tabnet = df_tabnet_municipio.copy()
    df_tabnet.columns = ['municipio', 'quantidade_tabnet']

    # Remover linha de total do TABNET, se existir
    df_tabnet = df_tabnet[~df_tabnet['municipio'].astype(
        str).str.contains('Total', case=False, na=False)]

    # Remover linhas de nota e outras informações não relevantes
    df_tabnet = df_tabnet[~df_tabnet['municipio'].astype(
        str).str.contains('Nota|Fonte|partir|Até', case=False, na=False)]

    # Extrair código e nome dos municípios do TABNET
    df_tabnet['codigo'], df_tabnet['nome'] = zip(
        *df_tabnet['municipio'].apply(extrair_codigo_nome))

    # Normalizar nomes dos municípios para comparação
    df_gold['municipio_norm'] = df_gold['municipio'].apply(normalizar_texto)
    df_tabnet['municipio_norm'] = df_tabnet['nome'].apply(normalizar_texto)

    # Mostrar amostra de municípios para verificação
    print("\nAmostra de municípios no Gold:")
    print(df_gold['municipio'].head(10).tolist())

    print("\nAmostra de municípios no TABNET (após extração):")
    print(df_tabnet['nome'].head(10).tolist())

    # Mesclar os dataframes para comparação
    df_comparacao = pd.merge(
        df_gold,
        df_tabnet[['municipio_norm', 'quantidade_tabnet', 'codigo']],
        on='municipio_norm',
        how='outer',
        suffixes=('', '_tabnet')
    )

    # Calcular diferenças
    df_comparacao['diferenca'] = df_comparacao['quantidade_gold'] - \
        df_comparacao['quantidade_tabnet']
    df_comparacao['percentual_diferenca'] = (
        df_comparacao['diferenca'] / df_comparacao['quantidade_tabnet'] * 100).round(2)
    df_comparacao['status'] = np.where(df_comparacao['diferenca'].abs() < 0.01, '✓',
                                       np.where(df_comparacao['diferenca'].abs() <= df_comparacao['quantidade_tabnet'] * 0.01, '⚠️', '❌'))

    # Identificar municípios que estão em uma base mas não na outra
    somente_gold = df_comparacao[df_comparacao['quantidade_tabnet'].isna()]
    somente_tabnet = df_comparacao[df_comparacao['quantidade_gold'].isna()]

    # Ordenar por percentual de diferença (absoluto) para destacar as maiores discrepâncias
    df_comparacao_validos = df_comparacao.dropna(
        subset=['quantidade_gold', 'quantidade_tabnet'])
    df_comparacao_validos = df_comparacao_validos.sort_values(
        by='percentual_diferenca', key=abs, ascending=False)

    # Criar visualização das diferenças significativas (mais de 5%)
    plt.figure(figsize=(12, 8))
    if not df_comparacao_validos.empty:
        df_plot = df_comparacao_validos[df_comparacao_validos['percentual_diferenca'].abs(
        ) > 5].head(10)
        if not df_plot.empty:
            sns.barplot(x='municipio', y='diferenca', data=df_plot)
            plt.xticks(rotation=45, ha='right')
            plt.title('Top 10 Municípios com Maiores Discrepâncias (>5%)')
            plt.ylabel('Diferença (Gold - TABNET)')
            plt.tight_layout()
            plt.savefig('discrepancias_municipio.png')
        plt.close()

    resultados = {
        'comparacao_completa': df_comparacao,
        'comparacao_ordenada': df_comparacao_validos,
        'somente_gold': somente_gold,
        'somente_tabnet': somente_tabnet,
        'total_inconsistencias': (df_comparacao['diferenca'].abs() > 0.01).sum(),
        'inconsistencias_significativas': (df_comparacao['percentual_diferenca'].abs() > 5).sum()
    }

    # Imprimir resultados
    print("\n=== Validação por Município ===")
    print(f"Total de municípios analisados: {len(df_comparacao)}")
    print(
        f"Total de inconsistências encontradas: {resultados['total_inconsistencias']}")
    print(
        f"Inconsistências significativas (>5%): {resultados['inconsistencias_significativas']}")

    print("\nMunicípios com maiores discrepâncias:")
    if not df_comparacao_validos.empty:
        print(df_comparacao_validos.head(10)[
            ['municipio', 'quantidade_gold', 'quantidade_tabnet',
                'diferenca', 'percentual_diferenca', 'status']
        ])

    if not somente_gold.empty:
        print(
            f"\nMunicípios presentes apenas na base Gold: {len(somente_gold)}")
        print(somente_gold.head(5)[['municipio', 'quantidade_gold']])

    if not somente_tabnet.empty:
        print(
            f"\nMunicípios presentes apenas na base TABNET: {len(somente_tabnet)}")
        print(somente_tabnet.head(5)[['municipio_norm', 'quantidade_tabnet']])

    return resultados


if __name__ == "__main__":
    # Carregar dataframes processados
    try:
        with open('dataframes_processados.pkl', 'rb') as f:
            dataframes = pickle.load(f)
    except:
        with open('dataframes.pkl', 'rb') as f:
            dataframes = pickle.load(f)

    # Executar validação por município
    resultados_municipio = validar_por_municipio(
        dataframes['gold_municipio'],
        dataframes['tabnet_municipio']
    )

    # Salvar resultados
    with open('resultados_municipio.pkl', 'wb') as f:
        pickle.dump(resultados_municipio, f)

    print("\nResultados da validação por município salvos com sucesso.")
