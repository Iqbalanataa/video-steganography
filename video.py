from flask import Flask, request, render_template
import os
import cv2 
from moviepy.editor import VideoFileClip

app = Flask(__name__)

# Fungsi untuk memecah video menjadi frame BMP dan audio terpisah
def split_video(video_path):
    # Membaca video
    clip = VideoFileClip(video_path)

    # Simpan audio terpisah
    audio_dir = 'audio'
    os.makedirs(audio_dir, exist_ok=True)
    audio_file = os.path.join(audio_dir, 'audio.wav')
    clip.audio.write_audiofile(audio_file)

    # Membuat direktori untuk frame BMP
    frame_dir = 'frames'
    os.makedirs(frame_dir, exist_ok=True)

    frame_count = 0

    for frame in clip.iter_frames(fps=clip.fps, dtype='uint8'):
        # Simpan setiap frame sebagai BMP
        frame_file = os.path.join(frame_dir, f'frame_{frame_count:04d}.bmp')
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Konversi ke format yang benar
        cv2.imwrite(frame_file, frame)
        frame_count += 1

# Fungsi untuk menggabungkan frame BMP dan audio menjadi video utuh
def merge_frames_and_audio(frame_dir, audio_dir, output_path):
    frame_files = sorted(os.listdir(frame_dir))
    frame_files = [os.path.join(frame_dir, file) for file in frame_files]

    # Membaca audio
    audio_file = os.path.join(audio_dir, 'audio.wav')

    # Mendapatkan informasi video dari frame pertama
    first_frame = cv2.imread(frame_files[0])
    height, width, layers = first_frame.shape

    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, 30.0, (width, height))

    for frame_file in frame_files:
        frame = cv2.imread(frame_file)
        out.write(frame)

    out.release()

# Halaman utama untuk mengunggah video
@app.route('/', methods=['GET', 'POST'])
def upload_video():
    if request.method == 'POST':
        video = request.files['video']
        if video:
            video_path = os.path.join('uploads', video.filename)
            video.save(video_path)

            split_video(video_path)
            return "Video berhasil dipecah menjadi frame BMP dan audio terpisah."

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
