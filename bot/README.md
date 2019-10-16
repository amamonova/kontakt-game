# Kontakt game bot

This Telegram bot will be the interface for Kontakt Game. 
Now it is simple local bot, which passes the message and return 
reversed echo.
Also the bot maintains the \/start function, which will return 
greeting.

## Installation 

1. Clone this repo  
`git clone https://github.com/amamonova/kontakt-game.git`
2. Change the directory to the bot folder   
`cd bot`
3. Download all requirements  
`pip install -r requirements.txt`
  
## Usage

1. Add token to the config.py file
2. To start the bot launch the script `bot.py`  
`python3.6 bot.py`
3. Test your bot.

JFYI: Telegram is prohibited in Russia, so we use proxy. It is
unstable: if you have some troubles with connection, please, 
feel free to contact us. Or just change the 
`proxy_url` parameter in `config.py`

## Output

The script has logging, so it returns logs to standard output. 