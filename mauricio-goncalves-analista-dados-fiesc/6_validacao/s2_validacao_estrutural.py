# s2_validacao_estrutural.py
import pandas as pd
import numpy as np
import pickle
import os


def processar_tabnet(df, tipo='microrregiao'):
    """
    Processa os dados TABNET que estão em formato de texto em uma única coluna
    """
    print(f"Processando TABNET {tipo}...")

    # Verificar se o dataframe tem apenas uma coluna
    if len(df.columns) == 1:
        coluna = df.columns[0]

        # Encontrar a linha que contém os cabeçalhos
        cabecalho_idx = None
        for i, valor in enumerate(df[coluna]):
            if 'Microrregião IBGE;"Quantidade"' in str(valor) or 'Município;"Quantidade"' in str(valor):
                cabecalho_idx = i
                break

        if cabecalho_idx is not None:
            # Extrair dados relevantes (ignorar cabeçalhos)
            dados = df.iloc[(cabecalho_idx + 1):].copy()

            # Dividir a coluna em duas usando o ponto e vírgula como delimitador
            dados_novos = dados[coluna].str.split(';', expand=True)

            if len(dados_novos.columns) >= 2:
                # Renomear colunas
                if tipo == 'microrregiao':
                    dados_novos.columns = ['Microrregião IBGE', 'Quantidade']
                else:
                    dados_novos.columns = ['Município', 'Quantidade']

                # Converter quantidade para número
                dados_novos['Quantidade'] = pd.to_numeric(
                    dados_novos['Quantidade'], errors='coerce')

                return dados_novos

    return df  # Retorna o dataframe original se não conseguir processar


def validar_estrutura(dataframes):
    """
    Verifica a estrutura dos dataframes, incluindo:
    - Verificação de colunas obrigatórias
    - Verificação de tipos de dados
    - Verificação de valores nulos
    - Verificação de formatação de texto (caracteres especiais)
    """
    print("Executando validação estrutural...")

    # Processar os dados TABNET se necessário
    if 'tabnet_micro' in dataframes:
        dataframes['tabnet_micro'] = processar_tabnet(
            dataframes['tabnet_micro'], 'microrregiao')

    if 'tabnet_municipio' in dataframes:
        dataframes['tabnet_municipio'] = processar_tabnet(
            dataframes['tabnet_municipio'], 'municipio')

    resultados = {}

    for nome, df in dataframes.items():
        resultado = {
            "total_linhas": len(df),
            "colunas_presentes": list(df.columns),
            "valores_nulos": df.isnull().sum().to_dict(),
            "tipos_dados": {col: str(df[col].dtype) for col in df.columns}
        }

        # Verificar problemas de codificação em colunas de texto
        problemas_codificacao = []
        for col in df.select_dtypes(include=['object']).columns:
            # Verificar caracteres problemáticos (indicativos de problemas de codificação)
            caracteres_problematicos = df[col].astype(
                str).str.contains('Ã|Â|Í|Ú|Ó|Ç', regex=True).sum()
            if caracteres_problematicos > 0:
                problemas_codificacao.append(
                    f"{col}: {caracteres_problematicos} valores com possíveis problemas de codificação")

        resultado["problemas_codificacao"] = problemas_codificacao
        resultados[nome] = resultado

    # Imprimir resultados da validação estrutural
    print("\n=== Resultados da Validação Estrutural ===")
    for nome, resultado in resultados.items():
        print(f"\n{nome.upper()}:")
        print(f"Total de linhas: {resultado['total_linhas']}")
        print(
            f"Colunas presentes: {', '.join(resultado['colunas_presentes'])}")

        nulos_encontrados = False
        for col, count in resultado['valores_nulos'].items():
            if count > 0:
                if not nulos_encontrados:
                    print("Valores nulos:")
                    nulos_encontrados = True
                print(f"  - {col}: {count}")

        if resultado['problemas_codificacao']:
            print("Problemas de codificação:")
            for problema in resultado['problemas_codificacao']:
                print(f"  - {problema}")

    return resultados


if __name__ == "__main__":
    # Carregar dataframes salvos
    with open('dataframes.pkl', 'rb') as f:
        dataframes = pickle.load(f)

    # Executar validação estrutural
    resultados_estrutura = validar_estrutura(dataframes)

    # Salvar resultados
    with open('resultados_estrutura.pkl', 'wb') as f:
        pickle.dump(resultados_estrutura, f)

    # Salvar também os dataframes processados
    with open('dataframes_processados.pkl', 'wb') as f:
        pickle.dump(dataframes, f)

    print("\nResultados da validação estrutural salvos com sucesso.")
