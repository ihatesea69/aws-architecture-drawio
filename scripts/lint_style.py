"""Check a .drawio file against the house style, independently of the generator that wrote it.
Works on hand-edited files too. Prints FAIL (rule broken) and WARN (deviation worth a look) lines.

Usage: python lint_style.py <file.drawio> [--public]
  --public  identifiers (12-digit account IDs, d-xxxxxxxxxx, ssoins-, arn:aws:...:<account>) become FAIL
Exit code 1 when any FAIL is found.
"""
import html
import re
import sys
import xml.etree.ElementTree as ET

ICON = 60
LABEL_MAX_CHARS = 20


def kv(style):
    out = {}
    for part in (style or "").split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
        elif part.strip():
            out[part.strip()] = "1"
    return out


def plain_lines(v):
    v = html.unescape(v or "")
    v = re.sub(r"<br\s*/?>|</div>|</p>", "\n", v)
    v = re.sub(r"<[^>]+>", "", v)
    v = html.unescape(v)
    return [l.strip() for l in v.split("\n") if l.strip()]


def font_size(st, value):
    sizes = [float(x) for x in re.findall(r"font-size:\s*(\d+(?:\.\d+)?)px", html.unescape(value or ""))]
    return max(sizes) if sizes else float(st.get("fontSize", 12))


def classify(c, st):
    if c.get("edge") == "1":
        return "edge"
    shape = st.get("shape", "")
    if shape == "mxgraph.aws4.group":
        return "frame"
    if shape in ("mxgraph.aws4.resourceIcon", "mxgraph.aws4.user") or shape == "image":
        return "icon"
    if shape.startswith("mxgraph.aws4."):
        return "icon"
    if "ellipse" in st:
        return "badge"
    if "text" in st:
        return "text"
    if st.get("container") == "1":
        return "frame"
    if "group" in st:
        return "group"
    return "rect"


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    path, public = argv[1], "--public" in argv
    root = ET.parse(path).getroot()
    fails, warns = [], []
    F = lambda page, m: fails.append(f"[{page}] {m}")
    W = lambda page, m: warns.append(f"[{page}] {m}")

    for p in root.findall("diagram"):
        pname = p.get("name")
        model = p.find("mxGraphModel")
        cells = {c.get("id"): c for c in p.iter("mxCell")}

        def geo(c):
            g = c.find("mxGeometry")
            if g is None:
                return 0, 0, 0, 0
            return tuple(float(g.get(k, 0)) for k in ("x", "y", "width", "height"))

        def absbox(c):
            x, y, w, h = geo(c)
            par = cells.get(c.get("parent"))
            while par is not None and par.get("vertex") == "1":
                px, py, _, _ = geo(par)
                x, y = x + px, y + py
                par = cells.get(par.get("parent"))
            return x, y, w, h

        roles = {}
        for cid, c in cells.items():
            if cid in ("0", "1"):
                continue
            roles[cid] = (classify(c, kv(c.get("style"))), kv(c.get("style")))

        # ---- background, title, legend ----
        pw, ph = float(model.get("pageWidth", 0)), float(model.get("pageHeight", 0))
        bgs = [cid for cid, (r, st) in roles.items() if r == "rect" and not plain_lines(cells[cid].get("value"))
               and abs(geo(cells[cid])[2] - geo(cells[cid])[3]) < 1 and geo(cells[cid])[2] > 0.8 * min(pw, ph)]
        if not bgs:
            W(pname, "no square background rectangle behind the diagram (exports will not be square/white)")
        texts = [(cid, st) for cid, (r, st) in roles.items() if r == "text"]
        titles = [cid for cid, st in texts if font_size(st, cells[cid].get("value")) >= 32]
        if not titles:
            W(pname, "no big title (>= 32 px bold); house style puts a 44 px two-line title bottom right")
        legend_nums, legend_ids = [], []
        for cid, st in texts:
            lines = plain_lines(cells[cid].get("value"))
            nums = [int(m.group(1)) for l in lines for m in [re.match(r"(\d+)[\s\u00a0]", l)] if m]
            if len(nums) >= 2:
                legend_ids.append(cid)
                legend_nums += nums
                if float(st.get("fontSize", 12)) != 10:
                    W(pname, f"legend font is {st.get('fontSize')} px, house style is 10 px")
                if st.get("fillColor", "none") not in ("none", "") or st.get("strokeColor", "none") not in ("none", ""):
                    W(pname, "legend has a box or fill; house style is plain text")
        if not legend_ids:
            W(pname, "no numbered legend found (lines starting with '1  ', '2  ', ...)")

        # ---- note boxes and edge labels: never ----
        for cid, (r, st) in roles.items():
            c = cells[cid]
            if r == "rect" and plain_lines(c.get("value")):
                F(pname, f"note/callout box '{plain_lines(c.get('value'))[0][:40]}' (id {cid}): move the text to the legend")
            if r == "edge" and plain_lines(c.get("value")):
                F(pname, f"text on an arrow '{plain_lines(c.get('value'))[0][:40]}': use a numbered badge + legend line")

        # ---- icons ----
        icon_ids = [cid for cid, (r, _) in roles.items() if r == "icon"]
        stacked = set()
        for i, a in enumerate(icon_ids):
            for b in icon_ids[i + 1:]:
                ra, rb = absbox(cells[a]), absbox(cells[b])
                if abs(ra[0] - rb[0]) < 4 and abs(ra[1] - rb[1]) < 4:
                    stacked.update((a, b))
                    la = plain_lines(cells[a].get("value")) or plain_lines(cells[b].get("value")) or ["?"]
                    W(pname, f"two icons stacked at ({ra[0]:.0f},{ra[1]:.0f}) near '{la[0]}': the lower one is hidden, delete it")
        for cid, (r, st) in roles.items():
            if r != "icon":
                continue
            c = cells[cid]
            x, y, w, h = geo(c)
            lines = plain_lines(c.get("value"))
            name = (lines[0] if lines else st.get("resIcon", st.get("shape", "?")))[:30]
            if round(w) != ICON or round(h) != ICON:
                W(pname, f"icon '{name}' is {w:.0f}x{h:.0f}, house size is 60x60")
            if not lines and cid in stacked:
                continue
            if not lines:
                sib = [o for o, (r2, _) in roles.items() if r2 == "text" and cells[o].get("parent") == c.get("parent")
                       and o != cid and cells[o].get("parent") != "1"]
                if not sib:
                    W(pname, f"icon {st.get('resIcon', st.get('shape'))} (id {cid}) has no label")
                continue
            if len(lines) > 2:
                F(pname, f"icon label '{' / '.join(lines)[:50]}' has {len(lines)} lines (max 2)")
            if max(len(l) for l in lines) > LABEL_MAX_CHARS:
                W(pname, f"icon label line '{max(lines, key=len)}' is {max(len(l) for l in lines)} chars (aim <= {LABEL_MAX_CHARS})")
            bold = st.get("fontStyle", "0") in ("1", "3", "5", "7") or "<b>" in html.unescape(c.get("value") or "")
            if not bold or float(st.get("fontSize", 12)) != 11:
                W(pname, f"icon label '{name}' is {st.get('fontSize', '12')} px {'bold' if bold else 'regular'}, house style is 11 px bold")

        # ---- frames ----
        for cid, (r, st) in roles.items():
            if r != "frame":
                continue
            gr = st.get("grIcon", "")
            if gr.endswith("group_account") and (st.get("strokeColor", "").upper() != "#CD2264" or st.get("dashed") == "1"):
                W(pname, f"account frame '{plain_lines(cells[cid].get('value'))[:1]}' is not solid #CD2264")
            if gr.endswith("group_region") and (st.get("strokeColor", "").upper() != "#00A4A6" or st.get("dashed") != "1"):
                W(pname, f"region frame '{plain_lines(cells[cid].get('value'))[:1]}' is not dashed #00A4A6")

        # ---- edges ----
        polys = []
        for cid, (r, st) in roles.items():
            if r != "edge":
                continue
            c = cells[cid]
            s, t = cells.get(c.get("source")), cells.get(c.get("target"))
            if s is None or t is None:
                F(pname, f"arrow {cid} is not attached at {'both ends' if s is None and t is None else ('source' if s is None else 'target')}")
                continue
            if st.get("endArrow") != "block" or st.get("endFill") != "1":
                W(pname, f"arrow {cid} head is {st.get('endArrow')}/{st.get('endFill')}, house style is block filled")
            color = st.get("strokeColor", "").upper()
            if color not in ("#545B64", "#879596") or st.get("strokeWidth") != "1.5":
                W(pname, f"arrow {cid} is {color or 'default'} width {st.get('strokeWidth', '1')}, house style is #545B64 (dashed #879596) 1.5")
            sx, sy, sw, sh = absbox(s)
            tx, ty, tw, th = absbox(t)
            a = (sx + float(st.get("exitX", 0.5)) * sw, sy + float(st.get("exitY", 0.5)) * sh)
            b = (tx + float(st.get("entryX", 0.5)) * tw, ty + float(st.get("entryY", 0.5)) * th)
            # waypoints are stored relative to the edge's parent container, not to the page
            par = cells.get(c.get("parent"))
            ox, oy = (absbox(par)[:2] if par is not None and par.get("vertex") == "1" else (0.0, 0.0))
            pts = [(float(m.get("x", 0)) + ox, float(m.get("y", 0)) + oy) for m in c.iter("mxPoint") if m.get("as") is None]
            poly = [a, *pts, b]
            polys.append((cid, poly))
            for p1, p2 in zip(poly, poly[1:]):
                d = min(abs(p1[0] - p2[0]), abs(p1[1] - p2[1]))
                if d > 2:
                    W(pname, f"arrow {cid} has a diagonal segment ({p1[0]:.0f},{p1[1]:.0f})->({p2[0]:.0f},{p2[1]:.0f}), off by {d:.0f} px")

        # ---- badges ----
        badge_nums = []
        for cid, (r, st) in roles.items():
            if r != "badge":
                continue
            v = "".join(plain_lines(cells[cid].get("value")))
            if not v.isdigit():
                continue
            badge_nums.append(int(v))
            x, y, w, h = absbox(cells[cid])
            if round(w) != 24 or round(h) != 24:
                W(pname, f"badge {v} is {w:.0f}x{h:.0f}, house size is 24x24")
            cx, cy = x + w / 2, y + h / 2
            best = min((_dist(cx, cy, p1, p2) for _, poly in polys for p1, p2 in zip(poly, poly[1:])), default=None)
            if best is not None and not 12 <= best <= 26:
                where = "on top of the line" if best < 12 else "far from any line"
                W(pname, f"badge {v} centre is {best:.0f} px from the nearest arrow ({where}); house gap is 18 px beside the line")
        if len(badge_nums) != len(set(badge_nums)):
            F(pname, f"badge numbers repeat: {sorted(n for n in set(badge_nums) if badge_nums.count(n) > 1)}")
        if badge_nums and sorted(set(badge_nums)) != list(range(1, max(badge_nums) + 1)):
            F(pname, f"badge numbers have gaps: {sorted(set(range(1, max(badge_nums) + 1)) - set(badge_nums))}")
        if legend_ids and set(badge_nums) != set(legend_nums):
            F(pname, f"legend vs badges: no legend line for {sorted(set(badge_nums) - set(legend_nums))}, "
                     f"legend line without badge {sorted(set(legend_nums) - set(badge_nums))}")

        # ---- text hygiene ----
        for cid, c in cells.items():
            for l in plain_lines(c.get("value")):
                if "\u2014" in l:
                    F(pname, f"em dash in '{l[:50]}'")
                ident = re.findall(r"(?<!\d)\d{12}(?!\d)|\bd-[0-9a-f]{10}\b|\bssoins-[0-9a-f]+|arn:aws[\w-]*:[\w-]*:[\w-]*:\d{12}", l)
                if ident:
                    (F if public else W)(pname, f"identifier-shaped text {ident[:2]} in '{l[:40]}'")

    for m in fails:
        print("FAIL", m)
    for m in warns:
        print("WARN", m)
    print(f"{path}: {'FAIL' if fails else 'PASS'} fails={len(fails)} warns={len(warns)}")
    return 1 if fails else 0


def _dist(px, py, a, b):
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5


if __name__ == "__main__":
    sys.exit(main(sys.argv))
