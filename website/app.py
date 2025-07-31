from os import getenv, path, remove
from datetime import datetime as dt

# Third Party modules
from flask import Flask, render_template, request, Request
from werkzeug.utils import secure_filename
from qdrant_client import QdrantClient, models
from qdrant_client.http import models

# Own modules
from vectorizer.main import gen_vector


COLLECTION_NAME = "Images"
QDRANT_HOST = getenv('QDRANT_HOST', 'localhost')  # 'qdrant' ist der Service-Name
QDRANT_PORT = getenv('QDRANT_PORT', 6333)
FLASK_DEBUG = getenv('FLAKS_DEBUG', bool('False'))

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

app = Flask(__name__, template_folder='templates', static_folder='statics')
app.config['UPLOAD_FOLDER'] = path.join('statics', 'uploads')
app.config['UPLOAD_EXTENSIONS'] = ['jpg', 'jpeg', 'png', 'gif']


def get_image(request: Request):
    """
    Get the uploaded image from the request.
    """
    file = request.files['file']
    filename = secure_filename(file.filename)

    # Check if the File is Empty
    if filename == '':
        raise Exception('Please select an image you would like to search.')

    # Check the File Extension
    if '.' in filename:
        file_ext = filename.split('.')[-1]
        if file_ext not in app.config['UPLOAD_EXTENSIONS']:
            raise Exception('Please select an valid image you would like to search.')

    if '.' not in filename:
        raise Exception('Please select an valid image you would like to search.')

    file.save(path.join(app.config['UPLOAD_FOLDER'], filename))

    return filename


def get_limit(request: Request):
    """
    Get the limit from the request. The limit is the number of images that will be returned.
    """
    limit = request.form.get("limit", type=int)
    if limit <= 0:
        limit = 1
    return limit


def get_image_count():
    """
    Get the number of images in the collection (Qdrant).
    """
    collection_info = client.get_collection(COLLECTION_NAME)
    return collection_info.points_count


@app.route("/", methods=['GET'])
def home():
    """
    Render the home page.
    """
    return render_template('home.html', image_count=get_image_count())


@app.route('/image', methods=['GET', 'POST'])
def upload_search():
    """
    Upload and search for images.
    """

    if request.method == 'POST':
        limit = get_limit(request)

        try:
            filename = get_image(request)
        except Exception as e:
            return render_template('image_search.html', error_message=e)


        vector = gen_vector(path.join(app.config['UPLOAD_FOLDER'], filename))
        search_result = client.search(
            collection_name=COLLECTION_NAME,
            query_vector=vector,
            limit=limit
        )
        print(f"Search Result: {search_result}")

        remove(path.join(app.config['UPLOAD_FOLDER'], filename))
        print(f"Cleaned up the uploaded file")
        
        # Check if the result is empty
        if not search_result:
            return render_template('image_search.html', error_message='Sorry, we have not found an image in the database.')


        result_images = []
        for hit in search_result:
            print(f"Image URL: {hit.payload['image_url']}")
            result_images.append(hit.payload['image_url'])

        # Render our find Images
        return render_template('result.html', len=len(result_images), result_images=result_images)
    
    # Render the base template (at a get request )
    return render_template('image_search.html')

if __name__ == '__main__':
    app.run(debug=FLASK_DEBUG)
