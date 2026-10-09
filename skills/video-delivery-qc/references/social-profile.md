# Social delivery profile

Use this profile for general social video, short-form vertical video, Reels, Shorts, and TikTok when the user has not supplied a stricter destination specification.

## Preferred master

- Container: MP4, with fast-start when the encoder supports it.
- Video: H.264 High Profile, progressive, square pixels, 4:2:0 (`yuv420p`) for SDR.
- Color: BT.709 for SDR. Do not silently convert HDR; verify HDR metadata and destination support separately.
- Audio: AAC-LC, 48 kHz, mono or stereo; stereo preferred when the mix is stereo.
- Frame rate: preserve the native rate. Common delivery rates are 23.976, 24, 25, 29.97, 30, 48, 50, 59.94, and 60 fps. Do not resample only to reach 30 fps.
- Preferred short-form canvas: 1080 × 1920 (9:16). Also accept intentional 1080 × 1080 (1:1), 1080 × 1350 (4:5), and 1920 × 1080 (16:9). Warn below 720 pixels on the short edge; prefer 1080-class output.
- Production loudness target: `-16 LUFS`, tolerance `±2 LU`, maximum true peak `-1 dBTP`. This is a creator-safe workflow target, not a universal platform mandate.

The script treats deviations from preferred encoding or canvas choices as warnings unless the user names them as explicit requirements. Decode failure, missing required audio/video, and explicit delivery mismatches remain blocking.

## Visual and editorial checks

- Use a current official safe-zone overlay for the named platform. UI controls vary by placement and can change; never hard-code one generic overlay as universally correct.
- Keep essential faces, products, subtitles, and calls to action out of UI exclusion zones.
- Check subtitles at phone-viewing size. Flag clipping, excessive line length, low contrast, unreadably short display time, or captions covering the subject.
- Confirm the first meaningful frame is intentional because platforms may use it during preview or thumbnail selection.
- Check that the opening communicates subject or action promptly, but treat creative pacing as advice rather than a technical gate.

## Source basis

As of October 2026, YouTube's official upload guidance recommends MP4, H.264, progressive scan, High Profile, 4:2:0, AAC-LC, 48 kHz, native frame rate, and BT.709 for SDR. Meta's official Reels guidance emphasizes 9:16 video with audio and key messages inside the safe zone. TikTok's official creative guidance recommends high-resolution video of at least 720p and adherence to safe zones. Re-check current official platform guidance when the user names a specific destination, because platform limits and UI overlays change.
