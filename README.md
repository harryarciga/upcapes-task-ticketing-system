# Welcome to UP CAPES Task Ticketing System
This repository has 2 files:

 - `main.py`
 - `task_checker.py`

The `main.py` is for running the task ticketing system itself. You may create or edit tasks in this [Google Sheet](https://docs.google.com/spreadsheets/d/1qQray0kmeoOms-TaKT5WAWekBjIvg7lVcWQT5s_WQSY/edit?usp=sharing) with just the ticketing system in the Discord. The `task_checker.py` is for the reminders of the tasks due in the organization. When it is run, it checks this [Google Sheet](https://docs.google.com/spreadsheets/d/1qQray0kmeoOms-TaKT5WAWekBjIvg7lVcWQT5s_WQSY/edit?usp=sharing) if there are tasks that are either past their deadlines or that have deadlines in less than 7 days. The program sends out reminders to the text channel every 9 AM and 9 PM everyday.

Before running these files (especially for testing purposes), it is recommended for you to have these two applications installed: (either one is fine)

 1. WSL
 2. VS Code
 3. Git (optional)

Here are the step by step process on how to run these files:

 1. In Github, download these files as ZIP file. You may click the green button with the 'Code' label and select the 'Download as ZIP file'. You may also type `git clone https://github.com/harryarciga/upcapes-task-ticketing-system.git` on your terminal to download.
 2. Extract the ZIP file you have downloaded.
 3. Ask me, [Harry Arciga](https://www.facebook.com/harry.arciga.9) for the other two files: `credentials.json` and `apikeys.py` (I can't upload these in Github since I tried it and all the credentials here are automatically changed by Google Cloud).
 4. Make sure to put `credentials.json` and `apikeys.py` in the same folder as `main.py` and `task_checker.py`.
 5. Open the folder in VS Code (if you use VS Code).
 6. Open your files on a code editor. Make sure change the IDs and links that are needed to be changed (instructions are in the first lines of `main.py` and `task_checker.py` and align them to the actual Google Sheets and UP CAPES server.
 7. Open your terminal (for both VS Code through `Ctrl J` and WSL users).
 8. Type `python3 main.py`. This will run the two files: `main.py` and `task_checker.py`.
 9. For any issues, please feel free to contact me:  [Harry Arciga](https://www.facebook.com/harry.arciga.9).

 Thank you!
