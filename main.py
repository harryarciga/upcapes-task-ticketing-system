"""
    This main.py file is responsible for running the task ticketing system itself. Please
    ask Harry Arciga for credentials.json and apikeys.py since these files can't be shared in
    Github (nag-aautomatic change siya ng keys and stuff once na-share sa Github huhu)
    
    If downloaded, Ctrl F niyo lang then type "Change this" to change links, IDs, etc.

"""

import discord
import time
from discord.ext import commands

import task_checker

from googleapiclient.discovery import build
from google.oauth2 import service_account


from apikeys import * 

import subprocess
subprocess.Popen(["python", "task_checker.py"])


     
SERVICE_ACCOUNT_FILE = "/home/harryarciga/task-ticketing-system/credentials.json"  # Change this to the path of credentials.json
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1DLGU03Z-3UxcL-zUGQcv34VonNVQ8tZ8YUaBj3KdSHM"  # Change this to the Google Spreadsheet ID
RANGE_NAME = "Tickets!B12:B503"  # You may adjust this once the tasks are over 500

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("sheets", "v4", credentials=credentials)

intents = discord.Intents.all()
client = commands.Bot(command_prefix='!', intents=intents)

def get_next_task_id():
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="Tickets!A:A"
        ).execute()

        values = result.get("values", [])
        if not values or not values[0]:
            return "2425-00001"

        last_task_id = values[-1][0]

        prefix, num = last_task_id.split("-")
        next_num = int(num) + 1
        return f"{prefix}-{next_num:05d}"

    except Exception as e:
        print(f"Error fetching the last task ID: {e}")
        return "2425-00001"

def add_to_google_sheets(data):
    values = [data]
    body = {"values": values}
    try:
        result = (
            service.spreadsheets()
            .values()
            .append(
                spreadsheetId=SPREADSHEET_ID,
                range="Tickets!A:O",
                valueInputOption="USER_ENTERED",
                body=body,
            )
            .execute()
        )
        print(f"{result.get('updates').get('updatedRows')} row/s appended.")
    except Exception as e:
        print(f"Error appending to Google Sheets: {e}")

def update_task_in_google_sheets(task_id, updated_data):
    try:
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range="Tickets!A:O"
        ).execute()

        rows = result.get("values", [])
        
        if not rows:
            print("Sheet is empty or range is invalid.")
            return
        

        row_index = None
        for index, row in enumerate(rows):
            if row and row[0] == task_id:
                row_index = index + 1
                break

        if row_index is None:
            print(f"Task ID {task_id} not found in the sheet.")
            return

        update_range = f"Tickets!A{row_index}:O{row_index}"

        body = {
            "values": [updated_data]
        }

        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=update_range,
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()

        print(f"Task ID {task_id} successfully updated.")
    except Exception as e:
        print(f"Error updating task in Google Sheets: {e}")

async def show_embed():
    print("The bot is now ready for use!")
    print("-----------------------------")

    channel_id = 1302238822720868374  # Change this to the text channel id
    channel = client.get_channel(channel_id)

    if channel:
        embed = discord.Embed(
            title="UP CAPES Task Ticketing System",
            description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button\nor modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
            color=0xffcc1a
        )

        view = MyView()

        await channel.send(embed=embed, view=view)
    else:
        print(f"Channel with ID {channel_id} not found.")


@client.event
async def on_ready():
    await show_embed() 

class MyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create Task", style=discord.ButtonStyle.primary)
    async def create_task(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message("Please select the **context** of the task:\n*Choose **Restart** if you want to restart again from the beginning*.", view=DropdownView("task_context","","",""), ephemeral=True)

    @discord.ui.button(label="Edit Task", style=discord.ButtonStyle.secondary)
    async def edit_task(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Please type the **task ID** of the task you wish to change in the chatbox below with this format: 2425-XXXXX",
            ephemeral=True,
        )
        

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        while True:
            msg = await client.wait_for("message", check=check)
            task_id = msg.content.strip()
            await msg.delete() 

            try:
                # Get all rows from the sheet
                result = service.spreadsheets().values().get(
                    spreadsheetId=SPREADSHEET_ID,
                    range="Tickets!A:O"
                ).execute()

                rows = result.get("values", [])
                headers = rows[0] 
                data_rows = rows[1:]

                task_details = None
                for row in data_rows:
                    if len(row) > 0 and row[0] == task_id:
                        task_details = row
                        break

                if task_details:
                    (
                        task_context,
                        task_description,
                        task_priority,
                        task_status,
                        requesting_committee,
                        committee_responsible,
                        subcommittee_responsible,
                        receiving_committee,
                        resolved_status,
                        deadline,
                        notes,
                        creator_mention,
                        respo_mentions,
                        cc
                    ) = task_details[1:]

                    await interaction.followup.send(
                        f"Task ID **{task_id}** found!. Here are the details of the task id:",
                        ephemeral=True,
                    )


                    embed = discord.Embed(
                        title=f"Task ID: {task_id}!",
                        description=(
                            f"**Task ID:** {task_id}\n"
                            f"**Task Name:** {task_description}\n"
                            f"**Task Context:** {task_context}\n"
                            f"**Task Priority:** {task_priority}\n"
                            f"**Task Status:** {task_status}\n"
                            f"**Requesting Committee:** {requesting_committee}\n"
                            f"**Committee Responsible:** {committee_responsible}\n"
                            f"**Subcommittee Responsible:** {subcommittee_responsible}\n"
                            f"**Receiving Committee:** {receiving_committee}\n"
                            f"**Resolved Status:** {"Resolved" if resolved_status == "TRUE" else "Not Yet Resolved"}\n"
                            f"**Due Date:** {deadline}\n"
                            f"**Notes:** {notes}\n"
                            f"**Task Creator:** {creator_mention}\n"
                            f"**Person/s in Charge:** {respo_mentions}\n"
                            f"\n"
                            f"***CC:** {cc}*"
                        ),
                        color=0xffcc1a,
                    )

                    channel_id = 1302238822720868374  # Change this to actual channel ID
                    channel = client.get_channel(channel_id)


                    time.sleep(0.2)

                    await channel.send(embed = embed)

                    await interaction.followup.send(
                        f"Is there anything you wish to change on the task details?\n*Choose **Restart** if you want to restart again from the beginning*.",
                        view=DropdownView("to_change", task_id, task_context, task_description, task_priority, task_status, requesting_committee, committee_responsible, subcommittee_responsible, receiving_committee, resolved_status, deadline, notes, creator_mention, respo_mentions, cc),
                        ephemeral=True,
                    )

                    break
                else:
                    await interaction.followup.send(
                        f"Task ID **{task_id}** was not found. Please try again with a valid Task ID.",
                        ephemeral=True,
                    )
            except Exception as e:
                print(f"Error checking Google Sheets: {e}")
                await interaction.followup.send(
                    "An error occurred while checking the Task ID. Please try again later.",
                    ephemeral=True,
                )
                break


class TaskContextDropdown(discord.ui.Select):
    def __init__(self, change="", task_id="", task_context="", task_description="", task_priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", creator_mention="", respo_mentions="", cc=""): 
        self.task_id = task_id
        self.task_context = task_context
        self.task_name = task_description
        self.task_priority = task_priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        self.creator_mention = creator_mention
        self.respo_mentions = respo_mentions
        self.cc = cc

        options = [
            discord.SelectOption(label="Year-long"),
            discord.SelectOption(label="One-time"),
            discord.SelectOption(label="Taiwan"),
            discord.SelectOption(label="CAPES Week"),
            discord.SelectOption(label="Upskill"),
            discord.SelectOption(label="JobFair"),
            discord.SelectOption(label="Mixer"),
            discord.SelectOption(label="Restart", description="Choose this if you want to start again from the beginning.")
        ]
        super().__init__(placeholder="Please select the context of the task...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_context = self.values[0]

        if selected_context == "Restart":
            await interaction.response.defer()

            channel_id = 1302238822720868374 # Change this to actual channel ID
            channel = client.get_channel(channel_id)

            embed = discord.Embed(
            title="UP CAPES Task Ticketing System",
            description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button or modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
            color=0xffcc1a
            )
            embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")

            view = MyView()

            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        elif self.change == "yes" and selected_context != "Restart":
            await interaction.response.defer(ephemeral=True)
            
            await interaction.followup.send(
                f"You have selected **{selected_context}** as your context.\nIs there anything you wish to change on the task details?\n*Choose **Restart** if you want to restart again from the beginning*.",
                view=DropdownView("to_change", self.task_id, selected_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc),
                ephemeral=True
            )
            

            
        elif self.change != "yes" and selected_context != "Restart":
            await interaction.response.send_message(
                f"You have selected **{selected_context}** as your context. Please type your **task description** in the chatbox below.\n*Type **R** if you want to restart again from the beginning*.",
                ephemeral=True
            )
 
            def check(msg):
                return msg.author == interaction.user and msg.channel == interaction.channel

            msg = await client.wait_for("message", check=check)
            task_name = msg.content
            await msg.delete() 

            if task_name == "R":
                channel_id = 1302238822720868374  # Change this to actual channel ID
                channel = client.get_channel(channel_id)

                embed = discord.Embed(
                title="UP CAPES Task Ticketing System",
                description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button or modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
                color=0xffcc1a
                )
                embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")

                view = MyView()

                await interaction.followup.send(embed=embed, view=view, ephemeral=True)

            else:
                await interaction.followup.send(
                    f"You wrote **{task_name}** as the task description. Please select the **priority** of the task:\n*Choose **Restart** if you want to restart again from the beginning*.",
                    view=DropdownView(section="priority", context=selected_context, task_name=task_name),
                    ephemeral=True
                )

class TaskPriorityDropdown(discord.ui.Select):
    def __init__(self, change="", task_id="", task_context="", task_description="", task_priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", creator_mention="", respo_mentions="", cc=""):
        self.task_id = task_id
        self.task_context = task_context
        self.task_description = task_description
        self.task_priority = task_priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        self.creator_mention = creator_mention
        self.respo_mentions = respo_mentions
        self.cc = cc

        options = [
            discord.SelectOption(label="P0 - Critical"),
            discord.SelectOption(label="P1 - High"),
            discord.SelectOption(label="P2 - Moderate"),
            discord.SelectOption(label="P3 - Low"),
            discord.SelectOption(label="P4 - Optional"),
            discord.SelectOption(label="Restart", description="Choose this if you want to start again from the beginning.")
        ]
        super().__init__(placeholder="Select the priority of the task...", options=options)


    async def callback(self, interaction: discord.Interaction):
        selected_priority = self.values[0]

        if selected_priority == "Restart":
            await interaction.response.defer()

            channel_id = 1302238822720868374  # Change this to actual channel ID
            channel = client.get_channel(channel_id)

            embed = discord.Embed(
            title="UP CAPES Task Ticketing System",
            description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button or modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
            color=0xffcc1a
            )
            embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")

            view = MyView()

            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        elif self.change == "yes" and selected_priority != "Restart":
            await interaction.response.defer(ephemeral=True)

            await interaction.followup.send(
                f"You have selected **{selected_priority}** as your task priority.\nIs there anything you wish to change on the task details?\n*Choose **Restart** if you want to restart again from the beginning*.",
                view=DropdownView("to_change", self.task_id, self.task_context, self.task_description, selected_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc),
                ephemeral=True
            )

        else:
            await interaction.response.send_message(f"You have selected **{selected_priority}** as your task priority. Select the **committee requesting** for the task:\n*Choose **Restart** if you want to restart again from the beginning*.", view=DropdownView("requesting_committee", context=self.task_context, task_name=self.task_description, priority=selected_priority), ephemeral=True)


class CommitteeDropdown(discord.ui.Select):
    def __init__(self, change="", label="", task_id="", context="", task_name="", priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", creator_mention="", respo_mentions="", cc=""):
        self.task_id = task_id
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        self.label = label
        self.creator_mention = creator_mention
        self.respo_mentions = respo_mentions
        self.cc = cc

        options = [
            discord.SelectOption(label="SB"),
            discord.SelectOption(label="CM"),
            discord.SelectOption(label="CX"),
            discord.SelectOption(label="HR"),
            discord.SelectOption(label="IT"),
            discord.SelectOption(label="MK"),
            discord.SelectOption(label="FS"),
            discord.SelectOption(label="Restart", description="Choose this if you want to start again from the beginning.")
        ]
        if self.label == "requesting_committee":
            super().__init__(placeholder="Select the committee requesting the task...", options=options)
        elif self.label == "committee_responsible":
            super().__init__(placeholder="Select the committee assigned or responsible for the task...", options=options)
        elif self.label == "receiving_committee":
            super().__init__(placeholder="Select the committee receiving the output of the task...", options=options)

    async def callback(self, interaction: discord.Interaction):
        cc = interaction.user.mention

        if self.label == "requesting_committee":
            sel_requesting_committee = self.values[0]

            if sel_requesting_committee == "Restart":
                await interaction.response.defer() 

                channel_id = 1302238822720868374  # Change this to actual channel ID
                channel = client.get_channel(channel_id)

                embed = discord.Embed(
                title="UP CAPES Task Ticketing System",
                description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button or modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
                color=0xffcc1a
                )
                embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")

                view = MyView()

                await interaction.followup.send(embed=embed, view=view, ephemeral=True)

            elif self.change == "yes" and sel_requesting_committee != "Restart":
                await interaction.response.defer(ephemeral=True)

                await interaction.followup.send(
                f"You have selected **{sel_requesting_committee}** as the committee requesting the task.\nIs there anything you wish to change on the task details?\n*Choose **Restart** if you want to restart again from the beginning*.",
                view=DropdownView("to_change", self.task_id, self.context, self.task_name, self.priority, self.task_status, sel_requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc),
                ephemeral=True
                )

            else:
                await interaction.response.send_message(
                    f"You have selected **{sel_requesting_committee}** as the committee requesting the task. Select the **committee assigned or responsible** for the task:\n*Choose **Restart** if you want to restart again from the beginning*.",
                    view=DropdownView(
                        section="committee_responsible",
                        context=self.context,
                        task_name=self.task_name,
                        priority=self.priority,
                        requesting_committee=sel_requesting_committee,
                    ),
                    ephemeral=True,
                )

        elif self.label == "committee_responsible":
            committee_responsible = self.values[0]
            if committee_responsible == "Restart":
                await interaction.response.defer()

                channel_id = 1302238822720868374  # Change this to actual channel ID
                channel = client.get_channel(channel_id)

                embed = discord.Embed(
                title="UP CAPES Task Ticketing System",
                description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button or modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
                color=0xffcc1a
                )
                embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")

                view = MyView()

                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            elif self.change == "yes" and committee_responsible != "Restart":
                await interaction.response.defer(ephemeral=True)

                await interaction.followup.send(
                f"You have selected **{committee_responsible}** as the committee assigned to do the task.\nIs there anything you wish to change on the task details?\n*Choose **Restart** if you want to restart again from the beginning*.",
                view=DropdownView("to_change", self.task_id, self.context, self.task_name, self.priority, self.task_status, self.requesting_committee, committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc),
                ephemeral=True
                )

            else:
                await interaction.response.send_message(
                    f"You have selected **{committee_responsible}** as the committee assigned to do the task. Select the **subcommittee assigned or responsible** for the task:\n*Choose **Restart** if you want to restart again from the beginning*.",
                    view=DropdownView(
                        section="subcommittee_responsible",
                        context=self.context,
                        task_name=self.task_name,
                        priority=self.priority,
                        requesting_committee=self.requesting_committee,
                        committee_responsible=committee_responsible,
                    ),
                    ephemeral=True,
                )

        elif self.label == "receiving_committee":
            selected_receiving_committee = self.values[0]
            if selected_receiving_committee == "Restart":
                await interaction.response.defer() 

                channel_id = 1302238822720868374  # Change this to actual channel ID
                channel = client.get_channel(channel_id)

                embed = discord.Embed(
                title="UP CAPES Task Ticketing System",
                description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button or modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
                color=0xffcc1a
                )
                embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")

                view = MyView()

                await interaction.followup.send(embed=embed, view=view, ephemeral=True)

            elif self.change == "yes" and selectec_receiving_committee != "Restart":
                await interaction.response.defer(ephemeral=True)

                await interaction.followup.send(
                f"You have selected **{selected_receiving_committee}** as the committee receiving the output of the task.\nIs there anything you wish to change on the task details?\n*Choose **Restart** if you want to restart again from the beginning*.",
                view=DropdownView("to_change", self.task_id, self.context, self.task_name, self.priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, selected_receiving_committee, self.resolved_status, self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc),
                ephemeral=True
                )

            else:
                await interaction.response.send_message(
                    f"You have selected **{selected_receiving_committee}** as the committee receiving the output of the task.\nPlease type the **deadline** for the task in this format:\nMM/DD/YYYY HH:MM\n with HH:MM in **24-hour format**.\n*Type **R** if you want to restart again from the beginning*.",
                    ephemeral=True,
                )

                def check(msg):
                    return msg.author == interaction.user and msg.channel == interaction.channel

                deadline_msg = await client.wait_for("message", check=check)
                deadline = deadline_msg.content
                await deadline_msg.delete()

                if deadline == "R":

                    channel_id = 1302238822720868374 # Change this to actual channel ID
                    channel = client.get_channel(channel_id)

                    embed = discord.Embed(
                    title="UP CAPES Task Ticketing System",
                    description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button or modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
                    color=0xffcc1a
                    )
                    embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")

                    view = MyView()

                    await interaction.followup.send(embed=embed, view=view, ephemeral=True)

                else:

                    await interaction.followup.send( # Change this to actual channel ID
                        f"You wrote **{deadline}** as your deadline.\nIs there anything you want to be noted?\nWrite **N/A** if None.\n*Type **R** if you want to restart again from the beginning*.",
                        ephemeral=True,
                    )

                    notes_msg = await client.wait_for("message", check=check)
                    notes = notes_msg.content
                    await notes_msg.delete()

                    if notes == "R":
                        channel_id = 1302238822720868374 # Change this to actual channel ID
                        channel = client.get_channel(channel_id)

                        embed = discord.Embed(
                        title="UP CAPES Task Ticketing System",
                        description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button or modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
                        color=0xffcc1a
                        )
                        embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")

                        view = MyView()

                        await interaction.followup.send(embed=embed, view=view, ephemeral=True)

                    else:

                        await interaction.followup.send(
                            f"You wrote **{notes}** as your note. Please mention **your Discord account** as the creator of this task.\nExample: @YourName\n*Type **R** if you want to restart again from the beginning*.",
                            ephemeral=True,
                            )

                        creator_mention_msg = await client.wait_for("message", check=check)
                        creator_mention = creator_mention_msg.content.strip()
                        await creator_mention_msg.delete() 

                        if creator_mention == "R":

                            channel_id = 1302238822720868374  # Change this to actual channel ID
                            channel = client.get_channel(channel_id)

                            embed = discord.Embed(
                            title="UP CAPES Task Ticketing System",
                            description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button or modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
                            color=0xffcc1a
                            )
                            embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")

                            view = MyView()

                            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

                        else:
                            await interaction.followup.send(
                                f"You tagged {creator_mention} as the task creator. Lastly, please mention the **specific person/s responsible** for the task.\nExample: @Juan @joaquin23\n*Choose **Restart** if you want to restart again from the beginning*.",
                                ephemeral=True,
                                )
                            respo_mentions_msg = await client.wait_for("message", check=check)
                            respo_mentions = respo_mentions_msg.content.strip()
                            await respo_mentions_msg.delete() 

                            if respo_mentions == "R":
                                await interaction.response.defer()  

                                channel_id = 1302238822720868374  # Change this to actual channel ID
                                channel = client.get_channel(channel_id)

                                embed = discord.Embed(
                                title="UP CAPES Task Ticketing System",
                                description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button or modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
                                color=0xffcc1a
                                )
                                embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")

                                view = MyView()

                                await interaction.followup.send(embed=embed, view=view, ephemeral=True)

                            else:

                                task_id = get_next_task_id() 

                                embed = discord.Embed(
                                    title="New Task Created!",
                                    description=(
                                        f"**Task ID:** {task_id}\n"
                                        f"**Task Name:** {self.task_name}\n"
                                        f"**Task Context:** {self.context}\n"
                                        f"**Task Priority:** {self.priority}\n"
                                        f"**Requesting Committee:** {self.requesting_committee}\n"
                                        f"**Committee Responsible:** {self.committee_responsible}\n"
                                        f"**Subcommittee Responsible:** {self.subcommittee_responsible}\n"
                                        f"**Receiving Committee:** {selected_receiving_committee}\n"
                                        f"**Due Date:** {deadline}\n"
                                        f"**Notes:** {notes}\n"
                                        f"**Task Creator:** {creator_mention}\n"
                                        f"**Person/s in Charge:** {respo_mentions}\n"
                                        f"\n"
                                        f"***CC:** {cc}*"

                                    ),
                                    color=0xffcc1a,
                                )

                                
                                target_guild = client.get_guild(1302238411020832780) # Change this to actual server ID
                                target_channel = target_guild.get_channel(1320416019272957993) # Change this to actual channel ID

                                if target_channel:
                                    await target_channel.send(embed=embed)
                                else:
                                    print('lala')


                                add_to_google_sheets([
                                    "",
                                    self.context,
                                    self.task_name,
                                    self.priority,
                                    "Unseen",
                                    self.requesting_committee,
                                    self.committee_responsible,
                                    self.subcommittee_responsible,
                                    selected_receiving_committee,
                                    "FALSE",
                                    deadline,
                                    notes,
                                    creator_mention,
                                    respo_mentions,
                                    cc
                                ])


                                await interaction.followup.send(embed=embed, ephemeral=True)

                                channel_id = 1302238822720868374  # Change this to actual channel ID
                                channel = client.get_channel(channel_id)

                                embed = discord.Embed(
                                title="UP CAPES Task Ticketing System",
                                description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button\nor modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
                                color=0xffcc1a
                                )
                                
                                view = MyView()

                                time.sleep(0.3)

                                await channel.send(embed = embed, view=view)


class SubcommitteeDropdown(discord.ui.Select):
    def __init__(self, label="", change="", task_id="", context="", task_name="", priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", creator_mention="", respo_mentions="", cc=""):
        self.task_id = task_id
        self.context = context
        self.task_name = task_name
        self.priority = priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        self.creator_mention = creator_mention
        self.respo_mentions = respo_mentions
        self.cc = cc

        options = []
        if committee_responsible == "SB":
            options = [
                discord.SelectOption(label="President (SB)"),
                discord.SelectOption(label="Executive Vice President (SB)"),
                discord.SelectOption(label="Process Excellence (SB)"),
                discord.SelectOption(label="University Affairs (SB)"),
                discord.SelectOption(label="Restart", description="Choose this if you want to start again from the beginning.")
            ]
        elif committee_responsible == "CM":
            options = [
                discord.SelectOption(label="Vice President (CM)"),
                discord.SelectOption(label="Brand Management (CM)"),
                discord.SelectOption(label="External Communications (CM)"),
                discord.SelectOption(label="Restart", description="Choose this if you want to start again from the beginning.")
            ]
        elif committee_responsible == "CX":
            options = [
                discord.SelectOption(label="Vice President (CX)"),
                discord.SelectOption(label="Customer Development (CX)"),
                discord.SelectOption(label="Sales (CX)"),
                discord.SelectOption(label="Restart", description="Choose this if you want to start again from the beginning.")
            ]
        elif committee_responsible == "HR":
            options = [
                discord.SelectOption(label="Vice President (HR)"),
                discord.SelectOption(label="Performance Management (HR)"),
                discord.SelectOption(label="Membership (HR)"),
                discord.SelectOption(label="Organization Management (HR)"),
                discord.SelectOption(label="Restart", description="Choose this if you want to start again from the beginning.")
            ]
        elif committee_responsible == "IT":
            options = [
                discord.SelectOption(label="Vice President (IT)"),
                discord.SelectOption(label="Web Development (IT)"),
                discord.SelectOption(label="Information Systems (IT)"),
                discord.SelectOption(label="Automation (IT)"),
                discord.SelectOption(label="Restart", description="Choose this if you want to start again from the beginning.")
            ]
        elif committee_responsible == "MK":
            options = [
                discord.SelectOption(label="Vice President (MK)"),
                discord.SelectOption(label="External Relations (MK)"),
                discord.SelectOption(label="Marketing Operations (MK)"),
                discord.SelectOption(label="Restart", description="Choose this if you want to start again from the beginning.")
            ]
        elif committee_responsible == "FS":
            options = [
                discord.SelectOption(label="Vice President (FS)"),
                discord.SelectOption(label="Events Operations (FS)"),
                discord.SelectOption(label="External Operations (FS)"),
                discord.SelectOption(label="Taiwan (FS)"),
                discord.SelectOption(label="CAPES Week (FS)"),
                discord.SelectOption(label="Upskill (FS)"),
                discord.SelectOption(label="JobFair (FS)"),
                discord.SelectOption(label="Mixer (FS)"),
                discord.SelectOption(label="Restart", description="Choose this if you want to start again from the beginning.")
            ]

        super().__init__(placeholder="Select the subcommittee assigned or responsible for the task...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_subcommittee = self.values[0]
        if selected_subcommittee == "Restart":
            await interaction.response.defer()  

            channel_id = 1302238822720868374  # Change this to actual channel ID
            channel = client.get_channel(channel_id)

            embed = discord.Embed(
            title="UP CAPES Task Ticketing System",
            description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button or modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
            color=0xffcc1a
            )
            embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")

            view = MyView()

            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        elif self.change == "yes" != selected_subcommittee != "Restart":
            await interaction.response.defer(ephemeral=True)

            await interaction.followup.send(
                f"You have selected **{selected_subcommittee}** as the subcommittee assigned or responsible for the task.\nIs there anything you wish to change on the task details?\n*Choose **Restart** if you want to restart again from the beginning*.",
                view=DropdownView("to_change", self.task_id, self.context, self.task_name, self.priority, self.task_status, self.requesting_committee, self.committee_responsible, selected_subcommittee, self.receiving_committee, self.resolved_status, self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc),
                ephemeral=True
            )

        else:
            await interaction.response.send_message(
                f"You have selected **{selected_subcommittee}** as the subcommittee assigned or responsible for the task.\nSelect the **committee receiving** the output of the task:\n*Choose **Restart** if you want to restart again from the beginning*.",
                view=DropdownView(
                    section="receiving_committee",
                    context=self.context,
                    task_name=self.task_name,
                    priority=self.priority,
                    requesting_committee=self.requesting_committee,
                    committee_responsible=self.committee_responsible,
                    subcommittee_responsible=selected_subcommittee,
                ),
                ephemeral=True,
            )


class TaskStatusDropdown(discord.ui.Select):
    def __init__(self, change="", task_id="", task_context="", task_description="", task_priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", creator_mention="", respo_mentions="", cc=""):
        self.task_id = task_id
        self.task_context = task_context
        self.task_description = task_description
        self.task_priority = task_priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        self.creator_mention = creator_mention
        self.respo_mentions = respo_mentions
        self.cc = cc

        options = [
            discord.SelectOption(label="Acknowledged"),
            discord.SelectOption(label="In Progress"),
            discord.SelectOption(label="Blocked"),
            discord.SelectOption(label="Completed"),
            discord.SelectOption(label="Restart", description="Choose this if you want to start again from the beginning.")
        ]
        super().__init__(placeholder="Select the status of the task...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_task_status = self.values[0]
        if selected_task_status == "Restart":
            await interaction.response.defer() 

            channel_id = 1302238822720868374  # Change this to actual channel ID
            channel = client.get_channel(channel_id)

            embed = discord.Embed(
            title="UP CAPES Task Ticketing System",
            description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button or modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
            color=0xffcc1a
            )
            embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")

            view = MyView()

            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        else:
            await interaction.followup.send(
                f"You have selected **{selected_task_status}** as your task status.Is there anything you wish to change on the task details?\n*Choose **Restart** if you want to restart again from the beginning*.",
                view=DropdownView("to_change", self.task_id, self.task_context, self.task_description, self.task_priority, selected_task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc),
                ephemeral=True
                )


class ResolvedStatusDropdown(discord.ui.Select):
    def __init__(self, change="", task_id="", task_context="", task_description="", task_priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", creator_mention="", respo_mentions="", cc=""):
        self.task_id = task_id
        self.task_context = task_context
        self.task_description = task_description
        self.task_priority = task_priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        self.creator_mention = creator_mention
        self.respo_mentions = respo_mentions
        self.cc = cc

        options = [
            discord.SelectOption(label="True"),
            discord.SelectOption(label="False"),
            discord.SelectOption(label="Restart", description="Choose this if you want to start again from the beginning.")
        ]
        super().__init__(placeholder="Select True if the task has been resolved, False if otherwise.", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_resolved_status = self.values[0]
        if selected_resolved_status  == "Restart":
            await interaction.response.defer()

            channel_id = 1302238822720868374  # Change this to actual channel ID
            channel = client.get_channel(channel_id)

            embed = discord.Embed(
            title="UP CAPES Task Ticketing System",
            description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button or modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
            color=0xffcc1a
            )
            embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")

            view = MyView()

            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        elif selected_resolved_status == "True":
            await interaction.followup.send(
            f"You have selected **{selected_resolved_status}** as the resolved status of the task.\nIs there anything you wish to change on the task details?\n*Choose **Restart** if you want to restart again from the beginning*.",
            view=DropdownView("to_change", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, "TRUE", self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc),
            ephemeral=True
            )
        else:
            await interaction.followup.send(
            f"You have selected **{selected_resolved_status}** as the resolved status of the task.",
            view=DropdownView("to_change", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, "FALSE", self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc),
            ephemeral=True
            )


class AnsweredNoneDropdown(discord.ui.Select):
    def __init__(self, change="", task_id="", task_context="", task_description="", task_priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", creator_mention="", respo_mentions="", cc=""):
        self.task_id = task_id
        self.task_context = task_context
        self.task_description = task_description
        self.task_priority = task_priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.change = change
        self.creator_mention = creator_mention
        self.respo_mentions = respo_mentions
        self.cc = cc

        options = [
            discord.SelectOption(label="Yes"), 
            discord.SelectOption(label="No"),
            discord.SelectOption(label="Restart", description="Choose this if you want to start again from the beginning.")
        ]
        super().__init__(placeholder="Select Yes if the task has been resolved, No if otherwise.", options=options)

    async def callback(self, interaction: discord.Interaction):
        cc = interaction.user.mention
        selected_resolved_status = self.values[0]
        if selected_resolved_status == "Restart":
            await interaction.response.defer()  

            channel_id = 1302238822720868374  # Change this to actual channel ID
            channel = client.get_channel(channel_id)

            embed = discord.Embed(
            title="UP CAPES Task Ticketing System",
            description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button or modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
            color=0xffcc1a
            )
            embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")

            view = MyView()

            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        elif selected_resolved_status == "Yes":
            result = service.spreadsheets().values().get(
                    spreadsheetId=SPREADSHEET_ID,
                    range="Tickets!A:O"  
                ).execute()

            rows = result.get("values", [])
            headers = rows[0]  
            data_rows = rows[1:]  

            task_details = None
            for row in data_rows:
                if len(row) > 0 and row[0] == self.task_id:
                    task_details = row
                    break

            if task_details:
                (
                    task_context_before,
                    task_description_before,
                    task_priority_before,
                    task_status_before,
                    requesting_committee_before,
                    committee_responsible_before,
                    subcommittee_responsible_before,
                    receiving_committee_before,
                    resolved_status_before,
                    deadline_before,
                    notes_before,
                    creator_before,
                    respo_before
                ) = task_details[1:14]  


            embed = discord.Embed(
                    title=f"Task {self.task_id} has been Edited!",
                    description=(
                        f"**Task ID:** {self.task_id}\n"
                        f"**Task Name:** {task_description_before if type(self.task_description) != str else self.task_description}\n"
                        f"**Task Context:** {task_context_before if type(self.task_context) != str else self.task_context}\n"
                        f"**Task Priority:** {task_priority_before if type(self.task_priority) != str else self.task_priority}\n"
                        f"**Task Status:** {task_status_before if type(self.task_status) != str else self.task_status}\n"
                        f"**Requesting Committee:** {requesting_committee_before if type(self.requesting_committee) != str else self.requesting_committee}\n"
                        f"**Committee Responsible:** {committee_responsible_before if type(self.committee_responsible) != str else self.committee_responsible}\n"
                        f"**Subcommittee Responsible:** {subcommittee_responsible_before if type(self.subcommittee_responsible) != str else self.subcommittee_responsible}\n"
                        f"**Receiving Committee:** {receiving_committee_before if type(self.receiving_committee) != str else self.receiving_committee}\n"
                        f"**Task Resolved?** {resolved_status_before if type(self.resolved_status) != str else self.resolved_status}\n"
                        f"**Due Date:** {deadline_before if type(self.deadline) != str else self.deadline}\n"
                        f"**Notes:** {notes_before if type(self.notes) != str else self.notes}\n"
                        f"**Task Creator:** {creator_before if creator_before == self.creator_mention else self.creator_mention}\n"
                        f"**Person/s in Charge:** {respo_before if respo_before == self.respo_mentions else self.respo_mentions}\n"
                        f"\n"
                        f"***CC:** {cc}*"
                    ),
                    color=0xffcc1a,
                )

            await interaction.response.defer(ephemeral=True)
            await interaction.followup.send(embed=embed, ephemeral=True)

            target_guild = client.get_guild(1302238411020832780) # Change this to actual server ID
            target_channel = target_guild.get_channel(1320416019272957993) # Change this to actual channel ID

            if target_channel:
                await target_channel.send(embed=embed)
            else:
                print('lala')

            update_task_in_google_sheets(self.task_id,[
                '',
                task_context_before if type(self.task_context) != str else self.task_context,
                task_description_before if type(self.task_description) != str else self.task_description,
                task_priority_before if type(self.task_priority) != str else self.task_priority,
                task_status_before if type(self.task_status) != str else self.task_status,
                requesting_committee_before if type(self.requesting_committee) != str else self.requesting_committee,
                committee_responsible_before if type(self.committee_responsible) != str else self.committee_responsible,
                subcommittee_responsible_before if type(self.subcommittee_responsible) != str else self.subcommittee_responsible,
                receiving_committee_before if type(self.receiving_committee) != str else self.receiving_committee,
                resolved_status_before if type(self.resolved_status) != str else self.resolved_status,
                deadline_before if type(self.deadline) != str else self.deadline,
                notes_before if type(self.notes) != str else self.notes,
                creator_before if creator_before == self.creator_mention else self.creator_mention,
                respo_before if respo_before == self.respo_mentions else self.respo_mentions,
                cc
            ])

            await interaction.followup.send(embed=embed, ephemeral=True)

            channel_id = 1302238822720868374  # Change this to actual channel ID
            channel = client.get_channel(channel_id)

            embed = discord.Embed(
                title="UP CAPES Task Ticketing System",
                description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button or modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
                color=0xffcc1a
            )
            embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")
            
            view = MyView()

            time.sleep(2)

            await channel.send(embed=embed, view=view)

        else:
            await interaction.followup.send(
            f"It seems like you still want to change some details.\nIs there anything you wish to change on the task details?\n*Choose **Restart** if you want to restart again from the beginning*.",
            view=DropdownView("to_change", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc),
            ephemeral=True
            )


class DropdownView(discord.ui.View):
    def __init__(self, section="", task_id="", context="", task_name="", priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", creator_mention="", respo_mentions="", cc=""):
        super().__init__(timeout=None)

        if section == "task_context":
            self.add_item(TaskContextDropdown())
        elif section == "priority":
            self.add_item(TaskPriorityDropdown(task_context=context, task_description=task_name))
        elif section in ("requesting_committee", "committee_responsible", "receiving_committee"):
            self.add_item(CommitteeDropdown(label=section, context=context, task_name=task_name, priority=priority, requesting_committee=requesting_committee, committee_responsible=committee_responsible, subcommittee_responsible=subcommittee_responsible, receiving_committee=receiving_committee))
        elif section == "subcommittee_responsible":
            self.add_item(SubcommitteeDropdown(label=section, context=context, task_name=task_name, priority=priority, requesting_committee=requesting_committee, committee_responsible=committee_responsible, subcommittee_responsible=subcommittee_responsible, receiving_committee=receiving_committee))
        elif section == "to_change":
            self.add_item(ToChangeDropdown(task_id=task_id, task_context=context, task_description=task_name, task_priority=priority, task_status=task_status, requesting_committee=requesting_committee, committee_responsible=committee_responsible, subcommittee_responsible=subcommittee_responsible, receiving_committee=receiving_committee, resolved_status=resolved_status, deadline=deadline, notes=notes, creator_mention=creator_mention, respo_mentions=respo_mentions, cc=cc))
        elif section == "answered_none":
            self.add_item(AnsweredNoneDropdown(change="yes", task_id=task_id, task_context=context, task_description=task_name, task_priority=priority, task_status=task_status, requesting_committee=requesting_committee, committee_responsible=committee_responsible, subcommittee_responsible=subcommittee_responsible, receiving_committee=receiving_committee, resolved_status=resolved_status, deadline=deadline, notes=notes, creator_mention=creator_mention, respo_mentions=respo_mentions, cc=cc))

class ToChangeDropdown(discord.ui.Select):
    def __init__(self, task_id="", task_context="", task_description="", task_priority="", task_status="", requesting_committee="", committee_responsible="", subcommittee_responsible="", receiving_committee="", resolved_status="", deadline="", notes="", creator_mention="", respo_mentions="", cc=""):
        self.task_id = task_id
        self.task_context = task_context
        self.task_description = task_description
        self.task_priority = task_priority
        self.task_status = task_status
        self.requesting_committee = requesting_committee
        self.committee_responsible = committee_responsible
        self.subcommittee_responsible = subcommittee_responsible
        self.receiving_committee = receiving_committee 
        self.resolved_status = resolved_status
        self.deadline = deadline
        self.notes = notes
        self.creator_mention = creator_mention
        self.respo_mentions = respo_mentions
        self.cc = cc

        options = [
            discord.SelectOption(label="Task Context"),
            discord.SelectOption(label="Task Description"),
            discord.SelectOption(label="Task Priority"),
            discord.SelectOption(label="Task Status"),
            discord.SelectOption(label="Requesting Committee"),
            discord.SelectOption(label="Committee Responsible"),
            discord.SelectOption(label="Subcommittee Responsible"),
            discord.SelectOption(label="Receiving Committee"),
            discord.SelectOption(label="Resolved Status"),
            discord.SelectOption(label="Deadline"),
            discord.SelectOption(label="Notes"),
            discord.SelectOption(label="Task Creator"),
            discord.SelectOption(label="Person/s in Charge"),
            discord.SelectOption(label="None"),
            discord.SelectOption(label="Restart", description="Choose this if you want to start again from the beginning.")

        ]
        super().__init__(placeholder=f"Is there any detail of Task {task_id} you would like to be changed?", options=options)


    async def callback(self, interaction: discord.Interaction):
        selected_to_change = self.values[0]
        if selected_to_change == "Task Context":
            await interaction.response.defer(ephemeral=True)

            view = discord.ui.View()
            view.add_item(TaskContextDropdown("yes", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc))
            
            await interaction.followup.send(
                f"You have selected **{selected_to_change}** as the detail you would like to change.\nIs there any detail of Task {self.task_id} you would like to be changed?\n*Choose **Restart** if you want to restart again from the beginning*.",
                view=view,
                ephemeral=True
            )          

        elif selected_to_change == "Task Description":
            await interaction.response.send_message(
                f"You have selected **{selected_to_change}** as the detail you would like to change. Please type your **task description** in the chatbox below.\nIs there any detail of Task {self.task_id} you would like to be changed?\n*Type **R** if you want to restart again from the beginning*.",
                ephemeral=True
            )

            def check(msg):
                return msg.author == interaction.user and msg.channel == interaction.channel

            msg = await client.wait_for("message", check=check)
            task_name = msg.content  
            if task_name == "R":
                channel_id = 1302238822720868374  # Change this to actual channel ID
                channel = client.get_channel(channel_id)

                embed = discord.Embed(
                title="UP CAPES Task Ticketing System",
                description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button or modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
                color=0xffcc1a
                )
                embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")

                view = MyView()

                await interaction.followup.send(embed=embed, view=view, ephemeral=True)

            else:
                await interaction.followup.send(
                    f"You wrote **{task_name}** as your task description.\nIs there any detail of Task {self.task_id} you would like to be changed?\n*Choose **Restart** if you want to restart again from the beginning*.",
                    view=DropdownView("to_change", self.task_id, self.task_context, task_name, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc),
                    ephemeral=True
                )

        elif selected_to_change == "Task Priority":
            await interaction.response.defer(ephemeral=True)

            view = discord.ui.View()
            view.add_item(TaskPriorityDropdown("yes", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc))

            await interaction.followup.send(
                f"You have selected **{selected_to_change}** as the detail you would like to change.\nIs there any detail of Task {self.task_id} you would like to be changed?\n*Choose **Restart** if you want to restart again from the beginning*.",
                view=view,  
                ephemeral=True
            )


        elif selected_to_change == "Task Status":
            await interaction.response.defer(ephemeral=True)
            
            view = discord.ui.View()
            view.add_item(TaskStatusDropdown("yes", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc))
            
            await interaction.followup.send(
                f"You have selected **{selected_to_change}** as the detail you would like to change.\nIs there any detail of Task {self.task_id} you would like to be changed?\n*Choose **Restart** if you want to restart again from the beginning*.",
                view=view,
                ephemeral=True
            )  

        elif selected_to_change == "Requesting Committee":
            await interaction.response.defer(ephemeral=True)
            
            view = discord.ui.View()
            view.add_item(CommitteeDropdown("yes", "requesting_committee", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc))            
            
            await interaction.followup.send(
                f"You have selected **{selected_to_change}** as the detail you would like to change.\nIs there any detail of Task {self.task_id} you would like to be changed?\n*Choose **Restart** if you want to restart again from the beginning*.",
                view=view,
                ephemeral=True
            )  

        elif selected_to_change == "Committee Responsible":
            await interaction.response.defer(ephemeral=True)
            
            view = discord.ui.View()
            view.add_item(CommitteeDropdown("yes", "committee_responsible", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc))
            
            await interaction.followup.send(
                f"You have selected **{selected_to_change}** as the detail you would like to change.\nIs there any detail of Task {self.task_id} you would like to be changed?\n*Choose **Restart** if you want to restart again from the beginning*.",
                view=view,
                ephemeral=True
            )  
            
        elif selected_to_change == "Subcommittee Responsible":
            await interaction.response.defer(ephemeral=True)
            
            view = discord.ui.View()
            view.add_item(SubcommitteeDropdown("yes", "", "subcommittee_responsible", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc))
            
            await interaction.followup.send(
                f"You have selected **{selected_to_change}** as the detail you would like to change.\nIs there any detail of Task {self.task_id} you would like to be changed?\n*Choose **Restart** if you want to restart again from the beginning*.",
                view=view,
                ephemeral=True
            )  


        elif selected_to_change == "Receiving Committee":
            await interaction.response.defer(ephemeral=True)
            
            view = discord.ui.View()
            view.add_item(CommitteeDropdown("yes", "receiving_committee", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc))
            
            await interaction.followup.send(
                f"You have selected **{selected_to_change}** as the detail you would like to change.\nIs there any detail of Task {self.task_id} you would like to be changed?\n*Choose **Restart** if you want to restart again from the beginning*.",
                view=view,
                ephemeral=True
            )  
            
        elif selected_to_change == "Resolved Status":
            await interaction.response.defer(ephemeral=True)
            
            view = discord.ui.View()
            view.add_item(ResolvedStatusDropdown("yes", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc))
            
            await interaction.followup.send(
                f"You have selected **{selected_to_change}** as the detail you would like to change.\nIs there any detail of Task {self.task_id} you would like to be changed?\n*Choose **Restart** if you want to restart again from the beginning*.",
                view=view,
                ephemeral=True
            )  


        elif selected_to_change == "Deadline":
            await interaction.response.send_message("You selected **Deadline** as the detail you wish to change.\nPlease type the **deadline** for the task in this format:\nMM/DD/YYYY HH:MM\n with HH:MM in **24-hour format**.\n*Type **R** if you want to restart again from the beginning*.", ephemeral=True)

            def check(msg):
                    return msg.author == interaction.user and msg.channel == interaction.channel

            msg = await client.wait_for("message", check=check)
            deadline = msg.content
            await msg.delete() 

            if deadline == "R":

                channel_id = 1302238822720868374  # Change this to actual channel ID
                channel = client.get_channel(channel_id)

                embed = discord.Embed(
                title="UP CAPES Task Ticketing System",
                description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button or modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
                color=0xffcc1a
                )
                embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")

                view = MyView()

                await interaction.followup.send(embed=embed, view=view, ephemeral=True)

            else:
                await interaction.followup.send(
                    f"You wrote **{deadline}** as your task deadline.\nIs there any detail of Task {self.task_id} you would like to be changed?\n*Choose **Restart** if you want to start again from the beginning.",
                    view=DropdownView("to_change", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc),
                    ephemeral=True
                )

        elif selected_to_change == "Notes":
            await interaction.response.send_message("You selected **Notes** as the detail you wish to change.\nPlease type the things you wish to be noted about the task.\n*Type **R** if you want to restart again from the beginning*.", ephemeral=True)

            def check(msg):
                    return msg.author == interaction.user and msg.channel == interaction.channel

            msg = await client.wait_for("message", check=check)
            notes = msg.content
            await msg.delete()

            if notes == "R":
                channel_id = 1302238822720868374  # Change this to actual channel ID
                channel = client.get_channel(channel_id)

                embed = discord.Embed(
                title="UP CAPES Task Ticketing System",
                description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button or modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
                color=0xffcc1a
                )
                embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")

                view = MyView()

                await interaction.followup.send(embed=embed, view=view, ephemeral=True)

            else:
                await interaction.followup.send(
                    f"You wrote **\"{notes}\"** as the things you wish to be noted about the task.\nIs there any detail of Task {self.task_id} you would like to be changed?\n*Choose **Restart** if you want to start again from the beginning.",
                    view=DropdownView("to_change", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, notes, self.creator_mention, self.respo_mentions, self.cc),
                    ephemeral=True
                )

        elif selected_to_change in ("Task Creator", "Person/s in Charge"):
            await interaction.response.send_message(f"You selected **{selected_to_change}** as the detail you wish to change.\nPlease tag new {selected_to_change}.\n*Type **R** if you want to restart again from the beginning*.", ephemeral=True)

            def check(msg):
                    return msg.author == interaction.user and msg.channel == interaction.channel

            msg = await client.wait_for("message", check=check)
            people = msg.content
            await msg.delete()

            if people == "R":

                channel_id = 1302238822720868374  # Change this to actual channel ID
                channel = client.get_channel(channel_id)

                embed = discord.Embed(
                title="UP CAPES Task Ticketing System",
                description="Welcome to UP CAPES Task Ticketing System!\n\nYou may assign tasks to members through the **'Create Task'** button or modify tasks through the **'Edit Task'** button.\n\nTo see the list of tasks for UP CAPES members,\nplease see the Google Sheets below:\n\nhttps://tinyurl.com/UPCAPES-Task-Sheets",
                color=0xffcc1a
                )
                embed.set_thumbnail(url="https://scontent.fmnl3-3.fna.fbcdn.net/v/t39.30808-6/325405449_488094626829126_7271643387150285464_n.jpg?_nc_cat=111&ccb=1-7&_nc_sid=6ee11a&_nc_eui2=AeHMGyftRxPw6qWcVaXDs8WwSCzP57N9u2pILM_ns327aqsHs3baBpSygqlpkkiMhhf2VbfzJPZjsHCjgrkXFvkY&_nc_ohc=qxPE1f-bEQwQ7kNvgF3_rU1&_nc_zt=23&_nc_ht=scontent.fmnl3-3.fna&_nc_gid=AK46GnscB1fRz81NBq278xZ&oh=00_AYDVmLujMPhUXAsy1nZzAhQpb4G0KsOHTZcIA0rtgDRdaA&oe=67761A95")

                view = MyView()

                await interaction.followup.send(embed=embed, view=view, ephemeral=True)

            else:
                if selected_to_change == "Task Creator":
                    await interaction.followup.send(
                        f"You wrote **\"{people}\"** as the new {selected_to_change}.",
                        view=DropdownView("to_change", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, people, self.respo_mentions, self.cc),
                        ephemeral=True
                    )

                else:
                    await interaction.followup.send(
                        f"You wrote **\"{people}\"** as the new {selected_to_change}.",
                        view=DropdownView("to_change", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, self.creator_mention, people, self.cc),
                        ephemeral=True
                    )

        elif selected_to_change == "None":
            await interaction.response.defer(ephemeral=True)

            await interaction.followup.send(
                f"You have selected **{selected_to_change}** as the detail you would like to change.\nPlease select **Yes** if you want to save your changes.\n*Choose **Restart** if you want to restart again from the beginning*.",
                view=DropdownView("answered_none", self.task_id, self.task_context, self.task_description, self.task_priority, self.task_status, self.requesting_committee, self.committee_responsible, self.subcommittee_responsible, self.receiving_committee, self.resolved_status, self.deadline, self.notes, self.creator_mention, self.respo_mentions, self.cc),
                ephemeral=True
            )                    



client.run(BOTTOKEN)  
