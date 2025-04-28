@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request."})
    
    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected."})

    if file and allowed_file(file.filename):
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

        try:
            # 🛠 Force re-convert the uploaded file into real WAV (even if already .wav)
            sound = AudioSegment.from_file(filename)
            filename_wav = filename.rsplit('.', 1)[0] + '_converted.wav'
            sound.export(filename_wav, format="wav")
            os.remove(filename)  # remove original uploaded file
            filename = filename_wav  # use the converted clean WAV
        except Exception as e:
            return jsonify({"error": f"Failed to process audio file: {str(e)}"})

        # Process the clean WAV file
        converted_text = speech_to_text_from_file(filename)

        # Return response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"text": converted_text})
        else:
            return render_template('result.html', text=converted_text)

    return jsonify({"error": "Invalid file format. Please upload a valid audio file."})
