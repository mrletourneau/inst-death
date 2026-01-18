# Reverse Engineering the Hapax Project File Format

A guide for analyzing the binary `.hapax` (or similar) project files used by Squarp's Hapax sequencer.

## Overview

The goal is to understand the binary structure so we can:
1. **Read** Hapax project files (decode patterns, tracks, settings)
2. **Write** valid project files (generate from Ableton or other sources)

Squarp hasn't published a specification, so this requires reverse engineering.

---

## Core Approach: Differential Analysis

Create minimal test cases on the Hapax and compare what changes:

```
project_empty.bin
project_one_note_C3.bin
project_one_note_C4.bin      # just pitch changed
project_two_notes.bin
project_different_track.bin
project_different_channel.bin
```

Use hex diff tools to see exactly what bytes changed:

```bash
# Create hex dumps
xxd project_a.bin > a.hex
xxd project_b.bin > b.hex

# Compare them
diff a.hex b.hex

# Or side-by-side
diff -y a.hex b.hex | head -50
```

For cleaner output:
```bash
hexdump -C project.bin | head -50
```

---

## What to Look For

### Magic Bytes / File Signature

Most formats start with a signature in the first 4-16 bytes:
- Could be ASCII like `HAPX`, `SQRP`, `HPAX`
- Or binary like `89 48 50 58`

```bash
xxd project.bin | head -1
```

### Strings

Find any readable text (track names, instrument names, etc.):

```bash
strings project.bin
```

### Compression or Encryption

Check if the file is compressed:

```bash
file project.bin           # might detect compression
binwalk project.bin        # scans for embedded formats/compression
```

High entropy or suspiciously small files might indicate compression (zlib, lz4, gzip) or encryption.

---

## Common Binary Patterns

| Pattern | What it might be |
|---------|------------------|
| `00 00 00 XX` | 32-bit big-endian length/count |
| `XX 00 00 00` | 32-bit little-endian length/count |
| `XX XX` | 16-bit value (version, count, etc.) |
| Repeating structures | Arrays of tracks/patterns/notes |
| `FF` or `00` padding | Alignment or section boundaries |
| `00 00 00 00` | Null terminator or empty field |

### MIDI-Specific Values

| Value Range | Likely Meaning |
|-------------|----------------|
| 0-127 (0x00-0x7F) | MIDI note, velocity, or CC value |
| 0-15 (0x00-0x0F) | MIDI channel or track index |
| 60 (0x3C) | Middle C (C3/C4 depending on convention) |
| 36 (0x24) | Common kick drum note |
| 0-255 | General byte value, pan, or other param |

---

## Note Data Structure

Each MIDI note event typically needs:

| Field | Size (likely) | Notes |
|-------|---------------|-------|
| Note number | 1 byte | 0-127, C3 = 60 (0x3C) |
| Velocity | 1 byte | 0-127 |
| Position | 2-4 bytes | Ticks, or bars+beats encoded |
| Duration | 2-4 bytes | Length of note |
| Channel | 1 byte (or nibble) | 0-15 |

**Test idea:** Record a single C3 note (MIDI 60 = `0x3C`) and search for that byte in the file.

---

## Tools

### Hex Editors

- **ImHex** (free) - Modern, cross-platform, has pattern language for defining structures
- **010 Editor** (paid, $50) - Industry standard, powerful templates
- **HxD** (free, Windows) - Simple and fast
- **Hex Fiend** (free, macOS) - Native Mac hex editor

### Analysis Tools

- **binwalk** - Detect embedded files, compression, signatures
- **Kaitai Struct** - Define format once, generate parsers for Python/JS/etc.
- **radare2** - Overkill for file formats, but powerful

### Command Line

```bash
# Basic hex dump
xxd file.bin | less

# Hex dump with ASCII
hexdump -C file.bin | less

# Find strings
strings -n 4 file.bin

# File type detection
file file.bin

# Scan for known signatures
binwalk file.bin
```

---

## Documenting the Format

Keep notes mapping byte offsets to meaning:

```
HAPAX PROJECT FILE FORMAT (DRAFT)
==================================

Header (0x00 - 0x??):
  0x00-0x03: Magic bytes "HAPX" (or whatever)
  0x04-0x05: Version (little-endian u16)
  0x06-0x07: Track count (u16)
  0x08-0x0B: Unknown (always 00 00 00 00 in test files)
  0x0C-0x0F: File size or data length?

Track Table (0x10 - 0x??):
  Each track entry is XX bytes:
    +0x00: Track type (0x00 = MIDI, 0x01 = CV?)
    +0x01: Channel number
    +0x02-0x03: Pattern count
    ...

Pattern Data:
  ...
```

---

## Quick Validation Script

Once you have a theory, write a Python script to test it:

```python
import struct

def parse_hapax_project(filepath):
    with open(filepath, "rb") as f:
        # Read header
        magic = f.read(4)
        print(f"Magic: {magic}")

        if magic != b"HAPX":  # adjust based on findings
            print("Warning: unexpected magic bytes")

        version = struct.unpack("<H", f.read(2))[0]
        track_count = struct.unpack("<H", f.read(2))[0]

        print(f"Version: {version}")
        print(f"Track count: {track_count}")

        # Read tracks
        for i in range(track_count):
            # Adjust based on discovered structure
            track_type = struct.unpack("B", f.read(1))[0]
            channel = struct.unpack("B", f.read(1))[0]
            print(f"  Track {i}: type={track_type}, channel={channel}")

if __name__ == "__main__":
    import sys
    parse_hapax_project(sys.argv[1])
```

---

## Test Case Ideas

Create these projects on the Hapax and save them:

1. **Empty project** - baseline
2. **One track, no notes** - track header structure
3. **One track, one note (C3, velocity 100)** - note structure
4. **One track, one note (C4, velocity 100)** - confirm note byte location
5. **One track, one note (C3, velocity 50)** - confirm velocity byte location
6. **One track, two notes** - note array structure
7. **One track, different lengths** - duration encoding
8. **Two tracks** - multi-track structure
9. **Different MIDI channels** - channel byte location
10. **With automation** - CC/automation data structure
11. **Drum track vs poly track** - track type differences
12. **Project with instrument definition loaded** - reference storage

---

## Related: Squarp Pyramid Format

The older Pyramid sequencer uses a hybrid approach:
- `trackXX.mid` - Standard MIDI files for note/CC data
- `core.pyr` - Binary file for project settings only
- `FX_trackXX.pyr` - Binary for effects automation

If Hapax uses a similar approach, the MIDI data might already be in standard format, with only core settings in proprietary binary.

**Check the SD card structure first** - you might get lucky.

---

## Resources

- [Reverse Engineering File Formats (Wikibooks)](https://en.wikibooks.org/wiki/Reverse_Engineering/File_Formats)
- [Apriorit Guide to RE File Formats](https://www.apriorit.com/dev-blog/780-reverse-reverse-engineer-a-proprietary-file-format)
- [FOSDEM Talk: RE of Binary File Formats (PDF)](https://archive.fosdem.org/2021/schedule/event/reverse_engineering/attachments/slides/4518/export/events/attachments/reverse_engineering/slides/4518/Reverse_Engineering_of_binary_File_Formats.pdf)
- [Kaitai Struct](https://kaitai.io/) - Declarative binary format parser
- [ImHex](https://imhex.werwolv.net/) - Hex editor with pattern language

---

## If You Crack It

Consider sharing your findings:
- Post on the [Squarp Community Forum](https://squarp.community/)
- Create a GitHub repo with parser code
- Document the format for others building tools

Good luck!
