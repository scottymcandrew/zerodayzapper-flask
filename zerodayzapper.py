import os
from flask import *
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/var/www/html/zerodayzapper/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'exe', ''}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('uploaded_file',
                                    filename=filename))
    return render_template('index.html')


@app.route('/uploads')
def list_uploaded_files():
    list_of_files = {}
    for filename in os.listdir(UPLOAD_FOLDER):
        list_of_files[filename] = "http://web.zerodayzapper.com/uploads/" + filename

    return render_template('uploads.html', list_of_files=list_of_files)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


# @app.route('/')
# def homepage():
#   return render_template('index.html')
#
#
# @app.route('/success', methods = ['POST'])
# def success():
#     if request.method == 'POST':
#         f = request.files['file']
#         f.save(f.filename)
#         return render_template("success.html", name=f.filename)


if __name__ == '__main__':
    app.run()
