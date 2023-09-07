from flask import Flask, request, render_template, redirect, send_file, url_for
import os
import cv2
from moviepy.editor import VideoFileClip
from PIL import Image

app = Flask(__name__)

UPLOAD_FOLDER = 'upload'
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'avi'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Fungsi untuk menyisipkan pesan pada bit gambar
def embed_message(image_path, message):
    img = Image.open(image_path)
    width, height = img.size
    encoded = message + '%%'
    binary_message = ''.join(format(ord(char), '08b') for char in encoded)
    binary_message += '1111111111111110'  # End of Message (EOM) marker

    if len(binary_message) > width * height:
        raise ValueError("Pesan terlalu panjang untuk disisipkan pada gambar")

    data_index = 0
    encoded_image = img.copy()

    for y in range(height):
        for x in range(width):
            pixel = list(img.getpixel((x, y)))

            for color_channel in range(3):
                if data_index < len(binary_message):
                    pixel[color_channel] = int(format(pixel[color_channel], '08b')[:-1] + binary_message[data_index], 2)
                    data_index += 1

            encoded_image.putpixel((x, y), tuple(pixel))

            if data_index == len(binary_message):
                break

    return encoded_image

# Fungsi untuk mendekripsi pesan dari bit gambar
def decrypt_message(encoded_image_path):
    encoded_image = Image.open(encoded_image_path)
    binary_message = ''

    for y in range(encoded_image.height):
        for x in range(encoded_image.width):
            pixel = encoded_image.getpixel((x, y))

            for color_channel in range(3):
                binary_message += format(pixel[color_channel], '08b')[-1]

    message = ''
    message_list = [binary_message[i:i + 8] for i in range(0, len(binary_message), 8)]

    for binary_char in message_list:
        if binary_char == '1111111111111110':
            break
        else:
            message += chr(int(binary_char, 2))

    return message

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']
    
    if file.filename == '':
        return "No selected file"
    
    if file and allowed_file(file.filename):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        
        output_frames_folder = os.path.join(app.config['OUTPUT_FOLDER'], 'frames')
        os.makedirs(output_frames_folder, exist_ok=True)
        
        output_audio_path = os.path.join(app.config['OUTPUT_FOLDER'], 'audio.wav')
        
        with VideoFileClip(file_path) as video:
            video.audio.write_audiofile(output_audio_path)
            
            frame_count = 0
            for frame in video.iter_frames(fps=30, dtype='uint8'):
                frame_path = os.path.join(output_frames_folder, f'frame_{frame_count:04d}.bmp')
                cv2.imwrite(frame_path, frame)
                frame_count += 1
        
        return "File uploaded and processed successfully"
    
    return "Invalid file format"

@app.route('/lsb')
def lsb():
    return render_template('lsb.html')

@app.route('/embed', methods=['POST'])
def embed():
    if 'image' not in request.files or 'message' not in request.form:
        return redirect(request.url)

    image = request.files['image']
    message = request.form['message']

    if image.filename == '':
        return redirect(request.url)

    try:
        encoded_image = embed_message(image, message)
        encoded_image.save('encoded_image.bmp')
        return send_file('encoded_image.bmp', mimetype='image/bmp')
    except Exception as e:
        return str(e)

@app.route('/decrypt', methods=['POST'])
def decrypt():
    if 'encoded_image' not in request.files:
        return redirect(request.url)

    encoded_image = request.files['encoded_image']

    if encoded_image.filename == '':
        return redirect(request.url)

    try:
        message = decrypt_message(encoded_image)
        return message
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    app.run(debug=True)
