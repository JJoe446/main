
import re
import json
import os

DATA_FILE = os.path.join("data", "tickets.json")

# 🧮 แปลงข้อความโพย 1 บรรทัด เช่น "59=50*50" → {"เลข": "59", "บน": 50, "ล่าง": 50}
def parse_poem_line(line):
    line = line.strip()
    m1 = re.match(r"(\d{2,3})[ =](\d+)\*(\d+)", line)
    if m1:
        return {
            "เลข": m1.group(1),
            "บน": int(m1.group(2)),
            "ล่าง": int(m1.group(3))
        }
    return None

# 💾 เพิ่มโพยใหม่ลงไฟล์ JSON
def save_ticket(new_tickets):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = []

    # ตรวจสอบว่า new_tickets เป็น list หรือไม่
    if isinstance(new_tickets, dict):
        data.append(new_tickets)
    elif isinstance(new_tickets, list):
        data.extend(new_tickets)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 📤 โหลดโพยทั้งหมด
def load_tickets():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []
