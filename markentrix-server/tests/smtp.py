import asyncio, email
from aiosmtpd.controller import Controller
class H:
    async def handle_DATA(self, server, session, envelope):
        open("/var/tmp/pt/mails.txt","a").write(envelope.content.decode("utf8","replace")+"\n=====\n"); return "250 OK"
c=Controller(H(),hostname="127.0.0.1",port=8025); c.start()
import time
while True: time.sleep(60)
