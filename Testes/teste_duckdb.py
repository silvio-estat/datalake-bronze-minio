import duckdb
con = duckdb.connect('datalake_analytics.duckdb')

# Qual o tamanho médio dos manuais?
con.sql("SELECT avg(num_caracteres) FROM documentos_ouro").show()

# Buscar manuais que falam de "Fuzil" (Busca textual simples)
con.sql("""
    SELECT filename, categoria_militar 
    FROM documentos_ouro 
    WHERE conteudo_markdown ILIKE '%fuzil%'
""").show()