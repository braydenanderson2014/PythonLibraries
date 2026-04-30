# Audio Dubbing Quality Fixes

## Summary of Issues Fixed

### Issue 1: Original Audio Being Lost
**Problem:** The output videos had no original audio, only the dubbed track
**Root Cause:** FFmpeg command structure was malformed - it used `-c copy` for all streams but then tried to override codecs afterward
**Fix:** Restructured the muxing command to:
- Explicitly map all video streams with copy codec
- Explicitly map all original audio streams with copy codec  
- Add new dubbed audio track with proper AAC encoding
- This ensures all original content is preserved

### Issue 2: Choppy/Super-Speed Audio
**Problems:**
- Dubbed audio was choppy and distorted
- TTS output was playing at wrong speed
- Audio quality degraded significantly

**Root Causes:**
1. **Aggressive audio stretching:** The `atempo` filter was changing tempo too drastically (steps up to 2.0x), causing audible artifacts
2. **Merged text synthesis:** Edge TTS was synthesizing ALL translated text at once without respect for segment timing
3. **Insufficient quality preservation:** No additional filters to handle resampling quality

**Fixes Applied:**

#### Fix 2a: Gentler Audio Tempo Adjustment
- Changed `_build_atempo_filter_chain()` to use smaller steps (1.5x instead of 2.0x)
- Added threshold check: only apply tempo adjustment if difference >10% from target
- Added lowpass filter for high-ratio stretching to minimize artifacts
- Better preserves audio quality during speed adjustments

#### Fix 2b: Per-Segment Edge TTS Synthesis
- Modified `_synthesize_edge_tts_audio()` to synthesize each subtitle segment separately
- Each segment now has proper timing and duration fitting
- Silence gaps are inserted between segments to maintain original timing
- Results in natural pacing that matches subtitle timing
- Similar approach to successful XTTS synthesis

#### Fix 2c: Improved Duration Fitting Logic
```python
# Old: Always applied aggressive tempo changes
tempo = source_seconds / target

# New: Only applies tempo if difference is significant
if abs(tempo_ratio - 1.0) > 0.1:
    # Apply gentle stretching with lowpass filter
```

### Issue 3: English Not Set as Default Audio Stream
**Problem:** Players would play the original language audio by default instead of the English dub
**Fix:** Added disposition flags to FFmpeg command:
- Mark dubbed audio track (when English) as `default`
- Clear default flag from original audio tracks
- Players will now automatically play the dubbed track first

## Technical Details

### FFmpeg Muxing Command Changes

**Before (Broken):**
```bash
ffmpeg -i video.mkv -i dub_audio.wav \
  -map 0 -map 1:a:0 \
  -c copy \
  -c:a:1 aac \
  output.mkv
```
Problem: `-c copy` copies everything, then codec override doesn't work properly

**After (Fixed):**
```bash
ffmpeg -i video.mkv -i dub_audio.wav \
  -map 0:v -map 0:a -map 0:s? -map 1:a:0 \
  -c:v copy -c:a:0 copy -c:a:1 aac \
  -metadata:s:a:1 language=eng \
  -disposition:a:1 default \
  output.mkv
```
Advantages:
- Explicit mapping of each stream type
- Proper codec specification for each stream
- Clear disposition flags for default selection
- All original content preserved

### Audio Synthesis Improvements

**Edge TTS Changes:**
```python
# Synthesize each subtitle segment separately
for segment in translated_segments:
    text = segment["text"]
    duration = segment["end"] - segment["start"]
    
    # Generate audio for just this segment
    synthesize_segment_audio(text)
    
    # Fit to exact duration
    fit_audio_to_duration(audio, duration)
    
    # Add silence gaps for timing
    add_silence_gap()
```

This matches the proven XTTS approach and provides:
- Better timing synchronization
- Reduced audio artifacts
- More natural pacing
- Easier to control individual segment quality

## Configuration Options

### Using Improved Dubbing Tab
When using the Subtitle Tool:

1. **Choose Reproduction Model:**
   - `xtts` - Line-by-line voice cloning (best quality, slower)
   - `edge:en|es|de|etc` - Microsoft Edge TTS (faster, good quality)
   - `auto` - Auto-select based on language

2. **Target Language:** Select your dubbing language
3. **Check "Compare extracted vs AI-generated":** Validates subtitle quality before dubbing
4. **License Confirmation:** For XTTS, accept license if prompted

### Output Files
The tool generates:
- `video_translated_dub.mkv` - Main output with dubbed audio
- `video.en.translated.srt` - Translated subtitle file (for reference)
- English audio is set as default stream in output

## Quality Tips

### For Best Results:

1. **Prefer longer segments:** Short clips (<0.5s) with aggressive speed changes sound choppy
2. **Use XTTS for critical content:** More naturalness despite slower processing
3. **Use Edge TTS for speed:** Good balance of speed and quality for most use cases
4. **Review speaker references:** Source audio quality affects voice cloning, especially for XTTS
5. **Check output in media player:** Verify dubbed track plays by default

### Performance Considerations:

- **XTTS per-segment:** Each segment requires voice extraction and synthesis (~20-30s per segment)
- **Edge TTS per-segment:** Network requests for each segment (~2-5s total)
- **Overall:** Add ~5-15 minutes for typical 1-hour video

### Fallback Options:

If audio quality is still not satisfactory:

1. **Manually adjust segments:** Edit the `.translated.srt` file, re-dub just those segments
2. **Use different voice:** Try alternative Edge TTS voices for your language
3. **Increase segment duration:** Very short subtitles get distorted; consider merging text
4. **Manual audio mixing:** Use Audacity to blend dubbed audio with original at lower volume

## Validation

The tool now validates muxed output:
- Checks all streams are present
- Verifies audio codec is correct
- Validates metadata tags
- Ensures default disposition is set

If validation fails, check:
- Sufficient disk space
- FFmpeg version is current
- No permission issues on output folder
- Input video is not corrupted

## Advanced: Custom FFmpeg Parameters

For future enhancement, can add settings for:
- Audio normalization levels
- Lowpass filter cutoff frequencies  
- Atempo adjustment sensitivity
- Silence gap handling
- Metadata preservation options

Let support know if you need these customization options!
