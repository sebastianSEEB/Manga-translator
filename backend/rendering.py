import os
from io import BytesIO
from pathlib import Path
from PIL import ImageDraw, ImageFont

# English only. Users can configure any local TrueType font.
def font(size):
    candidates = [os.getenv("RENDER_FONT", ""), "DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf", "C:/Windows/Fonts/arial.ttf"]
    for path in candidates:
        if not path: continue
        try: return ImageFont.truetype(path, size)
        except OSError: pass
    return ImageFont.load_default(size=size)

def wrap(draw, text, typeface, width):
    lines, line = [], ""
    # Character fallback handles long model codes/words without clipping width.
    for word in text.split():
        proposed = (line + " " + word).strip()
        if draw.textlength(proposed, font=typeface) <= width:
            line = proposed
        else:
            if line: lines.append(line)
            line = ""
            for char in word:
                if line and draw.textlength(line + char, font=typeface) > width:
                    lines.append(line); line = ""
                line += char
    if line: lines.append(line)
    return lines

def render(image, regions):
    result = image.copy()
    draw = ImageDraw.Draw(result)
    overflow = []
    for region in regions:
        x,y,w,h = region["bbox"]
        text = region["en"]
        fitted = False
        for size in range(min(28 if region["kind"] != "sfx" else 18, max(8, h//3)), 7, -1):
            face = font(size)
            lines = wrap(draw, text, face, max(1,w-6))
            line_height = size + 3
            if len(lines)*line_height <= h-6 and all(draw.textlength(t,font=face)<=w-6 for t in lines):
                fitted = True; break
        if not fitted:
            overflow.append((len(overflow)+1, text))
            lines = [f"[{len(overflow)}]"]; face=font(10); line_height=13
        draw.rectangle((x,y,x+w,y+h), fill="white")
        top = y + max(0,(h-len(lines)*line_height)/2)
        for line in lines:
            width = draw.textlength(line,font=face)
            draw.text((x+max(0,(w-width)/2),top),line,font=face,fill="black")
            top += line_height
    if overflow:
        # Preserve full English below the page when a narrow text region cannot fit it.
        from PIL import Image
        face=font(18); lines=[]
        for index,text in overflow: lines.extend(wrap(draw,f"[{index}] {text}",face,max(10,image.width-24)))
        canvas=Image.new("RGB",(image.width,image.height+24+len(lines)*24),"white")
        canvas.paste(result,(0,0)); draw=ImageDraw.Draw(canvas)
        for i,line in enumerate(lines): draw.text((12,image.height+12+i*24),line,font=face,fill="black")
        result=canvas
    buffer=BytesIO(); result.save(buffer,format="PNG")
    return buffer.getvalue()
