import discord
import discord.ui as ui
import random
import asyncio
from datetime import datetime, UTC, timedelta
from collections import defaultdict
from discord.ext import commands
import logging
import os
from dotenv import load_dotenv

load_dotenv()

APPLICATION_TOKEN = os.getenv("APPLICATION_TOKEN")
MODERATION_TOKEN = os.getenv("MODERATION_TOKEN")

if not APPLICATION_TOKEN or not MODERATION_TOKEN:
    raise ValueError("❌ Токены не найдены в переменных окружения. Проверьте .env файл или переменные среды.")

# Настройка логирования
logger = logging.getLogger("discord")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)

# Конфигурация
APPLICATION_MENU_CHANNEL_ID = 1376868344850026516
APPLICATION_SUBMISSION_CHANNEL_ID = 1376871959211540520
APPLICATION_COOLDOWN = 300
LOG_CHANNEL_ID = 1376859187794939974

# Токены
# Создание ботов
bot1 = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot2 = commands.Bot(command_prefix='?', intents=discord.Intents.all())

# Глобальные переменные
verification_codes = {}
last_application_times = {}
user_message_log = defaultdict(list)
user_repeat_messages = defaultdict(list)
user_violations = defaultdict(int)

# Константы для антикраш системы
SPAM_THRESHOLD = 5
SPAM_INTERVAL = 10
MENTION_LIMIT = 5
REPEAT_THRESHOLD = 3
CAPS_THRESHOLD = 70
TIMEOUT_DURATION = 1800

class VerificationModal(discord.ui.Modal, title="Верификация"):
    def __init__(self, code):
        super().__init__()
        self.user_code = code
        self.code_input = discord.ui.TextInput(
            label=f"Введите число: {code}",
            placeholder=f"Введите число: {code}",
            required=True,
            max_length=4
        )
        self.add_item(self.code_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            entered_code = self.code_input.value

            if entered_code == str(self.user_code):
                role_verified = discord.utils.get(interaction.guild.roles, name="User")
                role_unverified = discord.utils.get(interaction.guild.roles, name="unverify")

                if role_verified:
                    await interaction.user.add_roles(role_verified)
                    if role_unverified:
                        await interaction.user.remove_roles(role_unverified)

                    if interaction.user.id in verification_codes:
                        del verification_codes[interaction.user.id]

                    await interaction.response.send_message("✅ Вы успешно верифицированы! Роль 'unverify' снята, роль 'User' выдана!", ephemeral=True)
                    logger.info(f"User {interaction.user} successfully verified")
                else:
                    await interaction.response.send_message("⚠️ Роль 'User' не найдена на сервере.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Неверный код. Попробуйте ещё раз.", ephemeral=True)

        except discord.errors.NotFound:
            logger.error(f"Verification modal interaction expired for user {interaction.user}")
            try:
                embed = discord.Embed(
                    title="⚠️ Сеанс верификации истек",
                    description="Пожалуйста, начните процесс верификации заново.",
                    color=discord.Color.orange()
                )
                await interaction.user.send(embed=embed)
            except:
                pass
        except discord.errors.InteractionResponded:
            logger.error(f"Verification modal interaction already responded for user {interaction.user}")
        except Exception as e:
            logger.error(f"Error in verification modal submission: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Произошла ошибка при верификации.", ephemeral=True)
            except:
                pass

class ApplicationModal(discord.ui.Modal):
    def __init__(self, composition: str):
        super().__init__(title=f"Заявка в {composition}")
        self.composition = composition

    age = discord.ui.TextInput(
        label="Сколько Вам Лет?",
        placeholder="Ваш возраст...",
        required=True,
        max_length=3
    )

    clans_experience = discord.ui.TextInput(
        label="Опыт в Кланах",
        placeholder="Расскажите о вашем опыте в кланах...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=4000
    )

    skills = discord.ui.TextInput(
        label="Что Вы Умеете?",
        placeholder="Расскажите о ваших навыках и умениях...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=4000
    )

    time_dedication = discord.ui.TextInput(
        label="Сколько Готовы Уделять Времени Клану?",
        placeholder="Сколько времени в день/неделю готовы уделять клану...",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=4000
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = interaction.user.id
            now = datetime.now(UTC)

            if user_id in last_application_times:
                delta = now - last_application_times[user_id]
                if delta.total_seconds() < APPLICATION_COOLDOWN:
                    remaining = APPLICATION_COOLDOWN - delta.total_seconds()
                    await interaction.response.send_message(
                        f"⏰ Вы можете подать заявку снова через {int(remaining)} секунд.",
                        ephemeral=True
                    )
                    return

            last_application_times[user_id] = now

            channel = bot1.get_channel(1376871959211540520)
            if not channel:
                await interaction.response.send_message("❌ Канал для заявок не найден.", ephemeral=True)
                return

            embed = discord.Embed(
                title=f"📋 Новая заявка - {self.composition}",
                color=discord.Color.blue()
            )
            embed.add_field(name="👤 Пользователь", value=f"{interaction.user.mention}\n`{interaction.user}`", inline=True)
            embed.add_field(name="🎂 Возраст", value=f"`{self.age.value}`", inline=True)
            embed.add_field(name="⏰ Время для клана", value=f"```{self.time_dedication.value[:500]}```", inline=True)
            embed.add_field(name="🏛️ Опыт в кланах", value=f"```{self.clans_experience.value[:800]}```", inline=False)
            embed.add_field(name="🛠️ Навыки и умения", value=f"```{self.skills.value[:800]}```", inline=False)

            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.set_footer(text=f"ID: {interaction.user.id} • {now.strftime('%d.%m.%Y %H:%M')}")

            await channel.send(embed=embed, view=ModActionView(interaction.user, self.composition))

            try:
                user_embed = discord.Embed(
                    title="✅ Заявка отправлена!",
                    description=f"Ваша заявка на **{self.composition}** успешно отправлена на рассмотрение.",
                    color=discord.Color.green()
                )
                await interaction.user.send(embed=user_embed)
            except:
                pass

            await interaction.response.send_message("✅ Заявка успешно отправлена!", ephemeral=True)

        except Exception as e:
            logger.error(f"Ошибка при отправке заявки: {e}")
            await interaction.response.send_message("❌ Произошла ошибка при отправке заявки.", ephemeral=True)

class ModActionView(discord.ui.View):
    def __init__(self, applicant: discord.User, composition: str):
        super().__init__(timeout=86400)
        self.applicant = applicant
        self.composition = composition

    @discord.ui.button(label="✅ Принять", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.title = "✅ ЗАЯВКА ПРИНЯТА"
        embed.add_field(name="👨‍💼 Модератор", value=f"{interaction.user.mention}", inline=True)
        embed.add_field(name="📅 Время решения", value=f"<t:{int(datetime.now(UTC).timestamp())}:R>", inline=True)

        await interaction.response.edit_message(embed=embed, view=None)

        try:
            accept_embed = discord.Embed(
                title="🎉 Поздравляем! Заявка принята!",
                description=f"Ваша заявка на **{self.composition}** была **принята**!",
                color=discord.Color.green()
            )
            await self.applicant.send(embed=accept_embed)
        except:
            pass

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.title = "❌ ЗАЯВКА ОТКЛОНЕНА"
        embed.add_field(name="👨‍💼 Модератор", value=f"{interaction.user.mention}", inline=True)
        embed.add_field(name="📅 Время решения", value=f"<t:{int(datetime.now(UTC).timestamp())}:R>", inline=True)

        await interaction.response.edit_message(embed=embed, view=None)

        try:
            reject_embed = discord.Embed(
                title="😔 Заявка отклонена",
                description=f"Ваша заявка на **{self.composition}** была **отклонена**.",
                color=discord.Color.red()
            )
            await self.applicant.send(embed=reject_embed)
        except:
            pass



class ApplicationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="I", style=discord.ButtonStyle.secondary, custom_id="app_i_composition")
    async def i_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not interaction.response.is_done():
                await interaction.response.send_modal(ApplicationModal("🏆 I Состав"))
        except discord.errors.NotFound:
            logger.error("Interaction expired or unknown for I composition")
        except discord.errors.InteractionResponded:
            logger.error("Interaction already acknowledged for I composition")
        except Exception as e:
            logger.error(f"Error in I button: {e}")

    @discord.ui.button(label="II", style=discord.ButtonStyle.secondary, custom_id="app_ii_composition")
    async def ii_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not interaction.response.is_done():
                await interaction.response.send_modal(ApplicationModal("⚔️ II Состав"))
        except discord.errors.NotFound:
            logger.error("Interaction expired or unknown for II composition")
        except discord.errors.InteractionResponded:
            logger.error("Interaction already acknowledged for II composition")
        except Exception as e:
            logger.error(f"Error in II button: {e}")

    @discord.ui.button(label="III", style=discord.ButtonStyle.secondary, custom_id="app_iii_composition")
    async def iii_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not interaction.response.is_done():
                await interaction.response.send_modal(ApplicationModal("🛡️ III Состав"))
        except discord.errors.NotFound:
            logger.error("Interaction expired or unknown for III composition")
        except discord.errors.InteractionResponded:
            logger.error("Interaction already acknowledged for III composition")
        except Exception as e:
            logger.error(f"Error in III button: {e}")

    @discord.ui.button(label="IV", style=discord.ButtonStyle.primary, custom_id="apply_coders")
    async def coders_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not interaction.response.is_done():
                await interaction.response.send_modal(ApplicationModal("💻 IV Состав"))
        except discord.errors.NotFound:
            logger.error("Interaction expired or unknown for IV composition")
        except discord.errors.InteractionResponded:
            logger.error("Interaction already acknowledged for IV composition")
        except Exception as e:
            logger.error(f"Error in IV button: {e}")

    @discord.ui.button(label="Family", style=discord.ButtonStyle.primary, custom_id="apply_family")
    async def family_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not interaction.response.is_done():
                await interaction.response.send_modal(ApplicationModal("🏠 Family"))
        except discord.errors.NotFound:
            logger.error("Interaction expired or unknown for Family composition")
        except discord.errors.InteractionResponded:
            logger.error("Interaction already acknowledged for Family composition")
        except Exception as e:
            logger.error(f"Error in Family button: {e}")


class VerificationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Верификация", style=discord.ButtonStyle.primary, emoji="✅", custom_id="verify_button")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Проверяем, что взаимодействие еще действительно
            if interaction.response.is_done():
                logger.warning(f"Interaction already responded for user {interaction.user}")
                return

            user_id = interaction.user.id

            if user_id in verification_codes:
                code = verification_codes[user_id]
            else:
                code = random.randint(1000, 9999)
                verification_codes[user_id] = code

            # Быстрый ответ с модалкой
            await interaction.response.send_modal(VerificationModal(code))
            logger.info(f"Verification modal sent to {interaction.user}")

        except discord.errors.NotFound:
            logger.error(f"Interaction expired or unknown for verification from user {interaction.user}")
            # Отправляем сообщение напрямую пользователю если взаимодействие истекло
            try:
                embed = discord.Embed(
                    title="⚠️ Взаимодействие истекло",
                    description="Пожалуйста, попробуйте нажать кнопку верификации еще раз.",
                    color=discord.Color.orange()
                )
                await interaction.user.send(embed=embed)
            except:
                pass
        except discord.errors.InteractionResponded:
            logger.error(f"Interaction already acknowledged for verification from user {interaction.user}")
        except Exception as e:
            logger.error(f"Error in verification button: {e}")
            # Попытка отправить сообщение об ошибке если возможно
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Произошла ошибка. Попробуйте еще раз.", ephemeral=True)
            except:
                pass

# Антикраш система
async def timeout_user(member: discord.Member, reason="Нарушение", duration=TIMEOUT_DURATION):
    try:
        timeout_until = datetime.now(UTC) + timedelta(seconds=duration)
        await member.timeout(timeout_until, reason=reason)
        logger.info(f"Тайм-аут выдан {member} на {duration}с за: {reason}")
        return True
    except Exception as e:
        logger.error(f"Не удалось выдать тайм-аут {member}: {e}")
        return False

async def log_violation(guild, user, reason, msg_content="", deletion_success=True, timeout_success=True):
    try:
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if not log_channel:
            logger.warning(f"Лог-канал {LOG_CHANNEL_ID} не найден")
            return

        user_violations[user.id] += 1

        embed = discord.Embed(
            title="🚨 Антикраш: Нарушение обнаружено",
            color=discord.Color.red(),
            timestamp=datetime.now(UTC)
        )

        embed.add_field(name="👤 Пользователь", value=f"{user.mention}\n`{user.display_name}` ({user})", inline=True)
        embed.add_field(name="📍 Канал", value="Текстовый канал", inline=True)
        embed.add_field(name="⚠️ Тип нарушения", value=reason, inline=True)

        if msg_content:
            content_preview = msg_content[:100] + "..." if len(msg_content) > 100 else msg_content
            embed.add_field(name="💬 Содержимое", value=f"```{content_preview}```", inline=False)

        embed.add_field(name="🗑️ Удаление", value="✅ Успешно" if deletion_success else "❌ Неудача", inline=True)
        embed.add_field(name="⏳ Тайм-аут", value="✅ Выдан" if timeout_success else "❌ Неудача", inline=True)
        embed.add_field(name="📊 Всего нарушений", value=f"{user_violations[user.id]}", inline=True)

        await log_channel.send(embed=embed)

    except Exception as e:
        logger.error(f"Ошибка логирования нарушения: {e}")

async def handle_violation(message, member, reason):
    try:
        deletion_success = True
        try:
            await message.delete()
            logger.info(f"Сообщение от {member} удалено за: {reason}")
        except Exception as e:
            deletion_success = False
            logger.error(f"Не удалось удалить сообщение от {member}: {e}")

        timeout_success = await timeout_user(member, reason)

        await log_violation(
            message.guild, member, reason, 
            message.content[:100] if message.content else "Медиа/эмбед",
            deletion_success, timeout_success
        )

    except Exception as e:
        logger.error(f"Критическая ошибка в handle_violation: {e}")

async def check_spam(message):
    try:
        user_id = message.author.id
        now = datetime.now(UTC)

        # Логируем сообщение (время и содержание)
        user_message_log[user_id].append((now, message.content.strip().lower()))

        # Фильтрация по времени
        recent_messages = [
            (msg_time, content) for msg_time, content in user_message_log[user_id]
            if (now - msg_time).total_seconds() <= SPAM_INTERVAL
        ]
        user_message_log[user_id] = recent_messages

        # Подсчёт количества одинаковых сообщений
        contents = [content for _, content in recent_messages]
        most_common = max(set(contents), key=contents.count, default=None)
        count = contents.count(most_common) if most_common else 0

        if count >= SPAM_THRESHOLD:
            await handle_violation(message, message.author, f"Спам одинаковыми сообщениями: {count}/{SPAM_THRESHOLD}")
            return True

        return False
    except Exception as e:
        logger.error(f"Ошибка проверки спама: {e}")
        return False
    except Exception as e:
        logger.error(f"Ошибка проверки спама: {e}")
        return False

async def check_mentions(message):
    try:
        mention_count = len(message.mentions) + len(message.role_mentions)

        if mention_count > MENTION_LIMIT:
            await handle_violation(message, message.author, f"Превышен лимит упоминаний: {mention_count}/{MENTION_LIMIT}")
            return True

        return False
    except Exception as e:
        logger.error(f"Ошибка проверки упоминаний: {e}")
        return False

async def check_repeated_messages(message):
    try:
        if not message.content:
            return False

        user_id = message.author.id
        content = message.content.lower().strip()

        user_repeat_messages[user_id].append(content)

        if len(user_repeat_messages[user_id]) > 10:
            user_repeat_messages[user_id] = user_repeat_messages[user_id][-10:]

        recent_same = user_repeat_messages[user_id].count(content)

        if recent_same >= REPEAT_THRESHOLD:
            await handle_violation(message, message.author, f"Повторяющиеся сообщения: {recent_same}/{REPEAT_THRESHOLD}")
            return True

        return False
    except Exception as e:
        logger.error(f"Ошибка проверки повторов: {e}")
        return False

async def check_caps(message):
    try:
        if not message.content or len(message.content) < 10:
            return False

        caps_count = sum(1 for char in message.content if char.isupper())
        total_letters = sum(1 for char in message.content if char.isalpha())

        if total_letters == 0:
            return False

        caps_percentage = (caps_count / total_letters) * 100

        if caps_percentage >= CAPS_THRESHOLD:
            await handle_violation(message, message.author, f"Превышение заглавных букв: {caps_percentage:.1f}%/{CAPS_THRESHOLD}%")
            return True

        return False
    except Exception as e:
        logger.error(f"Ошибка проверки КАПС: {e}")
        return False

import re

import re

async def check_discord_links(message):
    try:
        content = message.content.lower()

        emoji_letter_map = {
            '🇦': 'a', '🇧': 'b', '🇨': 'c', '🇩': 'd', '🇪': 'e', '🇫': 'f',
            '🇬': 'g', '🇭': 'h', '🇮': 'i', '🇯': 'j', '🇰': 'k', '🇱': 'l',
            '🇲': 'm', '🇳': 'n', '🇴': 'o', '🇵': 'p', '🇶': 'q', '🇷': 'r',
            '🇸': 's', '🇹': 't', '🇺': 'u', '🇻': 'v', '🇼': 'w', '🇽': 'x',
            '🇾': 'y', '🇿': 'z'
        }

        # Удаление пробелов, точек, дефисов и других символов + эмодзи
        normalized = ''.join(emoji_letter_map.get(c, c) for c in content)
        normalized = re.sub(r'[^a-z0-9]', '', normalized)

        if message.author.guild_permissions.manage_messages or \
           message.author.guild_permissions.moderate_members or \
           message.author.guild_permissions.administrator:
            return False

        discord_patterns = [
            'discordgg', 'discordcominvite', 'discordappcominvite',
            'dscgg', 'discordme', 'topggservers'
        ]

        for pattern in discord_patterns:
            if pattern in normalized:
                await handle_violation(message, message.author, f"Обход фильтра Discord ссылки: {pattern}")
                return True

        return False
    except Exception as e:
        logger.error(f"Ошибка проверки Discord ссылок: {e}")
        return False
async def check_txt_attachments(message):
    for attachment in message.attachments:
        if attachment.filename.endswith(".txt"):
            try:
                content = await attachment.read()
                text = content.decode("utf-8", errors="ignore").lower()
                if any(x in text for x in ['discord.gg/', 'http://', 'https://']):
                    await handle_violation(message, message.author, f"Ссылки в txt-файле: {attachment.filename}")
                    return True
            except Exception as e:
                logger.error(f"Ошибка при проверке txt файла: {e}")
    return False

# ✅ Проверка exe-файлов (логирование)
async def check_exe_attachments(message):
    for attachment in message.attachments:
        if attachment.filename.endswith(".exe"):
            logger.warning(f"Пользователь {message.author} загрузил .exe файл: {attachment.filename}")
    return False


async def anticrash_check(message):
    try:
        checks = [
            check_spam,
            check_txt_attachments,
            check_exe_attachments,
            check_mentions,
            check_repeated_messages,
            check_caps,
            check_discord_links
        ]

        for check in checks:
            if await check(message):
                return True

        return False
    except Exception as e:
        logger.error(f"Ошибка антикраш проверки: {e}")
        return False




@bot1.event
async def on_ready():
    logger.info(f'🚀 Бот заявок {bot1.user} запущен!')

    # Безопасная регистрация View'шек
    try:
        bot1.add_view(ApplicationView())
        bot1.add_view(VerificationView())
        logger.info("✅ View'шки добавлены")
    except Exception as e:
        logger.error(f"❌ Ошибка при добавлении View: {e}")

    # Безопасная проверка меню заявок
    try:
        channel = bot1.get_channel(APPLICATION_SUBMISSION_CHANNEL_ID)
        if channel is None:
            logger.error(f"❌ Канал {APPLICATION_SUBMISSION_CHANNEL_ID} не найден (get_channel вернул None)")
            return

        async for msg in channel.history(limit=50):
            if (msg.author == bot1.user and msg.embeds and msg.embeds[0].title and "Заявки в клан" in msg.embeds[0].title):
                logger.info("📨 Меню заявок уже существует")
                break
        else:
            embed = discord.Embed(
                title="📨 Заявки в клан Forest of Reapers открыты!",
                description="Выберите состав...",
                color=discord.Color.blue()
            )
            await channel.send(embed=embed, view=ApplicationView())
            logger.info("✅ Меню заявок создано")
    except Exception as e:
        logger.error(f"❌ Ошибка при создании меню заявок: {e}")


@bot1.event
async def on_message(message):
    if message.author.bot:
        await bot1.process_commands(message)
        return

    if await anticrash_check(message):
        return

    await bot1.process_commands(message)


@bot1.command(name='app')
async def create_application_embed(ctx):
    embed = discord.Embed(
        title="📨 Заявки в клан Forest of Reapers открыты!",
        description="Выберите состав, в который хотите подать заявку:",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=ApplicationView())


# обновлённая версия verify

@bot1.command(name='verify')
async def create_verification_embed(ctx):
    embed = discord.Embed(
        title="✅ Верификация",
        description="Нажмите на кнопку ниже для прохождения верификации",
        color=discord.Color.green()
    )
    embed.set_image(url="https://cdn.discordapp.com/attachments/900731112811290655/1378050895337623693/Frame_2.png?ex=684271a8&is=68412028&hm=99e453b1b8ac8a879b809fde350bed1dc3bf59d54dfdce3c18de80f613002db4&")
    await ctx.send(embed=embed, view=VerificationView())


# События бота 2 (Модерация)
@bot2.event
async def on_ready():
    logger.info(f'Бот модерации {bot2.user} запущен!')

@bot2.event
async def on_message(message):
    if message.author.bot:
        await bot2.process_commands(message)
        return

    if await anticrash_check(message):
        return

    await bot2.process_commands(message)

@bot2.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear_messages(ctx, amount: int = 10):
    try:
        deleted = await ctx.channel.purge(limit=amount + 1)

        embed = discord.Embed(
            title="🧹 Сообщения очищены",
            description=f"Удалено {len(deleted)-1} сообщений",
            color=discord.Color.green()
        )

        msg = await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await msg.delete()

        logger.info(f"{len(deleted)-1} сообщений удалено в {ctx.channel} модератором {ctx.author}")

    except Exception as e:
        await ctx.send(f"❌ Ошибка: {e}")
        logger.error(f"Ошибка при очистке сообщений: {e}")

@bot2.command(name="warn")
@commands.has_permissions(moderate_members=True)
async def warn(ctx, member: discord.Member, *, reason="Без причины"):
    try:
        embed = discord.Embed(
            title="⚠️ Предупреждение выдано",
            description=f"{member.mention} получил предупреждение",
            color=discord.Color.yellow()
        )
        embed.add_field(name="Причина", value=reason, inline=False)
        embed.add_field(name="Модератор", value=ctx.author.mention, inline=True)

        await ctx.send(embed=embed)

        try:
            dm_embed = discord.Embed(
                title="⚠️ Вам выдано предупреждение",
                description=f"**Причина:** {reason}",
                color=discord.Color.yellow()
            )
            await member.send(embed=dm_embed)
        except:
            pass

    except Exception as e:
        await ctx.send(f"❌ Ошибка: {e}")

@bot2.command(name="timeout")
@commands.has_permissions(moderate_members=True)
async def timeout_command(ctx, member: discord.Member, duration: int, *, reason="Без причины"):
    try:
        success = await timeout_user(member, reason, duration)

        if success:
            embed = discord.Embed(
                title="⏳ Тайм-аут выдан",
                description=f"{member.mention} получил тайм-аут",
                color=discord.Color.orange()
            )
            embed.add_field(name="Длительность", value=f"{duration} секунд", inline=True)
            embed.add_field(name="Причина", value=reason, inline=False)
            embed.add_field(name="Модератор", value=ctx.author.mention, inline=True)

            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Не удалось выдать тайм-аут")

    except Exception as e:
        await ctx.send(f"❌ Ошибка: {e}")

# Запуск ботов
async def main():
    try:
        await asyncio.gather(
            bot1.start(APPLICATION_TOKEN),
            bot2.start(MODERATION_TOKEN)
        )
    except Exception as e:
        logger.error(f"Ошибка запуска ботов: {e}")

if __name__ == "__main__":
    asyncio.run(main())