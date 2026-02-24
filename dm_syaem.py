import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

OWNER_ID = 427563032080547840  # 👈 ใส่ไอดีเจ้าของบอท


# ==========================================
# ฟังก์ชันช่วยเหลือ
# ==========================================

def format_permissions(role: discord.Role) -> str:
    """แปลงสิทธิ์ของยศให้อ่านง่าย"""
    important_perms = {
        'administrator': '👑 ผู้ดูแลระบบ',
        'manage_guild': '⚙️ จัดการเซิร์ฟเวอร์',
        'manage_roles': '🎭 จัดการยศ',
        'manage_channels': '📝 จัดการห้อง',
        'kick_members': '👢 เตะสมาชิก',
        'ban_members': '🔨 แบนสมาชิก',
        'moderate_members': '⏰ ลงโทษสมาชิก',
        'mention_everyone': '📢 แท็ก @everyone',
        'manage_messages': '🗑️ จัดการข้อความ',
        'view_audit_log': '📜 ดูประวัติการจัดการ'
    }

    perms = []
    for perm_name, display_name in important_perms.items():
        if getattr(role.permissions, perm_name, False):
            perms.append(display_name)

    if not perms:
        return "ไม่มีสิทธิ์พิเศษ"

    return "\n".join(perms[:10])  # จำกัดแสดงแค่ 10 สิทธิ์


async def find_member(guild: discord.Guild, user_input: str) -> Optional[discord.Member]:
    """ค้นหาสมาชิกจาก ID, ชื่อ หรือ mention"""
    if not user_input:
        return None

    user_input = user_input.strip()

    # ลองค้นหาจาก ID หรือ mention
    try:
        # ลบ mention formatting ออก (<@123> หรือ <@!123>)
        clean_id = user_input.replace('<@', '').replace('>', '').replace('!', '')
        user_id = int(clean_id)
        member = guild.get_member(user_id)
        if member:
            return member
        # ถ้าไม่เจอใน cache ลอง fetch
        try:
            member = await guild.fetch_member(user_id)
            if member:
                return member
        except discord.NotFound:
            pass
        except discord.HTTPException:
            pass
    except ValueError:
        pass

    # ค้นหาจากชื่อ (ชื่อเต็ม หรือชื่อเล่น)
    user_input_lower = user_input.lower()

    # ค้นหาแบบตรงทั้งหมด
    for member in guild.members:
        if (member.name.lower() == user_input_lower or
                member.display_name.lower() == user_input_lower or
                str(member).lower() == user_input_lower):
            return member

    # ค้นหาแบบมีส่วนที่ตรง
    for member in guild.members:
        if (user_input_lower in member.name.lower() or
                user_input_lower in member.display_name.lower()):
            return member

    return None


async def find_role(guild: discord.Guild, role_input: str) -> Optional[discord.Role]:
    """ค้นหายศจาก ID, ชื่อ หรือ mention"""
    if not role_input:
        return None

    role_input = role_input.strip()

    # ลองค้นหาจาก ID หรือ mention
    try:
        # ลบ mention formatting ออก (<@&123>)
        clean_id = role_input.replace('<@&', '').replace('>', '')
        role_id = int(clean_id)
        role = guild.get_role(role_id)
        if role:
            return role
    except ValueError:
        pass

    # ค้นหาจากชื่อ
    role_input_lower = role_input.lower()

    # ค้นหาแบบตรงทั้งหมด
    for role in guild.roles:
        if role.name.lower() == role_input_lower:
            return role

    # ค้นหาแบบมีส่วนที่ตรง
    for role in guild.roles:
        if role_input_lower in role.name.lower():
            return role

    return None


# ==========================================
# VIEW ปุ่มยืนยัน
# ==========================================

class ConfirmView(discord.ui.View):
    def __init__(self, bot: commands.Bot, guild: discord.Guild, member: discord.Member, role: discord.Role):
        super().__init__(timeout=180)
        self.bot = bot
        self.guild = guild
        self.member = member
        self.role = role
        self.confirmed = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """ตรวจสอบว่าเป็นเจ้าของบอทหรือไม่"""
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message(
                "❌ **คุณไม่มีสิทธิ์ใช้ปุ่มนี้**\nเฉพาะเจ้าของบอทเท่านั้น",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="✅ ยืนยันให้ยศ", style=discord.ButtonStyle.success, custom_id="confirm")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ปุ่มยืนยันการให้ยศ"""

        # ตรวจสอบว่ายังอยู่ในเซิร์ฟหรือไม่
        current_member = self.guild.get_member(self.member.id)
        if not current_member:
            embed = discord.Embed(
                title="❌ เกิดข้อผิดพลาด",
                description=f"**{self.member.name}** ไม่ได้อยู่ในเซิร์ฟเวอร์แล้ว",
                color=discord.Color.red()
            )
            return await interaction.response.edit_message(embed=embed, view=None)

        # ตรวจสอบว่ายศยังมีอยู่หรือไม่
        current_role = self.guild.get_role(self.role.id)
        if not current_role:
            embed = discord.Embed(
                title="❌ เกิดข้อผิดพลาด",
                description=f"ยศ **{self.role.name}** ถูกลบไปแล้ว",
                color=discord.Color.red()
            )
            return await interaction.response.edit_message(embed=embed, view=None)

        # ตรวจลำดับยศ
        if current_role >= self.guild.me.top_role:
            embed = discord.Embed(
                title="❌ ไม่สามารถให้ยศได้",
                description=f"บอทไม่สามารถให้ยศ **{current_role.name}** ได้\nเพราะยศนี้สูงกว่าหรือเท่ากับยศสูงสุดของบอท",
                color=discord.Color.red()
            )
            embed.add_field(
                name="💡 วิธีแก้ไข",
                value="ลากยศของบอทให้สูงกว่ายศที่ต้องการให้",
                inline=False
            )
            return await interaction.response.edit_message(embed=embed, view=None)

        # ตรวจสอบว่ามียศนี้อยู่แล้วหรือไม่
        if current_role in current_member.roles:
            embed = discord.Embed(
                title="ℹ️ สมาชิกมียศนี้อยู่แล้ว",
                description=f"**{current_member.mention}** มียศ **{current_role.mention}** อยู่แล้ว",
                color=discord.Color.blue()
            )
            return await interaction.response.edit_message(embed=embed, view=None)

        # ให้ยศ
        try:
            await current_member.add_roles(current_role, reason=f"ให้โดย {interaction.user.name} (Owner)")
            self.confirmed = True

            embed = discord.Embed(
                title="✅ ให้ยศสำเร็จ",
                description=f"ให้ยศ **{current_role.mention}** แก่ **{current_member.mention}** เรียบร้อยแล้ว",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )

            embed.add_field(
                name="👤 ข้อมูลสมาชิก",
                value=(
                    f"**ชื่อ:** {current_member.name}\n"
                    f"**ชื่อเล่น:** {current_member.display_name}\n"
                    f"**ID:** `{current_member.id}`"
                ),
                inline=True
            )

            embed.add_field(
                name="🎭 ข้อมูลยศ",
                value=(
                    f"**ชื่อยศ:** {current_role.mention}\n"
                    f"**สี:** {str(current_role.color)}\n"
                    f"**ลำดับ:** {current_role.position}"
                ),
                inline=True
            )

            embed.add_field(
                name="🔑 สิทธิ์ที่ได้รับ",
                value=format_permissions(current_role),
                inline=False
            )

            embed.add_field(
                name="🌍 เซิร์ฟเวอร์",
                value=f"{self.guild.name} (`{self.guild.id}`)",
                inline=False
            )

            embed.set_thumbnail(url=current_member.display_avatar.url)
            embed.set_footer(text=f"ดำเนินการโดย {interaction.user.name}", icon_url=interaction.user.display_avatar.url)

            await interaction.response.edit_message(embed=embed, view=None)

        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ ไม่มีสิทธิ์",
                description="บอทไม่มีสิทธิ์ในการให้ยศนี้",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)

        except Exception as e:
            embed = discord.Embed(
                title="❌ เกิดข้อผิดพลาด",
                description=f"ไม่สามารถให้ยศได้: {str(e)}",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="❌ ยกเลิก", style=discord.ButtonStyle.danger, custom_id="cancel")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ปุ่มยกเลิก"""

        embed = discord.Embed(
            title="❌ ยกเลิกแล้ว",
            description="ยกเลิกการให้ยศเรียบร้อยแล้ว",
            color=discord.Color.orange()
        )

        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    async def on_timeout(self):
        """เมื่อหมดเวลา"""
        self.clear_items()


# ==========================================
# COG หลัก
# ==========================================

class AddRole(commands.Cog):
    """ระบบให้ยศสมาชิกในเซิร์ฟเวอร์ต่างๆ"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="add_role",
        description="ให้ยศแก่สมาชิกในเซิร์ฟเวอร์ใดก็ได้ (เฉพาะเจ้าของบอท)"
    )
    @app_commands.describe(
        server="ชื่อเซิร์ฟเวอร์หรือ ID ของเซิร์ฟเวอร์",
        member="ชื่อสมาชิก, ID, หรือ @mention ของสมาชิก",
        role="ชื่อยศ, ID, หรือ @mention ของยศ"
    )
    async def slash_add_role(
            self,
            interaction: discord.Interaction,
            server: str,
            member: str,
            role: str
    ):
        """คำสั่ง Slash Command สำหรับให้ยศ"""

        # ตรวจสอบสิทธิ์
        if interaction.user.id != OWNER_ID:
            embed = discord.Embed(
                title="❌ ไม่มีสิทธิ์",
                description="คำสั่งนี้ใช้ได้เฉพาะเจ้าของบอทเท่านั้น",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        # ค้นหาเซิร์ฟเวอร์
        guild = await self.find_guild(server)
        if not guild:
            embed = discord.Embed(
                title="❌ ไม่พบเซิร์ฟเวอร์",
                description=f"ไม่พบเซิร์ฟเวอร์ `{server}`",
                color=discord.Color.red()
            )
            embed.add_field(
                name="💡 คำแนะนำ",
                value="ลองใช้ `/list_servers` เพื่อดูรายชื่อเซิร์ฟเวอร์ทั้งหมด",
                inline=False
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        # ค้นหาสมาชิก
        found_member = await find_member(guild, member)
        if not found_member:
            # แสดงข้อมูล debug
            total_members = len([m for m in guild.members if not m.bot])
            embed = discord.Embed(
                title="❌ ไม่พบสมาชิก",
                description=f"ไม่พบสมาชิก `{member}` ในเซิร์ฟเวอร์ **{guild.name}**",
                color=discord.Color.red()
            )
            embed.add_field(
                name="📊 ข้อมูลเซิร์ฟเวอร์",
                value=f"สมาชิกทั้งหมด: {total_members:,} คน\nบอทสามารถเห็นสมาชิก: {len(guild.members):,} คน",
                inline=False
            )
            embed.add_field(
                name="💡 คำแนะนำ",
                value=(
                    "ลองใช้:\n"
                    "• **User ID** (เช่น `123456789`)\n"
                    "• **Username** (เช่น `john` หรือ `john#1234`)\n"
                    "• **@Mention** (แท็กสมาชิกโดยตรง)\n\n"
                    "⚠️ **หมายเหตุ:** บอทต้องอยู่ในเซิร์ฟเวอร์เดียวกับสมาชิกที่ต้องการค้นหา"
                ),
                inline=False
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        # ค้นหายศ
        found_role = await find_role(guild, role)
        if not found_role:
            embed = discord.Embed(
                title="❌ ไม่พบยศ",
                description=f"ไม่พบยศ `{role}` ในเซิร์ฟเวอร์ **{guild.name}**",
                color=discord.Color.red()
            )
            embed.add_field(
                name="💡 คำแนะนำ",
                value="ลองใช้:\n• Role ID (เช่น `987654321`)\n• ชื่อยศ (เช่น `Admin`)\n• @Mention",
                inline=False
            )
            return await interaction.followup.send(embed=embed, ephemeral=True)

        # สร้าง Embed ยืนยัน
        embed = self.create_confirmation_embed(guild, found_member, found_role)
        view = ConfirmView(self.bot, guild, found_member, found_role)

        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @commands.command(name="add_role", aliases=['giverole', 'addrole'])
    async def prefix_add_role(self, ctx: commands.Context, server: str, member: str, role: str):
        """คำสั่ง Prefix Command สำหรับให้ยศ"""

        # ตรวจสอบสิทธิ์
        if ctx.author.id != OWNER_ID:
            embed = discord.Embed(
                title="❌ ไม่มีสิทธิ์",
                description="คำสั่งนี้ใช้ได้เฉพาะเจ้าของบอทเท่านั้น",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        async with ctx.typing():
            # ค้นหาเซิร์ฟเวอร์
            guild = await self.find_guild(server)
            if not guild:
                embed = discord.Embed(
                    title="❌ ไม่พบเซิร์ฟเวอร์",
                    description=f"ไม่พบเซิร์ฟเวอร์ `{server}`",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)

            # ค้นหาสมาชิก
            found_member = await find_member(guild, member)
            if not found_member:
                embed = discord.Embed(
                    title="❌ ไม่พบสมาชิก",
                    description=f"ไม่พบสมาชิก `{member}` ในเซิร์ฟเวอร์ **{guild.name}**",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)

            # ค้นหายศ
            found_role = await find_role(guild, role)
            if not found_role:
                embed = discord.Embed(
                    title="❌ ไม่พบยศ",
                    description=f"ไม่พบยศ `{role}` ในเซิร์ฟเวอร์ **{guild.name}**",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)

            # สร้าง Embed ยืนยัน
            embed = self.create_confirmation_embed(guild, found_member, found_role)
            view = ConfirmView(self.bot, guild, found_member, found_role)

            await ctx.send(embed=embed, view=view)

    @app_commands.command(
        name="list_servers",
        description="แสดงรายชื่อเซิร์ฟเวอร์ทั้งหมดที่บอทอยู่ (เฉพาะเจ้าของบอท)"
    )
    async def list_servers(self, interaction: discord.Interaction):
        """แสดงรายชื่อเซิร์ฟเวอร์ทั้งหมด"""

        if interaction.user.id != OWNER_ID:
            embed = discord.Embed(
                title="❌ ไม่มีสิทธิ์",
                description="คำสั่งนี้ใช้ได้เฉพาะเจ้าของบอทเท่านั้น",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        guilds = sorted(self.bot.guilds, key=lambda g: g.member_count, reverse=True)

        embed = discord.Embed(
            title=f"📊 รายชื่อเซิร์ฟเวอร์ทั้งหมด ({len(guilds)} เซิร์ฟ)",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )

        server_list = []
        for i, guild in enumerate(guilds[:25], 1):  # จำกัดแค่ 25 เซิร์ฟแรก
            owner = guild.owner or "ไม่ทราบ"
            server_list.append(
                f"**{i}.** {guild.name}\n"
                f"└ ID: `{guild.id}`\n"
                f"└ สมาชิก: {guild.member_count:,} คน\n"
                f"└ เจ้าของ: {owner}"
            )

        if server_list:
            embed.description = "\n\n".join(server_list)
        else:
            embed.description = "ไม่มีเซิร์ฟเวอร์"

        if len(guilds) > 25:
            embed.set_footer(text=f"แสดง 25 จาก {len(guilds)} เซิร์ฟเวอร์")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def find_guild(self, guild_input: str) -> Optional[discord.Guild]:
        """ค้นหาเซิร์ฟเวอร์จาก ID หรือชื่อ"""
        if not guild_input:
            return None

        guild_input = guild_input.strip()

        # ลองค้นหาจาก ID
        try:
            guild_id = int(guild_input)
            guild = self.bot.get_guild(guild_id)
            if guild:
                return guild
            # ลอง fetch ถ้าไม่เจอใน cache
            try:
                guild = await self.bot.fetch_guild(guild_id)
                if guild:
                    return guild
            except discord.NotFound:
                pass
            except discord.HTTPException:
                pass
        except ValueError:
            pass

        # ค้นหาจากชื่อ
        guild_input_lower = guild_input.lower()

        # ค้นหาแบบตรงทั้งหมด
        for guild in self.bot.guilds:
            if guild.name.lower() == guild_input_lower:
                return guild

        # ค้นหาแบบมีส่วนที่ตรง
        for guild in self.bot.guilds:
            if guild_input_lower in guild.name.lower():
                return guild

        return None

    def create_confirmation_embed(
            self,
            guild: discord.Guild,
            member: discord.Member,
            role: discord.Role
    ) -> discord.Embed:
        """สร้าง Embed สำหรับยืนยันการให้ยศ"""

        embed = discord.Embed(
            title="⚠️ ยืนยันการให้ยศ",
            description="กรุณาตรวจสอบข้อมูลก่อนกดยืนยัน",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="👤 สมาชิก",
            value=(
                f"**ชื่อ:** {member.mention}\n"
                f"**ID:** `{member.id}`\n"
                f"**Username:** {member.name}"
            ),
            inline=True
        )

        embed.add_field(
            name="🎭 ยศที่จะให้",
            value=(
                f"**ยศ:** {role.mention}\n"
                f"**ID:** `{role.id}`\n"
                f"**ลำดับ:** {role.position}"
            ),
            inline=True
        )

        embed.add_field(
            name="🌍 เซิร์ฟเวอร์",
            value=f"{guild.name}\n`{guild.id}`",
            inline=False
        )

        embed.add_field(
            name="🔑 สิทธิ์ที่จะได้รับ",
            value=format_permissions(role),
            inline=False
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="กดปุ่มด้านล่างเพื่อยืนยันหรือยกเลิก")

        return embed


async def setup(bot: commands.Bot):
    await bot.add_cog(AddRole(bot))