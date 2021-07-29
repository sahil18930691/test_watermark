import os
import aiohttp
import requests
from io import BytesIO
from typing import Optional
from urllib.parse import urlparse

import numpy as np
from PIL import Image
from pydantic import BaseModel
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse


SQUARE_YARDS_LOGO = Image.open('images/slogo.png')

app = FastAPI(
    title="sqy-watermark-engine",
    description="Use this API to paste Square Yards logo as a watermark at the center of input images",
    version="1.0",
)


class ImageDetails(BaseModel):
    url_: str
    width_percentage: Optional[float] = 0.2


def extract_filename(URL):
    parsed = urlparse(URL)
    return os.path.basename(parsed.path)


@app.post("/addWatermark")
async def add_watermark(image_details: ImageDetails):
    """ 
    #### The endpoint takes two parameters as inputs in the form of JSON and pastes the Square Yards logo as a watermark on the input images.\n
    1. url_: Url of the image.
    2. width_percentage: Size of watermark based on the width of the image. Range (0-1).
    """
    URL = image_details.url_
    width_percentage = image_details.width_percentage
    
    filename = None
    try:
        filename = extract_filename(URL)
        filename = filename.strip()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=406, detail="Not a valid URL")

    if URL.lower().endswith((".jpg", ".png", ".jpeg", ".gif", ".webp")) == False:
        raise HTTPException(status_code=406, detail="Not a valid URL")

    if width_percentage > 1:
        raise HTTPException(status_code=406, detail="Please chose a value between 0.01 and 1.0")

    contents = None
    original_image = None
    try:
        # contents = requests.get(URL, timeout=10).content
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as resp:
                print(resp.status)
                contents = await resp.read()

        if contents == None:
            raise HTTPException(status_code=406, detail="No image found.")

        original_image = Image.open(BytesIO(contents))
    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Error while reading the image. Make sure that the URL is a correct image link.")
    
    try:
        squareyard_logo = SQUARE_YARDS_LOGO.copy()

        slogo_width = int(original_image.size[0]*width_percentage)
        slogo_height = int(squareyard_logo.size[1]*(slogo_width/squareyard_logo.size[0]))
        squareyard_logo = squareyard_logo.resize((slogo_width, slogo_height))

        top = (original_image.size[1]//2) - (slogo_height//2)
        left = (original_image.size[0]//2) - (slogo_width//2)
        original_image.paste(squareyard_logo, (left, top), mask=squareyard_logo)

        format_ = filename.split(".")[-1]
        if format_.lower() == "jpg":
            format_ = "jpeg"
        elif format_.lower == "webp":
            format_ = "WebP"

        buf = BytesIO()
        original_image.save(buf, format=format_, quality=100)
        buf.seek(0)
    except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail="Error while processing the image.")

    return StreamingResponse(buf, media_type="image/jpeg", headers={'Content-Disposition': 'inline; filename="%s"' %(filename,)})
