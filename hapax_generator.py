"""Generate Hapax instrument definition files."""

from typing import Any


def generate_instrument_def(track: dict[str, Any], midi_channel: int) -> str:
    """Generate Hapax .txt definition for instrument rack.

    Args:
        track: Track info dict with 'name' and 'macros'
        midi_channel: MIDI channel (1-16)

    Returns:
        String content of the Hapax definition file
    """
    track_name = _sanitize_name(track['name'])
    macros = track.get('macros', [])

    lines = [
        "VERSION 1",
        f"TRACKNAME {track_name}",
        "TYPE POLY",
        "OUTPORT USBD",
        f"OUTCHAN {midi_channel}",
        "",
        "[CC]"
    ]

    # Add CC mappings for macros (CC 1-8)
    for i, macro_name in enumerate(macros[:8], start=1):
        sanitized = _sanitize_name(macro_name)
        lines.append(f"{i} {sanitized}")

    lines.append("[/CC]")
    lines.append("")
    lines.append("[ASSIGN]")

    # Add assignments
    for i in range(1, min(len(macros) + 1, 9)):
        lines.append(f"{i} CC:{i}")

    lines.append("[/ASSIGN]")

    return "\n".join(lines)


def generate_drum_def(
    track: dict[str, Any],
    midi_channel: int,
    pads: list[dict[str, Any]],
    part_number: int | None = None
) -> str:
    """Generate Hapax .txt definition for drum rack.

    Args:
        track: Track info dict with 'name'
        midi_channel: MIDI channel (1-16)
        pads: List of pad dicts with 'note' and 'name'
        part_number: Optional part number for multi-part drums

    Returns:
        String content of the Hapax definition file
    """
    track_name = _sanitize_name(track['name'])
    if part_number is not None:
        track_name = f"{track_name}_p{part_number}"

    lines = [
        "VERSION 1",
        f"TRACKNAME {track_name}",
        "TYPE DRUM",
        "OUTPORT USBD",
        f"OUTCHAN {midi_channel}",
        "",
        "[DRUMLANES]"
    ]

    # Add drum lanes for each pad
    for i, pad in enumerate(pads, start=1):
        note = pad['note']
        name = _sanitize_name(pad['name'])
        # Format: lane:fill:len:note name
        lines.append(f"{i}:NULL:NULL:{note} {name}")

    lines.append("[/DRUMLANES]")

    return "\n".join(lines)


def _sanitize_name(name: str) -> str:
    """Sanitize a name for use in Hapax definitions.

    Removes or replaces characters that might cause issues.
    """
    # Replace problematic characters
    sanitized = name.replace('\n', ' ').replace('\r', '')

    # Limit length (Hapax has display limits)
    if len(sanitized) > 32:
        sanitized = sanitized[:32]

    return sanitized.strip()


def split_pads_into_groups(pads: list[dict[str, Any]], group_size: int = 8) -> list[list[dict[str, Any]]]:
    """Split drum pads into groups for separate Hapax definitions.

    Args:
        pads: List of all drum pads
        group_size: Maximum pads per group (default 8)

    Returns:
        List of pad groups
    """
    if not pads:
        return []

    groups = []
    for i in range(0, len(pads), group_size):
        groups.append(pads[i:i + group_size])

    return groups
