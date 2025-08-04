from os import listdir, path
from csv import DictReader
from json import dumps

# Own packages 
from vectorizer import gen_vector

# Third-party packages
from tqdm import tqdm
from minio import Minio
from minio.error import S3Error
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse

IMAGE_DIR = "/media/sebastian/508b3b03-3249-4806-abaa-d49b9a3e5af5/archive/Images"
CSV_FILE = "/media/sebastian/508b3b03-3249-4806-abaa-d49b9a3e5af5/archive/captions.txt"

QDRANT_COLLECTION_NAME = "images"
QDRANT_VECTOR_SIZE = 768

MINIO_URL = "localhost:9000"
MINIO_BUCKET_NAME = "images"

qdrant_client = QdrantClient(host="localhost", port=6333)

try: 
    qdrant_client.create_collection(
        collection_name=QDRANT_COLLECTION_NAME,
        vectors_config=VectorParams(size=QDRANT_VECTOR_SIZE, distance=Distance.COSINE),
    )
except UnexpectedResponse as e:
    if e.status_code == 409 and "already exists" in str(e):
        print(f"Collection {QDRANT_COLLECTION_NAME} existiert bereits.")

minio_client = Minio(
    MINIO_URL,
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False  # Setze auf True, wenn HTTPS verwendet wird
)

def ensure_bucket_exists():
    """Stellt sicher, dass der Bucket existiert und öffentlich ist"""
    try:
        if not minio_client.bucket_exists(MINIO_BUCKET_NAME):
            minio_client.make_bucket(MINIO_BUCKET_NAME)
            print(f"Bucket '{MINIO_BUCKET_NAME}' wurde erstellt.")

            # Öffentliche Read-Only-Policy setzen
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": ["*"]},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{MINIO_BUCKET_NAME}/*"]
                    }
                ]
            }

            policy_json = dumps(policy)
            minio_client.set_bucket_policy(MINIO_BUCKET_NAME, policy_json)
            print(f"Bucket '{MINIO_BUCKET_NAME}' ist nun öffentlich lesbar.")

    except S3Error as err:
        print(f"Fehler beim Erstellen oder Konfigurieren des Buckets: {err}")

def upload_image(image_path, object_name=None):
    """
    Lädt ein Bild in MinIO hoch und gibt die URL zurück
    
    Args:
        image_path (str): Pfad zur Bilddatei
        object_name (str, optional): Name des Objekts in MinIO. Wenn None, wird der Dateiname verwendet
    
    Returns:
        str: Die URL des hochgeladenen Bildes
    """
    try:
        if object_name is None:
            object_name = path.basename(image_path)
        
        ensure_bucket_exists()
        
        minio_client.fput_object(
            MINIO_BUCKET_NAME,
            object_name,
            image_path,
            content_type="image/jpeg"
        )

        url = f"http://{MINIO_URL}/{MINIO_BUCKET_NAME}/{object_name}"
        return url
        
    except S3Error as err:
        print(f"Fehler beim Hochladen des Bildes: {err}")
        return None

captions = {}
with open(CSV_FILE, newline='', encoding='utf-8') as csvfile:
    flicker = DictReader(csvfile, delimiter=',', quotechar='"')
    
    for row in flicker:
        captions[row['image']] = row['caption']

image_files = [file for file in listdir(IMAGE_DIR) if file.endswith(('.jpg', '.jpeg', '.png'))]
BATCH_SIZE = 500
point_id = 0
batch = []

for filename in tqdm(image_files, desc="Bilder werden vektorisiert"):
    try:
        full_path = path.join(IMAGE_DIR, filename)
        image_vector = gen_vector(full_path)
        caption = captions.get(filename)

        if image_vector is None and caption is None:
            continue

        image_url = upload_image(full_path)

        point = PointStruct(
            id=point_id,
            vector=image_vector.tolist(),
            payload={
                "image_url": image_url,
                "caption": caption
            }
        )
        batch.append(point)
        point_id += 1

        # Wenn die Batchgröße erreicht ist, hochladen
        if len(batch) >= BATCH_SIZE:
            qdrant_client.upsert(
                collection_name=QDRANT_COLLECTION_NAME,
                points=batch,
                wait=True
            )
            batch.clear()  # Leere Batch für nächste Runde

    except Exception as e:
        print(f"Fehler bei {filename}: {e}")

if batch:
    qdrant_client.upsert(
        collection_name=QDRANT_COLLECTION_NAME,
        points=batch,
        wait=True
    )

collection_info = qdrant_client.get_collection(collection_name=QDRANT_COLLECTION_NAME)
print(f"Anzahl der Punkte in der Collection: {collection_info.points_count}")
