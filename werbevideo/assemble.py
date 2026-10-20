"""Schnitt: Host-Hook + Original-Szenen (per Standbild auf VO-Länge gestreckt) + VO + Untertitel-Plates."""
import json, pathlib, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT, VO = ROOT / "output", ROOT / "output" / "vo"
SRC = pathlib.Path("/root/.claude/uploads/c0b321a2-ba62-5ff4-86a8-f451c6e47869/baf671b1-Markentrix_Website_Check_TikTok_Kontrast_25s.mp4")
HOOK = OUT / "clips" / "MKT_VIDEO_A_WebsiteCheck_H1_hook_5s_v1.mp4"
FONT = ROOT / "werbevideo" / "fonts" / "SpaceGrotesk-Bold.ttf"
NAME = "MKT_VIDEO_A_WebsiteCheck_H1_33s_v1_2026-10-20"
NAVY, CYAN = (11, 16, 32), (14, 143, 196)
TEMPO, LEAD, TAIL, END_HOLD = 1.05, 0.35, 0.35, 1.2
HOOK_LEN = 5.0

def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True, check=True).stdout)

def plate(lines, path):
    """Weißes Band mit feinem Rand, Navy-Text, Schlüsselwort (*wort*) in Cyan."""
    font = ImageFont.truetype(str(FONT), 64)
    W, pad, lh = 1080, 36, 82
    img = Image.new("RGBA", (W, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    widths = [d.textlength(l.replace("*", ""), font=font) for l in lines]
    bw, bh = max(widths) + 2 * pad, lh * len(lines) + 2 * pad - 14
    x0, y0 = (W - bw) / 2, 1560 - bh          # Unterkante oberhalb der unteren 330 px
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], 22, fill=(255, 255, 255, 242), outline=(184, 192, 204, 255), width=2)
    for i, l in enumerate(lines):
        x, y = (W - widths[i]) / 2, y0 + pad - 6 + i * lh
        for j, part in enumerate(l.split("*")):
            d.text((x, y), part, font=font, fill=CYAN if j % 2 else NAVY)
            x += d.textlength(part, font=font)
    img.save(path)

def main():
    work = OUT / "work"; work.mkdir(exist_ok=True)
    plate(["Schöne Website,", "aber kaum *Anfragen*?"], work / "sub1.png")
    plate(["Dann schauen wir nach,", "was sie *bremst*."], work / "sub2.png")

    # VO-Teile straffen, Szenenlängen bestimmen
    scenes, t = [], HOOK_LEN
    for i in range(1, 6):
        wav = work / f"s{i}.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(VO / f"s{i}.trim.wav"), "-af", f"atempo={TEMPO}",
                        "-ar", "44100", "-ac", "1", str(wav)], check=True)
        vo = dur(wav)
        slot = max(5.0, LEAD + vo + (END_HOLD if i == 5 else TAIL))
        scenes.append({"i": i, "wav": wav, "vo": vo, "slot": round(slot, 3), "start": round(t, 3)})
        t += slot
    total = t

    inputs = ["-i", str(HOOK), "-i", str(SRC), "-i", str(VO / "s0_hook_5s.wav")]
    for s in scenes:
        inputs += ["-i", str(s["wav"])]
    inputs += ["-loop", "1", "-i", str(work / "sub1.png"), "-loop", "1", "-i", str(work / "sub2.png")]
    sub1, sub2 = 3 + len(scenes), 4 + len(scenes)

    f = [f"[0:v]trim=0:{HOOK_LEN},setpts=PTS-STARTPTS,fps=30,scale=1080:1920,setsar=1,format=yuv420p[hook]"]
    vparts = ["[hook]"]
    for s in scenes:
        a, pad = 5 * (s["i"] - 1), s["slot"] - 5.0
        if s["i"] < 5:   # Standbild bei 4,5 s einschieben, damit der Übergang zur nächsten Szene unberührt bleibt
            f.append(f"[1:v]trim={a}:{a+4.5},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={pad:.3f}[v{s['i']}a]")
            f.append(f"[1:v]trim={a+4.5}:{a+5},setpts=PTS-STARTPTS[v{s['i']}b]")
            f.append(f"[v{s['i']}a][v{s['i']}b]concat=n=2:v=1:a=0,fps=30,setsar=1,format=yuv420p[v{s['i']}]")
        else:
            f.append(f"[1:v]trim={a}:{a+5},setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={pad:.3f},fps=30,setsar=1,format=yuv420p[v{s['i']}]")
        vparts.append(f"[v{s['i']}]")
    f.append(f"{''.join(vparts)}concat=n={len(vparts)}:v=1:a=0[base]")
    sub_f = [f"[base][{sub1}:v]overlay=0:0:enable='between(t,0.25,2.75)':shortest=1[o1]",
             f"[o1][{sub2}:v]overlay=0:0:enable='between(t,2.75,{HOOK_LEN})':shortest=1[vout]"]
    master_f = ["[base]null[vout]"]

    amix = ["[2:a]atrim=0:5,asetpts=PTS-STARTPTS[a0]"]
    labels = ["[a0]"]
    for k, s in enumerate(scenes):
        ms = int((s["start"] + LEAD) * 1000)
        amix.append(f"[{3+k}:a]adelay={ms}:all=1[a{s['i']}]")
        labels.append(f"[a{s['i']}]")
    amix.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0,apad,atrim=0:{total:.3f},"
                "afade=t=out:st=" + f"{total-0.6:.3f}:d=0.6,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[aout]")
    f += amix

    enc = ["-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.3f}"]
    final = OUT / f"{NAME}.mp4"
    master = OUT / f"{NAME}_MASTER_ohne_Untertitel.mp4"
    for extra, path in ((sub_f, final), (master_f, master)):
        subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(f + extra),
                        "-map", "[vout]", "-map", "[aout]", *enc, str(path)], check=True)
    (work / "timeline.json").write_text(json.dumps({"total": total, "scenes": [{k: str(v) for k, v in s.items()} for s in scenes]}, indent=2))
    print(final, round(total, 2))

if __name__ == "__main__":
    main()
