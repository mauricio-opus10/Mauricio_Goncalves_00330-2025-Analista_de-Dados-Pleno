import pandas as pd
import os


def gerar_demanda2():
    base_dir = os.path.dirname(__file__)
    demanda2_path = os.path.join(base_dir, "demanda2.csv")
    ncm_path = os.path.join(base_dir, "NCM.csv")
    output_excel = os.path.join(base_dir, "analise_carne_suina.xlsx")

    print("=== Lendo arquivos CSV ===")
    df_export = pd.read_csv(demanda2_path, sep=";",
                            dtype=str, encoding="latin-1")
    df_ncm = pd.read_csv(ncm_path, sep=";", dtype=str, encoding="latin-1")

    # Converter colunas
    df_export["CO_ANO"] = pd.to_numeric(df_export["CO_ANO"], errors="coerce")
    df_export["VL_FOB"] = pd.to_numeric(df_export["VL_FOB"], errors="coerce")
    df_export["CO_NCM"] = df_export["CO_NCM"].str.zfill(8)
    df_ncm["CO_NCM"] = df_ncm["CO_NCM"].str.zfill(8)

    print("=== Realizando merge e filtrando (2024, SC) ===")
    df_merged = pd.merge(df_export, df_ncm, on="CO_NCM", how="inner")
    df_merged = df_merged[(df_merged["CO_ANO"] == 2024) & (
        df_merged["SG_UF_NCM"] == "SC")].copy()
    print("Linhas após merge e filtro:", len(df_merged))

    # ========== ABA RESUMO ==========
    resumo_map = {
        "0203": "CARNES DE ANIMAIS DA ESPÉCIE SUÍNA, FRESCAS, REFRIGERADAS OU CONGELADAS",
        "0206": "MIUDEZAS COMESTÍVEIS (BOVINA, SUÍNA, ETC.), FRESCAS/REFRIGERADAS/CONGELADAS",
        "0209": "TOUCINHO, GORDURAS DE PORCO E DE AVES, NÃO FUNDIDAS, ETC.",
        "0210": "CARNES E MIUDEZAS, SALGADAS/DEFUMADAS; FARINHAS E PÓS COMESTÍVEIS"
    }
    prefixos_resumo = list(resumo_map.keys())

    resumo_data = []
    soma_resumo = 0
    for pfx in prefixos_resumo:
        mask = df_merged["CO_NCM"].str.startswith(pfx)
        valor = df_merged.loc[mask, "VL_FOB"].sum()
        soma_resumo += valor
        resumo_data.append({
            "Resumo": resumo_map[pfx],
            "carne_suina": "Sim",
            "VL_FOB": valor
        })
    # Linha final "Total"
    resumo_data.append({
        "Resumo": "Total",
        "carne_suina": "-",
        "VL_FOB": soma_resumo
    })

    df_resumo = pd.DataFrame(resumo_data, columns=[
                             "Resumo", "carne_suina", "VL_FOB"])
    print("RESUMO gerado com", len(df_resumo), "linhas.")

    # ========== ABA DETALHADO ==========
    # Filtrar pelos mesmos prefixos
    mask_prefixos = df_merged["CO_NCM"].str[:4].isin(prefixos_resumo)
    df_filtrado = df_merged.loc[mask_prefixos].copy()

    # Agrupar por CO_NCM (8 dígitos), somar VL_FOB e pegar a 1ª descrição
    df_detalhe = df_filtrado.groupby("CO_NCM", as_index=False).agg({
        "VL_FOB": "sum",
        "NO_NCM_POR": "first"  # primeira descrição
    })
    # Somente se VL_FOB > 0
    df_detalhe = df_detalhe[df_detalhe["VL_FOB"] > 0].copy()

    # Ordenar por CO_NCM
    df_detalhe.sort_values("CO_NCM", inplace=True)

    # Adicionar coluna carne_suina = "Sim"
    df_detalhe["carne_suina"] = "Sim"

    # Soma total
    soma_detalhado = df_detalhe["VL_FOB"].sum()
    # Adicionar linha "Total"
    total_row = {
        "CO_NCM": "Total",
        "NO_NCM_POR": "",
        "carne_suina": "-",
        "VL_FOB": soma_detalhado
    }
    df_detalhe = pd.concat(
        [df_detalhe, pd.DataFrame([total_row])], ignore_index=True)
    print("DETALHADO gerado com", len(df_detalhe), "linhas (incluindo Total).")

    # Reorganizar colunas
    df_detalhe = df_detalhe[["CO_NCM", "NO_NCM_POR", "carne_suina", "VL_FOB"]]

    print("=== Gerando Excel ===")
    with pd.ExcelWriter(output_excel, engine="xlsxwriter") as writer:
        # Escreve o RESUMO
        df_resumo.to_excel(writer, sheet_name="RESUMO",
                           index=False, startrow=1, header=False)
        ws_resumo = writer.sheets["RESUMO"]

        # Escreve o DETALHADO
        df_detalhe.to_excel(writer, sheet_name="DETALHADO",
                            index=False, startrow=1, header=False)
        ws_det = writer.sheets["DETALHADO"]

        workbook = writer.book

        # Ocultar gridlines, congelar cabeçalho
        ws_resumo.hide_gridlines(2)
        ws_resumo.freeze_panes(1, 0)
        ws_det.hide_gridlines(2)
        ws_det.freeze_panes(1, 0)

        # Formatos de cabeçalho
        header_format = workbook.add_format({
            "bold": True,
            "align": "center",
            "valign": "vcenter",
            "bg_color": "#DCE6F1",
            "border": 1
        })
        cell_left = workbook.add_format({"border": 1, "align": "left"})
        cell_center = workbook.add_format({"border": 1, "align": "center"})
        cell_currency = workbook.add_format({
            "border": 1,
            "align": "right",
            "num_format": "#,##0.00"
        })

        # Formatos para a linha "Total" em negrito
        bold_left = workbook.add_format(
            {"border": 1, "bold": True, "align": "left"})
        bold_center = workbook.add_format(
            {"border": 1, "bold": True, "align": "center"})
        bold_currency = workbook.add_format({
            "border": 1,
            "bold": True,
            "align": "right",
            "num_format": "#,##0.00"
        })

        # Ajustar cabeçalhos RESUMO
        resumo_cols = ["Resumo", "carne_suina", "VL_FOB"]
        for col_num, col_name in enumerate(resumo_cols):
            ws_resumo.write(0, col_num, col_name, header_format)

        ws_resumo.set_column(0, 0, 70, cell_left)   # Resumo
        ws_resumo.set_column(1, 1, 10, cell_center)  # carne_suina
        ws_resumo.set_column(2, 2, 18, cell_currency)

        # Ajustar cabeçalhos DETALHADO
        det_cols = ["CO_NCM", "NO_NCM_POR", "carne_suina", "VL_FOB"]
        for col_num, col_name in enumerate(det_cols):
            ws_det.write(0, col_num, col_name, header_format)

        ws_det.set_column(0, 0, 12, cell_left)       # CO_NCM
        ws_det.set_column(1, 1, 70, cell_left)       # NO_NCM_POR
        ws_det.set_column(2, 2, 10, cell_center)     # carne_suina
        ws_det.set_column(3, 3, 18, cell_currency)   # VL_FOB

        # ========== Formatar linha "Total" em negrito (RESUMO) ==========
        # A última linha do df_resumo é o total
        resumo_total_idx = len(df_resumo) - 1  # índice do df
        # No Excel, começamos a escrever na linha 1 => offset = +1
        resumo_total_row_xlsx = 1 + resumo_total_idx
        # Aplicar formatação em cada coluna
        ws_resumo.write(resumo_total_row_xlsx, 0,
                        df_resumo.iloc[resumo_total_idx, 0], bold_left)
        ws_resumo.write(resumo_total_row_xlsx, 1,
                        df_resumo.iloc[resumo_total_idx, 1], bold_center)
        ws_resumo.write(resumo_total_row_xlsx, 2,
                        df_resumo.iloc[resumo_total_idx, 2], bold_currency)

        # ========== Formatar linha "Total" em negrito (DETALHADO) ==========
        detalhe_total_idx = len(df_detalhe) - 1
        detalhe_total_row_xlsx = 1 + detalhe_total_idx
        ws_det.write(detalhe_total_row_xlsx, 0,
                     df_detalhe.iloc[detalhe_total_idx, 0], bold_left)
        ws_det.write(detalhe_total_row_xlsx, 1,
                     df_detalhe.iloc[detalhe_total_idx, 1], bold_left)
        ws_det.write(detalhe_total_row_xlsx, 2,
                     df_detalhe.iloc[detalhe_total_idx, 2], bold_center)
        ws_det.write(detalhe_total_row_xlsx, 3,
                     df_detalhe.iloc[detalhe_total_idx, 3], bold_currency)

    print("✅ Arquivo Excel gerado com sucesso!")
    print(f"📂 {output_excel}")


if __name__ == "__main__":
    gerar_demanda2()
