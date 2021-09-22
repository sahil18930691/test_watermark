import os
import pprint
import aiohttp
import requests
from enum import Enum
from io import BytesIO
from typing import Optional
from urllib.parse import urlparse

import io
import PIL
from PIL import Image, ImageEnhance

import numpy as np
from PIL import Image, ImageSequence
from pydantic import BaseModel
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse


SQUARE_YARDS_LOGO = Image.open('./slogo.png')
IC_LOGO = Image.open('./iclogo2.png')
POSI_LIST = ["centre", "bottom_left", "bottom_right", "bottom"]

app = FastAPI(
    title="sqy-watermark-engine",
    description="Use this API to paste Square Yards logo as a watermark at the center of input images",
    version="1.0",
)

@app.get("/")
async def root():
    return "Hello World!!!"

class URL(BaseModel):
    url_: str
 
 
class ImageDetails(BaseModel):
    url_: str
    width_percentage: Optional[float] = 0.2
    position: Optional[str] = "centre"

def extract_filename(URL):
    parsed = urlparse(URL)
    return os.path.basename(parsed.path)
 
 
async def get_image_properties(URL, width_percentage=None, position=None):
    filename = None
    try:
        filename = extract_filename(URL)
        filename = filename.strip()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=406, detail="Not a valid URL")
 
    if URL.lower().endswith((".jpg", ".png", ".jpeg", ".gif", ".webp")) == False:
        raise HTTPException(status_code=406, detail="Not a valid URL")
 
    if width_percentage and width_percentage > 1:
        raise HTTPException(status_code=406, detail="Please chose the value of width_percentage between 0.01 and 1.0")
 
    if position and position not in POSI_LIST:
        raise HTTPException(status_code=406, detail="Please chose a value of position from: " + ", ".join(POSI_LIST))
 
   
    contents = None
    original_image = None
    try:
        # contents = requests.get(URL, timeout=10).content
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as resp:
                contents = await resp.read()
 
        if contents == None:
            raise HTTPException(status_code=406, detail="No image found.")
 
        original_image = Image.open(BytesIO(contents))
        

    except Exception as e:
        print(e)
        raise HTTPException(status_code=400, detail="Error while reading the image. Make sure that the URL is a correct image link.")
    
    return filename, original_image
 
 
def paste_logo(original_image, width_percentage, logo, position="centre"):
 
    logo_width = int(original_image.size[0]*width_percentage)
    logo_height = int(logo.size[1]*(logo_width/logo.size[0]))
 
    if logo_height > original_image.size[1]:
        logo_height = original_image.size[1]
    
    if position == "centre":
        logo = logo.resize((logo_width, logo_height))
 
        top = (original_image.size[1]//2) - (logo_height//2)
        left = (original_image.size[0]//2) - (logo_width//2)
        original_image.paste(logo, (left, top), mask=logo)
 
    elif position == "bottom_right":
        logo = logo.resize((logo_width, logo_height))
 
        top = original_image.size[1] - logo_height
        left = original_image.size[0] - logo_width
        original_image.paste(logo, (left, top), mask=logo)
 
    elif position == "bottom_left":
        logo = logo.resize((logo_width, logo_height))
 
        top = original_image.size[1] - logo_height
        left = 0
        original_image.paste(logo, (left, top), mask=logo)
    elif position == "bottom":
        logo = logo.resize((logo_width, logo_height))
 
        top = original_image.size[1] - logo_height
        left = (original_image.size[0]//2) - (logo_width//2)
        original_image.paste(logo, (left, top), mask=logo)
 
    return original_image
 
 
def get_format(filename):
    format_ = filename.split(".")[-1]
    if format_.lower() == "jpg":
        format_ = "jpeg"
    elif format_.lower == "webp":
        format_ = "WebP"
 
    return format_
 
 
def get_content_type(format_):
    type_ = "image/jpeg"
    if format_ == "gif":
        type_ = "image/gif"
    elif format_ == "webp":
        type_ = "image/webp"
    elif format_ == "png":
        type_ = "image/png"

    return type_
 
 
def get_final_image(image_details, original_image, width_percentage, logo, position, filename):
    original_image = paste_logo(original_image, width_percentage, logo, position)
    format_ = get_format(filename)
    quality = 70

    return original_image, format_, quality

async def get_body(URL):

    #print(Enhance_image)
    response = requests.get(URL)
    image_bytes = io.BytesIO(response.content)
    #print(image_bytes)
    image = PIL.Image.open(image_bytes)
    #print(image)
    filename = URL
    #print(filename)
    #this function get the format type of input image
    def get_format(filename):
        format_ = filename.split(".")[-1]
        if format_.lower() == "jpg":
            format_ = "jpeg"
        elif format_.lower == "webp":
            format_ = "WebP"
    
        return format_
 
   
    #this function for gave the same type of format to output
    def get_content_type(format_):
        type_ = "image/jpeg"
        if format_ == "gif":
            type_ = "image/gif"
        elif format_ == "webp":
            type_ = "image/webp"
        elif format_ == "png":
            type_ = "image/png"
        #print(type_)
        return type_

    format_ = get_format(filename)#here format_ store the type of image by filename
    
    
    #This function calculate the brightness of input image 
    def calculate_brightness(image):
        greyscale_image = image.convert('L')
        histogram = greyscale_image.histogram()
        pixels = sum(histogram)
        brightness = scale = len(histogram)

        for index in range(0, scale):
            ratio = histogram[index] / pixels
            brightness += ratio * (-scale + index)

        return 1 if brightness == 255 else brightness / scale
    
    #print(calculate_brightness(image))#here print the float(calculate brightnes nummber)

                  
    #______Here apply the Brightness and Color on image automatically according to there condition_____
    if (calculate_brightness(image) > 0.6 and calculate_brightness(image) < 0.7 ): 
        
        enhancer_bright = ImageEnhance.Brightness(image)
        image = enhancer_bright.enhance(1.2)
        #print("bright 6")
        if image:
            enhancer_colors = ImageEnhance.Color(image)
            image = enhancer_colors.enhance(1.4)
            #print("color 6")
     

    if (calculate_brightness(image) > 0.5 and calculate_brightness(image) < 0.6): 
            
        enhancer_bright = ImageEnhance.Brightness(image)
        image = enhancer_bright.enhance(1.2)
        #print("bright 5")
        if image:
            enhancer_colors = ImageEnhance.Color(image)
            image = enhancer_colors.enhance(1.8)
            #print("color 5")



    if (calculate_brightness(image)  > 0.4 and calculate_brightness(image) < 0.5 ):
        
        enhancer_bright = ImageEnhance.Brightness(image)
        image = enhancer_bright.enhance(1.2)
        print("bright 4")
        if image:
            enhancer_colors = ImageEnhance.Color(image)
            image = enhancer_colors.enhance(1.5)
            #print("color 4")


    if (calculate_brightness(image)  > 0.3 and calculate_brightness(image) < 0.4):
            
        enhancer_bright = ImageEnhance.Brightness(image)
        image = enhancer_bright.enhance(1.7)
        #print("bright 3")
        if image:
            enhancer_colors = ImageEnhance.Color(image)
            image = enhancer_colors.enhance(1.5)
            #print("color 3")


    if (calculate_brightness(image)  > 0.2 and calculate_brightness(image) < 0.3 ):
        
        enhancer_bright = ImageEnhance.Brightness(image)
        image = enhancer_bright.enhance(1.8)
        #print("bright 2")
        if image:
            enhancer_colors = ImageEnhance.Color(image)
            image = enhancer_colors.enhance(1.5)
            #print("color 2")


    if (calculate_brightness(image)  > 0.1 and calculate_brightness(image) < 0.2):
            
        enhancer_bright = ImageEnhance.Brightness(image)
        image = enhancer_bright.enhance(2.0)
        #print("bright 1")
        if image:
            enhancer_colors = ImageEnhance.Color(image)
            image = enhancer_colors.enhance(1.6)
            #print("color 1")


    if (calculate_brightness(image)  > 0.001 and calculate_brightness(image) < 0.1 ):
        
        enhancer_bright = ImageEnhance.Brightness(image)
        image = enhancer_bright.enhance(2.0)
        #print("bright 001")
        if image:
            enhancer_colors = ImageEnhance.Color(image)
            image = enhancer_colors.enhance(1.6)
            print("color 001")

    
    def calculate_brightness(image):
        greyscale_image = image.convert('L')
        histogram = greyscale_image.histogram()
        pixels = sum(histogram)
        brightness = scale = len(histogram)

        for index in range(0, scale):
            ratio = histogram[index] / pixels
            brightness += ratio * (-scale + index)

        return 1 if brightness == 255 else brightness / scale
    
    #print("after",calculate_brightness(image))
    

    #buffer = BytesIO()
    #image.save(buffer, format=format_, quality=100)
    #buffer.seek(0)

    #return StreamingResponse(buffer, media_type=get_content_type(format_))
    original_image = image
    
    return original_image

@app.get("/enhancement")
async def enhancement(Enhance_image: str):
    """ 
    #### The endpoint takes image url as inputs in the form of JSON, enhance the image and then return the enhanced image.\n
    1. Enhance_image: Url of the image.
    """

    #print(Enhance_image)
    response = requests.get(Enhance_image)
    image_bytes = io.BytesIO(response.content)
    #print(image_bytes)
    image = PIL.Image.open(image_bytes)
    #print(image)
    filename = Enhance_image
    #print(filename)
    #this function get the format type of input image
    def get_format(filename):
        format_ = filename.split(".")[-1]
        if format_.lower() == "jpg":
            format_ = "jpeg"
        elif format_.lower == "webp":
            format_ = "WebP"
    
        return format_
 
   
    #this function for gave the same type of format to output
    def get_content_type(format_):
        type_ = "image/jpeg"
        if format_ == "gif":
            type_ = "image/gif"
        elif format_ == "webp":
            type_ = "image/webp"
        elif format_ == "png":
            type_ = "image/png"
        #print(type_)
        return type_

    format_ = get_format(filename)#here format_ store the type of image by filename
    
    
    #This function calculate the brightness of input image 
    def calculate_brightness(image):
        greyscale_image = image.convert('L')
        histogram = greyscale_image.histogram()
        pixels = sum(histogram)
        brightness = scale = len(histogram)

        for index in range(0, scale):
            ratio = histogram[index] / pixels
            brightness += ratio * (-scale + index)

        return 1 if brightness == 255 else brightness / scale
    
    #print(calculate_brightness(image))#here print the float(calculate brightnes nummber)

                  
    #______Here apply the Brightness and Color on image automatically according to there condition_____
    if (calculate_brightness(image) > 0.6 and calculate_brightness(image) < 0.7 ): 
        
        enhancer_bright = ImageEnhance.Brightness(image)
        image = enhancer_bright.enhance(1.2)
        #print("bright 6")
        if image:
            enhancer_colors = ImageEnhance.Color(image)
            image = enhancer_colors.enhance(1.4)
            #print("color 6")
     

    if (calculate_brightness(image) > 0.5 and calculate_brightness(image) < 0.6): 
            
        enhancer_bright = ImageEnhance.Brightness(image)
        image = enhancer_bright.enhance(1.2)
        #print("bright 5")
        if image:
            enhancer_colors = ImageEnhance.Color(image)
            image = enhancer_colors.enhance(1.8)
            #print("color 5")



    if (calculate_brightness(image)  > 0.4 and calculate_brightness(image) < 0.5 ):
        
        enhancer_bright = ImageEnhance.Brightness(image)
        image = enhancer_bright.enhance(1.2)
        print("bright 4")
        if image:
            enhancer_colors = ImageEnhance.Color(image)
            image = enhancer_colors.enhance(1.5)
            #print("color 4")


    if (calculate_brightness(image)  > 0.3 and calculate_brightness(image) < 0.4):
            
        enhancer_bright = ImageEnhance.Brightness(image)
        image = enhancer_bright.enhance(1.7)
        #print("bright 3")
        if image:
            enhancer_colors = ImageEnhance.Color(image)
            image = enhancer_colors.enhance(1.5)
            #print("color 3")


    if (calculate_brightness(image)  > 0.2 and calculate_brightness(image) < 0.3 ):
        
        enhancer_bright = ImageEnhance.Brightness(image)
        image = enhancer_bright.enhance(1.8)
        #print("bright 2")
        if image:
            enhancer_colors = ImageEnhance.Color(image)
            image = enhancer_colors.enhance(1.5)
            #print("color 2")


    if (calculate_brightness(image)  > 0.1 and calculate_brightness(image) < 0.2):
            
        enhancer_bright = ImageEnhance.Brightness(image)
        image = enhancer_bright.enhance(2.0)
        #print("bright 1")
        if image:
            enhancer_colors = ImageEnhance.Color(image)
            image = enhancer_colors.enhance(1.6)
            #print("color 1")


    if (calculate_brightness(image)  > 0.001 and calculate_brightness(image) < 0.1 ):
        
        enhancer_bright = ImageEnhance.Brightness(image)
        image = enhancer_bright.enhance(2.0)
        #print("bright 001")
        if image:
            enhancer_colors = ImageEnhance.Color(image)
            image = enhancer_colors.enhance(1.6)
            print("color 001")

    
    def calculate_brightness(image):
        greyscale_image = image.convert('L')
        histogram = greyscale_image.histogram()
        pixels = sum(histogram)
        brightness = scale = len(histogram)

        for index in range(0, scale):
            ratio = histogram[index] / pixels
            brightness += ratio * (-scale + index)

        return 1 if brightness == 255 else brightness / scale
    
    #print("after",calculate_brightness(image))
    

    buffer = BytesIO()
    image.save(buffer, format=format_, quality=100)
    buffer.seek(0)

    return StreamingResponse(buffer, media_type=get_content_type(format_))

@app.post("/enhancement_logo_without_ext")
async def enhancement_logo_without_ext(image_details: ImageDetails):
    """ 
    #### The endpoint takes image url without extension as inputs in the form of JSON ,enhance the image and then pastes the Square Yards logo as a watermark on the input images and then compresses it and returns file without extension.\n
    1. url_: Url of the image.
    2. width_percentage: Size of watermark based on the width of the image. Range (0-1).
    3. compression_info: Details regarding image compression.
    4. position: position of logo on image.
    """
    URL1 = image_details.url_
    URL = image_details.url_
    
    response = requests.get(URL)
    #print(response)
    img = Image.open(BytesIO(response.content))
    #print(img)
    #print(img.format.lower())

    URL = URL + "." + img.format.lower()
    
    width_percentage = image_details.width_percentage

    position = image_details.position

    filename, original_image = await get_image_properties(URL, width_percentage, position)
    original_image = await get_body(image_details.url_)
    

    try:

        squareyard_logo = SQUARE_YARDS_LOGO.copy()
        original_image, format_, quality = get_final_image(image_details, original_image, width_percentage, squareyard_logo, position, filename)
        buf = BytesIO()
        if format_ == 'gif':
            frames = [get_final_image(image_details, frame.copy(), width_percentage, squareyard_logo, position, filename)[0] for frame in ImageSequence.Iterator(original_image)]
            frames[0].save(buf, save_all=True, append_images=frames[1:], format=format_, quality=quality, optimize=True)
        elif format_ == 'png':
            format_ = 'webp'
            original_image.save(buf, format=format_, quality = 70, optimize=True)
        else:
            original_image.save(buf, format=format_, quality = 70, optimize=True)

            
    except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail="Error while processing the image.")
    buf.seek(0)

    filename = filename.replace(filename.split(".")[-1], '')
    


    filename = filename.replace(".","")
    
    #print(filename)
    
    
    return StreamingResponse(buf, media_type=get_content_type(format_), headers={'Content-Disposition': 'inline; filename="%s"' %(filename,)})


@app.post("/enhancement_logo_without_ext2")
async def enhancement_logo_without_ext(image_details: ImageDetails):
    """ 
    #### The endpoint takes image url without extension as inputs in the form of JSON ,enhance the image and then pastes the Square Yards logo as a watermark on the input images and then compresses it, return file with extension.\n
    1. url_: Url of the image.
    2. width_percentage: Size of watermark based on the width of the image. Range (0-1).
    3. compression_info: Details regarding image compression.
    4. position: position of logo on image.
    """
    URL1 = image_details.url_
    URL = image_details.url_
   
    response = requests.get(URL)
    #print(response)
    img = Image.open(BytesIO(response.content))
    #print(img)
    #print(img.format.lower())

    URL = URL + "." + img.format.lower()
    
    width_percentage = image_details.width_percentage

    position = image_details.position

    filename, original_image = await get_image_properties(URL, width_percentage, position)
    original_image = await get_body(image_details.url_)
    

    try:

        squareyard_logo = SQUARE_YARDS_LOGO.copy()
        original_image, format_, quality = get_final_image(image_details, original_image, width_percentage, squareyard_logo, position, filename)
        buf = BytesIO()
        if format_ == 'gif':
            frames = [get_final_image(image_details, frame.copy(), width_percentage, squareyard_logo, position, filename)[0] for frame in ImageSequence.Iterator(original_image)]
            frames[0].save(buf, save_all=True, append_images=frames[1:], format=format_, quality=quality, optimize=True)
        elif format_ == 'png':
            format_ = 'webp'
            original_image.save(buf, format=format_, quality = 70, optimize=True)
        else:
            original_image.save(buf, format=format_, quality = 70, optimize=True)

            
    except Exception as e:
            print(e)
            
            raise HTTPException(status_code=500, detail="Error while processing the image.")
    buf.seek(0)
    
    
    return StreamingResponse(buf, media_type=get_content_type(format_), headers={'Content-Disposition': 'inline; filename="%s"' %(filename,)})

@app.post("/enhancement_logo")
async def enhancement_logo(image_details: ImageDetails):
    """ 
    #### The endpoint takes multiple parameters as inputs in the form of JSON ,enhance the image and then pastes the Square Yards logo as a watermark on the input images and then compresses it.\n
    1. url_: Url of the image.
    2. width_percentage: Size of watermark based on the width of the image. Range (0-1).
    3. compression_info: Details regarding image compression.
    4. position: position of logo on image.
    """
    URL = image_details.url_
    width_percentage = image_details.width_percentage

    position = image_details.position
    
    filename, original_image = await get_image_properties(URL, width_percentage, position)

    original_image = await get_body(image_details.url_)
    

    try:

        squareyard_logo = SQUARE_YARDS_LOGO.copy()
        original_image, format_, quality = get_final_image(image_details, original_image, width_percentage, squareyard_logo, position, filename)
        buf = BytesIO()
        if format_ == 'gif':
            frames = [get_final_image(image_details, frame.copy(), width_percentage, squareyard_logo, position, filename)[0] for frame in ImageSequence.Iterator(original_image)]
            frames[0].save(buf, save_all=True, append_images=frames[1:], format=format_, quality=quality, optimize=True)
        elif format_ == 'png':
            format_ = 'webp'
            original_image.save(buf, format=format_, quality = 70, optimize=True)
        else:
            original_image.save(buf, format=format_, quality = 70, optimize=True)

            
    except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail="Error while processing the image.")
    buf.seek(0)


    return StreamingResponse(buf, media_type=get_content_type(format_), headers={'Content-Disposition': 'inline; filename="%s"' %(filename,)})

@app.post("/addWatermark")
async def add_watermark(image_details: ImageDetails):
    """ 
    #### The endpoint takes multiple parameters as inputs in the form of JSON, pastes the Square Yards logo as a watermark on the input images and then compresses it.\n
    1. url_: Url of the image.
    2. width_percentage: Size of watermark based on the width of the image. Range (0-1).
    3. compression_info: Details regarding image compression.
    4. position: position of logo on image.
    """
    URL = image_details.url_
    width_percentage = image_details.width_percentage

    position = image_details.position
    
    filename, original_image = await get_image_properties(URL, width_percentage, position)

    try:
        squareyard_logo = SQUARE_YARDS_LOGO.copy()
        original_image, format_, quality = get_final_image(image_details, original_image, width_percentage, squareyard_logo, position, filename)
        buf = BytesIO()
        if format_ == 'gif':
            frames = [get_final_image(image_details, frame.copy(), width_percentage, squareyard_logo, position, filename)[0] for frame in ImageSequence.Iterator(original_image)]
            frames[0].save(buf, save_all=True, append_images=frames[1:], format=format_, quality=quality, optimize=True)
        elif format_ == 'png':
            format_ = 'webp'
            original_image.save(buf, format=format_, quality = 70, optimize=True)
        else:
            original_image.save(buf, format=format_, quality = 70, optimize=True)

            
    except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail="Error while processing the image.")
    buf.seek(0)


    return StreamingResponse(buf, media_type=get_content_type(format_), headers={'Content-Disposition': 'inline; filename="%s"' %(filename,)})
 
 
@app.post("/addWatermarkIC")
async def add_watermarkIC(image_details: ImageDetails):
    """ 
    #### The endpoint takes multiple parameters as inputs in the form of JSON and pastes the Interior Company logo as a watermark on the input images.\n
    1. url_: Url of the image.
    2. width_percentage: Size of watermark based on the width of the image. Range (0-1).
    3. compression_info: Details regarding image compression.
    4. position: position of logo on image.
    """
    URL = image_details.url_
    width_percentage = image_details.width_percentage
    position = image_details.position
    filename, original_image = await get_image_properties(URL, width_percentage, position)
    
    try:
        ic_logo = IC_LOGO.copy()
        original_image, format_, quality = get_final_image(image_details, original_image, width_percentage, ic_logo, position, filename)
        buf = BytesIO()
        if format_ == 'gif':
            frames = [get_final_image(image_details, frame.copy(), width_percentage, ic_logo, position, filename)[0]\
                         for frame in ImageSequence.Iterator(original_image)]
            frames[0].save(buf, save_all=True, append_images=frames[1:], format=format_, quality=quality, optimize=True)
        else:
            original_image.save(buf, format=format_, quality=quality, optimize=True)
    except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail="Error while processing the image.")
    buf.seek(0)
    return StreamingResponse(buf, media_type=get_content_type(format_), headers={'Content-Disposition': 'inline; filename="%s"' %(filename,)})