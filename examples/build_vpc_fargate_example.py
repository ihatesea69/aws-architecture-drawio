"""Example in the house style: VPC with two Availability Zones, a public subnet with a NAT Gateway,
and one Fargate frame holding one ECS task per role (a CI/CD platform on Fargate).
Usage: python build_vpc_fargate_example.py <Sidebar-AWS4.js> <out.drawio>
Copy this file into a project and replace the layout; keep the call order.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from aws_drawio import Diagram, colors_from_sidebar  # noqa: E402

sidebar, out = sys.argv[1], sys.argv[2]
d = Diagram("Jenkins on Fargate", size=1080, colors=colors_from_sidebar(sidebar))

# frames: account > region > VPC > AZ columns > public subnets; one compute frame spans both AZs
d.account("acct", "Lab account", 140, 20, 920, 860)
d.region("reg", "ap-southeast-1", 160, 50, 885, 815, parent="acct")
d.vpc("vpc", "VPC", 180, 175, 690, 555, parent="reg")
d.az("az1", "Availability Zone 1", 200, 205, 250, 300, parent="vpc")
d.az("az2", "Availability Zone 2", 600, 205, 250, 300, parent="vpc")
d.subnet("pub1", "Public subnet", 215, 240, 220, 145, parent="az1", public=True)
d.subnet("pub2", "Public subnet", 615, 240, 220, 145, parent="az2", public=True)
d.service("ecs", 210, 515, 630, 200, parent="vpc")

# outside AWS
d.logo("github", None, 70, 120, os.path.join(HERE, "github-mark.png"), ["GitHub"], pos="top")
d.user("dev", None, 70, 310, ["Developer"])

# shared resources
d.icon("cf", "reg", 525, 120, "cloudfront", ["Amazon CloudFront"], pos="right")
d.glyph("nat", "pub1", 290, 310, "nat_gateway", ["NAT Gateway"])
d.icon("alb", "vpc", 525, 310, "elastic_load_balancing", ["Internal ALB"])
d.icon("efs", "az1", 395, 450, "elastic_file_system", ["Amazon EFS"], pos="left")
d.icon("rds", "az2", 680, 450, "rds", ["Amazon RDS"], pos="right")

# one Fargate frame, one task per role
d.icon("fargate", "ecs", 270, 605, "fargate", ["AWS Fargate"])
d.glyph("t_ctl", "ecs", 395, 605, "ecs_task", ["Jenkins controller"])
d.glyph("t_agent", "ecs", 510, 605, "ecs_task", ["Jenkins agent"], pos="top")
d.glyph("t_sonar", "ecs", 680, 605, "ecs_task", ["SonarQube"])
d.glyph("t_app", "ecs", 790, 605, "ecs_task", ["sample-app"], pos="top")

# regional managed services outside the VPC
d.icon("secrets", "reg", 300, 805, "secrets_manager", ["Secrets Manager"])
d.icon("s3", "reg", 510, 805, "s3", ["Amazon S3"])
d.icon("cb", "reg", 720, 805, "codebuild", ["AWS CodeBuild"])
d.icon("ecr", "reg", 930, 805, "ecr", ["Amazon ECR"])

# arrows, numbered along the data flow
d.edge("dev", "github", exit="top", entry="bottom", num=1)
d.edge("github", "cf", num=2)
d.edge("cf", "alb", exit="bottom", entry="top", num=3, badge_t=0.62)
d.edge("alb", "t_ctl", exit="left", entry=(0.75, 0), points=[(470, 310), (470, 535), (415, 535)], num=4)
d.edge("t_ctl", "efs", exit="top", entry="bottom", num=5, badge_t=0.33, badge="left")
d.edge("t_ctl", "t_agent", num=6)
d.edge("t_agent", "t_sonar", num=7)
d.edge("t_sonar", "rds", exit="top", entry="bottom", num=8, badge_t=0.33)
d.edge("t_agent", "s3", exit="bottom", entry="top", num=9, badge_t=0.85)
d.edge("s3", "cb", num=10)
d.edge("cb", "ecr", num=11)
d.edge("t_agent", "t_app", exit=(0.75, 1), entry="bottom", points=[(530, 698), (790, 698)], num=12,
       badge_seg=1, badge_t=0.85)
d.edge("ecr", "t_app", exit="top", entry="right", points=[(930, 605)], num=13)

d.legend({
    1: "The developer pushes code to the main branch on GitHub.",
    2: "GitHub sends a signed (HMAC) webhook over HTTPS to CloudFront.",
    3: "CloudFront reaches the internal ALB through a VPC origin, not the Internet.",
    4: "The ALB routes the UI and /github-webhook/ to the controller; ECS injects its secrets.",
    5: "JENKINS_HOME lives on EFS, so jobs and history survive every redeploy.",
    6: "The controller (0 executors) starts a fresh agent task for each build.",
    7: "The agent runs mvn verify and sends the analysis to SonarQube.",
    8: "SonarQube stores its data in RDS for PostgreSQL.",
    9: "After the quality gate passes, the agent uploads the jar and Docker context.",
    10: "CodeBuild (privileged mode) reads the context from S3 and builds the image.",
    11: "CodeBuild pushes the image, tagged commit-build number, to ECR.",
    12: "The agent registers a new task definition and updates the sample-app service.",
    13: "ECS pulls the new image from ECR and rolls the sample-app task.",
}, x=30, y=890)
d.title(["Jenkins on Fargate", "CI/CD lab"])

problems = d.check()
for p in problems:
    print("PROBLEM", p)
d.write(out)
print(f"wrote {out}: nodes={len(d.nodes)} edges={len(d.edges)} problems={len(problems)} crossings={d.crossings()}")
sys.exit(1 if problems else 0)
