# s1_importacao_e_compreensao_dados.py
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns

# Configurar visualização
plt.style.use('ggplot')
sns.set_theme()

# Definir caminho das pastas - ajustado para sua estrutura
base_path = ""  # Caminho atual
bronze_path = f"{base_path}1_bronze/"
silver_path = f"{base_path}2_silver/"
gold_path = f"{base_path}3_gold/"
tabnet_path = f"{base_path}dados_tabnet/"


def ler_csv_com_flexibilidade(arquivo, separadores=[';', ',', '\t']):
    """
    Tenta ler um arquivo CSV com diferentes separadores
    """
    for sep in separadores:
        try:
            # Tenta ler com diferentes codificações
            for encoding in ['latin1', 'utf-8', 'cp1252']:
                try:
                    df = pd.read_csv(arquivo, sep=sep, encoding=encoding)
                    print(
                        f"Lido com sucesso: {arquivo} (separador: '{sep}', encoding: {encoding})")
                    return df
                except UnicodeDecodeError:
                    continue
        except Exception as e:
            if "Expected" in str(e) and "fields" in str(e) and "saw" in str(e):
                # Tenta com engine python que é mais flexível
                try:
                    df = pd.read_csv(arquivo, sep=sep,
                                     encoding='latin1', engine='python')
                    print(
                        f"Lido com sucesso: {arquivo} (separador: '{sep}', engine: python)")
                    return df
                except:
                    pass
            continue

    raise ValueError(
        f"Não foi possível ler o arquivo {arquivo} com os separadores fornecidos.")


def importar_dados():
    """
    Importa os dados das pastas bronze, silver, gold e tabnet
    """
    print("Importando dados...")

    try:
        # Carregar dados da pasta gold
        print(f"Tentando carregar: {gold_path}gold_micro.csv")
        df_gold_micro = ler_csv_com_flexibilidade(f"{gold_path}gold_micro.csv")

        print(f"Tentando carregar: {gold_path}gold_municipio.csv")
        df_gold_municipio = ler_csv_com_flexibilidade(
            f"{gold_path}gold_municipio.csv")

        # Carregar dados da pasta tabnet (fonte oficial)
        print(f"Tentando carregar: {tabnet_path}cnes_microrregiao.csv")
        df_tabnet_micro = ler_csv_com_flexibilidade(
            f"{tabnet_path}cnes_microrregiao.csv")

        print(f"Tentando carregar: {tabnet_path}cnes_municipio.csv")
        df_tabnet_municipio = ler_csv_com_flexibilidade(
            f"{tabnet_path}cnes_municipio.csv")

        # Carregar dados da pasta silver para relações
        print(f"Tentando carregar: {silver_path}dim_mun.xlsx")
        try:
            df_silver = pd.read_excel(f"{silver_path}dim_mun.xlsx")
            print(f"Lido com sucesso: {silver_path}dim_mun.xlsx")
        except Exception as e:
            print(f"Erro ao ler Excel, tentando CSV: {e}")
            df_silver = ler_csv_com_flexibilidade(f"{silver_path}silver.csv")

        # Exibir informações básicas sobre os dataframes
        print("=== Informações sobre os dataframes ===")
        print("\nGold - Microrregião:")
        print(df_gold_micro.info())
        print("\nGold - Município:")
        print(df_gold_municipio.info())
        print("\nTABNET - Microrregião:")
        print(df_tabnet_micro.info())
        print("\nTABNET - Município:")
        print(df_tabnet_municipio.info())
        print("\nSilver:")
        print(df_silver.info())

        # Exibir as primeiras linhas de cada dataframe
        print("\n=== Primeiras linhas dos dataframes ===")
        print("\nGold - Microrregião:")
        print(df_gold_micro.head())
        print("\nGold - Município:")
        print(df_gold_municipio.head())
        print("\nTABNET - Microrregião:")
        print(df_tabnet_micro.head())
        print("\nTABNET - Município:")
        print(df_tabnet_municipio.head())
        print("\nSilver:")
        print(df_silver.head())

        return {
            'gold_micro': df_gold_micro,
            'gold_municipio': df_gold_municipio,
            'tabnet_micro': df_tabnet_micro,
            'tabnet_municipio': df_tabnet_municipio,
            'silver': df_silver
        }

    except Exception as e:
        print(f"Erro durante a importação: {e}")
        raise e  # Re-lança a exceção para ser capturada pelo bloco try/except externo


# Executar importação e retornar os dataframes
if __name__ == "__main__":
    try:
        dataframes = importar_dados()

        # Salvar os dataframes como pickle para uso em outros scripts
        import pickle
        with open('dataframes.pkl', 'wb') as f:
            pickle.dump(dataframes, f)

        print("\nDataframes salvos com sucesso para uso nos próximos scripts.")
    except Exception as e:
        print(f"Erro ao importar dados: {e}")

        # Imprimir os arquivos disponíveis para debug
        print("\nArquivos disponíveis:")
        print("1_bronze:", os.listdir(bronze_path) if os.path.exists(
            bronze_path) else "Diretório não encontrado")
        print("2_silver:", os.listdir(silver_path) if os.path.exists(
            silver_path) else "Diretório não encontrado")
        print("3_gold:", os.listdir(gold_path) if os.path.exists(
            gold_path) else "Diretório não encontrado")
        print("dados_tabnet:", os.listdir(tabnet_path) if os.path.exists(
            tabnet_path) else "Diretório não encontrado")

        # Mostrar conteúdo parcial do arquivo problemático
        print("\nVerificando conteúdo dos arquivos:")
        arquivos_csv = [
            f"{gold_path}gold_micro.csv",
            f"{gold_path}gold_municipio.csv",
            f"{tabnet_path}cnes_microrregiao.csv",
            f"{tabnet_path}cnes_municipio.csv"
        ]

        for arquivo in arquivos_csv:
            try:
                print(f"\nPrimeiras 5 linhas de {arquivo}:")
                with open(arquivo, 'r', encoding='latin1') as f:
                    for i, linha in enumerate(f):
                        if i < 5:
                            print(f"Linha {i+1}: {linha.strip()}")
                        else:
                            break
            except Exception as e:
                print(f"Erro ao ler {arquivo}: {e}")
