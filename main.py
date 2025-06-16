# Streamlit run main.py  

import streamlit as st
import re
import datetime
import pandas as pd
import json
import os
from itertools import permutations

# ตั้งค่า Streamlit
st.set_page_config(page_title="กินเต็ม", layout="wide")

# คำนวณยอดรวมจากยอดคำนวณ
total_sales = sum(ticket["ยอดคำนวณ"] for ticket in st.session_state.get('lotto_data', [])) if 'lotto_data' in st.session_state and st.session_state.lotto_data else 0
st.title(f"📊  ยอดรวม: {total_sales} บาท")

# CSS เพื่อทำให้ตารางเหมือนกระดาษและสไตล์ตามภาพ
st.markdown("""
<style>
    .stDataFrame {
        width: 100%;
        border-collapse: collapse;
        background: #fff;
        border: 1px solid #000;
    }
    .stDataFrame table {
        border: 1px solid #000;
        background-color: #fff;
    }
    .stDataFrame th {
        background-color: #90ee90; /* สีเขียวอ่อน */
        border: 1px solid #000;
        padding: 8px;
        text-align: center;
        font-weight: bold;
    }
    .stDataFrame td {
        border: 1px solid #000;
        padding: 8px;
        text-align: center;
    }
    .stDataFrame tr:nth-child(even) {
        background-color: #f2f2f2;
    }
    .two-digit-header {
        background-color: #ffa500; /* สีส้ม */
    }
    .three-digit-header {
        background-color: #ff6347; /* สีแดงอ่อน */
    }
    .table-container {
        display: flex;
        justify-content: space-between;
    }
    .table-section {
        width: 48%;
        border: 1px solid #000;
        padding: 10px;
    }
    .send-table {
        overflow-x: visible; /* ไม่มี scroll bar */
    }
</style>
""", unsafe_allow_html=True)

# --- ตัวแปรเริ่มต้น ---
today = datetime.date.today()

# โหลดข้อมูลจาก tickets.json เมื่อเริ่มแอป
if 'lotto_data' not in st.session_state:
    if os.path.exists("tickets.json"):
        try:
            with open("tickets.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                st.session_state.lotto_data = data if isinstance(data, list) else []
        except (json.JSONDecodeError, FileNotFoundError):
            st.session_state.lotto_data = []
    else:
        st.session_state.lotto_data = []

# --- ฟังก์ชันปรับแต่งโพย ---
def standardize_ticket(text):
    lines = text.strip().splitlines()
    standardized_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # ลบวันที่ออก
        line = re.sub(r"\d{1,2}/\d{1,2}/\d{2,4}", "", line).strip()

        # ลบข้อความที่ไม่เกี่ยวข้อง
        if re.search(r"บน-โต๊ด|บน-ล่าง|สาย|มู่|เจ๊", line, re.IGNORECASE):
            continue

        # แปลง "ยอด400" เป็น "ยอด 400"
        if re.match(r"^ยอด\d+$", line, re.IGNORECASE):
            match = re.match(r"ยอด(\d+)", line, re.IGNORECASE)
            amount = match.group(1)
            line = f"ยอด {amount}"

        # แปลงทุกรูปแบบเป็นเลข=จำนวน*จำนวน
        if re.match(r"(\d+)=(\d+)[×+]((\d+))", line):
            match = re.match(r"(\d+)=(\d+)[×+]((\d+))", line)
            number, top, bottom = match.groups()[:3]
            line = f"{number}={top}*{bottom}"
        elif re.match(r"(\d+)-(\d+)[×+]((\d+))", line):
            match = re.match(r"(\d+)-(\d+)[×+]((\d+))", line)
            number, top, bottom = match.groups()[:3]
            line = f"{number}={top}*{bottom}"
        elif re.match(r"(\d+)\s+(\d+)[×+]((\d+))", line):
            match = re.match(r"(\d+)\s+(\d+)[×+]((\d+))", line)
            number, top, bottom = match.groups()[:3]
            line = f"{number}={top}*{bottom}"
        elif re.match(r"(\d+)-(\d+)\*(\d+)", line):
            match = re.match(r"(\d+)-(\d+)\*(\d+)", line)
            number, top, bottom = match.groups()
            line = f"{number}={top}*{bottom}"
        elif re.match(r"(\d+)=(\d+)-(\d+)\*(\d+)", line):
            match = re.match(r"(\d+)=(\d+)-(\d+)\*(\d+)", line)
            number, top, bottom, todd = match.groups()
            line = f"{number}={top}*{bottom}*{todd}"
        elif re.match(r"(\d+)=(\d+)-(\d+)", line):
            match = re.match(r"(\d+)=(\d+)-(\d+)", line)
            number, top, bottom = match.groups()
            line = f"{number}={top}*{bottom}"
        elif re.match(r"(\d+)\s+(\d+)\*(\d+)", line):
            match = re.match(r"(\d+)\s+(\d+)\*(\d+)", line)
            number, top, bottom = match.groups()
            line = f"{number}={top}*{bottom}"

        standardized_lines.append(line)
    return "\n".join(standardized_lines)

# --- ฟังก์ชันประมวลผลโพย ---
def parse_tickets(tickets):
    data = []
    for ticket in tickets:
        lines = ticket["โพย"].strip().splitlines()
        customer = ticket["ลูกค้า"]

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if re.search(r"ยอด|สาย|มู่|เจ๊", line, re.IGNORECASE):
                continue

            number = None
            top, bottom, todd = 0, 0, 0

            match2 = re.match(r"^(\d{2,3})=(\d+)\*(\d+)$", line)
            match3 = re.match(r"^(\d{3})=(\d+)\*(\d+)\*(\d+)$", line)

            if match3:
                number, top, todd, bottom = match3.groups()
                top, bottom, todd = int(top), int(bottom), int(todd)
            elif match2:
                number, v1, v2 = match2.groups()
                v1, v2 = int(v1), int(v2)
                if len(number) == 3:
                    top, todd = v1, v2
                else:
                    top, bottom = v1, v2

            if number:
                data.append({
                    "เลข": number,
                    "บน": top,
                    "ล่าง": bottom,
                    "โต๊ด": todd,
                    "ลูกค้า": customer
                })

    return data

# --- ฟังก์ชันคำนวณยอดรวม ---
def calculate_total(standardized_lines):
    total = 0
    for line in standardized_lines:
        if re.match(r"^(\d+)=(\d+)\*(\d+)$", line):  # รองรับเฉพาะรูปแบบเลข=จำนวน*จำนวน
            match = re.match(r"^(\d+)=(\d+)\*(\d+)$", line)
            if match:
                _, top, bottom = match.groups()
                total += int(top) + int(bottom)
        elif re.match(r"^(\d+)=(\d+)\*(\d+)\*(\d+)$", line):  # รองรับเลข=จำนวน*จำนวน*จำนวน (โต๊ด)
            match = re.match(r"^(\d+)=(\d+)\*(\d+)\*(\d+)$", line)
            if match:
                _, top, bottom, todd = match.groups()
                total += int(top) + int(bottom) + int(todd)
    return total

# --- ฟังก์ชันแปลงเลข 6 ตัวกลับ ---
def generate_six_digit_permutations(number):
    if len(number) != 3:
        return []
    digits = list(number)
    perms = [''.join(p) for p in permutations(digits)]
    return sorted(list(set(perms)))

# --- เมนู sidebar ---
menu = st.sidebar.selectbox("📋 เมนู", ["แยกเลข", "เลขที่ซื้อเยอะ", "เลขแยกส่งเจ้า", "แปลงเลข 6 ตัวกลับ", "บันทึกยอด"])

# --- อินพุตจากผู้ใช้ ---
if menu == "แยกเลข":
    st.subheader("📋 เก็บโพยจาก LINE")
    col1, col2 = st.columns([3, 1])
    with col1:
        text_input = st.text_area("วางโพยที่นี่:", height=300)
    with col2:
        customer_name = st.text_input("👤 ชื่อลูกค้า")
        draw_date = st.date_input("📆 งวดวันที่", value=today)

    # --- เก็บโพยใน tickets.json ---
    if st.button("✅ เก็บโพย") and text_input and customer_name:
        # รวบรวมโพยทั้งหมดเป็นโพยเดียว
        lines = text_input.strip().splitlines()
        current_ticket = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            current_ticket.append(line)

        if current_ticket:
            standardized_text = standardize_ticket("\n".join(current_ticket))
            standardized_lines = standardized_text.strip().splitlines()
            calculated_total = calculate_total(standardized_lines)
            # ค้นหายอดที่ระบุจากโพย
            declared_total_match = re.search(r"ยอด\s+(\d+)", standardized_text, re.IGNORECASE)
            declared_total = int(declared_total_match.group(1)) if declared_total_match else 0
            if calculated_total != declared_total and calculated_total > 0:
                st.warning(f"⚠️ โพยผิด: ยอดรวมที่คำนวณได้ ({calculated_total}) ไม่ตรงกับยอดที่ระบุ ({declared_total}) สำหรับโพยของ {customer_name}")
                # อัปเดตโพยด้วยยอดที่คำนวณได้
                standardized_text = re.sub(r"ยอด\s+\d+", f"ยอด {calculated_total}", standardized_text, flags=re.IGNORECASE)
            ticket = {
                "โพย": standardized_text,
                "ลูกค้า": customer_name,
                "วันที่": draw_date.strftime("%d/%m/%Y"),
                "ยอดคำนวณ": calculated_total
            }
            st.session_state.lotto_data.append(ticket)

        # บันทึกข้อมูลลง tickets.json
        with open("tickets.json", "w", encoding="utf-8") as f:
            json.dump(st.session_state.lotto_data, f, ensure_ascii=False, indent=2)
        st.success(f"✅ เก็บโพยของ {customer_name} เรียบร้อยแล้ว")
        st.rerun()  # รีเฟรชเพื่ออัปเดตยอดรวมใน st.title

    # --- ปุ่มล้างข้อมูลทั้งหมด ---
    if st.button("🗑️ ล้างข้อมูลทั้งหมด"):
        st.session_state.lotto_data = []
        with open("tickets.json", "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        st.success("🗑️ ล้างข้อมูลใน tickets.json เรียบร้อยแล้ว")
        st.rerun()  # รีเฟรชเพื่ออัปเดตยอดรวมใน st.title

    # แสดงโพยที่เก็บและปุ่มลบ
    if st.session_state.lotto_data:
        st.subheader("📜 โพยที่เก็บไว้")
        for i, ticket in enumerate(st.session_state.lotto_data):
            col1, col2 = st.columns([9, 1])
            with col1:
                st.write(f"**ลูกค้า**: {ticket['ลูกค้า']} | **วันที่**: {ticket['วันที่']} | **ยอดคำนวณ**: {ticket['ยอดคำนวณ']} บาท")
                st.code(ticket["โพย"], language="text")
            with col2:
                if st.button("🗑️ ลบ", key=f"delete_{i}"):
                    st.session_state.lotto_data.pop(i)
                    with open("tickets.json", "w", encoding="utf-8") as f:
                        json.dump(st.session_state.lotto_data, f, ensure_ascii=False, indent=2)
                    st.rerun()

# --- แสดงผลตามเมนู ---
if st.session_state.lotto_data:
    tickets = st.session_state.lotto_data
    # ใช้วันที่ล่าสุดจาก tickets หากมี มิฉะนั้นใช้ today
    if tickets:
        try:
            last_date_str = tickets[-1]["วันที่"]
            draw_date = datetime.datetime.strptime(last_date_str, "%d/%m/%Y").date()
        except (KeyError, ValueError):
            draw_date = today
    else:
        draw_date = today

    if menu == "เลขที่ซื้อเยอะ":
        st.subheader("📊 เลขที่ซื้อเยอะ")
        data = parse_tickets(tickets)
        if data:
            df = pd.DataFrame(data)
            # แยกเลข 2 ตัวและ 3 ตัว
            df_two_digits = df[df["เลข"].str.len() == 2].groupby("เลข")[["บน", "ล่าง"]].sum().reset_index()
            df_two_digits['ถูกบน'] = df_two_digits['บน'] * 70
            df_two_digits['ถูกล่าง'] = df_two_digits['ล่าง'] * 70
            df_two_digits['รวมถูก'] = df_two_digits['ถูกบน'] + df_two_digits['ถูกล่าง']
            df_two_digits['ติดลบ'] = total_sales - df_two_digits['รวมถูก']
            df_two_digits = df_two_digits.sort_values(by=['ถูกบน', 'ถูกล่าง'], ascending=[False, False])

            df_three_digits = df[df["เลข"].str.len() == 3].groupby("เลข")[["บน", "ล่าง", "โต๊ด"]].sum().reset_index()
            df_three_digits['ถูกบน'] = df_three_digits['บน'] * 500
            df_three_digits['ถูกล่าง'] = df_three_digits['ล่าง'] * 100
            df_three_digits['ถูกโต๊ด'] = df_three_digits['โต๊ด'] * 100
            df_three_digits['รวมถูก'] = df_three_digits['ถูกบน'] + df_three_digits['ถูกล่าง'] + df_three_digits['ถูกโต๊ด']
            df_three_digits['ติดลบ'] = total_sales - df_three_digits['รวมถูก']
            df_three_digits = df_three_digits.sort_values(by=['ถูกบน', 'ถูกล่าง', 'ถูกโต๊ด'], ascending=[False, False, False])

            # ตารางส่ง
            df_two_digits_send = df_two_digits.copy()
            df_two_digits_send['ใส่เลขส่งบน'] = df_two_digits_send['บน'] * 0.5  # ตัวคูณ 0.5 สามารถปรับได้
            df_two_digits_send['ใส่เลขส่งล่าง'] = df_two_digits_send['ล่าง'] * 0.5  # ตัวคูณ 0.5 สามารถปรับได้
            df_two_digits_send['ใส่เลขส่งโต๊ด'] = 0  # ไม่มีโต๊ดสำหรับ 2 ตัว
            df_two_digits_send['ติดลบ'] = total_sales - df_two_digits_send['รวมถูก']

            df_three_digits_send = df_three_digits.copy()
            df_three_digits_send['ใส่เลขส่งบน'] = df_three_digits_send['บน'] * 0.5  # ตัวคูณ 0.5 สามารถปรับได้
            df_three_digits_send['ใส่เลขส่งล่าง'] = df_three_digits_send['ล่าง'] * 0.5  # ตัวคูณ 0.5 สามารถปรับได้
            df_three_digits_send['ใส่เลขส่งโต๊ด'] = df_three_digits_send['โต๊ด'] * 0.5  # ตัวคูณ 0.5 สามารถปรับได้
            df_three_digits_send['ติดลบ'] = total_sales - df_three_digits_send['รวมถูก']

            # ใช้คอนเทนเนอร์สำหรับจัดวางตาราง
            st.markdown('<div class="table-container">', unsafe_allow_html=True)
            with st.container():
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<div class="table-section">', unsafe_allow_html=True)
                    st.markdown('<h3 class="two-digit-header">เลข 2 ตัว</h3>', unsafe_allow_html=True)
                    if not df_two_digits.empty:
                        st.dataframe(df_two_digits[['เลข', 'บน', 'ล่าง', 'ถูกบน', 'ถูกล่าง', 'รวมถูก', 'ติดลบ']], use_container_width=True)
                    st.markdown('<h3 class="two-digit-header">2 ตัวส่ง</h3>', unsafe_allow_html=True)
                    if not df_two_digits_send.empty:
                        st.dataframe(df_two_digits_send[['เลข', 'ถูกบน', 'ถูกล่าง', 'รวมถูก', 'ใส่เลขส่งบน', 'ใส่เลขส่งล่าง', 'ใส่เลขส่งโต๊ด', 'ติดลบ']], use_container_width=True)
                        filename = f"2ตัวส่ง_{draw_date.strftime('%d_%m_%Y')}.csv"
                        csv = df_two_digits_send[['เลข', 'ถูกบน', 'ถูกล่าง', 'รวมถูก', 'ใส่เลขส่งบน', 'ใส่เลขส่งล่าง', 'ใส่เลขส่งโต๊ด', 'ติดลบ']].to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                        st.download_button("💾 ดาวน์โหลด 2 ตัวส่ง", csv, file_name=filename, mime="text/csv")
                    st.markdown('</div>', unsafe_allow_html=True)
                with col2:
                    st.markdown('<div class="table-section">', unsafe_allow_html=True)
                    st.markdown('<h3 class="three-digit-header">เลข 3 ตัว</h3>', unsafe_allow_html=True)
                    if not df_three_digits.empty:
                        st.dataframe(df_three_digits[['เลข', 'บน', 'ล่าง', 'โต๊ด', 'ถูกบน', 'ถูกล่าง', 'ถูกโต๊ด', 'รวมถูก', 'ติดลบ']], use_container_width=True)
                    st.markdown('<h3 class="three-digit-header">3 ตัวส่ง</h3>', unsafe_allow_html=True)
                    if not df_three_digits_send.empty:
                        st.dataframe(df_three_digits_send[['เลข', 'ถูกบน', 'ถูกล่าง', 'รวมถูก', 'ใส่เลขส่งบน', 'ใส่เลขส่งล่าง', 'ใส่เลขส่งโต๊ด', 'ติดลบ']], use_container_width=True)
                        filename = f"3ตัวส่ง_{draw_date.strftime('%d_%m_%Y')}.csv"
                        csv = df_three_digits_send[['เลข', 'ถูกบน', 'ถูกล่าง', 'รวมถูก', 'ใส่เลขส่งบน', 'ใส่เลขส่งล่าง', 'ใส่เลขส่งโต๊ด', 'ติดลบ']].to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                        st.download_button("💾 ดาวน์โหลด 3 ตัวส่ง", csv, file_name=filename, mime="text/csv")
                    st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("ไม่สามารถแยกข้อมูลจากโพยได้ กรุณาตรวจสอบรูปแบบโพย")

    elif menu == "เลขแยกส่งเจ้า":
        st.subheader("📤 เลขแยกส่งเจ้า")
        data = parse_tickets(tickets)
        if data:
            df = pd.DataFrame(data)
            owners = df["ลูกค้า"].unique()
            for owner in owners:
                owner_df = df[df["ลูกค้า"] == owner]
                if not owner_df.empty:
                    st.write(f"### เจ้ามือ: {owner}")
                    grouped = owner_df.groupby("เลข")[["บน", "ล่าง", "โต๊ด"]].sum().reset_index()
                    send_lines = []
                    for _, row in grouped.iterrows():
                        if row["บน"] > 0:
                            send_lines.append(f"{row['เลข']}={row['บน']}")
                        if row["ล่าง"] > 0:
                            send_lines.append(f"{row['เลข']}={row['ล่าง']}")
                        if row["โต๊ด"] > 0:
                            send_lines.append(f"{row['เลข']}t={row['โต๊ด']}")
                    send_text = ", ".join(send_lines)
                    st.code(send_text, language="text")
                    st.dataframe(grouped, use_container_width=True)

                    # ดาวน์โหลด CSV
                    filename = f"เลขส่งเจ้า_{owner}_{draw_date.strftime('%d_%m_%Y')}.csv"
                    csv = grouped.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button(f"💾 ดาวน์โหลดเลขส่งเจ้า {owner} เป็น CSV", csv, file_name=filename, mime="text/csv")
        else:
            st.warning("ไม่สามารถแยกข้อมูลจากโพยได้ กรุณาตรวจสอบรูปแบบโพย")

    elif menu == "แปลงเลข 6 ตัวกลับ":
        st.subheader("🔢 แปลงเลข 6 ตัวกลับ")
        data = parse_tickets(tickets)
        if data:
            df = pd.DataFrame(data)
            three_digit_numbers = df[df["เลข"].str.len() == 3]["เลข"].unique()
            if len(three_digit_numbers) > 0:
                perm_data = []
                for num in three_digit_numbers:
                    perms = generate_six_digit_permutations(num)
                    for perm in perms:
                        perm_data.append({"เลข 3 ตัว": num, "เลข 6 ตัวกลับ": perm})
                perm_df = pd.DataFrame(perm_data)
                st.dataframe(perm_df, use_container_width=True)

                # ดาวน์โหลด CSV
                filename = f"เลข6ตัวกลับ_{draw_date.strftime('%d_%m_%Y')}.csv"
                csv = perm_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                st.download_button("💾 ดาวน์โหลดเลข 6 ตัวกลับเป็น CSV", csv, file_name=filename, mime="text/csv")
            else:
                st.warning("ไม่พบเลข 3 ตัวในโพย")
        else:
            st.warning("ไม่สามารถแยกข้อมูลจากโพยได้ กรุณาตรวจสอบรูปแบบโพย")

    elif menu == "บันทึกยอด":
        st.subheader("💰 บันทึกยอด")
        data = parse_tickets(tickets)
        if data:
            df = pd.DataFrame(data)
            customer_summary = df.groupby("ลูกค้า")[["บน", "ล่าง", "โต๊ด"]].sum().reset_index()
            customer_summary['ยอดรวม'] = customer_summary['บน'] + customer_summary['ล่าง'] + customer_summary['โต๊ด']
            st.dataframe(customer_summary, use_container_width=True)

            # ดาวน์โหลด CSV
            filename = f"ยอดรวม_{draw_date.strftime('%d_%m_%Y')}.csv"
            csv = customer_summary.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("💾 ดาวน์โหลดยอดรวมเป็น CSV", csv, file_name=filename, mime="text/csv")
        else:
            st.warning("ไม่สามารถแยกข้อมูลจากโพยได้ กรุณาตรวจสอบรูปแบบโพย")
else:
    if menu != "แยกเลข":
        st.warning("กรุณาเก็บโพยในหน้า 'แยกเลข' ก่อนเพื่อดูข้อมูลในหน้านี้")