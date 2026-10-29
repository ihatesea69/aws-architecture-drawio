"""Generic example in the house style: two accounts, two logical boxes, 12 numbered arrows.
Usage: python build_example.py <Sidebar-AWS4.js> <out.drawio>
Copy this file into a new project and replace the layout; keep the call order.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from aws_drawio import Diagram, colors_from_sidebar  # noqa: E402

sidebar, out = sys.argv[1], sys.argv[2]
d = Diagram("Example Platform", size=1080, colors=colors_from_sidebar(sidebar))

# frames: accounts side by side with a 30 px gap, region inset 20 px, logical boxes inside the region
d.account("src", "Source account", 20, 20, 360, 720)
d.region("src_r", "us-east-1", 40, 50, 320, 330, parent="src")
d.account("ctr", "Central account", 410, 20, 650, 720)
d.region("ctr_r", "ap-southeast-1", 430, 50, 610, 680, parent="ctr")
d.box("ingest", "Ingestion stack", 450, 100, 280, 150, parent="ctr_r")
d.box("sync", "Sync stack", 450, 420, 280, 150, parent="ctr_r")

# icons: 140 px between centres in a row; label on top when an arrow leaves from the bottom
d.user("users", "src_r", 100, 160, ["Users"])
d.icon("api", "src_r", 240, 160, "api_gateway", ["API Gateway", "public API"], pos="top")
d.icon("raw", "src_r", 240, 290, "s3", ["Amazon S3", "raw data"])
d.icon("role", "src", 240, 560, "identity_and_access_management", ["IAM role", "read-only"])
d.icon("idc", "src", 100, 560, "single_sign_on", ["IAM Identity", "Center"])
d.icon("collect", "ingest", 520, 170, "lambda", ["Lambda", "collector"])
d.icon("curated", "ingest", 660, 170, "s3", ["Amazon S3", "curated"])
d.icon("idsync", "sync", 520, 490, "lambda", ["Lambda", "identity sync"])
d.icon("idmap", "sync", 660, 490, "s3", ["Amazon S3", "identity map"])
d.icon("athena", "ctr_r", 850, 170, "athena", ["Amazon Athena", "Glue tables"], pos="top")
d.icon("spice", "ctr_r", 960, 170, "quick_suite", ["Amazon Quick", "SPICE"], pos="top")
d.icon("dash", "ctr_r", 960, 330, "quicksight", ["Amazon QuickSight", "Dashboard"], color="#8C4FFF")
d.user("viewers", "ctr_r", 850, 330, ["Viewers"])

# arrows: numbered in reading order; dashed = the central account reads the source (pull)
d.edge("users", "api", num=1)
d.edge("api", "raw", exit="bottom", entry="top", num=2)
d.edge("collect", "raw", exit="left", entry="right", points=[(400, 170), (400, 290)], dashed=True, num=3, badge_seg=2)
d.edge("collect", "curated", num=4)
d.edge("curated", "athena", exit=(1, 0.25), entry=(0, 0.25), num=5)
d.edge("athena", "spice", num=6)
d.edge("spice", "dash", exit="bottom", entry="top", num=7)
d.edge("viewers", "dash", num=8)
d.edge("idsync", "role", exit="left", entry="right", points=[(400, 490), (400, 560)], dashed=True, num=9)
d.edge("role", "idc", exit="left", entry="right", num=10)
d.edge("idsync", "idmap", num=11)
d.edge("idmap", "athena", exit="right", entry=(0, 0.75), points=[(770, 490), (770, 190)], num=12)

d.legend({
    1: "Users call the public API.",
    2: "The API writes each request to the raw-data bucket.",
    3: "The collector reads new raw objects every hour (cross-account read).",
    4: "The collector writes the cleaned copy to the curated bucket.",
    5: "Athena reads the curated data through the Glue tables.",
    6: "SPICE refreshes the datasets every day at 04:00 UTC.",
    7: "The dashboard reads the SPICE datasets.",
    8: "Viewers open the dashboard.",
    9: "The identity-sync Lambda assumes the read-only role (ExternalId).",
    10: "The role reads users and groups from IAM Identity Center.",
    11: "User names are written to the identity-map bucket.",
    12: "Athena joins the identity map to the curated data.",
}, notes=["Dashed line: the central account reads the source account (pull).",
          "Ingestion stack and Sync stack: one deployment each per source account."])
d.title(["Example Platform", "Architecture"])

problems = d.check()
for p in problems:
    print("PROBLEM", p)
d.write(out)
print(f"wrote {out}: nodes={len(d.nodes)} edges={len(d.edges)} problems={len(problems)} crossings={d.crossings()}")
sys.exit(1 if problems else 0)
