"""ui/help_text.py - the text shown by Help (F1)."""

HELP_HTML = """
<h3>1 &nbsp;Record screen and edit screen</h3>
<p>SpotClip opens on the <b>record screen</b>. As soon as a recording has been
scanned, or a file is loaded, appended or joined, it switches to the <b>edit
screen</b>. Exporting returns you to the record screen. To scrap the current
clip and record again use <b>File &#8594; New recording (Ctrl+N)</b>.</p>

<h3>2 &nbsp;Recording</h3>
<ul>
<li><b>Source</b> button (or <b>Settings &#8594; Select audio source</b>): pick a
<b>LOOPBACK</b> device to capture what your speakers play.</li>
<li><b>Record</b> starts; the same button then pauses and resumes.
<b>Stop rec</b> finishes and opens the clip for editing. Audio goes straight to disk.</li>
<li><b>Mark</b> (Ctrl+B) drops a bookmark at the current recording time without
stopping. It shows as a yellow dot on the live waveform.</li>
<li>The <b>View</b> button switches the live waveform between the whole recording
so far and the last 8 seconds. It shows the view you would switch <i>to</i>.</li>
<li>Sample rate and <b>Mono</b> are remembered between sessions.</li>
</ul>

<h3>3 &nbsp;Finding a spot</h3>
<ul>
<li><b>Go to</b> box: type <b>4:20</b>, <b>1:04:20</b>, <b>4m20s</b> or <b>260</b>
and press Enter.</li>
<li>The <b>scrollbar</b> pans when zoomed in. <b>&minus; / +</b> (or the <b>-</b> and
<b>+</b> keys) zoom around the playhead. The wheel zooms at the cursor; Shift+wheel
or middle-drag pans.</li>
<li><b>Home / End</b> jump to the ends, <b>PageUp / PageDown</b> pan a screen.</li>
<li>Click the <b>ruler</b> to place the playhead. <b>Ctrl+, / Ctrl+.</b> jump to the
previous / next bookmark.</li>
</ul>

<h3>4 &nbsp;Selecting</h3>
<ul>
<li><b>Drag</b> across the waveform to select; drag a blue edge to adjust it.
Clicking an empty area deselects.</li>
<li><b>Double-click</b> a block to select exactly that block &mdash; a kept piece
or a deleted gap. The pieces list opens with that piece highlighted.</li>
<li><b>Mark in [</b> then click another spot, then <b>Mark out ]</b>. Your first mark
stays until the second is placed. Right-click &#8594; Mark in / out uses the spot
you right-clicked.</li>
<li><b>Esc</b> deselects everything. <b>Ctrl+A</b> selects all.</li>
</ul>

<h3>5 &nbsp;Cutting</h3>
<ul>
<li><b>Delete</b> removes the selection. <b>Ctrl+R</b> restores it (also works on a
selected deleted gap).</li>
<li><b>Ctrl+Z / Ctrl+Y</b> undo / redo. <b>Auto-trim silence (Ctrl+T)</b> deletes
the quiet head and tail. <b>Reset all edits</b> keeps the whole recording.</li>
<li>Green = kept, dark / dashed = deleted. The pieces list (<b>Ctrl+L</b>) lists
every kept piece; click one to jump to it.</li>
</ul>

<h3>6 &nbsp;Fades</h3>
<ul>
<li>Every <b>cut</b> fades: each kept piece fades in and out at its cut edges by
<b>Fade per cut</b> (default 500 ms). The very start and very end of the
recording get no fade.</li>
<li><b>End fade</b> adds a long fade on the end of the clip (default 0 s = off).</li>
<li><b>Ctrl+F</b> (or double-click a piece in the list) sets a custom fade in /
fade out for one piece. Untick <i>Default</i> and enter seconds.</li>
<li>Fades show as yellow wedges on the waveform. They thin out as you zoom out and
the shading disappears when they are very small.</li>
</ul>

<h3>7 &nbsp;Combining recordings</h3>
<p><b>File &#8594; Join audio files</b> (Ctrl+J) joins several files in the order
you choose; each becomes its own piece. <b>Append audio file</b> adds one to the
end of the current clip and keeps your cuts.</p>

<h3>8 &nbsp;Output settings</h3>
<ul>
<li><b>Quiet down loud parts</b>: compressor plus ceiling. It only turns things
<i>down</i>. <b>Threshold</b>: audio above it is compressed (-20 gentle, -28
aggressive). <b>Ceiling</b>: nothing in the file exceeds it; <b>Test</b> plays a tone
at that level.</li>
<li><b>Bitrate</b>: 48 kbps AAC is plenty for speech. <b>Cover</b> is embedded in
.m4a and .mp3.</li>
<li><b>Settings &#8594; All settings</b> shows every setting in one window.
Folders, cover, source and these options are remembered.</li>
</ul>

<h3>9 &nbsp;Export and phone</h3>
<p><b>Export (Ctrl+E)</b> writes to <b>exports/</b>, auto-numbered. <b>Finalize
(Ctrl+Shift+F)</b> writes into <b>finals/</b>. <b>Export as</b> lets you pick a
name and format. After an export the app returns to the record screen.
<b>File &#8594; Move last export to finals</b> moves the most recent export.
<b>Send folder to phone (Ctrl+P)</b> serves a folder over Wi-Fi: scan the QR code,
pick a file. Sending is not saving.</p>
<p>Personal use only.</p>
"""