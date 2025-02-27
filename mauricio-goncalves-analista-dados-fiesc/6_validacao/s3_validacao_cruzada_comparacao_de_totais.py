# s3_validacao_cruzada_comparacao_totais.py
import pandas as pd
import numpy as np
import pickle
import os


def validar_totais(df_gold_micro, df_tabnet_micro, df_gold_municipio, df_tabnet_municipio):
    """
    Compara os totais de estabelecimentos entre as bases gold e tabnet
    """
    print("Executando validação de totais...")

    # Colunas para análise - já conhecemos os nomes
    col_gold_micro = 'nu_quantidade'
    col_tabnet_micro = 'Quantidade'
    col_gold_municipio = 'nu_quantidade'
    col_tabnet_municipio = 'Quantidade'

    # Obter totais da gold
    total_gold_micro = df_gold_micro[col_gold_micro].sum()
    total_gold_municipio = df_gold_municipio[col_gold_municipio].sum()

    # Obter totais da TABNET (excluindo linhas nulas)
    total_tabnet_micro = df_tabnet_micro[col_tabnet_micro].dropna().sum()
    total_tabnet_municipio = df_tabnet_municipio[col_tabnet_municipio].dropna(
    ).sum()

    # Verificar se há uma linha de total no TABNET
    if 'Total' in df_tabnet_micro['Microrregião IBGE'].values:
        try:
            total_linha_tabnet_micro = df_tabnet_micro[df_tabnet_micro['Microrregião IBGE']
                                                       == 'Total'][col_tabnet_micro].values[0]
            print(
                f"Total na linha 'Total' TABNET-Micro: {total_linha_tabnet_micro}")
        except:
            total_linha_tabnet_micro = None
    else:
        total_linha_tabnet_micro = None

    if 'Total' in df_tabnet_municipio['Município'].values:
        try:
            total_linha_tabnet_municipio = df_tabnet_municipio[df_tabnet_municipio['Município']
                                                               == 'Total'][col_tabnet_municipio].values[0]
            print(
                f"Total na linha 'Total' TABNET-Município: {total_linha_tabnet_municipio}")
        except:
            total_linha_tabnet_municipio = None
    else:
        total_linha_tabnet_municipio = None

    # Usar a linha de total se disponível, caso contrário usar a soma
    if total_linha_tabnet_micro is not None:
        total_tabnet_micro_final = total_linha_tabnet_micro
    else:
        total_tabnet_micro_final = total_tabnet_micro

    if total_linha_tabnet_municipio is not None:
        total_tabnet_municipio_final = total_linha_tabnet_municipio
    else:
        total_tabnet_municipio_final = total_tabnet_municipio

    # Comparar totais
    resultados = {
        "total_gold_micro": total_gold_micro,
        "total_tabnet_micro": total_tabnet_micro_final,
        "diferenca_micro": total_gold_micro - total_tabnet_micro_final,
        "percentual_diferenca_micro": ((total_gold_micro - total_tabnet_micro_final) / total_tabnet_micro_final * 100) if total_tabnet_micro_final != 0 else float('inf'),

        "total_gold_municipio": total_gold_municipio,
        "total_tabnet_municipio": total_tabnet_municipio_final,
        "diferenca_municipio": total_gold_municipio - total_tabnet_municipio_final,
        "percentual_diferenca_municipio": ((total_gold_municipio - total_tabnet_municipio_final) / total_tabnet_municipio_final * 100) if total_tabnet_municipio_final != 0 else float('inf'),

        "consistencia_interna_gold": total_gold_micro == total_gold_municipio,
        "consistencia_interna_tabnet": total_tabnet_micro_final == total_tabnet_municipio_final
    }

    # Imprimir resultados
    print("\n=== Validação de Totais ===")
    print(f"Total Gold Microrregião: {resultados['total_gold_micro']}")
    print(f"Total TABNET Microrregião: {resultados['total_tabnet_micro']}")
    print(
        f"Diferença: {resultados['diferenca_micro']} ({resultados['percentual_diferenca_micro']:.2f}%)")
    print(f"\nTotal Gold Município: {resultados['total_gold_municipio']}")
    print(f"Total TABNET Município: {resultados['total_tabnet_municipio']}")
    print(
        f"Diferença: {resultados['diferenca_municipio']} ({resultados['percentual_diferenca_municipio']:.2f}%)")
    print(
        f"\nConsistência interna Gold: {resultados['consistencia_interna_gold']}")
    print(
        f"Consistência interna TABNET: {resultados['consistencia_interna_tabnet']}")

    return resultados


if __name__ == "__main__":
    # Carregar dataframes processados
    try:
        with open('dataframes_processados.pkl', 'rb') as f:
            dataframes = pickle.load(f)
    except:
        with open('dataframes.pkl', 'rb') as f:
            dataframes = pickle.load(f)

    # Executar validação de totais
    resultados_totais = validar_totais(
        dataframes['gold_micro'],
        dataframes['tabnet_micro'],
        dataframes['gold_municipio'],
        dataframes['tabnet_municipio']
    )

    # Salvar resultados
    with open('resultados_totais.pkl', 'wb') as f:
        pickle.dump(resultados_totais, f)

    print("\nResultados da validação de totais salvos com sucesso.")
