import os
import discord
from discord import app_commands
import requests
from dotenv import load_dotenv
from datetime import datetime, date
import pytz
import logging
from datetime import timedelta

# 設置日誌
logging.basicConfig(filename='bot.log', level=logging.INFO)

# 載入環境變量
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
    now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
    logging.info(f'{now}: {bot.user} 已連線到Discord!')
    try:
        synced = await tree.sync()
        logging.info(f"{now}: 已同步 {len(synced)} 條斜線命令")
    except Exception as e:
        logging.error(f"{now}: 同步命令失敗: {e}")

# 國家旗幟映射
COUNTRY_FLAGS = {
    'England': '🇬🇧', 'Spain': '🇪🇸', 'Germany': '🇩🇪', 'Italy': '🇮🇹', 'France': '🇫🇷',
    'Netherlands': '🇳🇱', 'Portugal': '🇵🇹', 'Belgium': '🇧🇪', 'Brazil': '🇧🇷', 'Argentina': '🇦🇷',
    'Bahrain': '🇧🇭', 'Australia': '🇦🇺', 'China': '🇨🇳', 'Monaco': '🇲🇨', 'Canada': '🇨🇦',
    'Austria': '🇦🇹', 'Hungary': '🇭🇺', 'Singapore': '🇸🇬', 'Japan': '🇯🇵', 'United States': '🇺🇸',
    'Mexico': '🇲🇽', 'Qatar': '🇶🇦', 'United Arab Emirates': '🇦🇪', 'Saudi Arabia': '🇸🇦',
    'British': '🇬🇧', 'Dutch': '🇳🇱', 'Spanish': '🇪🇸', 'Finnish': '🇫🇮', 'Mexican': '🇲🇽',
    'Monegasque': '🇲🇨', 'Australian': '🇦🇺', 'Canadian': '🇨🇦', 'French': '🇫🇷', 'German': '🇩🇪',
    'Italian': '🇮🇹', 'Thai': '🇹🇭', 'Azerbaijan': '🇦🇿' , 'USA': '🇺🇸'
}

# 英超球隊emoji（保留shortname and short name）
TEAM_EMOJIS = {
    'AFC Bournemouth': '<:bou:1404703461211115611> ',
    'West Ham United FC': '<:wes:1404703431414780025> ',
    'Brentford FC': '<:bre:1404703388310048799> ',
    'Brighton & Hove Albion FC': '<:bri:1404703345079353395> ',
    'Crystal Palace FC': '<:cry:1404703320974688318> ',
    'Nottingham Forest FC': '<:not:1404703264510836807> ',
    'Leeds United FC': '<:lee:1404703235821928499> ',
    'Burnley FC': '<:bur:1404703096617304186> ',
    'Wolverhampton Wanderers FC': '<:wol:1404703054913081487> ',
    'Tottenham Hotspur FC': '<:tot:1404703032385474611> ',
    'Sunderland AFC': '<:sun:1404702964354121824> ',
    'Newcastle United FC': '<:new:1404702938030669834> ',
    'Manchester United FC': '<:mu:1404702913787465739> ',
    'Manchester City FC': '<:mc:1404702893444960286> ',
    'Liverpool FC': '<:liv:1404702872259526707> ',
    'Fulham FC': '<:ful:1404702776348377160> ',
    'Everton FC': '<:eve:1404702731654008903> ',
    'Chelsea FC': '<:che:1404702690570670104> ',
    'Aston Villa FC': '<:ast:1404702655812735008> ',
    'Arsenal FC': '<:ars:1404702558374858822> ',

    'Bournemouth': '<:bou:1404703461211115611> ',
    'West Ham': '<:wes:1404703431414780025> ',
    'Brentford': '<:bre:1404703388310048799> ',
    'Brighton Hove': '<:bri:1404703345079353395> ',
    'Crystal Palace': '<:cry:1404703320974688318> ',
    'Nottingham': '<:not:1404703264510836807> ',
    'Leeds United': '<:lee:1404703235821928499> ',
    'Burnley': '<:bur:1404703096617304186> ',
    'Wolverhampton': '<:wol:1404703054913081487> ',
    'Tottenham': '<:tot:1404703032385474611> ',
    'Sunderland': '<:sun:1404702964354121824> ',
    'Newcastle': '<:new:1404702938030669834> ',
    'Man United': '<:mu:1404702913787465739> ',
    'Man City': '<:mc:1404702893444960286> ',
    'Liverpool': '<:liv:1404702872259526707> ',
    'Fulham': '<:ful:1404702776348377160> ',
    'Everton': '<:eve:1404702731654008903> ',
    'Chelsea': '<:che:1404702690570670104> ',
    'Aston Villa': '<:ast:1404702655812735008> ',
    'Arsenal': '<:ars:1404702558374858822> '
}

# 聯賽國家emoji映射
LEAGUE_EMOJI = {
    'PL': '<:PL2:1406265845239255120>',  # Premier League
    'PD': '<:laliga:1406264996429828136>',   # La Liga
    'BL1': '<:BL1:1406264975172833341>',
    'SA': '<:SA:1406265008265891930>'
    # 若有其他聯賽，可加
}

# 將UTC轉為香港時間
def to_hkt(utc_time_str):
    try:
        utc_time = datetime.fromisoformat(utc_time_str.replace('Z', '+00:00'))
        hkt_tz = pytz.timezone('Asia/Hong_Kong')
        hkt_time = utc_time.astimezone(hkt_tz)
        return hkt_time.strftime('%d/%m %H:%M')
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
        message = "<:PL2:1406265845239255120>🏆 英超積分榜:\n"
        stand = 1
        for team in standings:            
            team_name = team['team']['name']
            emoji = TEAM_EMOJIS.get(team_name, '')
            message += f"{stand}. {emoji} {team_name} - {team['points']} 分\n"
            stand += 1
        await interaction.followup.send(message)
    except requests.HTTPError as e:
        if e.response.status_code == 403:
            await interaction.followup.send("⚠️ 英超數據訪問被拒，請檢查API金鑰或訂閱權限。")
        else:
            await interaction.followup.send(f"⚠️ 無法搵到英超數據，請稍後再試。錯誤: {str(e)}")
    except requests.RequestException as e:
        await interaction.followup.send(f"⚠️ 無法搵到英超數據，請稍後再試。錯誤: {str(e)}")

# 英超賽程（最近10場）
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
        message = "<:PL2:1406265845239255120> 英超賽程（最近10場）:\n"
        if not matches:
            message += "暫無未來賽程\n"
        for match in matches:
            home = match['homeTeam']['shortName']
            away = match['awayTeam']['shortName']
            home_emoji = TEAM_EMOJIS.get(home, '')
            away_emoji = TEAM_EMOJIS.get(away, '')
            date_hkt = to_hkt(match['utcDate'])
            message += f"{date_hkt} \n{home_emoji}{home} vs {away_emoji}{away}\n\n"
        message += f"📅 剩餘比賽數: {remaining} 場"
        await interaction.followup.send(message)
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
            home = next_match['homeTeam']['shortName']
            away = next_match['awayTeam']['shortName']
            home_emoji = TEAM_EMOJIS.get(home, '')
            away_emoji = TEAM_EMOJIS.get(away, '')
            date_hkt = to_hkt(next_match['utcDate'])
            message = f"英超下場比賽: \n📅 {date_hkt} \n{home_emoji}{home} 🆚 {away_emoji}{away}"
        else:
            message = "英超下場比賽: 暫無未來比賽"
        await interaction.followup.send(message)
    except requests.HTTPError as e:
        if e.response.status_code == 403:
            await interaction.followup.send("⚠️ 英超賽程訪問被拒，請檢查API金鑰或訂閱權限。")
        else:
            await interaction.followup.send(f"⚠️ 無法搵到英超賽程，請稍後再試。錯誤: {str(e)}")
    except requests.RequestException as e:
        await interaction.followup.send(f"⚠️ 無法搵到英超賽程，請稍後再試。錯誤: {str(e)}")

# 下3場利物浦比賽
@tree.command(name="next_liverpool", description="利物浦下3場比賽")
async def next_liverpool(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        url = "https://api.football-data.org/v4/teams/64/matches?status=SCHEDULED"
        headers = {'X-Auth-Token': FOOTBALL_API_KEY}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
        future_matches = [m for m in data['matches'] if datetime.fromisoformat(m['utcDate'].replace('Z', '+00:00')).astimezone(pytz.timezone('Asia/Hong_Kong')) > now]
        matches = sorted(future_matches, key=lambda x: x['utcDate'])[:3]
        message = "利物浦下3場比賽:\n"
        if not matches:
            message += "暫無未來比賽\n"
        for match in matches:
            home = match['homeTeam']['shortName']
            away = match['awayTeam']['shortName']
            home_emoji = TEAM_EMOJIS.get(home, '')
            away_emoji = TEAM_EMOJIS.get(away, '')
            date_hkt = to_hkt(match['utcDate'])
            message += f"📅 {date_hkt}\n{home_emoji}{home} 🆚 {away_emoji}{away}\n\n"
        await interaction.followup.send(message)
    except requests.HTTPError as e:
        if e.response.status_code == 403:
            await interaction.followup.send("⚠️ 利物浦比賽數據訪問被拒，請檢查API金鑰或訂閱權限。")
        else:
            await interaction.followup.send(f"⚠️ 無法搵到利物浦比賽，請稍後再試。錯誤: {str(e)}")
    except requests.RequestException as e:
        await interaction.followup.send(f"⚠️ 無法搵到利物浦比賽，請稍後再試。錯誤: {str(e)}")

# 今日比賽賽程
@tree.command(name="today_matches", description="今日比賽賽程")
async def today_matches(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        #today = (date.today()).strftime('%Y-%m-%d')
        #tomorrow = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        url = f"https://api.football-data.org/v4/matches"#?dateFrom={today}&dateTo={tomorrow}"
        headers = {'X-Auth-Token': FOOTBALL_API_KEY}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        filtered_codes = ['DED', 'PPL', 'ELC', 'BSA', 'CLI', 'FL1']
        filtered_matches = [m for m in data['matches'] if m['competition']['code'] not in filtered_codes]
        matches = sorted(filtered_matches, key=lambda x: x['utcDate'])
        message = "⚽ 今日比賽賽程:\n"
        if not matches:
            message += "暫無今日比賽\n"
        for match in matches:
            home = match['homeTeam']['shortName']
            away = match['awayTeam']['shortName']
            home_emoji = TEAM_EMOJIS.get(home, '')
            away_emoji = TEAM_EMOJIS.get(away, '')
            date_hkt = to_hkt(match['utcDate'])
            comp_code = match['competition']['code']
            league_name = "La Liga" if match['competition']['name'] == "Primera Division" else match['competition']['name']
            league_emoji = LEAGUE_EMOJI.get(comp_code, '')
            live_emoji = '<:LIVE3:1406332600900915232> ' if match['status'] == 'IN_PLAY' else '<:HT:1406255894643216435> ' if match['status'] == 'PAUSED' else '**Finished** ' if match['status'] == 'FINISHED' else ''
            if match['status'] == 'IN_PLAY' or match['status'] == 'PAUSED' or match['status'] == 'FINISHED':
                score = f"| {match['score']['fullTime']['home']} : {match['score']['fullTime']['away']}"
            else:
                score = ''
            message += f"{date_hkt} | {league_emoji} {league_name}\n{live_emoji}{home_emoji}**{home}** vs {away_emoji}**{away}** {score}\n\n"
            #print(url)
        await interaction.followup.send(message)
    except requests.HTTPError as e:
        if e.response.status_code == 403:
            await interaction.followup.send("⚠️ 今日比賽數據訪問被拒，請檢查API金鑰或訂閱權限。")
        else:
            await interaction.followup.send(f"⚠️ 無法搵到今日比賽，請稍後再試。錯誤: {str(e)}")
    except requests.RequestException as e:
        await interaction.followup.send(f"⚠️ 無法搵到今日比賽，請稍後再試。錯誤: {str(e)}")

# F1賽程（最近5場未來比賽）
@tree.command(name="f1_schedule", description="F1賽程（最近5場未來比賽）")
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
        message = "🏎️ F1賽程（最近5場）:\n"
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

bot.run(TOKEN)