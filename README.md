# Nyastra Discord Bot

Nyastra is a modular Discord bot built with discord.py, designed to be fun and extendable. It uses cog-based architecture for clean separation of commands and features.

---
## Features
- Modular cog system (general commands and lots of fun commands)
- Custom help command
- Responds to mentions with a cute personalized message
- Easily extendable with new cogs
- Uses environment variables for security

---
## Requirements
- Python 3.9 or higher
- `discord.py` library
- `python-dotenv` for environment variable management

---
## Installation
1.  Clone the repository:
    ```bash
    git clone <repo-url>
    cd Nyastra
    ```
2.  Create and activate a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Create a `.env` file in the root directory with your Discord bot token:
    ```ini
    DISCORD_BOT_TOKEN=your_bot_token_here
    ```

---

## Usage
Start the bot by running:
```bash
python main.py
```
The bot will load all cogs from the cogs/ directory and connect to your Discord server.

## Project Structure
```
Nyastra/
├── cogs/
│   ├── general/          # General command cogs (help, ping, etc.)
│   └── fun/              # Fun and miscellaneous command cogs
├── venv/               # Python virtual environment (ignored)
├── .env                  # Environment variables (ignored)
├── requirements.txt      # Python package requirements
└── main.py               # Main bot entrypoint
```

## Contributions
Feel free to open issues or submit pull requests! Please keep code consistent and modular by adding commands
