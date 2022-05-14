import os
import praw
import requests
import logging
from better_profanity import profanity
import urllib.parse
import time
from PIL import Image, ImageOps
import io
from base64 import b64encode
from nltk.corpus import stopwords
import re

INSTAGRAM_APP_ID = os.environ['INSTAGRAM_APP_ID']
IG_USER_ID = os.environ['IG_USER_ID']

IMGUR_CLIENT_ID =  os.environ['IMGUR_CLIENT_ID']
IMGUR_CLIENT_SECRET = my_secret = os.environ['IMGUR_CLIENT_SECRET']

REDDIT_CLIENT_SECRET = os.environ['REDDIT_CLIENT_SECRET']
REDDIT_CLEINT_ID = os.environ['REDDIT_CLEINT_ID']
INSTAGRAM_APP_SECRET = os.environ['INSTAGRAM_APP_SECRET']

USER_ACCESS = os.environ['USER_ACCESS']
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
IMGUR_UPLOAD_URL = "https://api.imgur.com/3/upload.json"
stopword_english = stopwords.words('english')
# logging
logging.basicConfig(filename='logs.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)

red = praw.Reddit(client_id = REDDIT_CLEINT_ID, 
                  client_secret = REDDIT_CLIENT_SECRET,
                  user_agent = USER_AGENT)

def url_to_red_post(url):
	global red_post
	try:
		red_post = red.submission(url=url)
	except:
		logger.fatal('reddit post didn\'t have a valid image post increase the limit!')
		return "No post found!"

def get_long_url():
    global thumb_url
    if not any([red_post.stickied, red_post.over_18, red_post.is_video]):
        thumb_url = red_post.preview['images'][0]['source']['url']
        short_link = red_post.shortlink
        
    else: 
        return "the url doesn't have a valid thumbnail"

def PilImage_to_good_lookingImage():
    global img_resized
    image = Image.open(requests.get(thumb_url, stream=True).raw)
    width = image.width
    height = image.height
    img_aspect_ratio = width/height
    desired_aspect_ratio=0.8
    
    if (img_aspect_ratio != desired_aspect_ratio):
        bigside = width if width > height else height
        other_side = int(bigside * desired_aspect_ratio)
        background = Image.new('RGBA', (other_side, bigside), (0, 0, 0, 255))
        offset = (int(round(((bigside - width) / 2), 0)), int(round(((bigside - height) / 2),0)))
        background.paste(image, offset)
        img_with_border = ImageOps.expand(background,border=5,fill='#FF0000')
        img_resized = img_with_border.resize(background.size)
        img_resized.save('with_boarder.png')
        print("Image has been converted !")
        
    else:
        return "Image is already in valid aspect ratio, it has not been resized !"    

def PIL_to_imgur():
    global imgur_link_jpg
    
    img_byte_arr = io.BytesIO()
    img_resized.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    unique_id = red_post.shortlink.split('/')[-1]
    
    data = {
        'image': b64encode(img_byte_arr),
        'type': 'base64',
        'name': f'{unique_id}',
        'title': f'{red_post.title}',
        'privacy': 'public',
    }

    headers = {
        "Authorization": f"Client-ID {IMGUR_CLIENT_ID}"
    }
    
    r_imgur = requests.post(
            IMGUR_UPLOAD_URL,
            headers=headers,
            data=data
        )
    
    try:
        imgur_link = r_imgur.json()['data']['link']
        imgur_link_jpg = '.'.join(imgur_link.split('.')[:-1]) + '.jpg'
        print(imgur_link_jpg)
		
    except:
        logger.error('image has not uploaded to imgur')
        return f"{r_imgur.text}"



def Get_containerid():
	global container_id, short_article_url
	tiny_php = f'https://tinyurl.com/api-create.php?url={red_post.url}'
	r_tiny = requests.get(tiny_php)
	short_article_url = r_tiny.text
	caption = red_post.title
	caption = profanity.censor(caption, censor_char='⚙️')
	caption_for_hashtags = re.sub(r'[^\w\s]', '', caption)
	caption_hashtags = '#'+' #'.join([word for word in caption_for_hashtags.split() if word not in stopword_english])
	extra_hashtags = '#tech #technology #dailytech #news #technews #article #readmore #loop #loopofficial #NFT'
	caption_final = caption + f"\n👉Follow --> @loop._official\n👉Stay updated with latest tech news\n\n-----------------------------\n🚀From --> {red_post.domain.split('.')[0]}\n📖Read the original article here \n---> {short_article_url.split('://')[-1]}\n[Not affiliated]\n-----------------------------\n\n\nHashtags - \n{caption_hashtags} {extra_hashtags}"     
	caption_encoded = urllib.parse.quote(caption_final.encode('utf8'))
	posting_url   = f'https://graph.facebook.com/v13.0/{IG_USER_ID}/media?image_url={imgur_link_jpg}&caption={caption_encoded}&access_token={USER_ACCESS}'
	
	r_container = requests.post(posting_url)
	if r_container.status_code == 200:
		container_id = r_container.json()['id']
		return container_id
	else:
		logger.fatal(f'status is not 200 but it is {r_container.status_code} and value is {r_container.text}')
		return f"{r_container.text}"

def container_to_live():
	# posting
	print(container_id)
	status_code = ''
	while status_code != 'FINISHED':
		con_url = f'https://graph.facebook.com/{container_id}?fields=id,status,status_code&access_token={USER_ACCESS}'
		r_con = requests.get(con_url)
		status_code = r_con.json()['status_code']
		time.sleep(3)
		print(status_code)
		
	publish_url = f'https://graph.facebook.com/v13.0/{IG_USER_ID}/media_publish?creation_id={container_id}&access_token={USER_ACCESS}'
	try:
		r_publish = requests.post(publish_url)
		print(r_publish.text)
		return f"post is live"
	
	
	except Exception as e:
		logger.log(10, e)
		return "You broke something at the end, check logs"
