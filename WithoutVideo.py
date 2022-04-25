import requests
import praw
import urllib.parse
import urllib.request
import logging
import pandas as pd
import time
from pytz import timezone
from datetime import datetime
import os

start = time.time()
print('running...')

INSTAGRAM_APP_ID = os.environ['INSTAGRAM_APP_ID']
IG_USER_ID = os.environ['IG_USER_ID']

IMGUR_CLIENT_ID =  os.environ['IMGUR_CLIENT_ID']
IMGUR_CLIENT_SECRET = my_secret = os.environ['IMGUR_CLIENT_SECRET']

REDDIT_CLIENT_SECRET = os.environ['REDDIT_CLIENT_SECRET']
REDDIT_CLEINT_ID = os.environ['REDDIT_CLEINT_ID']
INSTAGRAM_APP_SECRET = os.environ['INSTAGRAM_APP_SECRET']

IMGUR_UPLOAD_URL = "https://api.imgur.com/3/upload.json"

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'

# valid for two months]
USER_ACCESS = os.environ['USER_ACESS']

# logging
logging.basicConfig(filename='logs.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger(__name__)

# database update this to sql
df = pd.read_csv('my_reddit_meme_posts.csv')
database_links = df['short_link'].tolist()


# Task 1 Get the reddit posts
red = praw.Reddit(client_id=REDDIT_CLEINT_ID,
                  client_secret=REDDIT_CLIENT_SECRET,
                  user_agent=USER_AGENT)

subred = red.subreddit('memes').hot(limit=15)

red_post = None
for i in subred:
    if (i.stickied is False) & (i.is_video is False) & (i.shortlink not in database_links) & (i.over_18 is False):
        # valid instagram aspect ratios
        width = i.preview['images'][0]['source']['width']
        height = i.preview['images'][0]['source']['height']
        aspect_ratio = width/height
        if (aspect_ratio >= 0.8) & (aspect_ratio <= 1.19):
            red_post = i
            break

if red_post:
    red_image_url = red_post.preview['images'][0]['source']['url']
    short_link = red_post.shortlink
    caption = red_post.title
    redditor = red_post.author.name

else:
    print('red post not defined')
    logger.fatal('reddit post didn\'t have a valid image post increase the limit!')
    raise Exception

caption_final = caption + f"\n\n\n#reddit #redditmemes #memesdaily #meme #memes #dailymemes #everyhour\n\nOP u/{redditor}\n      {short_link}\n\nNew memes every hour from Reddit"
caption_encoded = urllib.parse.quote(caption_final.encode('utf8'))
unique_id = short_link.split('/')[-1]

# for image
data = {
    'image': red_image_url,
    'type': 'URL',
    'name': f'{unique_id}.jpg',
    'title': caption,
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

imgur_link_jpg = None
try:
    imgur_link = r_imgur.json()['data']['link']
    imgur_link_jpg = '.'.join(imgur_link.split('.')[:-1]) + '.jpg'

    df.loc[len(df.index)] = [red_image_url, short_link, caption, redditor, imgur_link]
    df.to_csv('my_reddit_meme_posts.csv', index=False)
    df.to_csv('copy_my_reddit_database.csv', index=False)
except Exception as e:
    logger.error(e)

container_id = None
if imgur_link_jpg:
    # post meme on my instagram
    posting_url = f'https://graph.facebook.com/v13.0/{IG_USER_ID}/media?image_url={imgur_link_jpg}&caption={caption_encoded}&access_token={USER_ACCESS}'
    r_container = requests.post(posting_url)

    if r_container.status_code == 200:
        container_id = r_container.json()['id']

    else:
        logger.fatal(f'status is not 200 but it is {r_container.status_code} and value is {r_container.text}')

# posting
if container_id:
    publish_url = f'https://graph.facebook.com/v13.0/{IG_USER_ID}/media_publish?creation_id={container_id}&access_token={USER_ACCESS}'
    try:
        lim = requests.get(f'https://graph.facebook.com/v13.0/{IG_USER_ID}/content_publishing_limit?fields=quota_usage,rate_limit_settings&access_token={USER_ACCESS}')
        lim_num = lim.json()['data'][0]['quota_usage']
        
        if lim_num < 25:
            r_publish = requests.post(publish_url)
            print(r_publish.json()['id'])
            print('Post is live!', 25 - int(lim_num), 'posts left!')
            logger.log(10, f'{25-lim_num} posts left')
            
        else:
            logger.fatal(f'limit exhausted! {25-lim_num} left')
            print('fatal error, no post left please stop!')
            
    except Exception as e:
        logger.log(e)


end = time.time()
ind_time = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d %I:%M:%S %p')
print('I ran at', ind_time)
logger.info(f"Post created at {ind_time}")
print('Run time ', round(end-start, 2), 'seconds')









