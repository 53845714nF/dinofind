# 🦕 Dinofind 

## Description

This project is a minimal search for finding visually similar images.
It is an experimental project designed to explore the use of vector databases for image similarity search.

The core components of the system include:

- **Qdrant** as the vector database for storing and querying image embeddings.
- **DINOv2** as the image vectorizer to convert images into high-dimensional embeddings.
- **Flask** as the backend web service framework.
- **MinIO** as the object storage system to store the original image files.

## Features

- Upload and vectorize in advance.
- Search for visually similar images.
- Store image metadata and embeddings efficiently.
- Scalable and modular architecture.


## ⚙ Setup

Start with:
```
docker compose up
```

Uploade your Images:
Put your Images in the `images` Folder then run:
```
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
python -m upload.main
```

