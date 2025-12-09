from os import getenv, path, remove
from datetime import datetime as dt
from random import choices
from string import ascii_letters, digits

# Third Party modules
from flask import Flask, render_template, request, Request
from werkzeug.utils import secure_filename
from qdrant_client import QdrantClient

# Own modules
from vectorizer import gen_vector

random_string = ''.join(choices(ascii_letters + digits, k=12))

COLLECTION_NAME = "images"
QDRANT_HOST = getenv('QDRANT_HOST', 'localhost')  # 'qdrant' ist der Service-Name
QDRANT_PORT = getenv('QDRANT_PORT', '6333')
QDRANT_API_KEY = getenv('QDRANT_API_KEY', None)
QDRANT_HTTPS = getenv('QDRANT_HTTPS', bool('')) # Default False

FLASK_DEBUG = getenv('FLASK_DEBUG', bool('')) # Default False
FLASK_SECRET_KEY = getenv('FLASK_SECRET_KEY', random_string)

qdrant_client = QdrantClient(host=QDRANT_HOST, port=int(QDRANT_PORT), api_key=QDRANT_API_KEY, https=bool(QDRANT_HTTPS))

app = Flask(__name__, template_folder='templates', static_folder='statics')
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
app.config['UPLOAD_FOLDER'] = path.join('statics', 'uploads')
app.config['UPLOAD_EXTENSIONS'] = ['jpg', 'jpeg', 'png', 'gif']


def get_image(request: Request):
    """
    Get the uploaded image from the request.
    """
    file = request.files['file']
    if not file.filename:
        raise Exception('Filename in None')
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

    # Check MIME-Type
    if not file.mimetype.startswith('image/'):
        raise Exception('Invalid image MIME type.')

    # Check file size
    MAX_FILE_SIZE_MB = 5
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    
    file.seek(0, 2)  # Move to end of file
    file_length = file.tell()
    file.seek(0)     # Reset file pointer to start
    if file_length > MAX_FILE_SIZE_BYTES:
        raise Exception(f'Image is too large. Maximum size allowed is 5 MB.')
    
    file.save(path.join(app.config['UPLOAD_FOLDER'], filename))

    return filename


def get_limit(request: Request):
    """
    Get the limit from the request. The limit is the number of images that will be returned.
    """
    limit = request.form.get("limit", type=int) or 1

    if limit <= 0:
        limit = 1

    return limit

@app.route('/', methods=['GET'])
def home():
    """
    Render the home page.
    """
    return render_template('search.html')

@app.route('/privacy', methods=['GET'])
def privacy():
    """
    Render privacy Page
    """
    return render_template('privacy.html')

@app.route('/datenschutz', methods=['GET'])
def datenschutz():
    """
    Render Datenschutz Page
    """
    return render_template('datenschutz.html')

@app.route('/technology', methods=['GET'])
def technology():
    """
    Render technology Page
    """
    return render_template('technology.html')

@app.route('/image', methods=['GET', 'POST'])
def upload_search():
    """
    Upload and search for images.
    """

    if request.method == 'POST':

        try:
            limit = get_limit(request)
            filename = get_image(request)
        except Exception as e:
            return render_template('search.html', error_message=e)

        try:
            image_path = path.join(app.config['UPLOAD_FOLDER'], filename)
            vector = gen_vector(image_path)
            remove(image_path)
        except Exception as e:
            return render_template('search.html', error_message='Can not genrate Vector.')
        

        search_result = qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=vector,
            limit=limit
        )

        if not search_result:
            return render_template('search.html', error_message='Sorry, we have not found an image in the database.')


        result_images = []
        for point in search_result.points:
            if point.payload and 'image_url' in point.payload:
                print(f"Image URL: {point.payload['image_url']}")
                result_images.append(point.payload['image_url'])
            else:
                return render_template('search.html', error_message='Sorry, we have not found an image point in the database.')

        return render_template('result.html', len=len(result_images), result_images=result_images)

    else:
        return render_template('search.html')

if __name__ == '__main__':
    app.run(debug=FLASK_DEBUG)
