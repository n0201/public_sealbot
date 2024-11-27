# public_sealbot
iykyk

## Run
<details>
<summary>Standalone</summary>

  First install required pip packages: `pip install -r requirements.txt`
  
  Then run the bot: `SEALBOT_SECRET=<your secret> SEALBOT_UPDATE_CHATID=<your chat id> python3 main.py`
</details>

<details>
<summary>With Docker</summary>
  
  Set your `SEALBOT_SECRET` and `SEALBOT_UPDATE_CHATID` in [docker-compose.yml](docker-compose.yml).
  
  Then run `docker compose up -d`.

  
  To view logs: `docker compose up logs`
  
  To rebuild: `docker compose up --force-recreate --build -d`
  
  
</details>

#### you're welcome :)

# DISCLAIMER
I'm not the one to blame for use of copyrighted pictures. The Person who hosts this bot is in charge of that!
This Project uses the EUPL-1.2 license. Check the LICENSE file for more information