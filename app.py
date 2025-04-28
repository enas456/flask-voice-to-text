from flask import Flask, request, render_template, jsonify
import speech_recognition as sr
import os
from pydub import AudioSegment

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Access the API key stored as an environment variable
google_api_key = os.getenv('GOOGLE_API_KEY')

# Make sure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Helpers
def allowed_file(filename):
    """Check if the file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def speech_to_text_from_file(audio_file):
    """Convert speech to text from a given audio file"""
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

# Routes
@app.route('/')
def home():
    """Serve the home page"""
    return render_template('index.html', google_api_key=google_api_key)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads and speech recognition"""
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request."})
    
    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected."})
    
    if file and allowed_file(file.filename):
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

        # Convert MP3 to WAV if needed
        if file.filename.lower().endswith('.mp3'):
            sound = AudioSegment.from_mp3(filename)
            filename_wav = filename.rsplit('.', 1)[0] + '.wav'
            sound.export(filename_wav, format="wav")
            os.remove(filename)  # Remove original MP3
            filename = filename_wav  # Use WAV

        # Convert to text
        converted_text = speech_to_text_from_file(filename)

        # Handle depending on request type
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"text": converted_text})
        else:
            return render_template('result.html', text=converted_text)

    return jsonify({"error": "Invalid file format. Please upload an MP3 or WAV file."})

# Main
if __name__ == "__main__":
    app.run(debug=True)
