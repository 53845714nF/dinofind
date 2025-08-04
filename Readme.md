# 🦕 Dinofind 

## Description

This project is a minimal search for finding visually similar images.
It is an experimental project designed to explore the use of vector databases for image similarity search.

The core components of the system include:

- [Kaggle](https://www.kaggle.com/datasets/adityajn105/flickr30k) is a Dataset of 30k Images from Flickr
- [DINOv2](https://github.com/facebookresearch/dinov2) as the image vectorizer to convert images into high-dimensional embeddings.
- [Qdrant](https://github.com/qdrant/qdrant) as the vector database for storing and querying image embeddings.
- [MinIO](https://github.com/minio/minio) as the object storage system to store the original image files.
- [Flask](https://github.com/pallets/flask) as the backend web service framework.

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

