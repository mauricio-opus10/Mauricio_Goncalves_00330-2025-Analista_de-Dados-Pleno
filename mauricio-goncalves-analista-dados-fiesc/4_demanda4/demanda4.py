import pandas as pd
import os


def estimar_estoque_trabalhadores_formatado():
    """
    Exemplo de script que:
      - Lê rais.xlsx (2002 a 2022) e novo_caged.xlsx (2023, 2024)
      - Calcula o estoque observado (2002..2022) e as estimativas (2023..2024)
      - Gera um DataFrame final com colunas [dt_ano, origem do dado, quantidade],
        ordenado em ordem decrescente (2024 no topo, 2002 na base).
      - Salva em Excel com formatação: sem gridlines, painel congelado, cabeçalho
        personalizado, colunas com formatação apropriada.
    """

    # === 1) Configurações de caminho ===
    base_dir = os.path.dirname(__file__)
    rais_path = os.path.join(base_dir, "rais.xlsx")
    caged_path = os.path.join(base_dir, "novo_caged.xlsx")
    output_excel = os.path.join(base_dir, "estimativa_estoque.xlsx")

    # === 2) Ler a base RAIS (2002..2022) ===
    df_rais = pd.read_excel(rais_path)
    # Supondo que a planilha tenha as colunas: dt_ano e nu_quantidade
    # Se houver múltiplas linhas por ano, agrupe:
    df_rais_agg = df_rais.groupby("dt_ano", as_index=False)[
        "nu_quantidade"].sum()

    # Filtrar os anos de 2002 a 2022
    df_rais_agg = df_rais_agg.loc[(df_rais_agg["dt_ano"] >= 2002) & (
        df_rais_agg["dt_ano"] <= 2022)].copy()

    # === 3) Ler a base Novo CAGED (2023, 2024) ===
    df_caged = pd.read_excel(caged_path)
    # Supondo que o arquivo contenha as colunas: dt_ano, nu_admitidos, nu_desligados
    # Se os dados forem mensais, agrupe por ano (descomente se necessário)
    # df_caged = df_caged.groupby("dt_ano", as_index=False)[["nu_admitidos","nu_desligados"]].sum()

    # Calcular o saldo: admissões - desligamentos
    df_caged["saldo"] = df_caged["nu_admitidos"] - df_caged["nu_desligados"]
    df_caged_agg = df_caged.groupby("dt_ano", as_index=False)["saldo"].sum()

    # === 4) Montar os dados "Dado Observado" (2002..2022) ===
    data_final = []
    for year in range(2002, 2023):  # 2002..2022
        row = df_rais_agg.loc[df_rais_agg["dt_ano"] == year]
        if not row.empty:
            quantidade = row["nu_quantidade"].values[0]
        else:
            quantidade = 0
        data_final.append({
            "dt_ano": year,
            "origem do dado": "Dado Observado",
            "quantidade": quantidade
        })

    # Encontrar estoque final de 2022 (base para a estimativa)
    estoque_2022 = next((item["quantidade"]
                        for item in data_final if item["dt_ano"] == 2022), 0)

    # === 5) Calcular as estimativas para 2023 e 2024 ===
    saldo_2023 = df_caged_agg.loc[df_caged_agg["dt_ano"]
                                  == 2023, "saldo"].sum()
    saldo_2024 = df_caged_agg.loc[df_caged_agg["dt_ano"]
                                  == 2024, "saldo"].sum()

    estoque_2023 = estoque_2022 + saldo_2023
    estoque_2024 = estoque_2023 + saldo_2024

    data_final.append(
        {"dt_ano": 2023, "origem do dado": "Estimativa", "quantidade": estoque_2023})
    data_final.append(
        {"dt_ano": 2024, "origem do dado": "Estimativa", "quantidade": estoque_2024})

    # === 6) Ordenar do maior ano para o menor ===
    df_final = pd.DataFrame(data_final)
    df_final.sort_values("dt_ano", ascending=False, inplace=True)

    # === 7) Salvar em Excel com formatação ===
    with pd.ExcelWriter(output_excel, engine="xlsxwriter") as writer:
        # Escrever a partir da linha 1 (startrow=1) e sem cabeçalho (header=False)
        df_final.to_excel(writer, sheet_name="Estoque",
                          index=False, startrow=1, header=False)
        ws = writer.sheets["Estoque"]
        workbook = writer.book

        # Ocultar gridlines e congelar a primeira linha
        ws.hide_gridlines(2)
        ws.freeze_panes(1, 0)

        # Formatos
        header_format = workbook.add_format({
            "border": 1,
            "bold": True,
            "bg_color": "#DCE6F1",
            "align": "center",
            "valign": "vcenter"
        })
        cell_center = workbook.add_format({"border": 1, "align": "center"})
        cell_left = workbook.add_format({"border": 1, "align": "left"})
        cell_right = workbook.add_format({
            "border": 1,
            "align": "right",
            "num_format": "#,##0"
        })

        # Cabeçalhos (linha 0)
        columns = ["dt_ano", "origem do dado", "quantidade"]
        for col_num, col_name in enumerate(columns):
            ws.write(0, col_num, col_name, header_format)

        # Ajustar colunas:
        ws.set_column(0, 0, 10, cell_center)  # dt_ano (centralizado)
        # origem do dado (alinhado à esquerda)
        ws.set_column(1, 1, 20, cell_left)
        # quantidade (alinhado à direita)
        ws.set_column(2, 2, 15, cell_right)

    print("✅ Planilha gerada com sucesso!")
    print(f"📂 Arquivo salvo em: {output_excel}")


if __name__ == "__main__":
    estimar_estoque_trabalhadores_formatado()
