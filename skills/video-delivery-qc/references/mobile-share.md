# Attachment-budget share copies

Use only when a smaller share file is requested or needed to deliver the approved preview. Keep the higher-quality captioned export. Start each attempt from that export, not from an already compressed share. Do not re-cut, rerun ASR, or upscale a proxy into a master.

Obtain the current destination limit or use an explicitly recorded conservative budget after a size rejection. Configure exact bytes with headroom; 19,000,000 bytes was a successful workflow example, **not an official or permanent platform limit**. Do not blindly reuse it for all destinations. Estimate total bytes from duration, copied audio bytes and container reserve. If audio alone makes the budget impossible, report the tradeoff rather than silently lowering audio quality or truncating the film.

For an approved SDR/yuv420p export:

```sh
python3 scripts/mobile_share.py approved.mp4 phone-share.mp4 --max-bytes YOUR_BUDGET_BYTES
```

The helper uses two-pass H.264 at a budget-derived target, preserves dimensions/timing, copies compatible audio, refuses an existing output and checks measured size, streams, audio packet payload/timestamps and full decode. It does not authorize delivery or claim perceptual quality. Record requested and measured video rates separately. Audio copy retains the existing measured rate even if it differs from a prior encode target; never re-encode merely to make a report's numbers match.

Inspect actual frames with the longest and smallest captions, proper nouns, two-line cues and motion; reject unreadable results. If compression is insufficient at acceptable quality, offer another delivery route or explicit resolution/audio tradeoff. Recheck all changed properties after any retry. Record derivative/source hashes and inherit unresolved content/audio findings. Overall positive feedback is not proof that each candidate noise or uncertain proper noun has been reviewed.

Upload one verified derivative and retain its Library identity. An upload success does not prove the chat attachment can be sent: if the attachment rejects its size, record that and create a new smaller derivative from the retained high-quality export. Never repeatedly upload identical bytes to bypass a limit. Do not re-upload an unchanged subtitle ZIP that was already delivered.
