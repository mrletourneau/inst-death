"""Flask application for Hapax Instrument Definition Generator."""

import io
import zipfile
from flask import Flask, render_template, request, jsonify, send_file

from als_parser import parse_als
from hapax_generator import (
    generate_instrument_def,
    generate_drum_def,
    split_pads_into_groups
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload


# Store parsed data temporarily (in production, use proper session/cache)
parsed_data = {}


@app.route('/')
def index():
    """Serve the web UI."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    """Upload and parse .als file."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.endswith('.als'):
        return jsonify({'error': 'File must be an .als file'}), 400

    try:
        content = file.read()
        result = parse_als(content)

        # Store for later generation
        filename = file.filename
        parsed_data[filename] = result

        # Add filename to response
        result['filename'] = filename

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': f'Failed to parse file: {str(e)}'}), 500


@app.route('/generate', methods=['POST'])
def generate():
    """Generate Hapax definitions for selected tracks."""
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    filename = data.get('filename')
    selections = data.get('selections', [])

    if not filename or filename not in parsed_data:
        return jsonify({'error': 'File not found. Please upload again.'}), 400

    if not selections:
        return jsonify({'error': 'No tracks selected'}), 400

    tracks_by_index = {t['index']: t for t in parsed_data[filename]['tracks']}

    # Create zip file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for selection in selections:
            track_index = selection.get('track_index')
            midi_channel = selection.get('midi_channel', 1)

            if track_index not in tracks_by_index:
                continue

            track = tracks_by_index[track_index]

            if track['type'] == 'instrument_rack':
                # Generate single instrument definition
                content = generate_instrument_def(track, midi_channel)
                safe_name = _make_safe_filename(track['name'])
                zip_file.writestr(f'{safe_name}.txt', content)

            elif track['type'] == 'drum_rack':
                # Handle drum rack with pad groups
                pad_groups = selection.get('pad_groups', [])

                if not pad_groups:
                    # Default: split all pads into groups of 8
                    all_pads = track.get('pads', [])
                    groups = split_pads_into_groups(all_pads)
                    for i, group in enumerate(groups, start=1):
                        content = generate_drum_def(
                            track, midi_channel, group,
                            part_number=i if len(groups) > 1 else None
                        )
                        safe_name = _make_safe_filename(track['name'])
                        part_suffix = f'_part{i}' if len(groups) > 1 else ''
                        zip_file.writestr(f'{safe_name}{part_suffix}.txt', content)
                else:
                    # Use specified pad groups
                    for group_info in pad_groups:
                        group_channel = group_info.get('midi_channel', midi_channel)
                        pad_indices = group_info.get('pad_indices', [])
                        part_number = group_info.get('part_number')

                        # Get pads by indices
                        all_pads = track.get('pads', [])
                        selected_pads = [all_pads[i] for i in pad_indices if i < len(all_pads)]

                        if selected_pads:
                            content = generate_drum_def(
                                track, group_channel, selected_pads,
                                part_number=part_number
                            )
                            safe_name = _make_safe_filename(track['name'])
                            part_suffix = f'_part{part_number}' if part_number else ''
                            zip_file.writestr(f'{safe_name}{part_suffix}.txt', content)

    zip_buffer.seek(0)

    # Create download filename
    base_name = filename.rsplit('.', 1)[0]
    download_name = f'{base_name}_hapax.zip'

    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=download_name
    )


def _make_safe_filename(name: str) -> str:
    """Convert a name to a safe filename."""
    # Replace problematic characters
    safe = name.replace('/', '-').replace('\\', '-')
    safe = safe.replace(':', '-').replace('*', '-')
    safe = safe.replace('?', '-').replace('"', '-')
    safe = safe.replace('<', '-').replace('>', '-')
    safe = safe.replace('|', '-')
    return safe.strip()


if __name__ == '__main__':
    app.run(debug=True, port=5001)
