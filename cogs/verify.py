import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# ================= จัดการข้อมูล =================
VERIFY_FILE = "verify_data.json"

def load_data():
    if os.path.exists(VERIFY_FILE):
        try:
            with open(VERIFY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_data(data):
    with open(VERIFY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ================= VIEW =================
class VerifyView(discord.ui.View):
    def __init__(self, role: discord.Role, button_text: str, button_emoji: str | None):
        super().__init__(timeout=None)  # ✅ ไม่หมดอายุ
        self.role = role

        self.verify_button = discord.ui.Button(
            label=button_text,
            emoji=button_emoji,
            style=discord.ButtonStyle.success,
            custom_id="verify_role"  # ✅ custom_id คงที่ ทำให้ปุ่มทำงานได้หลัง restart
        )
        self.verify_button.callback = self.verify_callback
        self.add_item(self.verify_button)

    async def verify_callback(self, interaction: discord.Interaction):
        member = interaction.user

        # ✅ ดึง role จาก JSON (แทนการใช้ self.role ที่หายหลัง restart)
        data = load_data()
        message_id = str(interaction.message.id)

        if message_id in data:
            role = interaction.guild.get_role(data[message_id]["role_id"])
        else:
            role = self.role  # fallback ถ้าไม่มีในไฟล์

        if not role:
            return await interaction.response.send_message(
                "❌ ไม่พบยศ กรุณาแจ้งแอดมิน",
                ephemeral=True
            )

        if role in member.roles:
            await member.remove_roles(role)
            embed = discord.Embed(
                title="`🪣 ลบ Role สำเร็จ`",
                description=f"> ยศที่ถูกลบ: {role.mention}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await member.add_roles(role)
            embed = discord.Embed(
                title="`✅ ได้รับ Role สำเร็จ`",
                description=f"> ยศที่ได้รับ: {role.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

# ✅ Persistent View แยกต่างหาก สำหรับโหลดตอน restart
class PersistentVerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="ยืนยันตัวตน",
        style=discord.ButtonStyle.success,
        custom_id="verify_role"  # ✅ ต้องตรงกับ VerifyView
    )
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.user
        data = load_data()
        message_id = str(interaction.message.id)

        if message_id not in data:
            return await interaction.response.send_message(
                "❌ ไม่พบข้อมูล กรุณาแจ้งแอดมิน",
                ephemeral=True
            )

        role = interaction.guild.get_role(data[message_id]["role_id"])

        if not role:
            return await interaction.response.send_message(
                "❌ ไม่พบยศ กรุณาแจ้งแอดมิน",
                ephemeral=True
            )

        if role in member.roles:
            await member.remove_roles(role)
            embed = discord.Embed(
                title="`🪣 ลบ Role สำเร็จ`",
                description=f"> ยศที่ถูกลบ: {role.mention}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await member.add_roles(role)
            embed = discord.Embed(
                title="`✅ ได้รับ Role สำเร็จ`",
                description=f"> ยศที่ได้รับ: {role.mention}",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

# ================= COG =================
class VerifyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # ✅ โหลด persistent view ตอนบอทเริ่มทำงาน ปุ่มเก่าๆ จะใช้งานได้ทันที
        self.bot.add_view(PersistentVerifyView())

    @app_commands.command(
        name="create_verify",
        description="สร้างกล่องยืนยันตัวตน (สาธารณะ)"
    )
    @app_commands.describe(
        title="หัวข้อ Embed",
        description="ข้อความใน Embed",
        color="สี Embed (hex เช่น ff0000)",
        role="ยศที่จะให้เมื่อกดปุ่ม",
        button_text="ข้อความบนปุ่ม",
        button_emoji="emoji บนปุ่ม (เว้นว่างได้)",
        image_url="ลิงก์รูป (เว้นว่างได้)"
    )
    async def verify_create(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        color: str,
        role: discord.Role,
        button_text: str,
        button_emoji: str | None = None,
        image_url: str | None = None
    ):
        embed_color = discord.Color(int(color.replace("#", ""), 16))
        embed = discord.Embed(
            title=title,
            description=description,
            color=embed_color
        )

        if image_url:
            embed.set_image(url=image_url)

        view = VerifyView(role, button_text, button_emoji)

        await interaction.response.send_message(
            "**✅ สร้างกล่องยืนยันตัวตนเรียบร้อย**",
            ephemeral=True
        )

        # ✅ บันทึก message id + role id ลงไฟล์
        message = await interaction.channel.send(embed=embed, view=view)
        data = load_data()
        data[str(message.id)] = {
            "role_id": role.id,
            "guild_id": interaction.guild.id,
            "channel_id": interaction.channel.id
        }
        save_data(data)

# ================= SETUP =================
async def setup(bot: commands.Bot):
    await bot.add_cog(VerifyCog(bot))