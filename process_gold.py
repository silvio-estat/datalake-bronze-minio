import boto3
import duckdb
import os
import pandas as pd
from datetime import datetime
from botocore.client import Config

# --- CONFIGURAÇÕES ---
# MINIO_URL = f"http://{os.getenv('MINIO_ENDPOINT', 'minio:9000')}"
# ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
# SECRET_KEY = os.getenv('MINIO_SECRET_KEY')

MINIO_URL = 'http://minio:9000'
ACCESS_KEY = 'admin'
SECRET_KEY = 'brasil123'

SILVER_BUCKET = 'silver-layer'
DUCKDB_FILE = 'datalake_analytics.duckdb' # O arquivo do banco ficará na raiz

# Conexão MinIO
def get_s3_client():
    return boto3.client('s3',
        endpoint_url=MINIO_URL,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )

# --- 1. PREPARAÇÃO DO DUCKDB (OLAP) ---
def init_duckdb():
    print(f"🦆 Conectando ao DuckDB: {DUCKDB_FILE}")
    con = duckdb.connect(DUCKDB_FILE)
    
    # Criamos uma tabela Ouro para armazenar o conhecimento dos manuais
    # Adicionei campos úteis para NLP (tokens, data de processamento)
    con.execute("""
        CREATE TABLE IF NOT EXISTS documentos_ouro (
            filename VARCHAR,
            conteudo_markdown TEXT,
            num_caracteres INTEGER,
            categoria_militar VARCHAR,
            data_processamento TIMESTAMP,
            origem_silver VARCHAR
        )
    """)
    return con

# --- 2. ÁREA DE TRANSFORMAÇÃO (SEU PARQUINHO) ---
def transform_data(filename, content):
    """
    AQUI é onde você brilha. Aplique regras de negócio.
    Exemplo: Categorizar baseado no nome do arquivo ou limpar texto.
    """
    
    # Exemplo simples de transformação:
    # Se o nome do arquivo tem "defesa", categoriza como "Doutrina", senão "Geral"
    categoria = "Geral"
    if "defesa" in filename.lower() or "md33" in filename.lower():
        categoria = "Doutrina Militar"
    
    # Limpeza básica (ex: remover excesso de quebras de linha)
    content_clean = content.strip()
    
    return {
        'filename': filename,
        'conteudo_markdown': content_clean,
        'num_caracteres': len(content_clean),
        'categoria_militar': categoria,
        'data_processamento': datetime.now(),
        'origem_silver': f"s3://{SILVER_BUCKET}/processed/markdown/{filename}"
    }

# --- 3. EXECUÇÃO DO ETL ---
def process_silver_to_gold():
    s3 = get_s3_client()
    con = init_duckdb()
    
    # Lista arquivos na Camada Prata
    prefix = 'processed/markdown/'
    try:
        response = s3.list_objects_v2(Bucket=SILVER_BUCKET, Prefix=prefix)
    except Exception as e:
        print(f"❌ Erro ao acessar MinIO: {e}")
        return

    if 'Contents' not in response:
        print("⚠️ Camada Prata vazia.")
        return

    novos_registros = []

    print("🚀 Iniciando carga Silver -> Gold...")
    
    for item in response['Contents']:
        file_key = item['Key']
        if not file_key.endswith('.md'):
            continue
            
        filename = os.path.basename(file_key)
        
        # Verifica se já processamos esse arquivo antes (Idempotência)
        # O DuckDB permite query SQL direto na variável
        check = con.execute("SELECT 1 FROM documentos_ouro WHERE filename = ?", [filename]).fetchone()
        if check:
            print(f"   ⏭️  Pulando {filename} (já existe na Gold).")
            continue

        print(f"   🔄 Transformando: {filename}...")
        
        # 1. EXTRACT
        obj = s3.get_object(Bucket=SILVER_BUCKET, Key=file_key)
        markdown_text = obj['Body'].read().decode('utf-8')
        
        # 2. TRANSFORM
        dados_tratados = transform_data(filename, markdown_text)
        novos_registros.append(dados_tratados)

    # 3. LOAD (Batch Insert é mais rápido)
    if novos_registros:
        print(f"   💾 Salvando {len(novos_registros)} documentos no DuckDB...")
        
        # Convertemos para Pandas para facilitar a inserção no DuckDB
        df = pd.DataFrame(novos_registros)
        
        # Comando mágico do DuckDB para inserir DataFrame direto na tabela
        con.execute("INSERT INTO documentos_ouro SELECT * FROM df")
        
        print("✅ Carga concluída com sucesso!")
    else:
        print("✅ Nenhum documento novo para processar.")

    # --- 4. VALIDAÇÃO FINAL (Query de Teste) ---
    print("\n🔎 --- Espiando a Camada Ouro (Top 3) ---")
    con.table("documentos_ouro").show(max_rows=3)
    
    con.close()

if __name__ == "__main__":
    process_silver_to_gold()