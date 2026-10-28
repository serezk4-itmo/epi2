"""Render report figures from the current YouTrack project state."""

import collections
import datetime as dt
import json
import os
import pathlib
import tomllib
import urllib.parse
import urllib.request

from PIL import Image, ImageDraw, ImageFont


HERE = pathlib.Path(__file__).parent
FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
BG = "#ffffff"
INK = "#19304b"
MUTED = "#60738c"
BLUE = "#3e78c5"
TEAL = "#32a79c"
GRID = "#dce5ef"


def font(size):
    return ImageFont.truetype(FONT_PATH, size)


def canvas(width, height, title, subtitle):
    im = Image.new("RGB", (width, height), BG)
    d = ImageDraw.Draw(im)
    d.text((60, 35), title, font=font(33), fill=INK)
    d.text((60, 82), subtitle, font=font(21), fill=MUTED)
    d.line((60, 125, width - 60, 125), fill=GRID, width=2)
    return im, d


def get_data():
    config = tomllib.loads((pathlib.Path.home() / ".codex/config.toml").read_text())
    server = config["mcp_servers"]["youtrack"]
    parsed = urllib.parse.urlparse(server["url"])
    root = f"{parsed.scheme}://{parsed.netloc}"
    token = os.environ[server["bearer_token_env_var"]]

    def get(path):
        req = urllib.request.Request(root + path, headers={"Authorization": "Bearer " + token})
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.load(response)

    issues = []
    for skip in (0, 100):
        issues += get(
            "/api/issues?query=project:%20DPRO&"
            "fields=idReadable,resolved,customFields(name,value(name,login,minutes))"
            f"&$top=100&$skip={skip}"
        )
    sprints = get("/api/agiles/204-1/sprints?fields=id,name,start,finish&$top=100")
    return issues, [s for s in sprints if s["name"].startswith("Спринт")]


def fields(issue):
    return {f["name"]: f.get("value") for f in issue.get("customFields", [])}


def assignees(issues):
    counts = collections.Counter()
    for issue in issues:
        values = fields(issue)
        if (values.get("Type") or {}).get("name") != "Task":
            continue
        counts[(values.get("Assignee") or {}).get("login", "Без исполнителя")] += 1
    rows = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    im, d = canvas(1400, 780, "Задачи по исполнителям", "Текущие карточки Type: Task в проекте DPRO")
    max_count = max(counts.values())
    for idx, (name, count) in enumerate(rows):
        y = 160 + idx * 72
        d.text((75, y + 9), name, font=font(26), fill=INK)
        d.rounded_rectangle((310, y, 310 + int(890 * count / max_count), y + 46), radius=8, fill=BLUE)
        d.text((1235, y + 8), str(count), font=font(26), fill=INK)
    d.text((75, 735), f"Всего задач: {sum(counts.values())}", font=font(22), fill=MUTED)
    im.save(HERE / "assignees.png")


def burndown(issues, sprints):
    planned = 0
    for issue in issues:
        values = fields(issue)
        if (values.get("Type") or {}).get("name") == "Task":
            planned += (values.get("DPRO Estimation") or {}).get("minutes", 0) / 60
    im, d = canvas(1400, 700, "Burndown", "Плановая линия и состояние на дату отчёта")
    x0, y0, x1, y1 = 150, 170, 1320, 575
    for n in range(6):
        y = y1 - (y1 - y0) * n / 5
        d.line((x0, y, x1, y), fill=GRID, width=2)
        d.text((40, y - 14), f"{planned * n / 5:.0f}", font=font(20), fill=MUTED)
    d.line((x0, y0, x0, y1), fill=INK, width=3)
    d.line((x0, y1, x1, y1), fill=INK, width=3)
    d.line((x0, y0, x1, y1), fill=BLUE, width=5)
    d.ellipse((x0 - 10, y0 - 10, x0 + 10, y0 + 10), fill=TEAL)
    d.text((x0 + 20, y0 - 40), f"Факт на 29.10.2026: {planned:.0f} ч осталось", font=font(23), fill=TEAL)
    d.text((x0, y1 + 20), "02.11.2026", font=font(21), fill=MUTED)
    d.text((x1 - 115, y1 + 20), "14.06.2027", font=font(21), fill=MUTED)
    d.text((450, 630), "Фактическая динамика появится после начала спринтов", font=font(21), fill=MUTED)
    im.save(HERE / "burndown.png")


def time_report(issues):
    im, d = canvas(1400, 490, "Отчёт по времени", "Срез из work items проекта DPRO")
    d.rounded_rectangle((80, 165, 1320, 370), radius=18, outline=GRID, width=3)
    d.text((140, 205), "Учтено по разработке MVP", font=font(29), fill=INK)
    d.text((1030, 190), "0 ч", font=font(54), fill=BLUE)
    d.text((140, 285), "Плановая оценка детальных задач — 7 500 ч", font=font(25), fill=MUTED)
    d.text((80, 420), "Время вносят после выполнения работ; план не является фактом.", font=font(22), fill=MUTED)
    im.save(HERE / "time_report.png")


def gantt(sprints):
    sprints = sorted(sprints, key=lambda s: s["start"] or 0)
    im, d = canvas(1600, 1050, "Диаграмма Ганта", "Календарь спринтов и контрольные релизы YouTrack")
    x0, x1 = 260, 1510
    left = min(s["start"] for s in sprints)
    right = max(s["finish"] for s in sprints)
    span = right - left

    def xpos(timestamp):
        return x0 + int((timestamp - left) / span * (x1 - x0))

    month = dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc)
    while month <= dt.datetime(2027, 6, 1, tzinfo=dt.timezone.utc):
        stamp = int(month.timestamp() * 1000)
        if left <= stamp <= right:
            x = xpos(stamp)
            d.line((x, 165, x, 890), fill=GRID, width=2)
            d.text((x + 7, 145), month.strftime("%m.%Y"), font=font(19), fill=MUTED)
        month = dt.datetime(month.year + (month.month == 12), (month.month % 12) + 1, 1, tzinfo=dt.timezone.utc)
    for idx, sprint in enumerate(sprints):
        y = 190 + idx * 42
        d.text((75, y + 3), f"S{idx + 1:02d}", font=font(22), fill=INK)
        d.rounded_rectangle((xpos(sprint["start"]), y, xpos(sprint["finish"]) - 3, y + 26), radius=5, fill=BLUE if idx % 2 == 0 else TEAL)
    for label, index in (("Alpha", 4), ("Beta", 10), ("MVP", 16)):
        x = xpos(sprints[index - 1]["finish"])
        d.line((x, 185, x, 905), fill="#d15b56", width=3)
        d.text((min(x + 8, 1460), 920), label, font=font(21), fill="#bb4742")
    im.save(HERE / "gantt.png")


if __name__ == "__main__":
    issues, sprints = get_data()
    assert len(sprints) == 16
    assignees(issues)
    burndown(issues, sprints)
    time_report(issues)
    gantt(sprints)
    print("Created 4 figures from YouTrack data")
