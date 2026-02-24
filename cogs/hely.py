import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone

# ═══════════════════════════════════════════════════════════════
# ข้อมูลคำสั่งทั้งหมด — อัปเดตครบทุกไฟล์
# ═══════════════════════════════════════════════════════════════
COMMANDS: list[dict] = [

    # ── verify.py ──────────────────────────────────────────────
    {
        "icon": "✅",
        "name": "/create_verify",
        "category": "✅ ยืนยันตัวตน",
        "short": "สร้างกล่องยืนยันตัวตน",
        "desc": "สร้างกล่องปุ่มให้สมาชิกกดรับ/คืนยศได้ด้วยตัวเอง ปุ่มจะไม่หายแม้บอทรีสตาร์ท เพราะระบบบันทึกข้อมูลลง verify_data.json อัตโนมัติ",
        "usage": (
            "1️⃣ พิมพ์ /create_verify แล้วกด Enter\n"
            "2️⃣ กรอก title → ชื่อหัวข้อกล่อง เช่น ✅ ยืนยันตัวตน\n"
            "3️⃣ กรอก description → ข้อความอธิบาย เช่น กดปุ่มเพื่อรับยศสมาชิก\n"
            "4️⃣ กรอก color → สีเป็นรหัส HEX เช่น 5865F2 (ไม่ต้องใส่ #)\n"
            "5️⃣ กรอก role → แท็กยศ @Member หรือ ID ยศ เช่น 123456789\n"
            "6️⃣ กรอก button_text → ข้อความบนปุ่ม เช่น 🎉 รับยศ\n"
            "7️⃣ (ไม่บังคับ) button_emoji → อิโมจิหน้าปุ่ม\n"
            "8️⃣ (ไม่บังคับ) image_url → URL รูปภาพประกอบ"
        ),
        "example": "/create_verify title:✅ ยืนยันตัวตน description:กดรับยศเพื่อเข้าถึงห้องต่างๆ color:57F287 role:@Member button_text:รับยศ",
        "permission": "ทุกคนใช้ได้",
        "note": (
            "• สมาชิกที่มียศอยู่แล้วกดปุ่มจะ ลบยศ ออก (toggle)\n"
            "• ปุ่มใช้ custom_id คงที่ จึงทำงานได้หลังบอทรีสตาร์ท\n"
            "• ถ้า verify_data.json ถูกลบ ปุ่มเก่าจะใช้ไม่ได้"
        ),
    },

    # ── admin.py ───────────────────────────────────────────────
    {
        "icon": "📋",
        "name": "/logs_channel",
        "category": "🛡️ การจัดการ",
        "short": "ตั้งค่าห้อง Logs",
        "desc": "กำหนดห้องที่บอทจะส่งรายงานการกระทำของแอดมินทุกครั้ง ได้แก่ แบน ปลดแบน timeout ปลด timeout และเตะสมาชิก",
        "usage": (
            "1️⃣ พิมพ์ /logs_channel แล้วกด Enter\n"
            "2️⃣ กรอก channel → แท็กห้อง #mod-logs หรือ ID ห้อง\n"
            "3️⃣ กด Enter → บอทจะยืนยันการตั้งค่าเฉพาะคุณเห็น"
        ),
        "example": "/logs_channel channel:#mod-logs",
        "permission": "เจ้าของเซิร์ฟเวอร์เท่านั้น",
        "note": (
            "• ต้องตั้งค่าก่อน จึงจะมี log บันทึกทุกครั้งที่ใช้คำสั่ง admin\n"
            "• ถ้าไม่ตั้งค่า คำสั่ง admin ยังทำงานได้แต่จะไม่มี log"
        ),
    },
    {
        "icon": "👑",
        "name": "/add_admin",
        "category": "🛡️ การจัดการ",
        "short": "เพิ่มสิทธิ์ Admin",
        "desc": "มอบยศ Admin ให้สมาชิก และบันทึกยศนั้นลงระบบ เพื่อให้สมาชิกที่ได้รับสามารถใช้คำสั่ง admin ต่างๆ ได้",
        "usage": (
            "1️⃣ พิมพ์ /add_admin แล้วกด Enter\n"
            "2️⃣ กรอก member → แท็กสมาชิก @John หรือ ID เช่น 123456789\n"
            "3️⃣ กรอก role → แท็กยศ @Admin ที่ต้องการมอบให้\n"
            "4️⃣ กด Enter → บอทจะมอบยศและส่ง Embed ยืนยัน\n"
            "5️⃣ ข้อความจะลบตัวเองใน 30 วินาที"
        ),
        "example": "/add_admin member:@John role:@Admin",
        "permission": "เจ้าของเซิร์ฟเวอร์เท่านั้น",
        "note": (
            "• ยศที่มอบจะถูกจดจำในระบบ ทำให้ผู้รับใช้คำสั่ง Admin ได้\n"
            "• บันทึกใน logs_channel อัตโนมัติ (ถ้าตั้งค่าไว้)"
        ),
    },
    {
        "icon": "🚫",
        "name": "/remove_admin",
        "category": "🛡️ การจัดการ",
        "short": "ลบสิทธิ์ Admin",
        "desc": "ถอดยศ Admin ออกจากสมาชิก พร้อมระบุเหตุผล และบันทึก log การกระทำ",
        "usage": (
            "1️⃣ พิมพ์ /remove_admin แล้วกด Enter\n"
            "2️⃣ กรอก member → แท็กสมาชิก @John ที่ต้องการถอดยศ\n"
            "3️⃣ กรอก role → แท็กยศ @Admin ที่ต้องการลบออก\n"
            "4️⃣ กรอก reason → เหตุผล เช่น ลาออกจากทีม\n"
            "5️⃣ กด Enter → บอทลบยศและส่ง Embed แจ้งผล\n"
            "6️⃣ ข้อความลบตัวเองใน 30 วินาที"
        ),
        "example": "/remove_admin member:@John role:@Admin reason:ลาออกจากทีม",
        "permission": "เจ้าของเซิร์ฟเวอร์เท่านั้น",
        "note": "บันทึกใน logs_channel อัตโนมัติ (ถ้าตั้งค่าไว้)",
    },
    {
        "icon": "🔨",
        "name": "/ban_add",
        "category": "🛡️ การจัดการ",
        "short": "แบนสมาชิก",
        "desc": "แบนสมาชิกออกจากเซิร์ฟเวอร์อย่างถาวร สมาชิกจะไม่สามารถเข้าเซิร์ฟได้จนกว่าจะถูกปลดแบน",
        "usage": (
            "1️⃣ พิมพ์ /ban_add แล้วกด Enter\n"
            "2️⃣ กรอก member → แท็กสมาชิก @Spammer ที่ต้องการแบน\n"
            "3️⃣ กรอก reason → เหตุผลการแบน เช่น สแปมในช่องทั่วไป\n"
            "4️⃣ กด Enter → บอทแบนทันทีและส่ง Embed ยืนยัน\n"
            "5️⃣ ข้อความลบตัวเองใน 60 วินาที"
        ),
        "example": "/ban_add member:@Spammer reason:สแปมซ้ำๆ ไม่หยุด",
        "permission": "Admin และเจ้าของเซิร์ฟเวอร์",
        "note": (
            "• ใช้ /ban_remove เพื่อปลดแบนภายหลัง\n"
            "• บันทึกใน logs_channel อัตโนมัติ"
        ),
    },
    {
        "icon": "🔓",
        "name": "/ban_remove",
        "category": "🛡️ การจัดการ",
        "short": "ปลดแบนสมาชิก",
        "desc": "ปลดแบนสมาชิกที่เคยถูกแบน ให้สามารถเข้าเซิร์ฟได้อีกครั้งผ่านลิงก์เชิญ",
        "usage": (
            "1️⃣ หา User ID ของสมาชิกที่ถูกแบน\n"
            "   วิธีหา ID: เปิด Discord Developer Mode → คลิกขวาที่ชื่อ → Copy ID\n"
            "2️⃣ พิมพ์ /ban_remove แล้วกด Enter\n"
            "3️⃣ กรอก user_id → ตัวเลข ID เช่น 123456789012345678\n"
            "4️⃣ กรอก reason → เหตุผลการปลดแบน เช่น ขอโอกาสใหม่\n"
            "5️⃣ กด Enter → บอทปลดแบนทันที"
        ),
        "example": "/ban_remove user_id:123456789012345678 reason:ขอโอกาสและสัญญาว่าจะปฏิบัติตามกฎ",
        "permission": "Admin และเจ้าของเซิร์ฟเวอร์",
        "note": "ต้องใช้ User ID (ตัวเลข) เพราะสมาชิกถูกแบนแล้ว ไม่สามารถ @mention ได้",
    },
    {
        "icon": "⏰",
        "name": "/timeout_add",
        "category": "🛡️ การจัดการ",
        "short": "ลงโทษ Timeout",
        "desc": "ทำให้สมาชิกพิมพ์ข้อความและเข้าร่วมช่องเสียงไม่ได้ชั่วคราว มีตัวเลือกระยะเวลาให้เลือก 9 ระดับ",
        "usage": (
            "1️⃣ พิมพ์ /timeout_add แล้วกด Enter\n"
            "2️⃣ กรอก member → แท็กสมาชิก @Noisy ที่ต้องการลงโทษ\n"
            "3️⃣ เลือก duration → คลิกเมนูแล้วเลือกระยะเวลา\n"
            "   ตัวเลือก: 5นาที / 10นาที / 30นาที / 1ชม / 6ชม / 12ชม / 1วัน / 3วัน / 7วัน\n"
            "4️⃣ กรอก reason → เหตุผล เช่น พูดจาไม่เหมาะสม\n"
            "5️⃣ กด Enter → บอทลงโทษทันที แท็กสมาชิกให้รู้ตัว"
        ),
        "example": "/timeout_add member:@Noisy duration:1 ชั่วโมง reason:ส่งเสียงรบกวนในช่องเสียง",
        "permission": "Admin และเจ้าของเซิร์ฟเวอร์",
        "note": "บันทึกใน logs_channel อัตโนมัติ",
    },
    {
        "icon": "🔄",
        "name": "/timeout_remove",
        "category": "🛡️ การจัดการ",
        "short": "ปลด Timeout",
        "desc": "ยกเลิกโทษ timeout ก่อนครบกำหนด ให้สมาชิกกลับมาพิมพ์ข้อความและเข้าช่องเสียงได้ทันที",
        "usage": (
            "1️⃣ พิมพ์ /timeout_remove แล้วกด Enter\n"
            "2️⃣ กรอก member → แท็กสมาชิก @Noisy ที่ต้องการปลดโทษ\n"
            "3️⃣ กรอก reason → เหตุผลการปลด เช่น ขอโทษแล้วและรับปากว่าจะแก้ไข\n"
            "4️⃣ กด Enter → บอทปลดโทษและส่ง Embed ยืนยัน"
        ),
        "example": "/timeout_remove member:@Noisy reason:ขอโทษแล้วและรับปากว่าจะปรับปรุง",
        "permission": "Admin และเจ้าของเซิร์ฟเวอร์",
        "note": "บันทึกใน logs_channel อัตโนมัติ",
    },
    {
        "icon": "👢",
        "name": "/kick_add",
        "category": "🛡️ การจัดการ",
        "short": "เตะสมาชิก",
        "desc": "เตะสมาชิกออกจากเซิร์ฟ สมาชิกสามารถกลับเข้าได้ใหม่ด้วยลิงก์เชิญ (ต่างจากแบน)",
        "usage": (
            "1️⃣ พิมพ์ /kick_add แล้วกด Enter\n"
            "2️⃣ กรอก member → แท็กสมาชิก @Toxic ที่ต้องการเตะ\n"
            "3️⃣ กรอก reason → เหตุผล เช่น พูดจาไม่เหมาะสมกับสมาชิกคนอื่น\n"
            "4️⃣ กด Enter → บอทเตะทันทีและส่ง Embed ยืนยัน"
        ),
        "example": "/kick_add member:@Toxic reason:พูดจาไม่เหมาะสมกับสมาชิกคนอื่น",
        "permission": "Admin และเจ้าของเซิร์ฟเวอร์",
        "note": (
            "• สมาชิกที่ถูกเตะยังสามารถกลับเข้าเซิร์ฟได้ด้วยลิงก์เชิญ\n"
            "• ถ้าต้องการบล็อกถาวร ใช้ /ban_add แทน"
        ),
    },
    {
        "icon": "📢",
        "name": "/announce_channel",
        "category": "📢 ประกาศ",
        "short": "ประกาศในนามบอท",
        "desc": "ส่งข้อความประกาศในนามบอท (ไม่แสดงชื่อผู้ส่ง) รองรับการแท็กยศและแนบรูปภาพ",
        "usage": (
            "1️⃣ พิมพ์ /announce_channel แล้วกด Enter\n"
            "2️⃣ กรอก channel → แท็กห้อง #ประกาศ ที่ต้องการส่ง\n"
            "3️⃣ กรอก message → ข้อความที่ต้องการประกาศ\n"
            "4️⃣ (ไม่บังคับ) กรอก role → @everyone หรือยศที่ต้องการ mention\n"
            "5️⃣ (ไม่บังคับ) กรอก image_url → ลิงก์รูปภาพ เช่น https://i.imgur.com/xxx.png\n"
            "6️⃣ กด Enter → บอทส่งประกาศ คุณจะเห็นข้อความยืนยันเฉพาะตัวเอง"
        ),
        "example": "/announce_channel channel:#ประกาศ message:🎉 กิจกรรมพิเศษคืนนี้ 20.00น. อย่าลืมนะครับ role:@everyone",
        "permission": "Admin และเจ้าของเซิร์ฟเวอร์",
        "note": "ชื่อผู้ส่งจะไม่ปรากฏ ข้อความจะดูเหมือนบอทส่งเอง",
    },

    # ── add_role.py ─────────────────────────────────────────────
    {
        "icon": "🎭",
        "name": "/add_role",
        "category": "🔧 ระบบ Owner",
        "short": "ให้ยศข้ามเซิร์ฟ",
        "desc": "ให้ยศแก่สมาชิกในเซิร์ฟเวอร์ใดก็ได้ที่บอทอยู่ มีหน้ายืนยันก่อนดำเนินการจริง",
        "usage": (
            "1️⃣ ใช้ /list_servers ก่อนเพื่อดูชื่อเซิร์ฟที่บอทอยู่\n"
            "2️⃣ พิมพ์ /add_role แล้วกด Enter\n"
            "3️⃣ กรอก server → ชื่อเซิร์ฟ (บางส่วนก็ได้) หรือ ID เซิร์ฟ\n"
            "4️⃣ กรอก member → ชื่อ / username / ID ของสมาชิก\n"
            "5️⃣ กรอก role → ชื่อยศ / ID ยศ ที่ต้องการมอบ\n"
            "6️⃣ กด Enter → จะมีหน้ายืนยันโชว์ขึ้นมาเฉพาะคุณเห็น\n"
            "7️⃣ กด ✅ ยืนยันให้ยศ เพื่อดำเนินการ หรือ ❌ ยกเลิก\n\n"
            "📌 รองรับ Prefix ด้วย:\n"
            "`!add_role <เซิร์ฟ> <สมาชิก> <ยศ>`\n"
            "`!giverole` / `!addrole` ก็ใช้ได้เช่นกัน"
        ),
        "example": "/add_role server:MyServer member:123456789 role:Member",
        "permission": "เจ้าของบอทเท่านั้น",
        "note": (
            "• ค้นหาสมาชิกได้ทั้ง ID, ชื่อ, display name หรือ @mention\n"
            "• ถ้าไม่พบสมาชิก ให้เปิด Server Members Intent ใน Developer Portal"
        ),
    },
    {
        "icon": "📊",
        "name": "/list_servers",
        "category": "🔧 ระบบ Owner",
        "short": "ดูรายชื่อเซิร์ฟ",
        "desc": "แสดงรายชื่อเซิร์ฟเวอร์ทั้งหมดที่บอทอยู่ พร้อม ID และจำนวนสมาชิก เรียงจากมากไปน้อย",
        "usage": (
            "1️⃣ พิมพ์ /list_servers แล้วกด Enter\n"
            "2️⃣ บอทจะส่ง Embed รายชื่อเซิร์ฟ เฉพาะคุณเห็น\n"
            "3️⃣ คัดลอก ชื่อ หรือ ID เซิร์ฟที่ต้องการ\n"
            "4️⃣ นำไปใช้กับคำสั่ง /add_role ต่อได้เลย"
        ),
        "example": "/list_servers",
        "permission": "เจ้าของบอทเท่านั้น",
        "note": "แสดงสูงสุด 25 เซิร์ฟแรก เรียงตามจำนวนสมาชิกมากสุด",
    },

    # ── clear.py ────────────────────────────────────────────────
    {
        "icon": "🗑️",
        "name": "!clear",
        "category": "🔧 ระบบ Owner",
        "short": "ลบข้อความจำนวนมาก",
        "desc": "ลบข้อความในช่องสนทนาได้สูงสุด 10,000 ข้อความพร้อมกัน พร้อมรายงานสถิติเวลาและความเร็ว",
        "usage": (
            "1️⃣ ไปที่ช่องที่ต้องการลบข้อความ\n"
            "2️⃣ พิมพ์ !clear ตามด้วยจำนวน เช่น !clear 100\n"
            "3️⃣ กด Enter → บอทแจ้งว่ากำลังดำเนินการ (Embed สีเหลือง)\n"
            "4️⃣ รอสักครู่จนบอทลบเสร็จ\n"
            "5️⃣ บอทส่งรายงานสถิติ (จำนวน, เวลา, ความเร็ว)\n"
            "6️⃣ รายงานจะลบตัวเองใน 60 วินาที"
        ),
        "example": "!clear 500",
        "permission": "Administrator และเจ้าของเซิร์ฟเวอร์",
        "note": (
            "• จำกัดสูงสุด 10,000 ข้อความต่อครั้ง\n"
            "• ข้อความที่เก่ากว่า 14 วันลบแบบ bulk ไม่ได้ (Discord จำกัด)\n"
            "• รายงานลบตัวเองใน 60 วินาที"
        ),
    },

    # ── userinfo.py ─────────────────────────────────────────────
    {
        "icon": "🔍",
        "name": "/userinfo",
        "category": "📋 ข้อมูล",
        "short": "ดูข้อมูลสมาชิก",
        "desc": "แสดงข้อมูลสมาชิกแบบละเอียดครบถ้วน ได้แก่ ชื่อ, ID, badge Discord, วันสร้างบัญชี, วันเข้าร่วมเซิร์ฟ, ยศทั้งหมด, สถานะยืนยันตัวตน และสิทธิ์",
        "usage": (
            "ดูข้อมูลตัวเอง:\n"
            "1️⃣ พิมพ์ /userinfo แล้วกด Enter ได้เลย (ไม่ต้องระบุ member)\n\n"
            "ดูข้อมูลสมาชิกคนอื่น:\n"
            "1️⃣ พิมพ์ /userinfo แล้วกด Enter\n"
            "2️⃣ กรอก member → แท็กสมาชิก @John หรือ ID\n"
            "3️⃣ กด Enter → Embed ข้อมูลจะแสดงในช่องให้ทุกคนเห็น"
        ),
        "example": "/userinfo member:@John",
        "permission": "ทุกคนใช้ได้",
        "note": (
            "• สี Embed ตามยศสูงสุดของสมาชิก\n"
            "• แสดง badge Discord (ถ้ามี) เช่น Early Supporter, Active Developer\n"
            "• วันที่แสดงเป็น พ.ศ. พร้อมระบุว่ากี่วัน/เดือน/ปีที่แล้ว"
        ),
    },
]

# ── จัดกลุ่มตาม category ─────────────────────────────────────
CATEGORIES: dict[str, list[dict]] = {}
for _c in COMMANDS:
    CATEGORIES.setdefault(_c["category"], []).append(_c)

CATEGORY_COLORS: dict[str, int] = {
    "✅ ยืนยันตัวตน": 0x57F287,
    "🛡️ การจัดการ":   0xED4245,
    "📢 ประกาศ":       0x5865F2,
    "🔧 ระบบ Owner":   0xFEE75C,
    "📋 ข้อมูล":        0x00B0F4,
}


# ═══════════════════════════════════════════════════════════════
# สร้าง Embeds
# ═══════════════════════════════════════════════════════════════

def _home_embed(bot_user: discord.ClientUser, user: discord.User | discord.Member) -> discord.Embed:
    lines = "\n".join(
        f"{cat}  ─  **{len(cmds)} คำสั่ง**"
        for cat, cmds in CATEGORIES.items()
    )
    embed = discord.Embed(
        title="📚 คู่มือการใช้งานบอท",
        description=(
            "ใช้ **◀️ ▶️** เพื่อเลื่อนดูคำสั่งทีละตัว\n"
            "กด **📘 วิธีใช้ละเอียด** เพื่อดูคำอธิบายแบบจูงมือเดิน\n\n"
            f"{lines}\n\n"
            f"**รวม {len(COMMANDS)} คำสั่ง**"
        ),
        color=0x5865F2,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_thumbnail(url=bot_user.display_avatar.url)
    embed.set_footer(
        text=f"ใช้โดย {user.name}",
        icon_url=user.display_avatar.url,
    )
    return embed


def _cmd_embed(cmd: dict, user: discord.User | discord.Member) -> discord.Embed:
    """Embed หน้าหลัก — ไม่มีวิธีใช้ / ตัวอย่าง / สิทธิ์"""
    color = CATEGORY_COLORS.get(cmd["category"], 0x5865F2)
    embed = discord.Embed(
        title=f"{cmd['icon']}  {cmd['name']}",
        description=f"**หมวดหมู่:** {cmd['category']}\n\n{cmd['desc']}",
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(
        text=f"ใช้โดย {user.name}  •  กด 📘 เพื่อดูวิธีใช้ละเอียด",
        icon_url=user.display_avatar.url,
    )
    return embed


def _detail_embed(cmd: dict) -> discord.Embed:
    """Embed ละเอียด — ephemeral เฉพาะผู้กดเห็น"""
    color = CATEGORY_COLORS.get(cmd["category"], 0x5865F2)
    embed = discord.Embed(
        title=f"📘  {cmd['icon']}  {cmd['name']}",
        description=f"**หมวดหมู่:** {cmd['category']}\n\n{cmd['desc']}",
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    embed.add_field(name="📋 วิธีใช้ทีละขั้นตอน", value=cmd["usage"],      inline=False)
    embed.add_field(name="📌 ตัวอย่าง",            value=f"`{cmd['example']}`", inline=False)
    embed.add_field(name="🔑 สิทธิ์ที่ต้องการ",    value=cmd["permission"], inline=False)
    if cmd.get("note"):
        embed.add_field(name="📎 หมายเหตุสำคัญ", value=cmd["note"], inline=False)
    embed.set_footer(text="ข้อมูลนี้เห็นเฉพาะคุณเท่านั้น")
    return embed


# ═══════════════════════════════════════════════════════════════
# View ปุ่มควบคุม
# ═══════════════════════════════════════════════════════════════

class HelpView(discord.ui.View):
    def __init__(
        self,
        embeds: list[discord.Embed],
        cmd_map: list[dict | None],
        author_id: int,
    ) -> None:
        super().__init__(timeout=300)
        self.embeds    = embeds
        self.cmd_map   = cmd_map    # None = หน้าแรก
        self.page      = 0
        self.author_id = author_id
        self._sync()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ คำสั่งนี้เป็นของคนที่เปิดเท่านั้น", ephemeral=True
            )
            return False
        return True

    def _sync(self) -> None:
        total = len(self.embeds)
        self.btn_back.disabled   = (self.page == 0)
        self.btn_next.disabled   = (self.page == total - 1)
        self.btn_home.label      = f"🏠  {self.page + 1}/{total}"
        self.btn_detail.disabled = (self.page == 0)

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary, row=0)
    async def btn_back(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        if self.page > 0:
            self.page -= 1
            self._sync()
            await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    @discord.ui.button(label="🏠  1/1", style=discord.ButtonStyle.success, row=0)
    async def btn_home(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        self.page = 0
        self._sync()
        await interaction.response.edit_message(embed=self.embeds[0], view=self)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.primary, row=0)
    async def btn_next(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        if self.page < len(self.embeds) - 1:
            self.page += 1
            self._sync()
            await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    @discord.ui.button(label="📘 วิธีใช้ละเอียด", style=discord.ButtonStyle.blurple, row=1)
    async def btn_detail(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        cmd = self.cmd_map[self.page]
        if cmd is None:
            await interaction.response.defer()
            return
        await interaction.response.send_message(embed=_detail_embed(cmd), ephemeral=True)

    @discord.ui.button(label="❌ ปิด", style=discord.ButtonStyle.danger, row=1)
    async def btn_close(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await interaction.message.delete()
        self.stop()

    async def on_timeout(self) -> None:
        self.clear_items()


# ═══════════════════════════════════════════════════════════════
# COG
# ═══════════════════════════════════════════════════════════════

class Hely(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="help", description="📖 แสดงคู่มือการใช้งานและคำสั่งทั้งหมด")
    async def hely(self, interaction: discord.Interaction) -> None:
        user = interaction.user

        embeds:  list[discord.Embed] = [_home_embed(self.bot.user, user)]
        cmd_map: list[dict | None]   = [None]

        for cmd in COMMANDS:
            embeds.append(_cmd_embed(cmd, user))
            cmd_map.append(cmd)

        view = HelpView(embeds, cmd_map, user.id)
        await interaction.response.send_message(embed=embeds[0], view=view, ephemeral=True)


# ═══════════════════════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════════════════════

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Hely(bot))