# Integrated pipeline

## Responsibilities

| Stage | Owner | Output |
|---|---|---|
| Generative media | Dreamina Canvas CLI | Selected and downloaded image, video, voice, or music assets |
| Coded motion | canvas-video | MP4, ProRes, transparent MOV, or review PNG |
| Editorial assembly | HyperFrames | Timed multi-scene composition and delivery render |
| Delivery validation | video-delivery-qc | Technical report, subtitle/audio checks, and review evidence |

Keep each runtime isolated. Pass files and a small production manifest across boundaries; do not share `node_modules` or private credentials.

## Production manifest

For each generated or rendered asset, preserve the useful public provenance available to the workflow:

- stable business key and local filename
- media kind, duration, dimensions, FPS, and checksum
- source tool and tool version
- prompt/model/source references where applicable
- generation or render timestamp
- user approval status
- intended HyperFrames scene or track

Never persist access tokens, cookies, signed URLs, provider payloads, or credit-confirmation tokens.

## Voice and TTS boundary

For a commercial deliverable, verify that the provider and the exact voice or model permit the intended commercial use. Record the provider, voice or model identifier, version, license source, and review date in the production manifest. Do not assume an F5-TTS checkpoint or any pretrained voice model is commercially cleared. If the license cannot be verified, use it only as an explicitly marked temporary voice and replace it before final delivery.

## Dreamina boundary

Use the installed Dreamina CLI schema and model catalog as the executable authority. Credit approval happens before paid generation. Download only a completed, selected result. Canvas rendering never triggers or retries Dreamina generation.

## HyperFrames boundary

Add Canvas output as a normal local media asset. Prefer a transparent Canvas overlay when the coded treatment should sit above generated footage; prefer an opaque Canvas render for a standalone motion scene. HyperFrames remains the owner of the final timeline.

Do not embed the canvas-video Playwright renderer inside a HyperFrames render. If a scene should ultimately become a native HyperFrames component, port it deliberately against the HyperFrames composition and animation contracts, then compare representative frames before retiring the Canvas source.

## QC boundary

Run QC after the final audio mix and encode. A nominal mux loudness target is not proof of compliance. Treat measured integrated loudness, true peak, subtitle timing, decoding, black/freeze/silence findings, and human semantic review as the delivery result.
