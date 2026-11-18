# Audio Clipper


Record, edit and export audio clips. Captures system audio (loopback) or any
input device straight to disk, edits non-destructively with unlimited undo,
and exports with fades, loudness control and embedded cover art. A 2 hour
recording costs ~15 MB of RAM because samples live on disk behind a memmap
and everything streams block by block.


Personal use only.


## Requirements


- Python 3.10+
- `PySide6`, `numpy`, `sounddevice`, `soundcard`, `soundfile`
- `qrcode` (optional - for the Send to phone QR code)
- **ffmpeg / ffprobe on PATH** (loading mp3/m4a/mp4 and exporting anything
  other than .wav fails without them)


Install into a virtual environment:


    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt


## Run


    python main.py


## Project layout


```
AudioClip/
├── main.py                  entry point
├── app.py                   MainWindow: state + wiring only
├── config.py                paths and constants (exports/, finals/, session/ live beside main.py)
├── utils.py                 reveal_folder, mbytes, clean_orphan_sessions
├── theme.py                 dark theme, colours, dark title bars for every window
├── processing.py            loudness guard + ffmpeg decode / encode / insert
├── store.py                 disk-backed audio + peak pyramid
├── share.py                 send-a-folder-to-phone HTTP server + dialogs
├── requirements.txt
├── README.md
│
├── editor/                  the edit model (no GUI)
│   ├── __init__.py
│   ├── timeline.py          Keep, Piece, Timeline (cuts, undo, per-piece fades)
│   ├── splice.py            insert_into_keeps: keep-list maths for dropped files
│   ├── streamer.py          ClipStreamer (renders the clip block by block)
│   ├── fades.py             all fade gain math
│   └── timefmt.py           format_time, parse_time
│
├── audio_backends/          capture and playback
│   ├── __init__.py
│   ├── devices.py           device discovery
│   ├── recorder.py          capture thread -> disk, live overview
│   ├── glitches.py          dropout counter
│   └── player.py            StreamPlayer (queue-buffered output)
│
├── waveform/                waveform widget
│   ├── __init__.py
│   ├── metrics.py           shared sizes and constants
│   ├── view.py              WaveformView: state, model, peak cache
│   ├── zoom.py              visible window, time <-> pixel maths
│   ├── selection.py         selection, in/out marks, playhead
│   ├── input.py             mouse, wheel, keyboard, context menu
│   ├── dropping.py          drag and drop of audio files
│   ├── painter.py           ruler, waveform, selection, bookmarks, playhead
│   ├── fade_painter.py      fade wedges
│   └── live_painter.py      live view while recording
│
├── ui/                      widget construction only
│   ├── __init__.py
│   ├── actions.py           QActions and shortcuts
│   ├── menus.py             menu bar (including Open recent)
│   ├── panels.py            top row, waveform + pieces panel, nav row, edit group
│   ├── output_panel.py      fades / loudness / export controls
│   ├── widgets.py           sep, make_button, make_line_edit, action_button,
│   │                        add_widgets, add_action_buttons
│   ├── dialogs.py           Busy, Source, Join, Help, PieceFade, Settings dialogs, confirm()
│   └── help_text.py         HELP_HTML
│
├── controllers/             MainWindow behaviour, one mixin per concern
│   ├── __init__.py
│   ├── source.py            capture source selection
│   ├── recording.py         record / pause / resume / stop / abort
│   ├── fileio.py            load / append / insert / join, drag and drop, session files
│   ├── recent.py            File > Open recent list
│   ├── recovery.py          crash recovery of unsaved clips
│   ├── export.py            output chain, export, finalize
│   ├── folders.py           export / finals folders, send to phone
│   ├── cover.py             cover art
│   ├── editing.py           delete / restore / undo / trim / piece fades
│   ├── transport.py         play / pause / seek / raw / test tone
│   ├── navigation.py        scrollbar, go-to, pieces list, record/edit mode
│   ├── bookmarks.py         bookmarks (also while recording)
│   ├── settings.py          persisted settings + settings window
│   ├── status.py            action enabling, status bar, tick loop
│   └── tasks.py             TaskThread for background work
│
├── assets/                  thumbnail, test audio
├── exports/                 exported clips (configurable in-app)
├── finals/                  finished clips (configurable in-app)
└── session/                 scratch recordings + recovery files (auto-cleaned)
```


## What each script does


### main.py
- Entry point: Qt app, dark theme, ffmpeg check, show the window.


### app.py
- `MainWindow`: owns state, builds the window from the `ui/` mixins, combines
  the `controllers/` mixins, runs the timers, confirms before discarding work,
  remembers its size and position.


### config.py / utils.py
- Paths (`exports/`, `finals/`, `session/`), block sizes, file filters.
- `reveal_folder`, `mbytes`, `clean_orphan_sessions`.


### editor/
- `timeline.py` - `Keep` (with optional per-piece fades), `Piece`, `Timeline`:
  delete / restore / trim / reset, undo / redo, `plan()`, `block_at()`.
- `splice.py` - `insert_into_keeps`: splits and shifts keeps when audio is
  inserted into the middle of a clip.
- `streamer.py` - `ClipStreamer`: renders the edited clip block by block with
  fades, end fade and the loudness guard; source / output frame mapping.
- `fades.py` - fade gain curves.
- `timefmt.py` - `format_time`, `parse_time`.


### processing.py
- `LoudnessGuard` - streaming compressor + ceiling with carried gain state.
- `probe_audio`, `decode_to_raw`, `append_decoded`, `insert_decoded` - ffmpeg
  decode to raw int16, appended or spliced into a session file.
- `prepare_cover`, `export_stream` - cover art and streamed export (.wav /
  .m4a / .mp3).
- ffmpeg runs without a console window on Windows.
- Small utilities: `db_to_lin`, `estimate_mb`, `unique_path`, `missing_tools`.


### store.py
- `AudioStore` - memmap over a raw int16 file, peak pyramid build / query,
  `loud_bounds` for auto-trim, close / delete lifecycle.


### share.py
- `FolderServer` - throwaway HTTP server for a folder behind a random token
  URL, with Range support.
- `qr_pixmap`, `ShareDialog`, `ShareFolderDialog` - QR code and folder picker.


### theme.py
- Colour constants, the Qt stylesheet, `apply_dark_theme()`.
- `TitleBarFilter` darkens the title bar of every window and dialog as it opens.


### audio_backends/
- `devices.py` - `CaptureDevice`, enumeration, default loopback pick, native
  sample rate lookup, loopback help text.
- `recorder.py` - `Recorder` (capture thread -> queue -> writer thread -> disk),
  live ring buffer and whole-recording overview.
- `glitches.py` - dropout counter.
- `player.py` - `StreamPlayer` (queue-buffered output).


### waveform/
- `view.py` - `WaveformView`: state, model, peak cache, paint entry point.
  Behaviour is split into `zoom.py`, `selection.py`, `input.py` and
  `dropping.py` mixins.
- `painter.py` - ruler, waveform, deleted zones, selection and flags,
  bookmarks, playhead. `fade_painter.py` draws fade wedges,
  `live_painter.py` the live recording view.


### ui/
- Widget construction only: actions, menus, panels, output panel, dialogs,
  help text. `widgets.py` holds the small builders (`make_button`,
  `make_line_edit`, `action_button`, `add_widgets`, `add_action_buttons`).


### controllers/
- One mixin per concern, all combined into `MainWindow`: recording, source
  selection, file I/O, recent files, crash recovery, export, folders, cover
  art, editing, transport, navigation (including record / edit screen
  switching), bookmarks, settings, status and tick loop.


## Workflow


1. **Record** (pick a LOOPBACK source) and press **Stop rec**, or
   **File -> Load** a file. The app switches to the edit screen.
2. Edit: drag or double-click to select, `[` `]` to mark in / out, `Del` to
   cut, `Ctrl+Z` to undo, `Ctrl+F` for a custom fade on one piece.
3. Add more audio by dragging files in (see below).
4. **Export (Ctrl+E)** writes to `exports/`; **Finalize (Ctrl+Shift+F)**
   writes to `finals/`. The app returns to the record screen.
5. **Send to phone (Ctrl+P)** serves a folder over Wi-Fi via QR code.
6. **File -> New recording (Ctrl+N)** scraps the current clip and returns to the
   record screen. **Settings -> All settings** shows every option in one window.


## How audio is stored


Nothing is held in RAM as float samples. A 2 hour stereo recording would cost
~2.8 GB that way, and drawing it by scanning every sample would take ~400 ms
per repaint.


- **Raw file.** Every clip lives in `session/` as a raw interleaved int16 file
  with no header. Recording writes straight into it; loading decodes into it
  with ffmpeg. int16 is lossless here because the source is already
  compressed audio.
- **Memmap.** `AudioStore` opens that file with `np.memmap`, read only, as
  `(frames, channels)`. The OS pages in only what is touched and reclaims it
  under memory pressure. `read(start, count)` converts just that slice to
  float32.
- **Peak pyramid.** One streaming pass records min / max per 256 frames, then
  per 2048, 16384 and so on (8x coarser each level) until the top level is
  small. Drawing picks the level that gives about one bucket per pixel, so a
  repaint is O(pixels), not O(samples). Zoomed in past the finest level, the
  visible frames are read directly.
- **Cost.** For 2 hours of 48 kHz stereo: ~1.4 GB on disk, ~12 MB of pyramid
  in RAM, repaints in well under a millisecond.
- **Lifecycle.** The mapping must be closed before the file can be deleted or
  replaced on Windows, which is why `AudioStore.close()` is called before
  every append, insert and cleanup.


## How editing works


- **Editing never touches samples.** A clip is a sorted list of `Keep` ranges
  (start, end, optional fade in / out, in seconds of the source). Delete
  subtracts a range, restore adds one back, trim and reset rewrite the list.
  Deleted audio stays on disk and can always be restored.
- **Tidying.** Kept ranges that touch are merged, and ranges shorter than
  10 ms are dropped.
- **Undo** is a stack of copies of the keep list (up to 400), so it is cheap
  and unlimited in practice. Adding audio to the clip changes the source
  positions, so it resets the history.
- **Rendering.** `plan()` turns the keeps into `Piece`s (output position,
  source position, length, fade frames). `ClipStreamer` walks the pieces block
  by block for both playback and export, applying fades and the loudness
  guard, so preview and export always match.


## Recording


Capture runs in a thread, hands blocks to a bounded queue, and a second
thread writes them to the raw file, so a slow disk never stalls the audio
device. If the queue fills, the take is flagged rather than silently glitched.
Two small structures feed the live view: a 10 second ring buffer for "last
8 s" and a running min / max overview of the whole take. Pausing stops
capture but keeps the file open, so a resumed take continues in the same
file.


## Export


`export_stream` renders the clip through `ClipStreamer` and the loudness
guard one block at a time. WAV is written with soundfile; m4a and mp3 are
piped as raw PCM into ffmpeg's stdin. The clip is never held in memory, so
export cost stays flat however long it is. Cover art is re-encoded to a
640 px JPEG first so embedding costs tens of kilobytes.


The loudness guard is a streaming compressor plus ceiling. Its gain is
computed per 4 ms block but applied as a per-sample ramp, which avoids the
"zipper" noise a per-block step would add. When disabled it does nothing at
all, so bypass is a true A/B reference.


## Drag and drop


- **Record screen:** drop one audio file to open it, or several to join them
  in the order dropped.
- **Edit screen, onto the waveform:** the files are inserted at the drop
  point, shown by an orange line. Drop into a deleted gap to fill it, or into
  a kept piece to split it. Bookmarks after the point move with the audio.
- **Edit screen, anywhere else in the window (or past the end of the
  waveform):** the files are appended to the end.


Appending is a fast write to the end of the session file. Inserting in the
middle rewrites it through a temporary copy, so it needs about twice the
clip's size in free disk space while it runs, and the original is only
replaced once the copy is complete.


## Crash recovery


Each session file in `session/` has a small `.json` beside it holding the
sample rate, channels, keeps, bookmarks and clip name. It is written when a
recording starts, after every edit, and every 30 seconds. A normal exit
deletes the whole `session/` folder. If the app dies instead, the next start
finds the leftovers and offers to recover them.


A recovered recording is whole-file with no cuts. Audio is flushed to disk
about every 2 seconds, so at most that much is lost.