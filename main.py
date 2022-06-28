from fastapi import FastAPI
from fastapi_socketio import SocketManager
from fastapi.responses import HTMLResponse
# 導入Request上下文對象，用來在前後台之間傳遞參數
from starlette.requests import Request
# 實例化一個模板引擎對象，指定模板所在路徑
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

import asyncio

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

socketio = SocketManager(app)
templates = Jinja2Templates(directory="./templates")

KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
KAFKA_TOPIC = "chat-topic"
KAFKA_CONSUMER_GROUP = "chat-topic-group"
loop = asyncio.get_event_loop()

async def produce(message: str):
    producer = AIOKafkaProducer(
        loop=loop, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    try:
        value_json = message.encode('utf-8')
        await producer.send_and_wait(topic=KAFKA_TOPIC, value=value_json)
    finally:
        await producer.stop()

async def consume():
    consumer = AIOKafkaConsumer(
            KAFKA_TOPIC,
            loop=loop,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=KAFKA_CONSUMER_GROUP
        )
    await consumer.start()
    try:
        async for msg in consumer:
            return (msg.value).decode("utf-8")
    finally:
        await consumer.stop()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse('index.html', {"request": request})

@app.sio.on('send')
async def chat(sid, *args, **kwargs):
    await produce("".join(args))
    msg = await consume()
    await app.sio.emit('get', msg)

