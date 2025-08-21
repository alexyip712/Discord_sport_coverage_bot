import discord
import re
from typing import List, Optional
import logging
import asyncio
from discord.ui import Button, View

# 設置日誌
logger = logging.getLogger('twitter_handler')
logger.setLevel(logging.INFO)
handler = logging.FileHandler('bot.log')
handler.setFormatter(logging.Formatter('%(asctime)s: %(levelname)s: %(name)s: %(message)s'))
logger.addHandler(handler)

# 提取 x.com 或 twitter.com 連結
async def extract_x_links(message: str) -> List[str]:
    pattern = r'https?://(?:www\.)?(x|twitter)\.com/(\w+/status/\d+)(?:\?\S*)?'
    links = re.findall(pattern, message, re.IGNORECASE)
    return [f"https://{domain}.com/{path}" for domain, path in links]

# 將 x.com/twitter.com 轉為 fixupx.com 子域名
def replace_to_fixupx(url: str, subdomain: str = '') -> str:
    base = url.replace('x.com', 'fixupx.com').replace('twitter.com', 'fixupx.com')
    if subdomain:
        return base.replace('fixupx.com', f'{subdomain}.fixupx.com')
    return base

# 按鈕視圖類
class TweetView(discord.ui.View):
    def __init__(self, original_url: str, timeout: float = 600.0):
        super().__init__(timeout=timeout)
        self.original_url = original_url

    @discord.ui.button(label="Gallery", style=discord.ButtonStyle.secondary, custom_id="gallery_button")
    async def gallery_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        fixupx_url = replace_to_fixupx(self.original_url, 'g')
        logger.debug(f"更新回覆為 Gallery 連結: {fixupx_url}")
        await interaction.response.edit_message(content=fixupx_url)

    @discord.ui.button(label="Download", style=discord.ButtonStyle.secondary, custom_id="download_button")
    async def download_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        fixupx_url = replace_to_fixupx(self.original_url, 'd')
        logger.debug(f"更新回覆為 Download 連結: {fixupx_url}")
        await interaction.response.edit_message(content=fixupx_url)

    @discord.ui.button(label="Origin", style=discord.ButtonStyle.secondary, custom_id="origin_button")
    async def origin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        fixupx_url = replace_to_fixupx(self.original_url)
        logger.debug(f"更新回覆為 Origin 連結: {fixupx_url}")
        await interaction.response.edit_message(content=fixupx_url)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, custom_id="delete_button")
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        logger.debug("刪除回覆訊息")
        await interaction.response.defer()
        await interaction.message.delete()

# 主處理函數
async def process_x_links(message: discord.Message) -> List[dict]:
    links = await extract_x_links(message.content)
    if not links:
        logger.debug("無 x.com 或 twitter.com 連結")
        return []
    
    results = []
    for link in links:
        logger.debug(f"發現連結: {link}")
        fixupx_url = replace_to_fixupx(link)
        view = TweetView(link)
        
        # 壓制原始嵌入
        try:
            await message.edit(suppress=True)
        except discord.errors.Forbidden:
            logger.error("無法壓制原始嵌入：缺少 manage_messages 權限")
        except Exception as e:
            logger.error(f"無法壓制原始嵌入: {str(e)}")
        
        results.append({
            'type': 'reply',
            'result': {
                'content': fixupx_url,
                'view': view
            }
        })
        # 添加延遲避免速率限制
        await asyncio.sleep(0.5)
    
    return results