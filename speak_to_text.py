from flask import Flask, request, render_template, jsonify
import speech_recognition as sr
import os
from pydub import AudioSegment

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Check if the file format is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Convert speech to text using SpeechRecognition
def speech_to_text_from_file(audio_file):
    recognizer = sr.Recognizer()

    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Sorry, I could not understand the audio."
        except sr.RequestError as e:
            return f"Could not request results from Google Speech Recognition service; {e}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"})
    
    if file and allowed_file(file.filename):
        # Get the file extension and handle accordingly
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

        # Convert MP3 to WAV if the file is in MP3 format
        if file.filename.lower().endswith('.mp3'):
            sound = AudioSegment.from_mp3(filename)
            filename_wav = filename.rsplit('.', 1)[0] + '.wav'
            sound.export(filename_wav, format="wav")
            os.remove(filename)  # Delete the MP3 file after conversion
            filename = filename_wav  # Use the converted WAV file

        # Process the audio file and convert speech to text
        converted_text = speech_to_text_from_file(filename)
        return jsonify({"text": converted_text})

    return jsonify({"error": "Invalid file format. Please upload an MP3 or WAV file."})

if __name__ == "__main__":
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
