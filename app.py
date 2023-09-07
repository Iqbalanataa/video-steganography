from flask import Flask, request, render_template, send_file
import os
import cv2
import numpy as np

app = Flask(__name__)

def msgtobinary(msg):
    if type(msg) == str:
        result= ''.join([ format(ord(i), "08b") for i in msg ])
    
    elif type(msg) == bytes or type(msg) == np.ndarray:
        result= [ format(i, "08b") for i in msg ]
    
    elif type(msg) == int or type(msg) == np.uint8:
        result=format(msg, "08b")

    else:
        raise TypeError("Input type is not supported in this function")
    
    return result

def KSA(key):
    key_length = len(key)
    S=list(range(256)) 
    j=0
    for i in range(256):
        j=(j+S[i]+key[i % key_length]) % 256
        S[i],S[j]=S[j],S[i]
    return S

def PRGA(S,n):
    i=0
    j=0
    key=[]
    while n>0:
        n=n-1
        i=(i+1)%256
        j=(j+S[i])%256
        S[i],S[j]=S[j],S[i]
        K=S[(S[i]+S[j])%256]
        key.append(K)
    return key

def preparing_key_array(s):
    return [ord(c) for c in s]

def encryption(plaintext):
    print("Enter the key : ")
    key=input()
    key=preparing_key_array(key)

    S=KSA(key)

    keystream=np.array(PRGA(S,len(plaintext)))
    plaintext=np.array([ord(i) for i in plaintext])

    cipher=keystream^plaintext
    ctext=''
    for c in cipher:
        ctext=ctext+chr(c)
    return ctext

# Fungsi untuk melakukan embedding pesan pada video
def embed_video_data(video_file, data):
    cap = cv2.VideoCapture(video_file)
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    out = cv2.VideoWriter('stego_video.avi', cv2.VideoWriter_fourcc(*'XVID'), 25.0, (frame_width, frame_height))

    frame_number = 0
    while(cap.isOpened()):
        ret, frame = cap.read()
        if ret == False:
            break
        if frame_number == 0:
            change_frame_with = embed(frame, data)
            frame = change_frame_with
        out.write(frame)
        frame_number += 1

    cap.release()
    out.release()

def encryption(plaintext):
    print("Enter the key : ")
    key=input()
    key=preparing_key_array(key)

    S=KSA(key)

    keystream=np.array(PRGA(S,len(plaintext)))
    plaintext=np.array([ord(i) for i in plaintext])

    cipher=keystream^plaintext
    ctext=''
    for c in cipher:
        ctext=ctext+chr(c)
    return ctext

def decryption(ciphertext):
    print("Enter the key : ")
    key=input()
    key=preparing_key_array(key)

    S=KSA(key)

    keystream=np.array(PRGA(S,len(ciphertext)))
    ciphertext=np.array([ord(i) for i in ciphertext])

    decoded=keystream^ciphertext
    dtext=''
    for c in decoded:
        dtext=dtext+chr(c)
    return dtext

# Fungsi untuk melakukan ekstraksi pesan dari video
def extract_video_data(video_file):
    cap = cv2.VideoCapture(video_file)
    frame_number = 0

    while(cap.isOpened()):
        ret, frame = cap.read()
        if ret == False:
            break
        if frame_number == 0:
            extracted_data = extract(frame)
            return extracted_data
        frame_number += 1

    cap.release()

# Implementasi fungsi embedding (sesuaikan dengan kode embedding video Anda)
def embed(frame):
    data=input("\nEnter the data to be Encoded in Video :") 
    data=encryption(data)
    print("The encrypted data is : ",data)
    if (len(data) == 0): 
        raise ValueError('Data entered to be encoded is empty')

    data +='*^*^*'
    
    binary_data=msgtobinary(data)
    length_data = len(binary_data)
    
    index_data = 0
    
    for i in frame:
        for pixel in i:
            r, g, b = msgtobinary(pixel)
            if index_data < length_data:
                pixel[0] = int(r[:-1] + binary_data[index_data], 2) 
                index_data += 1
            if index_data < length_data:
                pixel[1] = int(g[:-1] + binary_data[index_data], 2) 
                index_data += 1
            if index_data < length_data:
                pixel[2] = int(b[:-1] + binary_data[index_data], 2) 
                index_data += 1
            if index_data >= length_data:
                break
        return frame

# Implementasi fungsi ekstraksi (sesuaikan dengan kode ekstraksi video Anda)
def extract(frame):
    data_binary = ""
    final_decoded_msg = ""
    for i in frame:
        for pixel in i:
            r, g, b = msgtobinary(pixel) 
            data_binary += r[-1]  
            data_binary += g[-1]  
            data_binary += b[-1]  
            total_bytes = [ data_binary[i: i+8] for i in range(0, len(data_binary), 8) ]
            decoded_data = ""
            for byte in total_bytes:
                decoded_data += chr(int(byte, 2))
                if decoded_data[-5:] == "*^*^*": 
                    for i in range(0,len(decoded_data)-5):
                        final_decoded_msg += decoded_data[i]
                    final_decoded_msg = decryption(final_decoded_msg)
                    print("\n\nThe Encoded data which was hidden in the Video was :--\n",final_decoded_msg)
                    return 

@app.route('/', methods=['GET', 'POST'])
def index():
    stego_video_exists = 'stego_video.mp4' in os.listdir()
    if request.method == 'POST':
        if 'embed' in request.form:
            # Mendapatkan file video dari form
            video_file = request.files['video']
            # Mendapatkan pesan yang akan di-embed dari form
            data = request.form['data']
            # Simpan file video yang di-embed pesan
            video_file.save('cover_video.mp4')
            embed_video_data('cover_video.mp4', data)
            return "Video telah di-embed dengan pesan."

        elif 'extract' in request.form:
            # Mendapatkan file video dari form
            video_file = request.files['video']
            # Ekstraksi pesan dari file video
            extracted_data = extract_video_data(video_file)
            return f"Pesan yang diekstraksi dari video: {extracted_data}"

    return render_template('index.html', stego_video_exists=stego_video_exists)

if __name__ == '__main__':
    app.run(debug=True)
