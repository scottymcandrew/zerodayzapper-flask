import os
from flask import *
from werkzeug.utils import secure_filename
import hashlib
import argparse
import asyncio
import sys
import vt
from dotenv import load_dotenv

UPLOAD_FOLDER = os.path.join(os.environ.get("ZDZ_DIR"), "uploads")
# ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'exe', ''}

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# The following isn't used for security, this is just to enable flash messages
app.secret_key = 'supersecretk3y'


# def allowed_file(filename):
#     return '.' in filename and \
#            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('Successfully uploaded file')
            return redirect(url_for('list_uploaded_files'))

    return render_template('index.html')


@app.route('/uploads')
def list_uploaded_files():
    files_list = []
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = UPLOAD_FOLDER + "/" + filename
        file_hash = get_file_hash(file_path)
        # list_of_files[filename] = filename
        file_details = {
            "file_name": filename,
            "file_hash": file_hash
        }
        files_list.append(file_details)

    return render_template('uploads.html', files_list=files_list)


def get_file_hash(file):
    block_size = 65536  # The size of each read from the file

    file_hash = hashlib.sha256()  # Create the hash object, can use something other than `.sha256()` if you wish
    with open(file, 'rb') as f:  # Open the file to read it's bytes
        fb = f.read(block_size)  # Read from the file. Take in the amount declared above
        while len(fb) > 0:  # While there is still data being read from the file
            file_hash.update(fb)  # Update the hash
            fb = f.read(block_size)  # Read the next block from the file

    return file_hash.hexdigest()  # Get the hexadecimal digest of the hash


@app.route('/vt-download')
def vt_download():
    parser = argparse.ArgumentParser()
    #  parser.add_argument('--apikey',
    #      required=False,
    #      default='./apikey',
    #      help='your VirusTotal API key')
    parser.add_argument('--input',
                        default='./malware-hashlist.txt',
                        help='path to a file containing the hashes')
    parser.add_argument('--output',
                        default='./uploads/',
                        help='path to output directory')
    parser.add_argument('--workers',
                        type=int,
                        required=False,
                        default=4,
                        help='number of concurrent workers')
    args = parser.parse_args()
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    if args.input:
        input_file = open(args.input)
    else:
        input_file = sys.stdin
    loop = asyncio.get_event_loop()
    queue = asyncio.Queue(loop=loop)
    loop.create_task(read_hashes(queue, input_file))
    _worker_tasks = []
    for i in range(args.workers):
        _worker_tasks.append(
            loop.create_task(download_files(queue, args)))
    # Wait until all worker tasks has completed.
    loop.run_until_complete(asyncio.gather(*_worker_tasks))
    loop.close()

    return redirect(url_for('list_uploaded_files'))


@app.route('/uploads/exe-files')
def exe_files():
    for filename in os.listdir(UPLOAD_FOLDER):
        os.rename(UPLOAD_FOLDER + '/' + filename, UPLOAD_FOLDER + '/' + filename + ".exe")

    return redirect(url_for('list_uploaded_files'))


@app.route('/uploads/mutate-files')
def mutate_files():
    for filename in os.listdir(UPLOAD_FOLDER):
        # Append to binary file
        f = open(UPLOAD_FOLDER + '/' + filename, "ab")
        b1 = bytearray(b'AdditionalStuff')
        f.write(b1)
        f.close()

    flash('Files mutated!')

    return redirect(url_for('list_uploaded_files'))


@app.route('/uploads/delete-files')
def delete_files():
    for filename in os.listdir(UPLOAD_FOLDER):
        os.remove(UPLOAD_FOLDER + '/' + filename)

    return redirect(url_for('list_uploaded_files'))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


"""
Function used in the VirusTotal downloader feature
"""


async def read_hashes(queue, input_file):
    for file_hash in input_file:
        await queue.put(file_hash.strip('\n'))


"""
Function used in the VirusTotal downloader feature
"""


async def download_files(queue, args):
    async with vt.Client(os.environ.get('VT_API_KEY')) as client:
        while not queue.empty():
            file_hash = await queue.get()
            file_path = os.path.join(args.output, file_hash)
            with open(file_path, 'wb') as f:
                await client.download_file_async(file_hash, f)
            print(file_hash)
            queue.task_done()


if __name__ == '__main__':
    app.run()
