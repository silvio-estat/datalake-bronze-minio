import boto3
import os
import glob
from botocore.client import Config

# --- CONFIGURAÇÕES ---
MINIO_URL = 'http://minio:9000'
ACCESS_KEY = 'admin'
SECRET_KEY = 'brasil123'
BUCKET_NAME = 'bronze-layer'
SOURCE_FOLDER = 'Manuais'  # A pasta local onde você jogou os arquivos
DEST_FOLDER = 'raw/pdfs'     # A "pasta" virtual dentro do MinIO

def get_s3_client():
    session = boto3.Session(
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name='us-east-1'
    )
    return session.client('s3', # Usamos client aqui (mais baixo nível que resource)
        endpoint_url=MINIO_URL,
        config=Config(signature_version='s3v4')
    )

def upload_pdfs():
    s3 = get_s3_client()
    
    # 1. Garante que o bucket existe
    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
    except:
        s3.create_bucket(Bucket=BUCKET_NAME)
        print(f"📦 Bucket '{BUCKET_NAME}' criado.")

    # 2. Lista todos os PDFs da pasta local
    # O glob ajuda a pegar tudo que termina com .pdf
    pdf_files = glob.glob(os.path.join(SOURCE_FOLDER, '*.pdf'))
    
    if not pdf_files:
        print(f"⚠️ Nenhum PDF encontrado na pasta '{SOURCE_FOLDER}'.")
        return

    print(f"Encontrados {len(pdf_files)} arquivos. Iniciando upload...")

    # 3. Loop de Upload
    for file_path in pdf_files:
        filename = os.path.basename(file_path)
        s3_key = f"{DEST_FOLDER}/{filename}" # Caminho final no MinIO
        
        try:
            print(f"⬆️ Subindo: {filename}...", end='', flush=True)
            
            # O upload_file lida com arquivos grandes automaticamente
            s3.upload_file(file_path, BUCKET_NAME, s3_key)
            
            print(" ✅")
        except Exception as e:
            print(f" ❌ Erro: {e}")

if __name__ == "__main__":
    # Verifica se a pasta existe antes de começar
    if not os.path.exists(SOURCE_FOLDER):
        os.makedirs(SOURCE_FOLDER)
        print(f"📁 Pasta '{SOURCE_FOLDER}' criada. Coloque seus PDFs lá e rode novamente!")
    else:
        upload_pdfs()