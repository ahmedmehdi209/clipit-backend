from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import os
import uuid

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/split", methods=["POST"])
def split_video():
    if "video" not in request.files:
        return jsonify({"error": "No video uploaded"}), 400

    video = request.files["video"]
    duration = int(request.form.get("duration", 60))

    video_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_FOLDER, f"{video_id}.mp4")
    video.save(input_path)

    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", input_path],
        capture_output=True, text=True
    )
    total_duration = float(result.stdout.strip())

    clips = []
    start = 0
    clip_index = 1

    while start < total_duration:
        output_filename = f"{video_id}_clip{clip_index}.mp4"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        subprocess.run([
            "ffmpeg", "-i", input_path,
            "-ss", str(start),
            "-t", str(duration),
            "-c", "copy",
            output_path
        ])

        clips.append(f"/download/{output_filename}")
        start += duration
        clip_index += 1

    return jsonify({"clips": clips})


@app.route("/download/<filename>")
def download_clip(filename):
    if not filename.endswith(".mp4"):
        return "Invalid file", 400
    path = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(path):
        return "File not found", 404
    return send_file(
        path,
        mimetype="video/mp4",
        as_attachment=True,
        download_name=filename
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
