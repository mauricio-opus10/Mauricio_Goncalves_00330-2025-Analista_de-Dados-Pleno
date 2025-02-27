# s7_gera_relat_consolidado_recomendacoes.py
import pandas as pd
import numpy as np
import pickle
import os
from datetime import datetime


def gerar_relatorio_consolidado():
    """
    Gera um relatório consolidado com os resultados de todas as validações
    """
    print("Gerando relatório consolidado...")

    # Carregar resultados das validações
    with open('resultados_estrutura.pkl', 'rb') as f:
        resultados_estrutura = pickle.load(f)

    with open('resultados_totais.pkl', 'rb') as f:
        resultados_totais = pickle.load(f)

    with open('resultados_microrregiao.pkl', 'rb') as f:
        resultados_microrregiao = pickle.load(f)

    with open('resultados_municipio.pkl', 'rb') as f:
        resultados_municipio = pickle.load(f)

    with open('resultados_consistencia.pkl', 'rb') as f:
        resultados_consistencia = pickle.load(f)

    # Criar DataFrame de inconsistências
    inconsistencias = []

    # 1. Problemas de codificação
    for nome, resultado in resultados_estrutura.items():
        if resultado['problemas_codificacao']:
            for problema in resultado['problemas_codificacao']:
                coluna, contagem = problema.split(':')
                inconsistencias.append({
                    'tipo': 'Codificação',
                    'entidade': f"{nome} - {coluna.strip()}",
                    'descricao': f"{contagem.strip()} valores com possíveis problemas de codificação",
                    'severidade': 'Média',
                    'impacto': 'Causa problemas de correspondência entre bases'
                })

    # 2. Inconsistências por microrregião
    if 'comparacao_ordenada' in resultados_microrregiao:
        for _, row in resultados_microrregiao['comparacao_ordenada'].iterrows():
            if abs(row.get('diferenca', 0)) > 0:
                inconsistencias.append({
                    'tipo': 'Microrregião',
                    'entidade': row['microrregiao'],
                    'descricao': f"Diferença de {row['diferenca']} estabelecimentos ({row['percentual_diferenca']}%) entre Gold ({row['quantidade_gold']}) e TABNET ({row['quantidade_tabnet']})",
                    'severidade': 'Alta' if abs(row['percentual_diferenca']) > 5 else 'Média' if abs(row['percentual_diferenca']) > 1 else 'Baixa',
                    'impacto': 'Afeta a confiabilidade dos dados por microrregião'
                })

    # 3. Inconsistências por município
    if 'comparacao_ordenada' in resultados_municipio:
        for _, row in resultados_municipio['comparacao_ordenada'].iterrows():
            if abs(row.get('diferenca', 0)) > 0:
                inconsistencias.append({
                    'tipo': 'Município',
                    'entidade': row['municipio'],
                    'descricao': f"Diferença de {row['diferenca']} estabelecimentos ({row['percentual_diferenca']}%) entre Gold ({row['quantidade_gold']}) e TABNET ({row['quantidade_tabnet']})",
                    'severidade': 'Alta' if abs(row['percentual_diferenca']) > 5 else 'Média' if abs(row['percentual_diferenca']) > 1 else 'Baixa',
                    'impacto': 'Afeta a confiabilidade dos dados por município'
                })

    # 4. Inconsistências de consistência interna
    if 'comparacao_micro' in resultados_consistencia:
        for _, row in resultados_consistencia['comparacao_micro'].iterrows():
            if abs(row.get('diferenca', 0)) > 0:
                inconsistencias.append({
                    'tipo': 'Consistência Interna',
                    'entidade': row['microrregiao_norm'],
                    'descricao': f"Diferença de {row['diferenca']} estabelecimentos ({row['percentual_diferenca']}%) entre a soma dos municípios ({row['quantidade_calculada']}) e o valor declarado da microrregião ({row['quantidade_declarada']})",
                    'severidade': 'Alta' if abs(row['percentual_diferenca']) > 10 else 'Média' if abs(row['percentual_diferenca']) > 5 else 'Baixa',
                    'impacto': 'Afeta a integridade referencial entre microrregiões e municípios'
                })

    # 5. Municípios sem correspondência
    if 'municipios_sem_match' in resultados_consistencia:
        total_sem_match = len(resultados_consistencia['municipios_sem_match'])
        if total_sem_match > 0:
            inconsistencias.append({
                'tipo': 'Mapeamento',
                'entidade': 'Municípios-Microrregiões',
                'descricao': f"{total_sem_match} municípios sem correspondência na tabela silver",
                'severidade': 'Alta' if total_sem_match > 50 else 'Média' if total_sem_match > 10 else 'Baixa',
                'impacto': 'Impede a validação completa de consistência interna'
            })

    # Criar DataFrame de inconsistências
    df_inconsistencias = pd.DataFrame(inconsistencias)

    # Calcular estatísticas
    total_alta = len(
        df_inconsistencias[df_inconsistencias['severidade'] == 'Alta'])
    total_media = len(
        df_inconsistencias[df_inconsistencias['severidade'] == 'Média'])
    total_baixa = len(
        df_inconsistencias[df_inconsistencias['severidade'] == 'Baixa'])

    # Criar recomendações
    recomendacoes = []

    # 1. Recomendações para problemas de codificação
    if 'gold_micro' in resultados_estrutura and resultados_estrutura['gold_micro']['problemas_codificacao']:
        recomendacoes.append({
            'categoria': 'Codificação',
            'descricao': 'Padronizar a codificação de caracteres em todos os arquivos',
            'acao': 'Converter todos os arquivos para UTF-8 e garantir tratamento correto de caracteres especiais.',
            'prioridade': 'Alta'
        })

    # 2. Recomendações para inconsistências em microrregiões
    micro_inconsistentes = 0
    if 'comparacao_ordenada' in resultados_microrregiao:
        micro_inconsistentes = resultados_microrregiao['total_inconsistencias']

    if micro_inconsistentes > 0:
        recomendacoes.append({
            'categoria': 'Dados de Microrregião',
            'descricao': f'Revisar dados das {micro_inconsistentes} microrregiões com inconsistências',
            'acao': 'Comparar detalhadamente os valores das microrregiões com inconsistências e corrigir conforme a fonte oficial (TABNET).',
            'prioridade': 'Alta'
        })

        # Adicionar recomendação específica para as maiores discrepâncias
        if 'comparacao_ordenada' in resultados_microrregiao and not resultados_microrregiao['comparacao_ordenada'].empty:
            top_discrepancias = resultados_microrregiao['comparacao_ordenada'].head(
                3)
            for _, row in top_discrepancias.iterrows():
                if abs(row.get('diferenca', 0)) > 0:
                    recomendacoes.append({
                        'categoria': 'Correção Específica',
                        'descricao': f'Corrigir dados da microrregião {row["microrregiao"]}',
                        'acao': f'Verificar a fonte da discrepância de {abs(row["diferenca"])} estabelecimentos ({abs(row["percentual_diferenca"])}%) e atualizar com o valor correto.',
                        'prioridade': 'Alta' if abs(row['percentual_diferenca']) > 5 else 'Média'
                    })

    # 3. Recomendações para inconsistências em municípios
    muni_inconsistentes = 0
    if 'comparacao_ordenada' in resultados_municipio:
        muni_inconsistentes = resultados_municipio['total_inconsistencias']

    if muni_inconsistentes > 0:
        recomendacoes.append({
            'categoria': 'Dados de Município',
            'descricao': f'Revisar dados dos {muni_inconsistentes} municípios com inconsistências',
            'acao': 'Comparar detalhadamente os valores dos municípios com inconsistências e corrigir conforme a fonte oficial (TABNET).',
            'prioridade': 'Alta'
        })

        # Adicionar recomendação específica para Blumenau (que apareceu como problemático)
        blumenau_inconsistencia = False
        if 'comparacao_ordenada' in resultados_municipio:
            for _, row in resultados_municipio['comparacao_ordenada'].iterrows():
                if 'blumenau' in normalizar_texto(str(row.get('municipio', ''))):
                    blumenau_inconsistencia = True
                    recomendacoes.append({
                        'categoria': 'Correção Prioritária',
                        'descricao': f'Corrigir dados do município de Blumenau',
                        'acao': f'Verificar a fonte da discrepância de {abs(row["diferenca"])} estabelecimentos ({abs(row["percentual_diferenca"])}%) e atualizar com o valor correto.',
                        'prioridade': 'Alta'
                    })

    # 4. Recomendações para consistência interna
    cons_inconsistencias = 0
    if 'total_inconsistencias' in resultados_consistencia:
        cons_inconsistencias = resultados_consistencia['total_inconsistencias']

    if cons_inconsistencias > 0:
        recomendacoes.append({
            'categoria': 'Consistência Interna',
            'descricao': f'Resolver inconsistências entre valores de microrregião e soma de municípios',
            'acao': 'Verificar a fonte das discrepâncias em que a soma dos municípios não corresponde ao valor declarado da microrregião. Reclassificar municípios ou ajustar valores conforme necessário.',
            'prioridade': 'Alta'
        })

    # 5. Recomendações para mapeamento
    if 'municipios_sem_match' in resultados_consistencia and not resultados_consistencia['municipios_sem_match'].empty:
        recomendacoes.append({
            'categoria': 'Mapeamento',
            'descricao': 'Melhorar o mapeamento entre municípios e microrregiões',
            'acao': 'Atualizar a tabela silver para incluir todos os municípios e suas respectivas microrregiões, garantindo consistência nos nomes.',
            'prioridade': 'Alta'
        })

    # 6. Recomendação geral para o pipeline de dados
    recomendacoes.append({
        'categoria': 'Pipeline de Dados',
        'descricao': 'Implementar validação automática no pipeline ETL',
        'acao': 'Criar scripts de validação que sejam executados automaticamente após cada carregamento de dados, alertando sobre possíveis inconsistências.',
        'prioridade': 'Média'
    })

    # Criar DataFrame de recomendações
    df_recomendacoes = pd.DataFrame(recomendacoes)

    # Gerar relatório HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Relatório de Validação - Estabelecimentos de Saúde em Santa Catarina</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
            h1, h2, h3 {{ color: #00557f; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .alta {{ background-color: #ffcccc; }}
            .media {{ background-color: #ffffcc; }}
            .baixa {{ background-color: #e6ffe6; }}
            .summary {{ background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .section {{ margin-top: 30px; }}
            .image-container {{ text-align: center; margin: 20px 0; }}
            .footer {{ margin-top: 50px; font-size: 0.8em; color: #666; text-align: center; }}
        </style>
    </head>
    <body>
        <h1>Relatório de Validação - Estabelecimentos de Saúde em Santa Catarina</h1>
        <p>Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        
        <div class="summary">
            <h2>Resumo da Validação</h2>
            <p><strong>Total de inconsistências encontradas:</strong> {len(df_inconsistencias)}</p>
            <p><strong>Severidade Alta:</strong> {total_alta}</p>
            <p><strong>Severidade Média:</strong> {total_media}</p>
            <p><strong>Severidade Baixa:</strong> {total_baixa}</p>
            
            <p><strong>Principais descobertas:</strong></p>
            <ul>
                <li>Problemas de codificação de caracteres em nomes de microrregiões e municípios</li>
                <li>Inconsistências nos dados de Blumenau entre as bases Gold e TABNET</li>
                <li>Várias microrregiões apresentam valores declarados maiores que a soma dos municípios</li>
                <li>Alto número de municípios sem mapeamento correto para microrregiões devido a problemas de normalização</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Inconsistências Identificadas</h2>
            <table>
                <tr>
                    <th>Tipo</th>
                    <th>Entidade</th>
                    <th>Descrição</th>
                    <th>Severidade</th>
                    <th>Impacto</th>
                </tr>
    """

    # Adicionar linhas da tabela de inconsistências
    for _, row in df_inconsistencias.iterrows():
        severidade_class = row['severidade'].lower()
        html += f"""
                <tr class="{severidade_class}">
                    <td>{row['tipo']}</td>
                    <td>{row['entidade']}</td>
                    <td>{row['descricao']}</td>
                    <td>{row['severidade']}</td>
                    <td>{row['impacto']}</td>
                </tr>
        """

    html += """
            </table>
        </div>
        
        <div class="section">
            <h2>Recomendações</h2>
            <table>
                <tr>
                    <th>Categoria</th>
                    <th>Descrição</th>
                    <th>Ação Recomendada</th>
                    <th>Prioridade</th>
                </tr>
    """

    # Adicionar linhas da tabela de recomendações
    for _, row in df_recomendacoes.iterrows():
        prioridade_class = row['prioridade'].lower()
        html += f"""
                <tr class="{prioridade_class}">
                    <td>{row['categoria']}</td>
                    <td>{row['descricao']}</td>
                    <td>{row['acao']}</td>
                    <td>{row['prioridade']}</td>
                </tr>
        """

    html += """
            </table>
        </div>
        
        <div class="section">
            <h2>Metodologia</h2>
            <p>O processo de validação foi estruturado nas seguintes etapas:</p>
            <ol>
                <li><strong>Compreensão dos dados:</strong> Análise inicial da estrutura dos conjuntos de dados (bronze, silver e gold)</li>
                <li><strong>Validação estrutural:</strong> Verificação de colunas, tipos de dados, valores nulos e problemas de codificação</li>
                <li><strong>Validação cruzada:</strong> Comparação entre os dados processados (pasta gold) e os dados oficiais do TABNET</li>
                <li><strong>Validação de consistência interna:</strong> Verificação da coerência entre os diferentes arquivos dentro da pasta gold</li>
                <li><strong>Detecção e documentação de inconsistências:</strong> Registro sistemático de discrepâncias encontradas</li>
                <li><strong>Propostas de correção:</strong> Recomendações para resolver os problemas identificados</li>
            </ol>
        </div>
        
        <div class="section">
            <h2>Conclusão</h2>
            <p>A validação dos dados de estabelecimentos de saúde em Santa Catarina identificou algumas inconsistências importantes que precisam ser corrigidas antes da disponibilização na plataforma Cidade Única. Os principais problemas estão relacionados a:</p>
            <ul>
                <li>Padronização dos nomes de microrregiões e municípios</li>
                <li>Discrepâncias em determinadas regiões, especialmente Blumenau e Joinville</li>
                <li>Consistência interna entre os valores de microrregião e a soma dos municípios</li>
            </ul>
            <p>A implementação das recomendações propostas neste relatório permitirá garantir a qualidade e confiabilidade dos dados na plataforma.</p>
        </div>
        
        <div class="footer">
            <p>Relatório gerado automaticamente pelo processo de validação de dados do Observatório FIESC</p>
        </div>
    </body>
    </html>
    """

    # Salvar relatório HTML
    with open('relatorio_validacao.html', 'w', encoding='utf-8') as f:
        f.write(html)

    # Salvar também em formato CSV para possível uso em outras ferramentas
    df_inconsistencias.to_csv('inconsistencias.csv',
                              index=False, encoding='utf-8')
    df_recomendacoes.to_csv('recomendacoes.csv', index=False, encoding='utf-8')

    print(f"\nRelatório de validação gerado em: relatorio_validacao.html")
    print(f"Inconsistências salvas em: inconsistencias.csv")
    print(f"Recomendações salvas em: recomendacoes.csv")

    return {
        'inconsistencias': df_inconsistencias,
        'recomendacoes': df_recomendacoes
    }


def normalizar_texto(texto):
    """Normaliza texto removendo acentos e convertendo para minúsculas"""
    if pd.isna(texto):
        return texto
    try:
        import unidecode
        return unidecode.unidecode(str(texto).lower().strip())
    except:
        return str(texto).lower().strip()


if __name__ == "__main__":
    # Verificar se unidecode está instalado
    try:
        import unidecode
    except ImportError:
        print("Instalando pacote unidecode...")
        import subprocess
        import sys
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "unidecode"])

    # Gerar relatório consolidado
    resultados = gerar_relatorio_consolidado()

    print("\nProcesso de validação concluído com sucesso!")
