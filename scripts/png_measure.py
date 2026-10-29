"""Measure a PNG exported by the draw.io CLI: dimensions, chunk types (no embedded diagram XML),
and the white-glyph share inside every AWS4 icon box. A blank (unknown) icon is a plain coloured
square and measures about 0%; a rendered glyph measures roughly 8-13%.
Usage: python png_measure.py <png> <drawio> [export_scale=2]"""
import struct
import sys
import xml.etree.ElementTree as ET
import zlib

png, drawio = sys.argv[1], sys.argv[2]
data = open(png, "rb").read()
pos, chunks, idat = 8, [], b""
while pos < len(data):
    ln, typ = struct.unpack(">I4s", data[pos:pos + 8])
    body = data[pos + 8:pos + 8 + ln]
    chunks.append(typ.decode())
    if typ == b"IHDR":
        W, H, depth, ctype = struct.unpack(">IIBB", body[:10])
    if typ == b"IDAT":
        idat += body
    pos += 12 + ln
print("size", W, "x", H, "depth", depth, "colortype", ctype, "chunks", sorted(set(chunks)))
print("mxfile text inside png:", b"mxfile" in data or b"mxGraphModel" in data)
bpp = {2: 3, 6: 4}[ctype]
raw = zlib.decompress(idat)
stride = W * bpp
rows, prev, i = [], bytearray(stride), 0
for _ in range(H):
    f = raw[i]; line = bytearray(raw[i + 1:i + 1 + stride]); i += 1 + stride
    for x in range(stride):
        a = line[x - bpp] if x >= bpp else 0
        b = prev[x]
        c = prev[x - bpp] if x >= bpp else 0
        if f == 1: line[x] = (line[x] + a) & 255
        elif f == 2: line[x] = (line[x] + b) & 255
        elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
        elif f == 4:
            pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
            line[x] = (line[x] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
    rows.append(bytes(line)); prev = line

# icon boxes from the drawio, mapped to png pixels. draw.io exports the diagram bounds, which in the
# house style is the white background rectangle: the largest top-level vertex.
root = ET.parse(drawio).getroot()
page = root.find("diagram")
cells = {c.get("id"): c for c in page.iter("mxCell")}
def absxy(c):
    g = c.find("mxGeometry"); x, y = float(g.get("x", 0)), float(g.get("y", 0))
    p = cells.get(c.get("parent"))
    if p is not None and p.get("vertex") == "1":
        px, py = absxy(p); x, y = x + px, y + py
    return x, y
tops = [c for c in cells.values() if c.get("vertex") == "1" and c.find("mxGeometry") is not None]
ox = min(absxy(c)[0] for c in tops)
oy = min(absxy(c)[1] for c in tops)
mx = max(absxy(c)[0] + float(c.find("mxGeometry").get("width", 0)) for c in tops)
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
print(f"origin ({ox:.0f},{oy:.0f}) = top-left of all shapes, export scale {scale} (a blank icon measures about 0% white)")
expected = (mx - ox + 1) * scale
if abs(expected - W) > 0.02 * W:
    print(f"UNRELIABLE: png is {W} px wide but the shapes span {expected:.0f} px at scale {scale}. "
          "The png is from another version of the file, or text overflows its box. Re-export, then re-run.")
    sys.exit(2)
for c in cells.values():
    st = c.get("style") or ""
    if "resIcon=" not in st:
        continue
    name = st.split("resIcon=mxgraph.aws4.")[1].split(";")[0]
    x, y = absxy(c)
    x0, y0 = int((x - ox) * scale) + 4, int((y - oy) * scale) + 4
    n = int(60 * scale) - 8
    white = tot = 0
    for yy in range(y0, y0 + n):
        r = rows[yy]
        for xx in range(x0, x0 + n):
            px = r[xx * bpp: xx * bpp + 3]
            tot += 1
            white += px[0] > 230 and px[1] > 230 and px[2] > 230
    print(f"  {name:32s} white glyph share {100 * white / tot:5.1f}%")
