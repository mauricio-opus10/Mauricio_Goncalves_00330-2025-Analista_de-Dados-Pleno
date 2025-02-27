import pandas as pd
import os
import numpy as np
from sklearn.linear_model import LinearRegression


def estimar_estoque_preditivo_long():
    """
    Exemplo de script que utiliza dados da RAIS de 2002 até 2022 para
    treinar um modelo de regressão linear e prever 2023 e 2024.

    Passos:
      1) Ler RAIS (2002..2022).
      2) Preparar X e Y para o modelo (X = ano, Y = estoque).
      3) Treinar modelo e prever 2023 e 2024.
      4) Montar DataFrame final:
         - 2002..2022 => Dado Observado
         - 2023..2024 => Estimativa
         Ordenar em ordem decrescente.
      5) Salvar em Excel com formatação (ocultar gridlines, congelar cabeçalho, etc.).
    """

    # === 1) Caminhos e leitura dos arquivos ===
    base_dir = os.path.dirname(__file__)
    rais_path = os.path.join(base_dir, "rais.xlsx")
    output_excel = os.path.join(
        base_dir, "estimativa_estoque_preditivo.xlsx")

    # Ler RAIS (assumindo colunas: dt_ano, nu_quantidade)
    df_rais = pd.read_excel(rais_path)
    # Se houver múltiplas linhas por ano, agrupe:
    df_rais_agg = df_rais.groupby("dt_ano", as_index=False)[
        "nu_quantidade"].sum()

    # Filtrar 2002..2022
    df_rais_agg = df_rais_agg.loc[(df_rais_agg["dt_ano"] >= 2002) & (
        df_rais_agg["dt_ano"] <= 2022)].copy()
    # Ordenar por ano ascendente
    df_rais_agg.sort_values("dt_ano", inplace=True)

    if df_rais_agg.empty:
        raise ValueError("Não há dados para 2002..2022 na base RAIS!")

    # === 2) Preparar X e Y para o modelo (LinearRegression) ===
    X = df_rais_agg["dt_ano"].values.reshape(-1, 1)
    Y = df_rais_agg["nu_quantidade"].values

    model = LinearRegression()
    model.fit(X, Y)

    # === 3) Prever 2023 e 2024 ===
    anos_futuros = np.array([[2023], [2024]])
    # array com 2 valores (para 2023 e 2024)
    previsoes = model.predict(anos_futuros)

    # === 4) Montar DataFrame final ===
    # Adicionar todos os anos observados (2002..2022)
    data_final = []
    for _, row in df_rais_agg.iterrows():
        data_final.append({
            "dt_ano": row["dt_ano"],
            "origem do dado": "Dado Observado",
            "quantidade": row["nu_quantidade"]
        })

    # Adicionar as estimativas de 2023 e 2024
    data_final.append(
        {"dt_ano": 2023, "origem do dado": "Estimativa", "quantidade": previsoes[0]})
    data_final.append(
        {"dt_ano": 2024, "origem do dado": "Estimativa", "quantidade": previsoes[1]})

    df_final = pd.DataFrame(data_final)
    # Ordenar decrescente (2024 no topo, 2002 na base)
    df_final.sort_values("dt_ano", ascending=False, inplace=True)

    # === 5) Salvar em Excel com formatação no estilo anterior ===
    with pd.ExcelWriter(output_excel, engine="xlsxwriter") as writer:
        df_final.to_excel(writer, sheet_name="Estoque",
                          index=False, startrow=1, header=False)
        ws = writer.sheets["Estoque"]
        workbook = writer.book

        # Ocultar gridlines e congelar primeira linha
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
        cell_right = workbook.add_format(
            {"border": 1, "align": "right", "num_format": "#,##0"})

        # Cabeçalhos (linha 0)
        columns = ["dt_ano", "origem do dado", "quantidade"]
        for col_num, col_name in enumerate(columns):
            ws.write(0, col_num, col_name, header_format)

        # Ajustar colunas
        ws.set_column(0, 0, 10, cell_center)  # dt_ano
        ws.set_column(1, 1, 20, cell_left)    # origem do dado
        ws.set_column(2, 2, 15, cell_right)   # quantidade

    print("✅ Planilha gerada com sucesso (Preditivo com dados 2002..2022)!")
    print(f"📂 Arquivo: {output_excel}")


if __name__ == "__main__":
    estimar_estoque_preditivo_long()
