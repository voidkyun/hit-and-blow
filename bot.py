import discord
from discord import app_commands
import re
import asyncio
import datetime
import random

TOKEN = 'Your token here'
intents = discord.Intents.all()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

class HitBlowMenue(discord.ui.View):
	@discord.ui.button(label='join',style=discord.ButtonStyle.primary)
	async def join(self, ctx:discord.Integration, button:discord.ui.Button):
		if ctx.user.id in self.members:
			await ctx.response.send_message('You have already joined!',ephemeral=True)
		elif len(self.members)>=self.digits:
			await ctx.response.send_message(f'Up to {self.digits} people!',ephemeral=True)
		else:
			await ctx.response.defer()
			self.members.append(ctx.user.id)
			content=f'## Hit&Blow\ndigits: {self.digits}\nmembers: '
			guild=ctx.guild
			for i in self.members:
				content+=guild.get_member(i).display_name+','
			content=content[:-1]
			await ctx.followup.edit_message(message_id=self.menue_message.id,content=content)
	@discord.ui.button(label='leave',style=discord.ButtonStyle.secondary)
	async def leave(self, ctx:discord.Integration, button:discord.ui.Button):
		if not(ctx.user.id in self.members):
			await ctx.response.send_message('You are not in the members!',ephemeral=True)
		else:
			await ctx.response.defer()
			self.members.remove(ctx.user.id)
			content=f'## Hit&Blow\ndigits: {self.digits}\nmembers: '
			guild=ctx.guild
			for i in self.members:
				content+=guild.get_member(i).display_name+','
			content=content[:-1]
			await ctx.followup.edit_message(message_id=self.menue_message.id,content=content)
	@discord.ui.button(label='start',style=discord.ButtonStyle.green)
	async def start(self, ctx:discord.Integration, button:discord.ui.Button):
		self.join.disabled=True
		self.leave.disabled=True
		button.disabled=True
		await ctx.response.edit_message(view=self)	
		master_numbers=random.sample(self.answer,len(self.members))
		for c,i in enumerate(self.members):
			self.guess[str(i)]=['## ']
			for j in self.answer:
				if j==master_numbers[c]:
					self.guess[str(i)][0]+=f'{j}  '
				else:
					self.guess[str(i)][0]+='?  '
			temp='guess'
			for _ in range(self.digits-len(temp)):
				temp+=' '
			self.guess[str(i)][0]+=f'\n```json\n{temp} H B name\n```'
			user=client.get_user(i)
			views=HitBlowGuess(self)
			sent_guess_message=await user.send(content=self.guess[str(i)][0],view=views)
			self.guess[str(i)].append(sent_guess_message.id)
		self.stime=datetime.datetime.now()
		while(datetime.datetime.now()-self.stime<datetime.timedelta(minutes=30) and not(self.IsFinished)):
			await views.reload()
			await asyncio.sleep(10)
	def __init__(self, *args, timeout: float | None = 180):
		super().__init__(timeout=timeout)
		self.digits=args[0]
		self.answer=random.sample(range(10),self.digits)
		self.members=[args[1].id]
		self.guess={}
		self.menue_message=args[2]
		self.menue_guild=args[3]
		self.IsFinished=False
		self.stime=datetime.datetime.now()
		
class HitBlowGuess(discord.ui.View):
	def __init__(self, menue:HitBlowMenue, timeout: float | None = 180):
		super().__init__(timeout=timeout)
		self.menue=menue
	@discord.ui.button(label='guess',style=discord.ButtonStyle.green)
	async def guess(self, ctx:discord.Integration,button:discord.ui.Button):
		channel=ctx.channel
		messages = [message async for message in channel.history(limit=5)]
		last_message=messages[0]
		def int_or_0(ch:str):
			try:
				return(int(ch))
			except:
				return(0)
		guess_numbers=list(map(int_or_0,last_message.content))
		if last_message.author.id==ctx.user.id and re.fullmatch(r'\d{'+re.escape(str(self.menue.digits))+r'}',last_message.content):
			await ctx.response.defer()
			for key,value in self.menue.guess.items():
				hit=0
				blow=0
				menue_guild=self.menue.menue_guild
				for c,i in enumerate(guess_numbers):
					if i==self.menue.answer[c]:
						hit+=1
					elif i in self.menue.answer:
						blow+=1
				temp=last_message.content
				if self.menue.digits<5:
					for i in range(5-self.menue.digits):
						temp+=' '
				self.menue.guess[key][0]=value[0][:-3]+f'{temp} {hit} {blow} {menue_guild.get_member(ctx.user.id).display_name}\n```'
				user=client.get_user(int(key))
				guess_message=await user.dm_channel.fetch_message(value[1])
				await guess_message.edit(content=self.menue.guess[key][0])
				if hit==self.menue.digits:
					button.disabled=True
					self.how_to_guess.disabled=True
					await guess_message.edit(view=self)
					await user.send(content=f'## Winner: {menue_guild.get_member(ctx.user.id).display_name}!!')
					self.menue.is_finished=True
		else:
			await ctx.response.send_message('Invalid text!',ephemeral=True)
	@discord.ui.button(label='How to guess?',style=discord.ButtonStyle.grey)
	async def how_to_guess(self, ctx:discord.Interaction,button:discord.ui.Button):
		await ctx.response.send_message(file=discord.File('how_to_guess.gif'),ephemeral=True)
	async def reload(args):
		pass


@tree.command(
	name='hb',
	description='Hit&Blow'
)
async def hitblow(ctx:discord.Interaction,digits:int):
	if 1<=digits<=10:
		await ctx.response.defer()
		menue=await ctx.followup.send('preparing...')
		views=HitBlowMenue(digits,ctx.user,menue,ctx.guild)
		content=f'## Hit&Blow\ndigits: {digits}\nmembers: '
		guild=ctx.guild
		for i in views.members:
			content+=guild.get_member(i).display_name+','
		content=content[:-1]
		await ctx.followup.edit_message(message_id=menue.id,content=content,view=views)
	else:
		await ctx.response.send_message('Failed!',ephemeral=True)

@client.event
async def on_ready():
	print('Succesfully logined')
	await tree.sync()

client.run(TOKEN)