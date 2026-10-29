"""House style for AWS architecture diagrams in draw.io (mxGraph XML). Python stdlib only.

Every constant here was measured from diagrams the owner finished by hand in draw.io
(see SKILL.md "Style rules"). Change a constant only when the owner's taste changes.

All coordinates you pass are ABSOLUTE page coordinates; the library converts them to the
parent-relative geometry draw.io stores for cells inside containers.

    d = Diagram("My system", size=1080, colors=colors_from_sidebar("Sidebar-AWS4.js"))
    d.account("a", "Source account", 20, 20, 380, 760)
    d.region("ar", "us-east-1", 40, 50, 340, 710, parent="a")
    d.icon("s3", "ar", 250, 160, "s3", ["Amazon S3", "raw data"])
    d.edge("users", "s3", num=1)
    d.legend({1: "Users upload files."}, notes=["Dashed line: cross-account read (pull)."])
    d.title(["My System", "Architecture"])
    problems = d.check()          # must be [] before you hand the file over
    d.write("out.drawio")
"""
import base64
import mimetypes
import re
from xml.sax.saxutils import escape

# ---- measured constants --------------------------------------------------------------
ICON = 60
BADGE = 24
BADGE_GAP = 18            # badge centre to line centre: beside the line, never on it
LABEL_FONT = 11           # icon labels: 11 px bold
LABEL_CHAR_PX = 6.6       # average width of an 11 px bold Helvetica character
LABEL_LINE_PX = 14
LEGEND_FONT = 10          # legend: 10 px bold, grey, no box
LEGEND_CHAR_PX = 5.8
LEGEND_LINE_PX = 13
TITLE_FONT = 44           # title: 44 px bold, bottom right, two lines
TITLE_CHAR_PX = 26.0
TITLE_LINE_PX = 53
FRAME_BAND = 30           # title band at the top of account / region / box frames

INK = "#232F3E"
EDGE = "#545B64"
EDGE_DASHED = "#879596"
LEGEND_INK = "#545B64"
ACCOUNT = "#CD2264"
REGION_STROKE = "#00A4A6"
REGION_FONT = "#147EBA"
USER_FILL = "#232F3D"

# Fallback category colours (AWS 2023 icon set). Prefer colors_from_sidebar(), which reads
# the colour draw.io itself assigns to each icon.
CATEGORY = {"analytics": "#8C4FFF", "networking": "#8C4FFF", "compute": "#ED7100", "containers": "#ED7100",
            "storage": "#7AA116", "cost": "#7AA116", "iot": "#7AA116", "database": "#C925D1",
            "devtools": "#C925D1", "integration": "#E7157B", "mgmt": "#E7157B", "security": "#DD344C",
            "business": "#DD344C", "ml": "#01A88D", "euc": "#01A88D"}

PTS = ("points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],"
       "[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];")
LABEL_POS = {
    "below": "verticalLabelPosition=bottom;verticalAlign=top;align=center;",
    "top": "verticalLabelPosition=top;verticalAlign=bottom;align=center;",
    "right": "labelPosition=right;verticalLabelPosition=middle;align=left;verticalAlign=middle;spacingLeft=2;",
    "left": "labelPosition=left;verticalLabelPosition=middle;align=right;verticalAlign=middle;spacingRight=2;",
}
SIDES = {"right": (1, 0.5), "left": (0, 0.5), "top": (0.5, 0), "bottom": (0.5, 1)}


def colors_from_sidebar(path):
    """Map AWS4 resIcon name -> fill colour, exactly as draw.io's own palette assigns it."""
    text = open(path, encoding="utf-8", errors="replace").read()
    var_color, out = {}, {}
    tok = re.compile(r"var (n\d*) = '[^\n]*?fillColor=(#[0-9A-Fa-f]{6})"
                     r"|createVertexTemplateEntry\((n\d*) \+ 'resourceIcon;resIcon=' \+ gn \+ '\.([A-Za-z0-9_]+);")
    for m in tok.finditer(text):
        if m.group(1):
            var_color[m.group(1)] = m.group(2).upper()
        elif m.group(3) in var_color:
            out.setdefault(m.group(4), var_color[m.group(3)])
    return out


def _attr(s):
    return escape(s, {'"': "&quot;"})


def _html_lines(lines):
    return "<br>".join(escape(s) for s in lines)


class Diagram:
    def __init__(self, name, size=1080, colors=None, border=True):
        self.name, self.size = name, size
        self.colors = colors or {}
        self.frames = {}          # key -> dict(id, x, y, w, h, parent, kind)
        self.nodes = {}           # key -> dict(id, x, y, w, h, parent)
        self.vertices = []        # (id, value, style, x, y, w, h, parent_key)
        self.boxes = []           # (key, kind, x, y, w, h, frame_key) for the geometry check
        self.edges = []
        self.legend_box = self.title_box = None
        self._n = 0
        bg_stroke = "#000000" if border else "none"
        self._bg = ("bg0", "", f"rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor={bg_stroke};",
                    10, 10, size - 20, size - 20, None)

    def _id(self, prefix):
        self._n += 1
        return f"{prefix}{self._n}"

    # ---- frames -------------------------------------------------------------------------
    def _frame(self, key, label, x, y, w, h, parent, kind, style):
        fid = self._id("g")
        self.frames[key] = dict(id=fid, x=x, y=y, w=w, h=h, parent=parent, kind=kind)
        self.vertices.append((fid, escape(label), style, x, y, w, h, parent))

    def account(self, key, label, x, y, w, h, parent=None):
        self._frame(key, label, x, y, w, h, parent, "account",
                    PTS + "outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=13;fontStyle=1;"
                    "container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;"
                    "grIcon=mxgraph.aws4.group_account;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;"
                    f"strokeColor={ACCOUNT};fontColor={ACCOUNT};dashed=0;")

    def region(self, key, label, x, y, w, h, parent=None):
        self._frame(key, label, x, y, w, h, parent, "region",
                    PTS + "outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=13;fontStyle=1;"
                    "container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;"
                    "grIcon=mxgraph.aws4.group_region;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;"
                    f"strokeColor={REGION_STROKE};fontColor={REGION_FONT};dashed=1;")

    def box(self, key, label, x, y, w, h, parent=None):
        """Logical boundary (a stack, a solution, a deployment unit): plain rectangle, no icon."""
        self._frame(key, label, x, y, w, h, parent, "box",
                    "rounded=0;whiteSpace=wrap;html=1;fillColor=none;"
                    f"strokeColor={ACCOUNT};fontColor={ACCOUNT};fontSize=13;fontStyle=1;verticalAlign=top;"
                    "align=left;spacingLeft=8;spacingTop=2;container=1;collapsible=0;recursiveResize=0;")

    def workflow(self, key, label, x, y, w, h, parent=None):
        """Step Functions workflow: the official AWS4 group shape."""
        self._frame(key, label, x, y, w, h, parent, "workflow",
                    PTS + "outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=13;fontStyle=1;"
                    "container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;"
                    "grIcon=mxgraph.aws4.group_aws_step_functions_workflow;fillColor=none;verticalAlign=top;"
                    f"align=left;spacingLeft=30;strokeColor={ACCOUNT};fontColor={ACCOUNT};dashed=0;")

    # ---- nodes --------------------------------------------------------------------------
    def _node(self, key, frame, cx, cy, style, lines, pos):
        if key in self.nodes:
            raise ValueError(f"duplicate node key {key}")
        if pos not in LABEL_POS:
            raise ValueError(f"label pos must be one of {sorted(LABEL_POS)}")
        x, y = cx - ICON / 2, cy - ICON / 2
        nid = self._id("n")
        self.nodes[key] = dict(id=nid, x=x, y=y, w=ICON, h=ICON, parent=frame)
        self.vertices.append((nid, _html_lines(lines), style + LABEL_POS[pos], x, y, ICON, ICON, frame))
        self.boxes.append((key, "icon", x, y, ICON, ICON, frame))
        lw = max(len(s) for s in lines) * LABEL_CHAR_PX
        lh = len(lines) * LABEL_LINE_PX
        lb = {"below": (cx - lw / 2, y + ICON + 2, lw, lh), "top": (cx - lw / 2, y - 2 - lh, lw, lh),
              "right": (x + ICON + 2, cy - lh / 2, lw, lh), "left": (x - 2 - lw, cy - lh / 2, lw, lh)}[pos]
        self.boxes.append((key + ":label", "label", *lb, frame))
        if len(lines) > 2:
            self.boxes.append((key + ":label", "too-many-lines", *lb, frame))

    def icon(self, key, frame, cx, cy, res, lines, pos="below", color=None, cat=None):
        """AWS service icon, 60 x 60. lines = [service name, role in this architecture]."""
        fill = color or (CATEGORY[cat] if cat else self.colors.get(res))
        if not fill:
            raise ValueError(f"no colour for resIcon '{res}': pass colors=colors_from_sidebar(...), cat= or color=")
        style = (PTS + f"outlineConnect=0;fontColor={INK};fillColor={fill};strokeColor=#ffffff;dashed=0;html=1;"
                 f"fontSize={LABEL_FONT};fontStyle=1;aspect=fixed;shape=mxgraph.aws4.resourceIcon;"
                 f"resIcon=mxgraph.aws4.{res};")
        self._node(key, frame, cx, cy, style, lines, pos)

    def user(self, key, frame, cx, cy, lines, pos="below"):
        style = (f"sketch=0;outlineConnect=0;fontColor={INK};gradientColor=none;fillColor={USER_FILL};"
                 f"strokeColor=none;dashed=0;html=1;fontSize={LABEL_FONT};fontStyle=1;aspect=fixed;"
                 "pointerEvents=1;shape=mxgraph.aws4.user;")
        self._node(key, frame, cx, cy, style, lines, pos)

    def logo(self, key, frame, cx, cy, image_path, lines, pos="below"):
        """A product with no AWS4 icon: its own logo, 60 x 60, embedded so the file stays self-contained."""
        mime = mimetypes.guess_type(image_path)[0] or "image/png"
        data = base64.b64encode(open(image_path, "rb").read()).decode("ascii")
        # draw.io writes data URIs without ';base64' because ';' separates style keys
        style = (f"shape=image;html=1;aspect=fixed;imageAspect=0;fontColor={INK};fontSize={LABEL_FONT};"
                 f"fontStyle=1;image=data:{mime},{data};")
        self._node(key, frame, cx, cy, style, lines, pos)

    # ---- edges --------------------------------------------------------------------------
    def _point(self, key, frac):
        n = self.nodes[key]
        return (n["x"] + frac[0] * n["w"], n["y"] + frac[1] * n["h"])

    def edge(self, src, tgt, exit="right", entry="left", points=(), dashed=False, num=None,
             badge="auto", badge_seg=None, badge_t=0.5):
        """Orthogonal arrow. exit/entry: a side name or an (x, y) fraction such as (0, 0.3) to spread
        several arrows along one side. points: absolute waypoints, every segment horizontal or vertical.
        badge: auto (above a horizontal segment, right of a vertical one) | above | below | left | right.
        badge_seg: index of the segment that carries the badge (default: the longest)."""
        ex = SIDES[exit] if isinstance(exit, str) else exit
        en = SIDES[entry] if isinstance(entry, str) else entry
        path = [self._point(src, ex), *points, self._point(tgt, en)]
        e = dict(src=src, tgt=tgt, ex=ex, en=en, points=list(points), dashed=dashed, num=num, path=path)
        self.edges.append(e)
        if num is None:
            return
        segs = list(zip(path, path[1:]))
        i = badge_seg if badge_seg is not None else max(range(len(segs)), key=lambda k: _seglen(segs[k]))
        (ax, ay), (bx, by) = segs[i]
        mx, my = ax + (bx - ax) * badge_t, ay + (by - ay) * badge_t
        side = badge
        if side == "auto":
            side = "above" if abs(ay - by) < 1 else "right"
        dx, dy = {"above": (0, -BADGE_GAP), "below": (0, BADGE_GAP), "left": (-BADGE_GAP, 0),
                  "right": (BADGE_GAP, 0)}[side]
        bx0, by0 = mx + dx - BADGE / 2, my + dy - BADGE / 2
        e["badge"] = (bx0, by0)
        self.boxes.append((f"badge{num}", "badge", bx0, by0, BADGE, BADGE, None))

    # ---- legend and title ---------------------------------------------------------------
    def legend(self, texts, notes=(), x=None, y=None):
        """texts: {number: one plain sentence} for every numbered arrow. notes: unnumbered lines
        (what a dashed line means, what a box name stands for, scope assumptions)."""
        if isinstance(texts, (list, tuple)):
            texts = {i + 1: t for i, t in enumerate(texts)}
        self.legend_texts = dict(texts)
        lines = [f"{n}\u00a0 {texts[n]}" for n in sorted(texts)] + list(notes)
        if x is None:
            x = 30
        if y is None:
            y = max(f["y"] + f["h"] for f in self.frames.values() if f["parent"] is None) + 10
        w = max(len(s) for s in lines) * LEGEND_CHAR_PX
        h = len(lines) * LEGEND_LINE_PX
        self.legend_box = (x, y, w, h)
        self.vertices.append((self._id("x"), _html_lines(lines),
                              f"text;html=1;align=left;verticalAlign=middle;fontSize={LEGEND_FONT};"
                              f"fontColor={LEGEND_INK};fontStyle=1;whiteSpace=nowrap;", x, y, w, h, None))
        self.boxes.append(("legend", "legend", x, y, w, h, None))

    def title(self, lines, cx=None, cy=None):
        """Big two-line title, bottom right next to the legend."""
        w = max(len(s) for s in lines) * TITLE_CHAR_PX
        h = len(lines) * TITLE_LINE_PX
        if cx is None or cy is None:
            lx, ly, lw, lh = self.legend_box or (30, self.size - 220, 0, 200)
            cx = cx if cx is not None else (lx + lw + self.size - 10) / 2
            cy = cy if cy is not None else ly + lh / 2
        x, y = cx - w / 2, cy - h / 2
        self.title_box = (x, y, w, h)
        self.vertices.append((self._id("x"), _html_lines(lines),
                              f"text;html=1;align=center;verticalAlign=middle;fontSize={TITLE_FONT};"
                              f"fontColor={INK};fontStyle=1;whiteSpace=nowrap;", x, y, w, h, None))
        self.boxes.append(("title", "title", x, y, w, h, None))

    # ---- output -------------------------------------------------------------------------
    def _rel(self, parent_key, x, y):
        if parent_key is None:
            return "1", x, y
        f = self.frames[parent_key]
        return f["id"], x - f["x"], y - f["y"]

    def page_xml(self, page_id="p1"):
        s = self.size
        out = [f'<diagram name="{_attr(self.name)}" id="{page_id}">',
               f'<mxGraphModel dx="{s}" dy="{s}" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" '
               f'arrows="1" fold="1" page="1" pageScale="1" pageWidth="{s}" pageHeight="{s}" math="0" '
               'shadow="0"><root>', '<mxCell id="0"/><mxCell id="1" parent="0"/>']
        for vid, val, style, x, y, w, h, pkey in [self._bg, *self.vertices]:
            pid, rx, ry = self._rel(pkey, x, y)
            out.append(f'<mxCell id="{vid}" value="{_attr(val)}" style="{style}" vertex="1" parent="{pid}">'
                       f'<mxGeometry x="{rx:.0f}" y="{ry:.0f}" width="{w:.0f}" height="{h:.0f}" as="geometry"/>'
                       '</mxCell>')
        for i, e in enumerate(self.edges):
            color = EDGE_DASHED if e["dashed"] else EDGE
            style = (f"edgeStyle=none;html=1;rounded=0;endArrow=block;endFill=1;strokeColor={color};"
                     f"strokeWidth=1.5;exitX={e['ex'][0]};exitY={e['ex'][1]};exitDx=0;exitDy=0;"
                     f"entryX={e['en'][0]};entryY={e['en'][1]};entryDx=0;entryDy=0;"
                     + ("dashed=1;" if e["dashed"] else ""))
            pts = "".join(f'<mxPoint x="{px:.0f}" y="{py:.0f}"/>' for px, py in e["points"])
            arr = f'<Array as="points">{pts}</Array>' if pts else ""
            out.append(f'<mxCell id="e{i + 1}" style="{style}" edge="1" parent="1" '
                       f'source="{self.nodes[e["src"]]["id"]}" target="{self.nodes[e["tgt"]]["id"]}">'
                       f'<mxGeometry relative="1" as="geometry">{arr}</mxGeometry></mxCell>')
        for e in self.edges:  # badges last so they sit on top of every line
            if e["num"] is None:
                continue
            bx, by = e["badge"]
            out.append(f'<mxCell id="b{e["num"]}" value="{e["num"]}" style="ellipse;whiteSpace=wrap;html=1;'
                       f'aspect=fixed;fillColor={INK};strokeColor=#FFFFFF;strokeWidth=2;fontColor=#FFFFFF;'
                       f'fontStyle=1;fontSize=11;" vertex="1" parent="1"><mxGeometry x="{bx:.0f}" y="{by:.0f}" '
                       f'width="{BADGE}" height="{BADGE}" as="geometry"/></mxCell>')
        out.append("</root></mxGraphModel></diagram>")
        return "\n".join(out)

    def xml(self):
        return '<mxfile host="app.diagrams.net" type="device">\n' + self.page_xml() + "\n</mxfile>\n"

    def write(self, path):
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(self.xml())

    # ---- geometry check -----------------------------------------------------------------
    def check(self):
        """Return a list of problems; [] means the layout follows the house rules."""
        P = []
        ov = lambda a, b: a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]
        inside = lambda a, b: a[0] >= b[0] and a[1] >= b[1] and a[0] + a[2] <= b[0] + b[2] and a[1] + a[3] <= b[1] + b[3]
        boxes = [(k, kind, (x, y, w, h), f) for k, kind, x, y, w, h, f in self.boxes]
        for k, kind, r, f in boxes:
            if kind == "too-many-lines":
                P.append(f"LABEL {k} has more than 2 lines")
        boxes = [b for b in boxes if b[1] != "too-many-lines"]
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                if a[0].split(":")[0] != b[0].split(":")[0] and ov(a[2], b[2]):
                    P.append(f"OVERLAP {a[0]} x {b[0]}")
        page = (10, 10, self.size - 20, self.size - 20)
        for k, kind, r, f in boxes:
            if f is None:
                if not inside(r, (page[0] + 2, page[1] + 2, page[2] - 4, page[3] - 4)):
                    P.append(f"OUTSIDE {k} of the page background")
                continue
            fr = self.frames[f]
            inner = (fr["x"] + 2, fr["y"] + FRAME_BAND, fr["w"] - 4, fr["h"] - FRAME_BAND - 2)
            if not inside(r, inner):
                P.append(f"OUTSIDE {k} of frame {f}")
        for key, fr in self.frames.items():
            outer = page if fr["parent"] is None else None
            if fr["parent"] is not None:
                p = self.frames[fr["parent"]]
                outer = (p["x"] + 2, p["y"] + FRAME_BAND - 5, p["w"] - 4, p["h"] - FRAME_BAND + 3)
            if not inside((fr["x"], fr["y"], fr["w"], fr["h"]), outer):
                P.append(f"OUTSIDE frame {key} of {fr['parent'] or 'page'}")
        # badges never straddle a frame border
        for k, kind, r, _ in boxes:
            if kind != "badge":
                continue
            for fk, fr in self.frames.items():
                fb = (fr["x"], fr["y"], fr["w"], fr["h"])
                if ov(r, fb) and not inside(r, fb):
                    P.append(f"BADGE {k} sits on the border of frame {fk}")
        # edges: orthogonal, never through an icon, label, badge, legend or title, never merged
        segs_by_edge = []
        for e in self.edges:
            segs = list(zip(e["path"], e["path"][1:]))
            segs_by_edge.append((e, segs))
            for a, b in segs:
                if abs(a[0] - b[0]) > 0.5 and abs(a[1] - b[1]) > 0.5:
                    P.append(f"DIAGONAL segment in edge {e['src']}->{e['tgt']} {a}->{b}")
            for a, b in segs:
                for k, kind, r, _ in boxes:
                    if k in (e["src"], e["tgt"]) or (kind == "badge" and k == f"badge{e['num']}"):
                        continue
                    if _seg_hits(a, b, r):
                        P.append(f"EDGE {e['src']}->{e['tgt']} crosses {k}")
            if e["num"] is not None:
                br = (e["badge"][0], e["badge"][1], BADGE, BADGE)
                for e2, segs2 in [(x, list(zip(x["path"], x["path"][1:]))) for x in self.edges]:
                    for a, b in segs2:
                        if _seg_hits(a, b, br):
                            P.append(f"BADGE {e['num']} lies on edge {e2['src']}->{e2['tgt']}")
        for i in range(len(segs_by_edge)):
            for j in range(i + 1, len(segs_by_edge)):
                for a in segs_by_edge[i][1]:
                    for b in segs_by_edge[j][1]:
                        if _collinear_overlap(a, b):
                            e1, e2 = segs_by_edge[i][0], segs_by_edge[j][0]
                            P.append(f"MERGED lines {e1['src']}->{e1['tgt']} and {e2['src']}->{e2['tgt']}")
        nums = [e["num"] for e in self.edges if e["num"] is not None]
        if len(nums) != len(set(nums)):
            P.append("BADGE numbers are not unique")
        if nums and sorted(nums) != list(range(1, len(nums) + 1)):
            P.append(f"BADGE numbers are not 1..{len(nums)}: {sorted(nums)}")
        legend_nums = set(getattr(self, "legend_texts", {}))
        if set(nums) != legend_nums:
            P.append(f"LEGEND mismatch: badges without a line {sorted(set(nums) - legend_nums)}, "
                     f"lines without a badge {sorted(legend_nums - set(nums))}")
        return P

    def crossings(self):
        """Count perpendicular crossings between different edges (allowed, keep it low)."""
        n = 0
        for i in range(len(self.edges)):
            for j in range(i + 1, len(self.edges)):
                for a in zip(self.edges[i]["path"], self.edges[i]["path"][1:]):
                    for b in zip(self.edges[j]["path"], self.edges[j]["path"][1:]):
                        n += _cross(a, b)
        return n


def _seglen(s):
    (ax, ay), (bx, by) = s
    return abs(bx - ax) + abs(by - ay)


def _seg_hits(p1, p2, r):
    x0, y0, w, h = r
    (ax, ay), (bx, by) = p1, p2
    if abs(ax - bx) < 0.5:
        return x0 < ax < x0 + w and max(min(ay, by), y0) < min(max(ay, by), y0 + h)
    if abs(ay - by) < 0.5:
        return y0 < ay < y0 + h and max(min(ax, bx), x0) < min(max(ax, bx), x0 + w)
    return False  # diagonals are reported separately


def _collinear_overlap(a, b):
    (ax1, ay1), (ax2, ay2) = a
    (bx1, by1), (bx2, by2) = b
    if abs(ax1 - ax2) < 0.5 and abs(bx1 - bx2) < 0.5 and abs(ax1 - bx1) < 0.5:
        return max(min(ay1, ay2), min(by1, by2)) < min(max(ay1, ay2), max(by1, by2)) - 0.5
    if abs(ay1 - ay2) < 0.5 and abs(by1 - by2) < 0.5 and abs(ay1 - by1) < 0.5:
        return max(min(ax1, ax2), min(bx1, bx2)) < min(max(ax1, ax2), max(bx1, bx2)) - 0.5
    return False


def _cross(a, b):
    (ax1, ay1), (ax2, ay2) = a
    (bx1, by1), (bx2, by2) = b
    if abs(ax1 - ax2) < 0.5 and abs(by1 - by2) < 0.5:
        return min(bx1, bx2) < ax1 < max(bx1, bx2) and min(ay1, ay2) < by1 < max(ay1, ay2)
    if abs(ay1 - ay2) < 0.5 and abs(bx1 - bx2) < 0.5:
        return _cross(b, a)
    return False
