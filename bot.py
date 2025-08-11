import os
import discord
from discord import app_commands
import requests
from dotenv import load_dotenv
import time
from datetime import datetime
import pytz

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
FOOTBALL_API_KEY = os.getenv('FOOTBALL_API_KEY')

# 設定bot，intent允許讀訊息
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    print(f'{bot.user} 已連線到Discord!')
    try:
        synced = await tree.sync()
        print(f"已同步 {len(synced)} 條斜線命令")
    except Exception as e:
        print(f"同步命令失敗: {e}")

# 國家旗幟映射
COUNTRY_FLAGS = {
    'England': '🇬🇧', 'Spain': '🇪🇸', 'Germany': '🇩🇪', 'Italy': '🇮🇹', 'France': '🇫🇷',
    'Netherlands': '🇳🇱', 'Portugal': '🇵🇹', 'Belgium': '🇧🇪', 'Brazil': '🇧🇷', 'Argentina': '🇦🇷',
    'Bahrain': '🇧🇭', 'Australia': '🇦🇺', 'China': '🇨🇳', 'Monaco': '🇲🇨', 'Canada': '🇨🇦',
    'Austria': '🇦🇹', 'Hungary': '🇭🇺', 'Singapore': '🇸🇬', 'Japan': '🇯🇵', 'United States': '🇺🇸',
    'Mexico': '🇲🇽', 'Qatar': '🇶🇦', 'United Arab Emirates': '🇦🇪', 'Saudi Arabia': '🇸🇦',
    'British': '🇬🇧', 'Dutch': '🇳🇱', 'Spanish': '🇪🇸', 'Finnish': '🇫🇮', 'Mexican': '🇲🇽',
    'Monegasque': '🇲🇨', 'Australian': '🇦🇺', 'Canadian': '🇨🇦', 'French': '🇫🇷', 'German': '🇩🇪',
    'Italian': '🇮🇹', 'Thai': '🇹🇭', 'Azerbaijan': '🇦🇿'
}

# 將UTC轉為香港時間
def to_hkt(utc_time_str):
    try:
        utc_time = datetime.fromisoformat(utc_time_str.replace('Z', '+00:00'))
        hkt_tz = pytz.timezone('Asia/Hong_Kong')
        hkt_time = utc_time.astimezone(hkt_tz)
        return hkt_time.strftime('%Y-%m-%d %H:%M')
    except:
        return "時間格式錯誤"

# 英超積分榜（全部隊伍）
@tree.command(name="pl_standings", description="英超積分榜")
async def pl_standings(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        url = "https://api.football-data.org/v4/competitions/PL/standings"
        headers = {'X-Auth-Token': FOOTBALL_API_KEY}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        standings = data['standings'][0]['table']
        message = "🏆 英超積分榜:\n"
        for team in standings:
            message += f"{team['team']['name']} - {team['points']} 分\n"
        await interaction.followup.send(message)
        time.sleep(6)
    except requests.HTTPError as e:
        if e.response.status_code == 403:
            await interaction.followup.send("⚠️ 英超數據訪問被拒，請檢查API金鑰或訂閱權限。")
        else:
            await interaction.followup.send(f"⚠️ 無法搵到英超數據，請稍後再試。錯誤: {str(e)}")
    except requests.RequestException as e:
        await interaction.followup.send(f"⚠️ 無法搵到英超數據，請稍後再試。錯誤: {str(e)}")

# 英超賽程（最近10場，無旗幟）
@tree.command(name="pl_schedule", description="英超賽程（最近10場）")
async def pl_schedule(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        url = "https://api.football-data.org/v4/competitions/PL/matches?status=SCHEDULED"
        headers = {'X-Auth-Token': FOOTBALL_API_KEY}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
        future_matches = [m for m in data['matches'] if datetime.fromisoformat(m['utcDate'].replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Hong_Kong')) > now]
        matches = sorted(future_matches, key=lambda x: x['utcDate'])[:10]
        remaining = len(future_matches)
        message = "⚽ 英超賽程（最近10場）:\n"
        if not matches:
            message += "暫無未來賽程\n"
        for match in matches:
            home = match['homeTeam']['name']
            away = match['awayTeam']['name']
            date_hkt = to_hkt(match['utcDate'])
            message += f"{date_hkt} {home} 🆚 {away}\n"
        message += f"📅 剩餘比賽數: {remaining} 場"
        await interaction.followup.send(message)
        time.sleep(6)
    except requests.HTTPError as e:
        if e.response.status_code == 403:
            await interaction.followup.send("⚠️ 英超賽程訪問被拒，請檢查API金鑰或訂閱權限。")
        else:
            await interaction.followup.send(f"⚠️ 無法搵到英超賽程，請稍後再試。錯誤: {str(e)}")
    except requests.RequestException as e:
        await interaction.followup.send(f"⚠️ 無法搵到英超賽程，請稍後再試。錯誤: {str(e)}")

# 英超下場比賽
@tree.command(name="pl_next", description="英超下場比賽")
async def pl_next(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        url = "https://api.football-data.org/v4/competitions/PL/matches?status=SCHEDULED"
        headers = {'X-Auth-Token': FOOTBALL_API_KEY}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
        next_match = next((m for m in sorted(data['matches'], key=lambda x: x['utcDate']) if datetime.fromisoformat(m['utcDate'].replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Hong_Kong')) > now), None)
        if next_match:
            home = next_match['homeTeam']['name']
            away = next_match['awayTeam']['name']
            date_hkt = to_hkt(next_match['utcDate'])
            message = f"下場比賽: \n📅{date_hkt} \n{home} 🆚 {away}"
        else:
            message = "下場比賽: 暫無未來比賽"
        await interaction.followup.send(message)
        time.sleep(6)
    except requests.HTTPError as e:
        if e.response.status_code == 403:
            await interaction.followup.send("⚠️ 英超賽程訪問被拒，請檢查API金鑰或訂閱權限。")
        else:
            await interaction.followup.send(f"⚠️ 無法搵到英超賽程，請稍後再試。錯誤: {str(e)}")
    except requests.RequestException as e:
        await interaction.followup.send(f"⚠️ 無法搵到英超賽程，請稍後再試。錯誤: {str(e)}")

# 歐聯賽程
@tree.command(name="cl_schedule", description="歐聯賽程（最近5場）")
async def cl_schedule(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        url = "https://api.football-data.org/v4/competitions/CL/matches?status=SCHEDULED"
        headers = {'X-Auth-Token': FOOTBALL_API_KEY}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
        future_matches = [m for m in data['matches'] if datetime.fromisoformat(m['utcDate'].replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Hong_Kong')) > now]
        matches = sorted(future_matches, key=lambda x: x['utcDate'])[:5]
        remaining = len(future_matches)
        message = "⚽ 歐聯賽程（最近5場）:\n"
        if not matches:
            message += "暫無未來賽程\n"
        for match in matches:
            home = match['homeTeam']['name']
            away = match['awayTeam']['name']
            date_hkt = to_hkt(match['utcDate'])
            home_flag = COUNTRY_FLAGS.get(match.get('homeTeam', {}).get('country', 'England'), '🏳️')
            away_flag = COUNTRY_FLAGS.get(match.get('awayTeam', {}).get('country', 'England'), '🏳️')
            message += f"{date_hkt} {home_flag} {home} 🆚 {away} {away_flag}\n"
        message += f"📅 剩餘比賽數: {remaining} 場"
        await interaction.followup.send(message)
        time.sleep(6)
    except requests.HTTPError as e:
        if e.response.status_code == 403:
            await interaction.followup.send("⚠️ 歐聯賽程訪問被拒，請檢查API金鑰或訂閱權限。")
        else:
            await interaction.followup.send(f"⚠️ 無法搵到歐聯賽程，請稍後再試。錯誤: {str(e)}")
    except requests.RequestException as e:
        await interaction.followup.send(f"⚠️ 無法搵到歐聯賽程，請稍後再試。錯誤: {str(e)}")

# 歐聯下場比賽
@tree.command(name="cl_next", description="歐聯下場比賽")
async def cl_next(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        url = "https://api.football-data.org/v4/competitions/CL/matches?status=SCHEDULED"
        headers = {'X-Auth-Token': FOOTBALL_API_KEY}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
        next_match = next((m for m in sorted(data['matches'], key=lambda x: x['utcDate']) if datetime.fromisoformat(m['utcDate'].replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Hong_Kong')) > now), None)
        if next_match:
            home = next_match['homeTeam']['name']
            away = next_match['awayTeam']['name']
            date_hkt = to_hkt(next_match['utcDate'])
            home_flag = COUNTRY_FLAGS.get(next_match.get('homeTeam', {}).get('country', 'England'), '🏳️')
            away_flag = COUNTRY_FLAGS.get(next_match.get('awayTeam', {}).get('country', 'England'), '🏳️')
            message = f"歐聯下場比賽: \n📅{date_hkt} \n{home_flag} {home} 🆚 {away} {away_flag}"
        else:
            message = "歐聯下場比賽: 暫無未來比賽"
        await interaction.followup.send(message)
        time.sleep(6)
    except requests.HTTPError as e:
        if e.response.status_code == 403:
            await interaction.followup.send("⚠️ 歐聯賽程訪問被拒，請檢查API金鑰或訂閱權限。")
        else:
            await interaction.followup.send(f"⚠️ 無法搵到歐聯賽程，請稍後再試。錯誤: {str(e)}")
    except requests.RequestException as e:
        await interaction.followup.send(f"⚠️ 無法搵到歐聯賽程，請稍後再試。錯誤: {str(e)}")

# F1賽程（最近5場未來比賽）
@tree.command(name="f1_schedule", description="F1當季賽程（最近5場未來比賽）")
async def f1_schedule(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        url = "https://api.jolpi.ca/ergast/f1/current.json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
        future_races = [r for r in data['MRData']['RaceTable']['Races'] if datetime.fromisoformat(f"{r['date']}T{r['time']}".replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Hong_Kong')) > now]
        races = sorted(future_races, key=lambda x: f"{x['date']}T{x['time']}")[:5]
        remaining = len(future_races)
        message = "🏎️ F1賽程表（最近5場）:\n"
        if not races:
            message += "暫無未來賽程\n"
        for race in races:
            date_time = f"{race['date']}T{race['time']}"
            date_hkt = to_hkt(date_time)
            name = race['raceName']
            country = race['Circuit']['Location']['country']
            flag = COUNTRY_FLAGS.get(country, '🏳️')
            message += f"{date_hkt} {flag} {name}\n"
        message += f"📅 剩餘比賽數: {remaining} 場"
        await interaction.followup.send(message)
    except requests.RequestException as e:
        await interaction.followup.send(f"⚠️ 無法搵到F1賽程，請稍後再試。錯誤: {str(e)}")

# F1下場比賽（含排位賽時間）
@tree.command(name="f1_next", description="F1下場比賽")
async def f1_next(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        url = "https://api.jolpi.ca/ergast/f1/current.json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
        next_race = next((r for r in sorted(data['MRData']['RaceTable']['Races'], key=lambda x: f"{x['date']}T{x['time']}") if datetime.fromisoformat(f"{r['date']}T{r['time']}".replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Hong_Kong')) > now), None)
        if next_race:
            date_time = f"{next_race['date']}T{next_race['time']}"
            date_hkt = to_hkt(date_time)
            name = next_race['raceName']
            country = next_race['Circuit']['Location']['country']
            flag = COUNTRY_FLAGS.get(country, '🏳️')
            quali_date_time = f"{next_race['Qualifying']['date']}T{next_race['Qualifying']['time']}"
            quali_hkt = to_hkt(quali_date_time)
            message = f"F1下場比賽: \n{date_hkt} \n{flag} {name}\n排位賽: {quali_hkt}"
        else:
            message = "F1下場比賽: 暫無未來比賽"
        await interaction.followup.send(message)
    except requests.RequestException as e:
        await interaction.followup.send(f"⚠️ 無法搵到F1賽程，請稍後再試。錯誤: {str(e)}")

# F1車手積分榜（頭10）
@tree.command(name="f1_standings", description="F1車手榜")
async def f1_standings(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        url = "https://api.jolpi.ca/ergast/f1/current/driverStandings.json"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        standings = data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings'][:10]
        message = "🏆 F1車手積分榜（頭10）:\n"
        for driver in standings:
            name = driver['Driver']['givenName'] + " " + driver['Driver']['familyName']
            points = driver['points']
            nationality = driver['Driver']['nationality']
            flag = COUNTRY_FLAGS.get(nationality, '🏳️')
            message += f"{flag} {name} - {points} 分\n"
        await interaction.followup.send(message)
    except requests.RequestException as e:
        await interaction.followup.send(f"⚠️ 無法搵到F1積分，請稍後再試。錯誤: {str(e)}")

# 下場利物浦比賽
@tree.command(name="next_liverpool", description="利物浦下場比賽")
async def next_liverpool(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        url = "https://api.football-data.org/v4/competitions/PL/matches?status=SCHEDULED"
        headers = {'X-Auth-Token': FOOTBALL_API_KEY}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
        next_match = next((m for m in sorted(data['matches'], key=lambda x: x['utcDate']) if (m['homeTeam']['name'] == "Liverpool FC" or m['awayTeam']['name'] == "Liverpool FC") and datetime.fromisoformat(m['utcDate'].replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Hong_Kong')) > now), None)
        if next_match:
            home = next_match['homeTeam']['name']
            away = next_match['awayTeam']['name']
            date_hkt = to_hkt(next_match['utcDate'])
            message = f"利物浦下場比賽:\n📅 {date_hkt} \n{home} 🆚 {away}"
        else:
            message = "下場比賽: 暫無未來比賽"
        await interaction.followup.send(message)
        time.sleep(6)
    except requests.HTTPError as e:
        if e.response.status_code == 403:
            await interaction.followup.send("⚠️ 利物浦比賽數據訪問被拒，請檢查API金鑰或訂閱權限。")
        else:
            await interaction.followup.send(f"⚠️ 無法搵到利物浦比賽，請稍後再試。錯誤: {str(e)}")
    except requests.RequestException as e:
        await interaction.followup.send(f"⚠️ 無法搵到利物浦比賽，請稍後再試。錯誤: {str(e)}")

bot.run(TOKEN)