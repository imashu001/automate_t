automate_t
Setup and Run
1. Create a virtual environment
powershell
py -m venv venv

2. Activate the virtual environment
powershell
.\venv\Scripts\Activate.ps1

3. Install dependencies
powershell
pip install -r requirements.txt

4. Run the project
powershell
py -m main

Notes
Make sure Python is installed.
Activate the virtual environment before installing dependencies or running the project.
Keep your .env file private.
Do not commit venv/, .env, or __pycache__/ to Git.