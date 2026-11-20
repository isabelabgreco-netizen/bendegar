---
name: gemini-video
description: >-
  Watch a video WITH its audio by sending it to Gemini - scene timeline, on-screen
  text, speech transcript, music and beat, what hooks in the first 2 seconds, and a
  shot-by-shot recipe. Use when the user sends a reel, reference video or their own
  footage and wants it watched, heard, analysed, transcribed or used as a reference.
---

# gemini-video

Claude cannot hear audio, and looking at extracted frames misses motion and sound.
This skill hands the file to Gemini, which watches and listens to the whole video.

```bash
python3 .claude/skills/gemini-video/scripts/watch.py VIDEO.mp4
python3 .claude/skills/gemini-video/scripts/watch.py A.mov B.mp4 --prompt "compare os dois"
python3 .claude/skills/gemini-video/scripts/watch.py VIDEO.mov --model gemini-2.5-pro
```

- Needs `GEMINI_API_KEY` in the environment. The script never prints it.
- Uploads with the Gemini File API, waits until processed, asks, then deletes the
  uploaded copy (`--keep` to keep it for follow-up questions, up to 48h on Google's side).
- Default prompt (Portuguese) returns: scene timeline with timecodes, on-screen text,
  audio and transcript, the first 2 seconds, cut rhythm, what works, and a recipe.
  Pass `--prompt` or `--prompt-file` for anything else.
- Default model order: gemini-3.1-pro-preview, gemini-2.5-pro, gemini-2.5-flash.

Treat Gemini's answer as a second opinion, not ground truth: cross-check timings
against `ffmpeg` scene detection and a frame sheet when they matter, and say where the
two disagree. Uploading sends the video to Google, so only send what the user asked for.
