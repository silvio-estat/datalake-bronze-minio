import boto3
import os
from botocore.client import Config
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractOcrOptions
from docling.datamodel.base_models import InputFormat

# --- CONFIGURAÇÕES ---
# MINIO_URL = f"http://{os.getenv('MINIO_ENDPOINT', 'minio:9000')}"
# ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
# SECRET_KEY = os.getenv('MINIO_SECRET_KEY')

MINIO_URL = 'http://minio:9000'
ACCESS_KEY = 'admin'
SECRET_KEY = 'brasil123'


BRONZE_BUCKET = 'bronze-layer'
SILVER_BUCKET = 'silver-layer'

# --- CONFIGURAÇÃO AVANÇADA DO DOCLING ---
print("⚙️ Configurando Pipeline de OCR (Tesseract - Português)...")

# 1. Configura opções do pipeline para PDF
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True
pipeline_options.do_table_structure = True

# 2. Força o uso do Tesseract (melhor para docs antigos) e define idioma Português
# Nota: 'por' é o código para português no Tesseract
pipeline_options.ocr_options = TesseractOcrOptions(lang=['por'])

# 3. Cria o conversor com essas opções
converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

def get_s3_client():
    return boto3.client('s3',
        endpoint_url=MINIO_URL,
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )

def ensure_silver_bucket(s3):
    try:
        s3.create_bucket(Bucket=SILVER_BUCKET)
    except Exception:
        pass

def process_bronze_to_silver():
    s3 = get_s3_client()
    ensure_silver_bucket(s3)
    
    prefix = 'raw/pdfs/'
    response = s3.list_objects_v2(Bucket=BRONZE_BUCKET, Prefix=prefix)
    
    if 'Contents' not in response:
        print("⚠️ Nenhum arquivo encontrado na Bronze.")
        return

    for item in response['Contents']:
        file_key = item['Key']
        if not file_key.endswith('.pdf'):
            continue

        filename = os.path.basename(file_key)
        print(f"\n📄 Processando: {filename}")

        local_input_path = f"/tmp/{filename}"
        s3.download_file(BRONZE_BUCKET, file_key, local_input_path)

        try:
            print("   🧠 Convertendo (Isso pode demorar um pouco devido ao OCR pesado)...")
            # A conversão agora usa as opções definidas acima
            result = converter.convert(local_input_path)
            
            markdown_content = result.document.export_to_markdown()
            
            markdown_filename = filename.replace('.pdf', '.md')
            silver_key = f"processed/markdown/{markdown_filename}"
            
            print(f"   ⬆️ Salvando {markdown_filename}...")
            s3.put_object(
                Bucket=SILVER_BUCKET,
                Key=silver_key,
                Body=markdown_content.encode('utf-8')
            )
            print("   ✅ Concluído!")

        except Exception as e:
            print(f"   ❌ Falha: {e}")
        
        finally:
            if os.path.exists(local_input_path):
                os.remove(local_input_path)

if __name__ == "__main__":
    process_bronze_to_silver()