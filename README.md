# Science Parser

Parser of the latest scientific publications from PubMed and not only, wrapped in telegram bot.

## How it works?

The most important component here is Entrez API, which is used to query Pubmed. Google scholar is also used to get the most relevant reviews. Finally, some web scraping is used to get press releases.

## Project structure

- `parsers` folder - tools to get the articles, reviews and press releases
- `prototyping` folder - some notebooks to test the parsers
- `backend.py` - functions, which help to work SQLalchemy database
- `configs.py` - config file, which is not publicly available (it is temporary solution)
- `db_map.py` - SQLalchemy models
- `frontend.py` - helper functions for rendering messages for the bot
- `helpers.py` - some helper functions
- `tgbot.py` - main file, which runs the aiogram bot
