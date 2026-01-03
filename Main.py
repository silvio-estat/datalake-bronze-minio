import boto3
from botocore.client import Config
import io
import pandas as pd

# Configuração para falar com o MinIO (que está na mesma rede Docker)
s3 = boto3.resource('s3',
                    endpoint_url='http://minio:9000',
                    aws_access_key_id='admin',
                    aws_secret_access_key='brasil123',
                    config=Config(signature_version='s3v4'),
                    region_name='us-east-1')

BUCKET_NAME = 'bronze-layer'

def setup_bronze():
    # 1. Cria o Bucket (se não existir)
    if s3.Bucket(BUCKET_NAME) not in s3.buckets.all():
        s3.create_bucket(Bucket=BUCKET_NAME)
        print(f"✅ Bucket '{BUCKET_NAME}' criado com sucesso.")
    else:
        print(f"ℹ️ Bucket '{BUCKET_NAME}' já existe.")

    # 2. Simula um dado bruto (CSV)
    df = pd.DataFrame({
        'id': [1, 2, 3],
        'nome': ['Soldado Ryan', 'Capitão Miller', 'Sargento Horvath'],
        'missao': ['Resgate', 'Comando', 'Apoio']
    })
    
    # Converte para CSV em memória
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    
    # 3. Upload para a camada Bronze
    s3.Bucket(BUCKET_NAME).put_object(Key='raw/militares.csv', Body=csv_buffer.getvalue())
    print("✅ Arquivo 'raw/militares.csv' enviado para a Bronze.")

if __name__ == "__main__":
    try:
        setup_bronze()
    except Exception as e:
        print(f"❌ Erro: {e}")