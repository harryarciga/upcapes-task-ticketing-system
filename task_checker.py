"""
    This file is for scheduled polling of deadlines for notification. This file goes over
    the UP CAPES Ticketing System GSheets https://tinyurl.com/UPCAPES-Task-Sheets every 9 AM
    and 9 PM and if the program sees that there are tasks that have deadlines in less than 7 days
    or those tasks that are past their deadlines.

    These tasks will be sent to the text channel with the channel ID {CHANNEL_ID} to remind the members
    of the tasks needed to be done.

    If downloaded, Ctrl F niyo lang then type "Change this" to change links, IDs, etc.

"""

import discord
import asyncio
import datetime
import time
from discord.ext import commands, tasks
from googleapiclient.discovery import build
from google.oauth2 import service_account

from apikeys import *


SERVICE_ACCOUNT_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_ID = "1DLGU03Z-3UxcL-zUGQcv34VonNVQ8tZ8YUaBj3KdSHM" # Change this into spreadsheet ID ng UP CAPES
RANGE_NAME = "Tickets!A:O"

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("sheets", "v4", credentials=credentials)

CHANNEL_ID = 1340238761317105714 # Change this into Channel ID ng text channel

intents = discord.Intents.all()
client = commands.Bot(command_prefix="!", intents=intents)

@tasks.loop(seconds=1)  
async def check_tasks():
    now = datetime.datetime.now()
    current_time = now.strftime("%I:%M %p") 

    if current_time not in ["09:00 AM", "09:00 PM"]:
        return

    print(f"\nChecking tasks at {now.strftime('%Y-%m-%d %I:%M %p')}")

    result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    rows = result.get("values", [])

    if not rows:
        print("No data found.")
        return

    headers = rows[0]
    data_rows = rows[1:]

    try:
        deadline_idx = headers.index("Deadline")
        resolved_idx = headers.index("Resolved?")
        task_id_idx = headers.index("Task ID")
        task_name_idx = headers.index("Task")
        task_context_idx = headers.index("Context")
        task_priority_idx = headers.index("Priority")
        task_status_idx = headers.index("Status")
        requesting_committee_idx = headers.index("Requesting Committee")
        committee_responsible_idx = headers.index("Committee Responsible")
        subcommittee_responsible_idx = headers.index("Subcommittee Responsible")
        receiving_committee_idx = headers.index("Receiving Committee")
        notes_idx = headers.index("Notes")
        creator_idx = headers.index("Task Creator ID")
        respo_idx = headers.index("Person/s Responsible ID")
        cc_idx = headers.index("CC ID")
    except ValueError as e:
        print(f"Error: Required column not found in sheet: {e}")
        return

    alert_tasks = []
    current_date = datetime.datetime.now()
    one_week_ahead = current_date + datetime.timedelta(days=7)

    for row in data_rows:
        try:
            task_id = row[task_id_idx]
            task_description = row[task_name_idx]
            task_context = row[task_context_idx]
            task_priority = row[task_priority_idx]
            task_status = row[task_status_idx]
            requesting_committee = row[requesting_committee_idx]
            committee_responsible = row[committee_responsible_idx]
            subcommittee_responsible = row[subcommittee_responsible_idx]
            receiving_committee = row[receiving_committee_idx]
            deadline = row[deadline_idx] if len(row) > deadline_idx else "N/A"
            resolved_status = row[resolved_idx].strip().upper() if len(row) > resolved_idx else "FALSE"
            notes = row[notes_idx] if len(row) > notes_idx else "N/A"
            creator_mention = row[creator_idx] if len(row) > creator_idx else "N/A"
            respo_mentions = row[respo_idx] if len(row) > respo_idx else "N/A"
            cc = row[cc_idx] if len(row) > cc_idx else "N/A"

            try:
                deadline_date = datetime.datetime.strptime(deadline, "%m/%d/%Y %H:%M")
            except ValueError:
                print(f"Invalid date format for task {task_id}: {deadline}")
                continue

            if resolved_status == "FALSE" and (deadline_date <= one_week_ahead):
                alert_tasks.append({
                    'task_id': task_id,
                    'task_description': task_description,
                    'task_context': task_context,
                    'task_priority': task_priority,
                    'task_status': task_status,
                    'requesting_committee': requesting_committee,
                    'committee_responsible': committee_responsible,
                    'subcommittee_responsible': subcommittee_responsible,
                    'receiving_committee': receiving_committee,
                    'deadline': deadline,
                    'resolved_status': resolved_status,
                    'notes': notes,
                    'creator_mention': creator_mention,
                    'respo_mentions': respo_mentions,
                    'cc': cc
                })
        except (IndexError, ValueError) as e:
            print(f"Error processing row: {e}")
            continue

    if alert_tasks:
        print(f"Found {len(alert_tasks)} tasks to send")
        
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            now = datetime.datetime.now().strftime("%B %d, %Y %I:%M %p")
            title = discord.Embed(
                    title=f"**Reminder!**",
                    description=(
                        f"Here are the tasks that are not yet resolved as of **{now}** and have deadlines in **less than one week**:"
                        ),
                        color=0xffcc1a,
                    )
            await channel.send(embed=title)
            for task in alert_tasks:
                embed = discord.Embed(
                    title=f"Task ID: {task['task_id']} Has Not Yet Been Resolved!",
                    description=(
                        f"**Task ID:** {task['task_id']}\n"
                        f"**Task Name:** {task['task_description']}\n"
                        f"**Task Context:** {task['task_context']}\n"
                        f"**Task Priority:** {task['task_priority']}\n"
                        f"**Task Status:** {task['task_status']}\n"
                        f"**Requesting Committee:** {task['requesting_committee']}\n"
                        f"**Committee Responsible:** {task['committee_responsible']}\n"
                        f"**Subcommittee Responsible:** {task['subcommittee_responsible']}\n"
                        f"**Receiving Committee:** {task['receiving_committee']}\n"
                        f"**Resolved Status:** {'Resolved' if task['resolved_status'] == 'TRUE' else 'Not Yet Resolved'}\n"
                        f"**Due Date:** {task['deadline']}\n"
                        f"**Notes:** {task['notes']}\n"
                        f"**Task Creator:** {task['creator_mention']}\n"
                        f"**Person/s in Charge:** {task['respo_mentions']}\n"
                        f"\n"
                        f"***CC:** {task['cc']}*"
                    ),
                    color=0xffcc1a,
                )
                await channel.send(embed=embed)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    check_tasks.start()

client.run(BOTTOKEN)
