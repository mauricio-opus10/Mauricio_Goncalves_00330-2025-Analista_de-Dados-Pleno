# s4_validacao_cruzada_comparacao_microrregiao.py
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
    """Extrai código e nome de uma string no formato '42001 SAO MIGUEL DO OESTE'"""
    if pd.isna(texto):
        return None, texto

    partes = str(texto).strip().split(' ', 1)
    if len(partes) == 2 and partes[0].isdigit():
        codigo = partes[0]
        nome = partes[1]
        return codigo, nome
    return None, texto


def validar_por_microrregiao(df_gold_micro, df_tabnet_micro):
    """
    Compara os dados por microrregião entre as bases gold e tabnet
    """
    print("Executando validação por microrregião...")

    # Preparar dataframe Gold
    df_gold = df_gold_micro.copy()
    df_gold.columns = ['microrregiao', 'quantidade_gold']

    # Preparar dataframe TABNET
    df_tabnet = df_tabnet_micro.copy()
    df_tabnet.columns = ['microrregiao', 'quantidade_tabnet']

    # Remover linha de total do TABNET, se existir
    df_tabnet = df_tabnet[~df_tabnet['microrregiao'].astype(
        str).str.contains('Total', case=False, na=False)]

    # Extrair código e nome das microrregiões do TABNET
    df_tabnet['codigo'], df_tabnet['nome'] = zip(
        *df_tabnet['microrregiao'].apply(extrair_codigo_nome))

    # Normalizar nomes das microrregiões para comparação
    df_gold['microrregiao_norm'] = df_gold['microrregiao'].apply(
        normalizar_texto)
    df_tabnet['microrregiao_norm'] = df_tabnet['nome'].apply(normalizar_texto)

    print("\nMicrorregiões no Gold:")
    print(df_gold['microrregiao'].tolist())

    print("\nMicrorregiões no TABNET (após extração):")
    print(df_tabnet['nome'].tolist())

    # Mesclar os dataframes para comparação
    # Primeiro, tentar mesclar por microrregiao_norm
    df_comparacao = pd.merge(
        df_gold,
        df_tabnet[['microrregiao_norm', 'quantidade_tabnet', 'codigo']],
        on='microrregiao_norm',
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

    # Identificar microrregiões que estão em uma base mas não na outra
    somente_gold = df_comparacao[df_comparacao['quantidade_tabnet'].isna()]
    somente_tabnet = df_comparacao[df_comparacao['quantidade_gold'].isna()]

    # Ordenar por percentual de diferença (absoluto) para destacar as maiores discrepâncias
    df_comparacao_validos = df_comparacao.dropna(
        subset=['quantidade_gold', 'quantidade_tabnet'])
    df_comparacao_validos = df_comparacao_validos.sort_values(
        by='percentual_diferenca', key=abs, ascending=False)

    # Criar visualização das diferenças
    plt.figure(figsize=(12, 8))
    if not df_comparacao_validos.empty:
        df_plot = df_comparacao_validos.head(10)
        sns.barplot(x='microrregiao', y='diferenca', data=df_plot)
        plt.xticks(rotation=45, ha='right')
        plt.title('Top 10 Microrregiões com Maiores Discrepâncias')
        plt.ylabel('Diferença (Gold - TABNET)')
        plt.tight_layout()
        plt.savefig('discrepancias_microrregiao.png')
        plt.close()

    resultados = {
        'comparacao_completa': df_comparacao,
        'comparacao_ordenada': df_comparacao_validos,
        'somente_gold': somente_gold,
        'somente_tabnet': somente_tabnet,
        'total_inconsistencias': (df_comparacao['diferenca'].abs() > 0.01).sum()
    }

    # Imprimir resultados
    print("\n=== Validação por Microrregião ===")
    print(f"Total de microrregiões analisadas: {len(df_comparacao)}")
    print(
        f"Total de inconsistências encontradas: {resultados['total_inconsistencias']}")

    print("\nMicrorregiões com maiores discrepâncias:")
    if not df_comparacao_validos.empty:
        print(df_comparacao_validos.head(10)[
            ['microrregiao', 'quantidade_gold', 'quantidade_tabnet',
                'diferenca', 'percentual_diferenca', 'status']
        ])

    if not somente_gold.empty:
        print("\nMicrorregiões presentes apenas na base Gold:")
        print(somente_gold[['microrregiao', 'quantidade_gold']])

    if not somente_tabnet.empty:
        print("\nMicrorregiões presentes apenas na base TABNET:")
        print(somente_tabnet[['microrregiao_norm', 'quantidade_tabnet']])

    return resultados


if __name__ == "__main__":
    # Carregar dataframes processados
    try:
        with open('dataframes_processados.pkl', 'rb') as f:
            dataframes = pickle.load(f)
    except:
        with open('dataframes.pkl', 'rb') as f:
            dataframes = pickle.load(f)

    # Executar validação por microrregião
    resultados_microrregiao = validar_por_microrregiao(
        dataframes['gold_micro'],
        dataframes['tabnet_micro']
    )

    # Salvar resultados
    with open('resultados_microrregiao.pkl', 'wb') as f:
        pickle.dump(resultados_microrregiao, f)

    print("\nResultados da validação por microrregião salvos com sucesso.")
