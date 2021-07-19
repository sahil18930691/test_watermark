import os
import requests
from io import BytesIO

import numpy as np
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse


SQUARE_YARDS_LOGO = Image.open('images/slogo.png')

app = FastAPI()


@app.get("/addWatermark")
async def replace_watermark_url(URL: str):
    if URL.lower().endswith((".jpg", ".png", ".jpeg")) == False:
        raise HTTPException(status_code=400, detail="Not a valid URL")

    try:
        contents = requests.get(URL, timeout=10).content
        original_image = Image.open(BytesIO(contents))
        squareyard_logo = SQUARE_YARDS_LOGO.copy()

        slogo_width = int(original_image.size[0]*0.3)
        slogo_height = int(squareyard_logo.size[1]*(slogo_width/squareyard_logo.size[0]))
        squareyard_logo = squareyard_logo.resize((slogo_width, slogo_height))

        top = (original_image.size[1]//2) - (slogo_height//2)
        left = (original_image.size[0]//2) - (slogo_width//2)
        original_image.paste(squareyard_logo, (left, top), mask=squareyard_logo)

        buf = BytesIO()
        original_image.save(buf, format='JPEG', quality=100)
        buf.seek(0)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Internal Server Error. Make sure that the URL is correct image link.")

    return StreamingResponse(buf, media_type="image/jpeg")
