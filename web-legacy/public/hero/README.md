# Hero Video Setup

The landing page includes a CSS-animated cinematic hero scene. To upgrade it with a high-quality background video, drop an MP4 file in this directory.

## Quick Setup

1. **Choose a video clip** from the recommendations below (or use your own 1920x1080, 10–30 seconds, H.264 codec)
2. **Download and save** as `reel.mp4` in this folder (`web/public/hero/reel.mp4`)
3. **Deploy** — the page will auto-fade in the video over the CSS hero scene

The video will:
- Auto-play, mute, and loop
- Fade in over 1 second once loaded
- Fall back silently to CSS hero if the file is missing or 404s
- Render at 60% opacity, dark enough to keep text readable

## Recommended Clips

All videos below are free (Pexels/Pixabay CC0), high-definition, and motorcycle-focused:

### Option 1: Burnout / Staging (BEST for drag racing vibe)
**Motorcyclist doing a motorcycle burnout**
- Source: Pexels (https://www.pexels.com/video/a-motorcycle-doing-burnout-9607153/)
- Duration: ~20 seconds
- Perfect for: Launch energy, smoke, raw power
- Download: Click "Free Download" → Select 1080p or higher

### Option 2: Wheelie / Launch
**Man doing a wheelie on a motorcycle**
- Source: Pexels (https://www.pexels.com/video/a-man-doing-a-wheelie-on-a-motorcycle-4905016/)
- Duration: ~15 seconds
- Perfect for: Mid-track action, traction, height
- Download: Click "Free Download" → Select 1080p or higher

### Option 3: Mid-Track / Speed
**Motorcycle race sport speed fast**
- Source: Pixabay (https://pixabay.com/videos/motorcycle-race-sport-speed-fast-24245/)
- Duration: ~45 seconds (trim to 20–30s)
- Perfect for: Speed, motion blur, night track
- Download: Click "Free Download" → Select 1080p

### Option 4: Night Trap / Speed
**Motorcycle rider traveling at night**
- Source: Pexels (https://www.pexels.com/video/a-motorcycle-rider-traveling-at-night-5267317/)
- Duration: ~20 seconds
- Perfect for: Cinematic night vibe, tail lights
- Download: Click "Free Download" → Select 1080p or higher

---

## How to Combine Multiple Clips (Optional)

If you want to concat multiple short clips into one longer hero video, use FFmpeg:

```bash
# Install FFmpeg if you don't have it:
# macOS:  brew install ffmpeg
# Ubuntu: sudo apt-get install ffmpeg
# Windows: https://ffmpeg.org/download.html

# Create a file list (clips.txt):
file '/path/to/clip1.mp4'
file '/path/to/clip2.mp4'
file '/path/to/clip3.mp4'

# Concat them:
ffmpeg -f concat -safe 0 -i clips.txt -c copy reel.mp4

# Or trim a single clip to 20 seconds:
ffmpeg -i input.mp4 -t 20 -c:v libx264 -crf 23 -c:a aac reel.mp4
```

---

## Size & Performance Notes

- **Target file size:** 5–15 MB (1080p, 20–30 second clip, H.264)
- **Codec:** H.264 (mp4 container) — required for broad browser support
- **Bitrate:** 5000–8000 kbps
- **Frame rate:** 24–30 fps

If your downloaded clip is too large:
```bash
ffmpeg -i input.mp4 -c:v libx264 -preset medium -crf 28 -c:a aac -b:a 128k -s 1920x1080 reel.mp4
```

---

## Testing Locally

1. Save `reel.mp4` in this directory
2. Run `npm run dev` from the web folder
3. Navigate to `http://localhost:3000`
4. Hero video should fade in after ~1 second

If it doesn't appear:
- Check browser console for network errors (F12 → Network tab)
- Verify the file exists: `web/public/hero/reel.mp4`
- Try a different video format or test with a small clip first

---

## Deployment

Once deployed to Vercel:
1. The video file will be served from `motoquant.in/hero/reel.mp4`
2. Hero section will auto-detect and load it
3. If missing, site still renders perfectly with CSS-only hero

No additional configuration needed.

---

## Recommended Final Setup

For best results, **use the burnout clip (Option 1)**. It's:
- Darkest (reads well with orange text overlay)
- Most drag-racing-authentic
- Perfectly 20 seconds (no trimming needed)
- Already 1080p on Pexels

Then deploy to production. Done.
