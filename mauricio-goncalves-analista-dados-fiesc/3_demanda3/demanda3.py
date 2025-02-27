import pandas as pd
import os

def salvar_excel_formatado(df, filename, sheet_name="Ranking"):
    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, header=False)
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        worksheet.hide_gridlines(2)
        worksheet.freeze_panes(1, 0)

        header_format = workbook.add_format({
            'border': 1,
            'bold': True,
            'bg_color': '#DCE6F1',
            'align': 'center',
            'valign': 'vcenter'
        })

        ranking_format = workbook.add_format({'border': 1, 'align': 'center'})
        text_left_format = workbook.add_format({'border': 1, 'align': 'left'})
        quantidade_format = workbook.add_format({
            'border': 1,
            'align': 'right',
            'num_format': '#,##0'
        })

        for col_num, col_name in enumerate(df.columns):
            worksheet.write(0, col_num, col_name, header_format)

        columns = df.columns.tolist()
        if "Ranking" in columns:
            idx = df.columns.get_loc("Ranking")
            worksheet.set_column(idx, idx, 8, ranking_format)
        if "Marca" in columns:
            idx = df.columns.get_loc("Marca")
            worksheet.set_column(idx, idx, 25, text_left_format)
        if "Modelo" in columns:
            idx = df.columns.get_loc("Modelo")
            worksheet.set_column(idx, idx, 25, text_left_format)
        if "Quantidade" in columns:
            idx = df.columns.get_loc("Quantidade")
            worksheet.set_column(idx, idx, 15, quantidade_format)

    print(f"Arquivo '{filename}' gerado com sucesso!")

def gerar_rankings_demanda3():
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, "demanda3.csv")
    df = pd.read_csv(csv_path, sep=";", encoding="utf-8")
    df.columns = ["UF", "Marca_Modelo", "Quantidade"]
    df = df[df["UF"] == "SANTA CATARINA"].copy()
    df[["Marca", "Modelo"]] = df["Marca_Modelo"].str.split(" ", n=1, expand=True)

    ranking_marca = (
        df.groupby("Marca", as_index=False)
          .agg({"Quantidade": "sum"})
          .sort_values("Quantidade", ascending=False)
          .reset_index(drop=True)
    )
    ranking_marca["Ranking"] = ranking_marca.index + 1
    ranking_marca = ranking_marca[["Ranking", "Marca", "Quantidade"]]

    ranking_marca_modelo = (
        df.groupby(["Marca", "Modelo"], as_index=False)
          .agg({"Quantidade": "sum"})
          .sort_values("Quantidade", ascending=False)
          .reset_index(drop=True)
    )
    ranking_marca_modelo["Ranking"] = ranking_marca_modelo.index + 1
    ranking_marca_modelo = ranking_marca_modelo[["Ranking", "Marca", "Modelo", "Quantidade"]]

    caminho_ranking_marca = os.path.join(base_dir, "ranking_marca.xlsx")
    caminho_ranking_marca_modelo = os.path.join(base_dir, "ranking_marca_modelo.xlsx")

    salvar_excel_formatado(ranking_marca, caminho_ranking_marca, sheet_name="RankingMarca")
    salvar_excel_formatado(ranking_marca_modelo, caminho_ranking_marca_modelo, sheet_name="RankingMarcaModelo")

    # Mensagens de sucesso
    print("✅ Arquivos Excel gerados com sucesso!")
    print(f"📂 {caminho_ranking_marca}")
    print(f"📂 {caminho_ranking_marca_modelo}")

if __name__ == "__main__":
    gerar_rankings_demanda3()
