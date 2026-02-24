import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional

# ═══════════════════════════════════════════════════════════════
# STORAGE ต่อ Guild
# ═══════════════════════════════════════════════════════════════
guild_data = {}


def get_data(guild_id: int) -> dict:
    """ดึงข้อมูล guild พร้อมสร้างถ้ายังไม่มี"""
    if guild_id not in guild_data:
        guild_data[guild_id] = {
            "admin_roles": [],
            "logs_channel": None
        }
    return guild_data[guild_id]


# ═══════════════════════════════════════════════════════════════
# ตรวจสิทธิ์
# ═══════════════════════════════════════════════════════════════

def is_owner_or_admin(member: discord.Member) -> bool:
    """ตรวจสอบว่าเป็น owner หรือมียศ admin หรือไม่"""
    data = get_data(member.guild.id)

    if member.guild.owner_id == member.id:
        return True

    for role in member.roles:
        if role.id in data["admin_roles"]:
            return True

    return False


def check_role_hierarchy(
        guild: discord.Guild,
        executor: discord.Member,
        target: discord.Member,
        bot_member: discord.Member,
) -> tuple[bool, Optional[str]]:
    """
    ตรวจสอบลำดับยศก่อนดำเนินการ moderation

    Returns:
        (True, None) ถ้าผ่าน
        (False, error_message) ถ้าไม่ผ่า�
    """
    # ห้ามจัดการ owner
    if target.id == guild.owner_id:
        return False, "❌ ไม่สามารถดำเนินการกับเจ้าของเซิร์ฟเวอร์ได้"

    # ห้ามจัดการตัวเอง
    if executor.id == target.id:
        return False, "❌ ไม่สามารถดำเนินการกับตัวเองได้"

    # ห้ามจัดการถ้า target role สูงกว่าหรือเท่ากับ executor
    if executor.id != guild.owner_id:  # owner ยกเว้น
        if target.top_role >= executor.top_role:
            return False, f"❌ ไม่สามารถดำเนินการกับ {target.mention} ได้\nเพราะยศของเขาสูงกว่าหรือเท่ากับคุณ"

    # ห้ามจัดการถ้า bot role ต่ำกว่า target
    if target.top_role >= bot_member.top_role:
        return False, f"❌ บอทไม่สามารถดำเนินการกับ {target.mention} ได้\nเพราะยศของเขาสูงกว่าหรือเท่ากับบอท"

    return True, None


# ═══════════════════════════════════════════════════════════════
# Embed Templates
# ═══════════════════════════════════════════════════════════════

def create_error_embed(message: str, title: str = "❌ เกิดข้อผิดพลาด") -> discord.Embed:
    """สร้าง Error Embed มาตรฐาน"""
    embed = discord.Embed(
        title=title,
        description=message,
        color=discord.Color.red(),
        timestamp=datetime.now(timezone.utc)
    )
    return embed


def create_success_embed(
        title: str,
        fields: list[tuple[str, str]],
        thumbnail_url: Optional[str] = None,
        footer_text: str = "ระบบจัดการเซิร์ฟเวอร์",
) -> discord.Embed:
    """สร้าง Success Embed มาตรฐาน"""
    embed = discord.Embed(
        title=title,
        color=discord.Color.green(),
        timestamp=datetime.now(timezone.utc)
    )

    for name, value in fields:
        embed.add_field(name=name, value=value, inline=False)

    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)

    embed.set_footer(text=footer_text)
    return embed


# ═══════════════════════════════════════════════════════════════
# ADMIN SYSTEM
# ═══════════════════════════════════════════════════════════════

class AdminSystem(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ───────────────────────────────────────────────────────────
    # LOG SYSTEM
    # ───────────────────────────────────────────────────────────

    async def send_log(self, guild: discord.Guild, embed: discord.Embed) -> None:
        """ส่ง log ไปยัง logs_channel (ถ้าตั้งค่าไว้)"""
        data = get_data(guild.id)

        if not data["logs_channel"]:
            return

        channel = guild.get_channel(data["logs_channel"])

        # Fallback: ถ้าไม่เจอใน cache ให้ลอง fetch
        if not channel:
            try:
                channel = await guild.fetch_channel(data["logs_channel"])
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                return

        # ส่ง log
        try:
            await channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            pass  # ถ้าส่งไม่ได้ก็ข้ามไป

    # ───────────────────────────────────────────────────────────
    # ตั้งค่าห้อง Logs
    # ───────────────────────────────────────────────────────────

    @app_commands.command(
        name="logs_channel",
        description="ตั้งค่าห้องบันทึกการกระทำ (แบน, ปลดแบน, หมดเวลา, ปลดหมดเวลา, เตะ)"
    )
    @app_commands.describe(
        channel="เลือกห้องที่จะใช้เป็นห้องบันทึก Logs"
    )
    async def logs_channel(
            self,
            interaction: discord.Interaction,
            channel: discord.TextChannel
    ):
        # ป้องกันใช้ใน DM
        if not interaction.guild:
            return await interaction.response.send_message(
                embed=create_error_embed("คำสั่งนี้ใช้ได้เฉพาะในเซิร์ฟเวอร์เท่านั้น"),
                ephemeral=True
            )

        # ตรวจสอบสิทธิ์
        if interaction.guild.owner_id != interaction.user.id:
            return await interaction.response.send_message(
                "**❌ เฉพาะเจ้าของเซิฟ**",
                ephemeral=True
            )

        # ตั้งค่า
        data = get_data(interaction.guild.id)
        data["logs_channel"] = channel.id

        await interaction.response.send_message(
            f"✅ ตั้งค่า Logs เป็น {channel.mention} แล้ว",
            ephemeral=True
        )

    # ───────────────────────────────────────────────────────────
    # ADD ADMIN ROLE
    # ───────────────────────────────────────────────────────────

    @app_commands.command(
        name="add_admin",
        description="เพิ่ม Admin(เฉพาะServrowner)"
    )
    @app_commands.describe(
        member="เลือกสมาชิกที่ต้องการให้ยศแอดมิน",
        role="เลือกยศที่ต้องการมอบให้สมาชิก"
    )
    async def add_admin(
            self,
            interaction: discord.Interaction,
            member: discord.Member,
            role: discord.Role
    ):
        # ป้องกันใช้ใน DM
        if not interaction.guild:
            return await interaction.response.send_message(
                embed=create_error_embed("คำสั่งนี้ใช้ได้เฉพาะในเซิร์ฟเวอร์เท่านั้น"),
                ephemeral=True
            )

        # ตรวจสอบสิทธิ์
        if interaction.guild.owner_id != interaction.user.id:
            return await interaction.response.send_message(
                "**❌ คำสั่งนี้เฉพาะเจ้าของเซิฟ**",
                ephemeral=True
            )

        # ตรวจสอบว่าบอทให้ role นี้ได้หรือไม่
        if role >= interaction.guild.me.top_role:
            return await interaction.response.send_message(
                embed=create_error_embed(
                    f"บอทไม่สามารถให้ยศ {role.mention} ได้\nเพราะยศนี้สูงกว่าหรือเท่ากับยศของบอท"
                ),
                ephemeral=True
            )

        # บันทึกยศลงระบบ admin
        data = get_data(interaction.guild.id)
        if role.id not in data["admin_roles"]:
            data["admin_roles"].append(role.id)

        # ให้ role
        try:
            await member.add_roles(role, reason=f"เพิ่ม Admin โดย {interaction.user}")
        except discord.Forbidden:
            return await interaction.response.send_message(
                embed=create_error_embed("บอทไม่มีสิทธิ์ให้ยศนี้"),
                ephemeral=True
            )
        except discord.HTTPException as e:
            return await interaction.response.send_message(
                embed=create_error_embed(f"เกิดข้อผิดพลาด: {str(e)}"),
                ephemeral=True
            )

        # สร้าง Embed
        embed = discord.Embed(
            title=f"**<:Shied_staff:1471131608148086805> เพิ่ม Admin สำเร็จ**",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )

        embed.add_field(
            name="รายละเอียด",
            value=(
                f"<a:emoji_220:1471131868782133381>**คุณได้รับ Role Admin สำเร็จ\n**"
                f"<:Regular:1471133591336652831>**รับได้รับRole**: {member.mention}\n"
                f"<a:gif22:1471132615544274987>**Role**: {role.mention}\n"
                f"<:BillingManager3:1471132936551010385>**ให้โดย**: {interaction.user.mention}"
            ),
            inline=False
        )

        embed.set_footer(text="ระบบจัดการเซิร์ฟเวอร์")

        await interaction.response.send_message(
            content=member.mention,
            embed=embed
        )

        await self.send_log(interaction.guild, embed)

        # ลบข้อความใน 30 วินาที
        await asyncio.sleep(30)
        try:
            await interaction.delete_original_response()
        except (discord.NotFound, discord.HTTPException):
            pass

    # ───────────────────────────────────────────────────────────
    # REMOVE ADMIN ROLE
    # ───────────────────────────────────────────────────────────

    @app_commands.command(
        name="remove_admin",
        description="ลบ Admin(เฉพาะServrowner)"
    )
    @app_commands.describe(
        member="เลือกสมาชิกที่ต้องการลบยศแอดมิน",
        role="เลือกยศที่ต้องการลบออกจากสมาชิก",
        reason="เหตุผลในการลบ Admin"
    )
    async def remove_admin(
            self,
            interaction: discord.Interaction,
            member: discord.Member,
            role: discord.Role,
            reason: str
    ):
        # ป้องกันใช้ใน DM
        if not interaction.guild:
            return await interaction.response.send_message(
                embed=create_error_embed("คำสั่งนี้ใช้ได้เฉพาะในเซิร์ฟเวอร์เท่านั้น"),
                ephemeral=True
            )

        # ตรวจสอบสิทธิ์
        if interaction.guild.owner_id != interaction.user.id:
            return await interaction.response.send_message(
                "**❌ คำสั่งนี้เฉพาะเจ้าของเซิฟ**",
                ephemeral=True
            )

        # ลบ role
        try:
            await member.remove_roles(role, reason=reason)
        except discord.Forbidden:
            return await interaction.response.send_message(
                embed=create_error_embed("บอทไม่มีสิทธิ์ลบยศนี้"),
                ephemeral=True
            )
        except discord.HTTPException as e:
            return await interaction.response.send_message(
                embed=create_error_embed(f"เกิดข้อผิดพลาด: {str(e)}"),
                ephemeral=True
            )

        # สร้าง Embed
        embed = discord.Embed(
            title=f"**<:Regular:1471133591336652831>คุณถูกลบRoleAdminสำเร็จ**",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )

        embed.add_field(
            name="รายละเอียด",
            value=(
                f"**<:MAYASTORE103:1471134921476280475>ผู้ถูกลบRole:** {member.mention}\n"
                f"**<:Ldelete:1471134544752148722>โรล:** {role.mention}\n"
                f"**<:Frame2:1471134268360101890>เหตุผล:** `{reason}`\n"
                f"**<a:v2:1471135162703282501>ลบโดย:** {interaction.user.mention}"
            ),
            inline=False
        )

        embed.set_footer(text="ระบบจัดการเซิร์ฟเวอร์")

        await interaction.response.send_message(embed=embed)
        await self.send_log(interaction.guild, embed)

        await asyncio.sleep(30)
        try:
            await interaction.delete_original_response()
        except (discord.NotFound, discord.HTTPException):
            pass

    # ───────────────────────────────────────────────────────────
    # BAN ADD
    # ───────────────────────────────────────────────────────────

    @app_commands.command(
        name="ban_add",
        description="แบนสมาชิก(เฉพาะAdminและเฉพาะServrowner)"
    )
    @app_commands.describe(
        member="เลือกสมาชิกที่ต้องการแบน",
        reason="ระบุเหตุผลในการแบน"
    )
    @app_commands.checks.cooldown(1, 10, key=lambda i: i.user.id)
    async def ban_add(
            self,
            interaction: discord.Interaction,
            member: discord.Member,
            reason: str = "ไม่ระบุ"
    ):
        # ป้องกันใช้ใน DM
        if not interaction.guild:
            return await interaction.response.send_message(
                embed=create_error_embed("คำสั่งนี้ใช้ได้เฉพาะในเซิร์ฟเวอร์เท่านั้น"),
                ephemeral=True
            )

        # ตรวจสอบสิทธิ์
        if not is_owner_or_admin(interaction.user):
            embed = discord.Embed(
                title=f"**<a:emoji_220:1471131868782133381> คุณไม่มีสิทธิ์ใช้คำสั่งนี้**",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # ตรวจสอบลำดับยศ
        can_proceed, error_msg = check_role_hierarchy(
            interaction.guild,
            interaction.user,
            member,
            interaction.guild.me,
        )

        if not can_proceed:
            return await interaction.response.send_message(
                embed=create_error_embed(error_msg),
                ephemeral=True
            )

        # ตรวจสอบ bot permission
        if not interaction.guild.me.guild_permissions.ban_members:
            return await interaction.response.send_message(
                embed=create_error_embed("บอทไม่มีสิทธิ์ **Ban Members**"),
                ephemeral=True
            )

        # แบนสมาชิก
        try:
            await member.ban(reason=f"{reason} | โดย {interaction.user}")
        except discord.Forbidden:
            return await interaction.response.send_message(
                embed=create_error_embed("บอทไม่มีสิทธิ์แบนสมาชิกนี้"),
                ephemeral=True
            )
        except discord.HTTPException as e:
            return await interaction.response.send_message(
                embed=create_error_embed(f"เกิดข้อผิดพลาด: {str(e)}"),
                ephemeral=True
            )

        # สร้าง Embed
        embed = discord.Embed(
            title=f"**<:moderator:1471136664800985182> สมาชิกถูกแบน**",
            color=discord.Color.dark_red(),
            timestamp=datetime.now(timezone.utc)
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(
            name="รายละเอียด",
            value=(
                f"**<:Regular:1471133591336652831>ชื่อ:** {member}\n"
                f"**<:MAYASTORE103:1471134921476280475>ไอดี:** `{member.id}`\n"
                f"**<:Frame2:1471134268360101890>เหตุผล:** {reason}\n"
                f"**<:blueban:1471167859978670142>แบนโดย:** {interaction.user.mention}"
            ),
            inline=False
        )

        embed.set_footer(text="ระบบจัดการเซิร์ฟเวอร์")

        await interaction.response.send_message(embed=embed)
        await self.send_log(interaction.guild, embed)

        await asyncio.sleep(60)
        try:
            await interaction.delete_original_response()
        except (discord.NotFound, discord.HTTPException):
            pass

    # ───────────────────────────────────────────────────────────
    # BAN REMOVE
    # ───────────────────────────────────────────────────────────

    @app_commands.command(
        name="ban_remove",
        description="ปลดแบนสมาชิก(เฉพาะAdminและเฉพาะServrowner)"
    )
    @app_commands.describe(
        user_id="ใส่ไอดีของผู้ใช้ที่ต้องการปลดแบน",
        reason="ระบุเหตุผลในการปลดแบน"
    )
    @app_commands.checks.cooldown(1, 10, key=lambda i: i.user.id)
    async def ban_remove(
            self,
            interaction: discord.Interaction,
            user_id: str,
            reason: str = "ไม่ระบุ"
    ):
        # ป้องกันใช้ใน DM
        if not interaction.guild:
            return await interaction.response.send_message(
                embed=create_error_embed("คำสั่งนี้ใช้ได้เฉพาะในเซิร์ฟเวอร์เท่านั้น"),
                ephemeral=True
            )

        # ตรวจสอบสิทธิ์
        if not is_owner_or_admin(interaction.user):
            embed = discord.Embed(
                title=f"**<a:emoji_220:1471131868782133381> คุณไม่มีสิทธิ์ใช้คำสั่งนี้**",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # ตรวจสอบ bot permission
        if not interaction.guild.me.guild_permissions.ban_members:
            return await interaction.response.send_message(
                embed=create_error_embed("บอทไม่มีสิทธิ์ **Ban Members**"),
                ephemeral=True
            )

        # แปลง user_id เป็น int
        try:
            uid = int(user_id.strip())
        except ValueError:
            return await interaction.response.send_message(
                embed=create_error_embed("User ID ต้องเป็นตัวเลขเท่านั้น"),
                ephemeral=True
            )

        # ดึงข้อมูล user
        try:
            user = await self.bot.fetch_user(uid)
        except discord.NotFound:
            return await interaction.response.send_message(
                embed=create_error_embed("ไม่พบผู้ใช้ที่มี ID นี้"),
                ephemeral=True
            )
        except discord.HTTPException as e:
            return await interaction.response.send_message(
                embed=create_error_embed(f"เกิดข้อผิดพลาด: {str(e)}"),
                ephemeral=True
            )

        # ปลดแบน
        try:
            await interaction.guild.unban(user, reason=f"{reason} | โดย {interaction.user}")
        except discord.NotFound:
            return await interaction.response.send_message(
                embed=create_error_embed("ผู้ใช้นี้ไม่ได้ถูกแบนในเซิร์ฟนี้"),
                ephemeral=True
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                embed=create_error_embed("บอทไม่มีสิทธิ์ปลดแบน"),
                ephemeral=True
            )
        except discord.HTTPException as e:
            return await interaction.response.send_message(
                embed=create_error_embed(f"เกิดข้อผิดพลาด: {str(e)}"),
                ephemeral=True
            )

        # สร้าง Embed
        embed = discord.Embed(
            title=f"**<a:gif22:1471132615544274987> ปลดแบนสำเร็จ**",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )

        embed.add_field(
            name="รายละเอียด",
            value=(
                f"**<:Regular:1471133591336652831>ชื่อ:** {user}\n"
                f"**<:MAYASTORE103:1471134921476280475>ไอดี:** `{user.id}`\n"
                f"**<:Frame2:1471134268360101890>เหตุผล:** {reason}\n"
                f"**<:kingblunts:1471168940423254049>ปลดโดย:** {interaction.user.mention}"
            ),
            inline=False
        )

        embed.set_footer(text="ระบบจัดการเซิร์ฟเวอร์")

        await interaction.response.send_message(embed=embed)
        await self.send_log(interaction.guild, embed)

    # ───────────────────────────────────────────────────────────
    # TIMEOUT ADD
    # ───────────────────────────────────────────────────────────

    @app_commands.command(
        name="timeout_add",
        description="ลงโทษสมาชิกด้วยการหมดเวลา (เฉพาะ Admin และ Server Owner)"
    )
    @app_commands.describe(
        member="เลือกสมาชิกที่ต้องการลงโทษหมดเวลา",
        duration="เลือกระยะเวลาหมดเวลา",
        reason="ระบุเหตุผลในการลงโทษ"
    )
    @app_commands.choices(duration=[
        app_commands.Choice(name="5 นาที", value=5),
        app_commands.Choice(name="10 นาที", value=10),
        app_commands.Choice(name="30 นาที", value=30),
        app_commands.Choice(name="1 ชั่วโมง", value=60),
        app_commands.Choice(name="6 ชั่วโมง", value=360),
        app_commands.Choice(name="12 ชั่วโมง", value=720),
        app_commands.Choice(name="1 วัน", value=1440),
        app_commands.Choice(name="3 วัน", value=4320),
        app_commands.Choice(name="7 วัน", value=10080),
    ])
    @app_commands.checks.cooldown(1, 10, key=lambda i: i.user.id)
    async def timeout_add(
            self,
            interaction: discord.Interaction,
            member: discord.Member,
            duration: app_commands.Choice[int],
            reason: str = "ไม่ระบุ"
    ):
        # ป้องกันใช้ใน DM
        if not interaction.guild:
            return await interaction.response.send_message(
                embed=create_error_embed("คำสั่งนี้ใช้ได้เฉพาะในเซิร์ฟเวอร์เท่านั้น"),
                ephemeral=True
            )

        # ตรวจสอบสิทธิ์
        if not is_owner_or_admin(interaction.user):
            embed = discord.Embed(
                title=f"**<a:emoji_220:1471131868782133381> คุณไม่มีสิทธิ์ใช้คำสั่งนี้**",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # ตรวจสอบลำดับยศ
        can_proceed, error_msg = check_role_hierarchy(
            interaction.guild,
            interaction.user,
            member,
            interaction.guild.me,
        )

        if not can_proceed:
            return await interaction.response.send_message(
                embed=create_error_embed(error_msg),
                ephemeral=True
            )

        # ตรวจสอบ bot permission
        if not interaction.guild.me.guild_permissions.moderate_members:
            return await interaction.response.send_message(
                embed=create_error_embed("บอทไม่มีสิทธิ์ **Moderate Members**"),
                ephemeral=True
            )

        # ลงโทษ timeout
        timeout_duration = timedelta(minutes=duration.value)
        try:
            await member.timeout(timeout_duration, reason=f"{reason} | โดย {interaction.user}")
        except discord.Forbidden:
            return await interaction.response.send_message(
                embed=create_error_embed("บอทไม่มีสิทธิ์ timeout สมาชิกนี้"),
                ephemeral=True
            )
        except discord.HTTPException as e:
            return await interaction.response.send_message(
                embed=create_error_embed(f"เกิดข้อผิดพลาด: {str(e)}"),
                ephemeral=True
            )

        # สร้าง Embed
        embed = discord.Embed(
            title=f"**<a:alert:1471170113213300766>  สมาชิกถูก Timeout**",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(
            name="รายละเอียด",
            value=(
                f"**<:Regular:1471133591336652831>ผู้ถูกลงโทษ:** {member.mention}\n"
                f"**<a:operational:1471170770003562597>ระยะเวลา:** {duration.name}\n"
                f"**<:Frame2:1471134268360101890>เหตุผล:** `{reason}`\n"
                f"**<:kingblunts:1471168940423254049>โดย:** {interaction.user.mention}"
            ),
            inline=False
        )

        embed.set_footer(text="ระบบจัดการเซิร์ฟเวอร์")

        await interaction.response.send_message(
            content=member.mention,
            embed=embed
        )

        await self.send_log(interaction.guild, embed)

    # ───────────────────────────────────────────────────────────
    # TIMEOUT REMOVE
    # ───────────────────────────────────────────────────────────

    @app_commands.command(
        name="timeout_remove",
        description="ปลดโทษหมดเวลาของสมาชิก(เฉพาะAdminและเฉพาะServrowner)"
    )
    @app_commands.describe(
        member="เลือกสมาชิกที่ต้องการปลดโทษ",
        reason="ระบุเหตุผลในการปลดโทษ"
    )
    @app_commands.checks.cooldown(1, 10, key=lambda i: i.user.id)
    async def timeout_remove(
            self,
            interaction: discord.Interaction,
            member: discord.Member,
            reason: str = "ไม่ระบุ"
    ):
        # ป้องกันใช้ใน DM
        if not interaction.guild:
            return await interaction.response.send_message(
                embed=create_error_embed("คำสั่งนี้ใช้ได้เฉพาะในเซิร์ฟเวอร์เท่านั้น"),
                ephemeral=True
            )

        # ตรวจสอบสิทธิ์
        if not is_owner_or_admin(interaction.user):
            embed = discord.Embed(
                title=f"**<a:emoji_220:1471131868782133381> คุณไม่มีสิทธิ์ใช้คำสั่งนี้**",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # ตรวจสอบ bot permission
        if not interaction.guild.me.guild_permissions.moderate_members:
            return await interaction.response.send_message(
                embed=create_error_embed("บอทไม่มีสิทธิ์ **Moderate Members**"),
                ephemeral=True
            )

        # ปลด timeout
        try:
            await member.timeout(None, reason=f"{reason} | โดย {interaction.user}")
        except discord.Forbidden:
            return await interaction.response.send_message(
                embed=create_error_embed("บอทไม่มีสิทธิ์ปลด timeout สมาชิกนี้"),
                ephemeral=True
            )
        except discord.HTTPException as e:
            return await interaction.response.send_message(
                embed=create_error_embed(f"เกิดข้อผิดพลาด: {str(e)}"),
                ephemeral=True
            )

        # สร้าง Embed
        embed = discord.Embed(
            title=f"**<a:gif22:1471132615544274987> ปลด Timeout สำเร็จ**",
            color=discord.Color.green(),
            timestamp=datetime.now(timezone.utc)
        )

        embed.add_field(
            name="รายละเอียด",
            value=(
                f"**<:Regular:1471133591336652831>สมาชิก:**  {member.mention}\n"
                f"**<:Frame2:1471134268360101890>เหตุผล:**  `{reason}`\n"
                f"**<:kingblunts:1471168940423254049>ปลดโดย:**  {interaction.user.mention}"
            ),
            inline=False
        )

        embed.set_footer(text="ระบบจัดการเซิร์ฟเวอร์")

        await interaction.response.send_message(embed=embed)
        await self.send_log(interaction.guild, embed)

    # ───────────────────────────────────────────────────────────
    # KICK
    # ───────────────────────────────────────────────────────────

    @app_commands.command(
        name="kick_add",
        description="เตะสมาชิกออกจากเซิร์ฟเวอร์(เฉพาะAdminและเฉพาะServrowner)"
    )
    @app_commands.describe(
        member="เลือกสมาชิกที่ต้องการเตะ",
        reason="ระบุเหตุผลในการเตะ"
    )
    @app_commands.checks.cooldown(1, 10, key=lambda i: i.user.id)
    async def kick(
            self,
            interaction: discord.Interaction,
            member: discord.Member,
            reason: str = "ไม่ระบุ"
    ):
        # ป้องกันใช้ใน DM
        if not interaction.guild:
            return await interaction.response.send_message(
                embed=create_error_embed("คำสั่งนี้ใช้ได้เฉพาะในเซิร์ฟเวอร์เท่านั้น"),
                ephemeral=True
            )

        # ตรวจสอบสิทธิ์
        if not is_owner_or_admin(interaction.user):
            embed = discord.Embed(
                title=f"**<a:emoji_220:1471131868782133381> คุณไม่มีสิทธิ์ใช้คำสั่งนี้**",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # ตรวจสอบลำดับยศ
        can_proceed, error_msg = check_role_hierarchy(
            interaction.guild,
            interaction.user,
            member,
            interaction.guild.me,
        )

        if not can_proceed:
            return await interaction.response.send_message(
                embed=create_error_embed(error_msg),
                ephemeral=True
            )

        # ตรวจสอบ bot permission
        if not interaction.guild.me.guild_permissions.kick_members:
            return await interaction.response.send_message(
                embed=create_error_embed("บอทไม่มีสิทธิ์ **Kick Members**"),
                ephemeral=True
            )

        # เตะสมาชิก
        try:
            await member.kick(reason=f"{reason} | โดย {interaction.user}")
        except discord.Forbidden:
            return await interaction.response.send_message(
                embed=create_error_embed("บอทไม่มีสิทธิ์เตะสมาชิกนี้"),
                ephemeral=True
            )
        except discord.HTTPException as e:
            return await interaction.response.send_message(
                embed=create_error_embed(f"เกิดข้อผิดพลาด: {str(e)}"),
                ephemeral=True
            )

        # สร้าง Embed
        embed = discord.Embed(
            title=f"**<a:emoji_226:1471172354322468864> สมาชิกถูกเตะออก**",
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc)
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(
            name="รายละเอียด",
            value=(
                f"**<:MAYASTORE103:1471134921476280475>ชื่อ:** {member}\n"
                f"**<:Frame2:1471134268360101890>เหตุผล:** `{reason}`\n"
                f"**<:kingblunts:1471168940423254049>โดย:** {interaction.user.mention}"
            ),
            inline=False
        )

        embed.set_footer(text="ระบบจัดการเซิร์ฟเวอร์")

        await interaction.response.send_message(embed=embed)
        await self.send_log(interaction.guild, embed)

    # ───────────────────────────────────────────────────────────
    # ANNOUNCE
    # ───────────────────────────────────────────────────────────

    @app_commands.command(
        name="announce_channel",
        description="ประกาศข้อความแบบบอท (ไม่แสดงชื่อผู้ใช้)"
    )
    @app_commands.describe(
        channel="เลือกห้องที่จะประกาศหรือIdช่อง",
        message="ข้อความที่ต้องการประกาศ",
        role="(ไม่บังคับ) เลือกยศที่ต้องการแท็ก",
        image_url="(ไม่บังคับ) URL ของรูปภาพที่ต้องการแนบ"
    )
    async def announce(
            self,
            interaction: discord.Interaction,
            channel: discord.TextChannel,
            message: str,
            role: discord.Role = None,
            image_url: str = None
    ):
        # ป้องกันใช้ใน DM
        if not interaction.guild:
            return await interaction.response.send_message(
                embed=create_error_embed("คำสั่งนี้ใช้ได้เฉพาะในเซิร์ฟเวอร์เท่านั้น"),
                ephemeral=True
            )

        # ตรวจสอบสิทธิ์
        if not is_owner_or_admin(interaction.user):
            return await interaction.response.send_message(
                "❌ ไม่มีสิทธิ์",
                ephemeral=True
            )

        # ตรวจสอบว่าบอทส่งข้อความในช่องนี้ได้หรือไม่
        bot_perms = channel.permissions_for(interaction.guild.me)
        if not bot_perms.send_messages or not bot_perms.embed_links:
            return await interaction.response.send_message(
                embed=create_error_embed(
                    f"บอทไม่มีสิทธิ์ส่งข้อความหรือ embed ใน {channel.mention}"
                ),
                ephemeral=True
            )

        # สร้าง Embed
        embed = discord.Embed(
            description=message,
            color=discord.Color.blue(),
            timestamp=datetime.now(timezone.utc)
        )

        if image_url:
            try:
                embed.set_image(url=image_url)
            except Exception:
                pass  # ถ้า URL ไม่ถูกต้องก็ข้าม

        embed.set_footer(text="ระบบประกาศ")

        # ส่งประกาศ
        try:
            if role:
                await channel.send(
                    content=role.mention,
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions(roles=[role])
                )
            else:
                await channel.send(embed=embed)

            return await interaction.response.send_message(
                "✅ ส่งประกาศแล้ว",
                ephemeral=True
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                embed=create_error_embed("บอทไม่มีสิทธิ์ส่งข้อความในช่องนี้"),
                ephemeral=True
            )
        except discord.HTTPException as e:
            return await interaction.response.send_message(
                embed=create_error_embed(f"เกิดข้อผิดพลาด: {str(e)}"),
                ephemeral=True
            )


# ═══════════════════════════════════════════════════════════════
# SETUP
# ═══════════════════════════════════════════════════════════════

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminSystem(bot))