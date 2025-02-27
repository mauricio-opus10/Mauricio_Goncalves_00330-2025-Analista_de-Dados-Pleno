import pandas as pd
import os

# Definir o caminho do arquivo CSV
file_path = "1_demanda1/demanda1.csv"

# Verificar se o arquivo existe
if not os.path.exists(file_path):
    print(f"❌ ERRO: O arquivo {file_path} não foi encontrado!")
    exit()

# Carregar o arquivo CSV
df = pd.read_csv(file_path, sep=";", dtype=str)

# Verificar se todas as colunas necessárias estão presentes
colunas_esperadas = {"nm_mun", "cnae", "nu_remuneracao", "setor"}
colunas_faltando = colunas_esperadas - set(df.columns)

if colunas_faltando:
    print(
        f"❌ ERRO: As seguintes colunas estão ausentes no CSV: {colunas_faltando}")
    exit()

# Remover espaços extras
df = df.rename(columns=lambda x: x.strip())
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

# Garantir que a coluna CNAE tenha exatamente 7 dígitos
df["cnae"] = df["cnae"].astype(str).str.zfill(7)

# Converter remuneração para número
df["nu_remuneracao"] = df["nu_remuneracao"].str.replace(",", ".")
df["nu_remuneracao"] = pd.to_numeric(df["nu_remuneracao"], errors="coerce")

# Remover linhas com remuneração inválida
if df["nu_remuneracao"].isnull().sum() > 0:
    print(
        f"⚠️ AVISO: Existem {df['nu_remuneracao'].isnull().sum()} registros com remuneração inválida. Eles serão removidos.")
    df = df.dropna(subset=["nu_remuneracao"])

# Filtrar apenas Joinville
df_joinville = df[df["nm_mun"].str.lower().str.strip() == "joinville"]

# Criar a tabela de remuneração por setor
df_setores = df_joinville.groupby(
    "setor")["nu_remuneracao"].mean().reset_index()
df_setores.columns = ["Setor", "Valor"]

# Lista de CNAEs industriais
cnaes_industriais = [
    "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19",
    "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33", "35",
    "36", "37", "38", "39", "41", "42", "43"
]

# Tabela de comparação Indústria vs. Não Industrial
df_comparacao = pd.DataFrame({
    "Grande Setor": ["Não industrial", "Indústria"],
    "Valor": [
        df_joinville[~df_joinville["cnae"].str[:2].isin(
            cnaes_industriais)]["nu_remuneracao"].mean(),
        df_joinville[df_joinville["cnae"].str[:2].isin(
            cnaes_industriais)]["nu_remuneracao"].mean()
    ]
})

# Definir caminho do arquivo Excel
output_excel = "1_demanda1/analise_remuneracao_joinville.xlsx"

with pd.ExcelWriter(output_excel, engine="xlsxwriter") as writer:
    # Salvar planilhas
    df_setores.to_excel(
        writer, sheet_name="Remuneração por Setor", index=False)
    df_comparacao.to_excel(
        writer, sheet_name="Comparação Indústria", index=False)

    workbook = writer.book

    # === Formatos ===
    header_format = workbook.add_format({
        "bold": True,
        "align": "center",
        "valign": "vcenter",
        "fg_color": "#1F4E78",
        "font_color": "white",
        "border": 1
    })
    cell_format = workbook.add_format({
        "align": "left",
        "valign": "vcenter",
        "border": 1
    })
    currency_format = workbook.add_format({
        "num_format": "R$ #,##0.00",
        "border": 1
    })

    # === Planilha 1: Remuneração por Setor ===
    worksheet1 = writer.sheets["Remuneração por Setor"]
    worksheet1.set_column("A:A", 40, cell_format)
    worksheet1.set_column("B:B", 15, currency_format)
    worksheet1.hide_gridlines(2)
    worksheet1.freeze_panes(1, 0)

    # Cabeçalho
    for col_num, value in enumerate(df_setores.columns.values):
        worksheet1.write(0, col_num, value, header_format)

    # === Planilha 2: Comparação Indústria ===
    worksheet2 = writer.sheets["Comparação Indústria"]
    worksheet2.set_column("A:A", 20, cell_format)
    worksheet2.set_column("B:B", 15, currency_format)
    worksheet2.hide_gridlines(2)
    worksheet2.freeze_panes(1, 0)  # Congelar linha de cabeçalho (opcional)

    for col_num, value in enumerate(df_comparacao.columns.values):
        worksheet2.write(0, col_num, value, header_format)

# Mensagens de sucesso
print("✅ Arquivo Excel gerado com sucesso!")
print(f"📂 {output_excel}")
