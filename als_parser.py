"""Parse Ableton .als files and extract track information."""

import gzip
import xml.etree.ElementTree as ET
from typing import Any


def parse_als(file_content: bytes) -> dict[str, Any]:
    """Parse .als file content and extract track info.

    Args:
        file_content: Raw bytes of the .als file

    Returns:
        Dictionary with parsed track information:
        {
            "tracks": [
                {
                    "index": 1,
                    "name": "1-Instrument Rack",
                    "type": "instrument_rack" | "drum_rack" | "other",
                    "macros": ["Macro 1", ...],  # for instrument racks
                    "pads": [{"note": 60, "name": "Kick"}, ...]  # for drum racks
                }
            ]
        }
    """
    # Decompress gzipped content
    try:
        xml_content = gzip.decompress(file_content)
    except gzip.BadGzipFile:
        # Maybe it's not compressed
        xml_content = file_content

    # Parse XML
    root = ET.fromstring(xml_content)

    tracks = []
    track_index = 1

    # Find all MIDI tracks
    for midi_track in root.findall('.//Tracks/MidiTrack'):
        track_info = _parse_midi_track(midi_track, track_index)
        if track_info:
            tracks.append(track_info)
            track_index += 1

    return {"tracks": tracks}


def _parse_midi_track(midi_track: ET.Element, index: int) -> dict[str, Any] | None:
    """Parse a single MIDI track element."""
    # Get track name
    name_elem = midi_track.find('.//Name/EffectiveName')
    if name_elem is None:
        name_elem = midi_track.find('.//Name/UserName')

    track_name = name_elem.get('Value', f'Track {index}') if name_elem is not None else f'Track {index}'

    # Check for Drum Rack first (DrumGroupDevice) - more specific than InstrumentGroupDevice
    # Drum Racks are often inside an InstrumentGroupDevice, so check first
    drum_rack = midi_track.find('.//DeviceChain//DrumGroupDevice')
    if drum_rack is not None:
        pads = _extract_drum_pads(drum_rack)
        return {
            "index": index,
            "name": track_name,
            "type": "drum_rack",
            "pads": pads
        }

    # Check for Instrument Rack (InstrumentGroupDevice)
    instrument_rack = midi_track.find('.//DeviceChain//InstrumentGroupDevice')
    if instrument_rack is not None:
        macros = _extract_macros(instrument_rack)
        return {
            "index": index,
            "name": track_name,
            "type": "instrument_rack",
            "macros": macros
        }

    # Other track type - skip for now
    return None


def _extract_macros(instrument_rack: ET.Element) -> list[str]:
    """Extract macro names from an Instrument Rack."""
    macros = []

    # Try to find MacroControls with custom names
    macro_controls = instrument_rack.find('.//Macros')
    if macro_controls is not None:
        for i in range(8):
            macro_elem = macro_controls.find(f'.//MacroControls.{i}')
            if macro_elem is not None:
                # Look for custom name
                custom_name = macro_elem.find('.//MacroDisplayNames.{}'.format(i))
                if custom_name is None:
                    custom_name = macro_elem.find('.//CustomName')

                if custom_name is not None:
                    name = custom_name.get('Value', '')
                    if name:
                        macros.append(name)
                        continue

                # Fallback: check for Name element
                name_elem = macro_elem.find('.//Name')
                if name_elem is not None:
                    name = name_elem.get('Value', f'Macro {i + 1}')
                    macros.append(name)
                else:
                    macros.append(f'Macro {i + 1}')
            else:
                macros.append(f'Macro {i + 1}')

    # Alternative path: Look for MacroDisplayNames directly under the device
    if not macros or all(m.startswith('Macro ') for m in macros):
        for i in range(8):
            display_name = instrument_rack.find(f'.//MacroDisplayNames.{i}')
            if display_name is not None:
                name = display_name.get('Value', '')
                if name:
                    if len(macros) > i:
                        macros[i] = name
                    else:
                        macros.append(name)

    # Ensure we have exactly 8 macros
    while len(macros) < 8:
        macros.append(f'Macro {len(macros) + 1}')

    return macros[:8]


def _extract_drum_pads(drum_rack: ET.Element) -> list[dict[str, Any]]:
    """Extract drum pad information from a Drum Rack."""
    pads = []

    # Find all DrumBranch elements
    branches = drum_rack.find('.//Branches')
    if branches is None:
        return pads

    for branch in branches.findall('.//DrumBranch'):
        # Debug: print all child elements to see structure
        print(f"DrumBranch children: {[child.tag for child in branch]}")

        # Get the receiving note (MIDI note number)
        receiving_note = branch.find('.//ReceivingNote')
        if receiving_note is None:
            continue

        note = int(receiving_note.get('Value', 0))

        # Get the pad name
        name_elem = branch.find('.//Name')
        if name_elem is not None:
            # Check for EffectiveName first, then UserName
            effective = name_elem.find('.//EffectiveName')
            if effective is not None:
                pad_name = effective.get('Value', '')
            else:
                user_name = name_elem.find('.//UserName')
                pad_name = user_name.get('Value', '') if user_name is not None else ''
        else:
            pad_name = ''

        # Skip empty pads (no name means likely unused)
        if pad_name:
            pads.append({
                "note": note,
                "name": pad_name
            })

    # Sort by note number (descending - highest internal note = lowest MIDI note)
    # Ableton uses inverted internal IDs: 92 -> C1 (36), 91 -> C#1 (37), etc.
    pads.sort(key=lambda x: x['note'], reverse=True)

    # Debug: print extracted pads to verify order
    for p in pads:
        print(f"  Note {p['note']}: {p['name']}")

    return pads
