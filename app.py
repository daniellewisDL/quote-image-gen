from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import os
import requests
from io import BytesIO
import random
import json
import string
from string import ascii_letters
import textwrap
import math
import numpy as np
import cv2
import pandas as pd
import streamlit as st
pexels_api_key = st.secrets["pexels_api_key"]

# standard list of stopwords to remove

stopwords = {'ourselves', 'hers', 'between', 'yourself', 'but', 'again', 'there',
             'about', 'once', 'during', 'out', 'very', 'having', 'with', 'they',
             'own', 'an', 'be', 'some', 'for', 'do', 'its', 'yours', 'such', 'into',
             'of', 'most', 'itself', 'other', 'off', 'is', 's', 'am', 'or', 'who',
             'as', 'from', 'him', 'each', 'the', 'themselves', 'until', 'below',
             'are', 'we', 'these', 'your', 'his', 'through', 'don', 'nor', 'me',
             'were', 'her', 'more', 'himself', 'this', 'down', 'should', 'our',
             'their', 'while', 'above', 'both', 'up', 'to', 'ours', 'had', 'she',
             'all', 'no', 'when', 'at', 'any', 'before', 'them', 'same', 'and',
             'been', 'have', 'in', 'will', 'on', 'does', 'yourselves', 'then',
             'that', 'because', 'what', 'over', 'why', 'so', 'can', 'did', 'not',
             'now', 'under', 'he', 'you', 'herself', 'has', 'just', 'where', 'too',
             'only', 'myself', 'which', 'those', 'i', 'after', 'few', 'whom', 't',
             'being', 'if', 'theirs', 'my', 'against', 'a', 'by', 'doing', 'it',
             'how', 'further', 'was', 'here', 'than', 'isnt', 'dont'}

cat_list = ['vegan', 'inspirational']

@st.cache
def get_quote_data():
    quote_df = pd.read_csv('consol.csv')
    quote_df = quote_df.drop(quote_df[quote_df.len_quote > 120].index)
    return quote_df

def get_quote():
    my_quote_data = get_quote_data()
    if random.randint(0,9) == 0:
        sampled_quote = my_quote_data[my_quote_data['Category']=="vegan"].sample(n=1)
    else:
        sampled_quote = my_quote_data[my_quote_data['Category']=="inspirational"].sample(n=1)
    return sampled_quote['Quote'].iloc[0], sampled_quote['Author'].iloc[0]

def choose_random_word_from_quote(quote, num_words):
    quote_word_list_no_stopwords = []
    quote_punc_strip_list = quote.translate(str.maketrans('', '', string.punctuation)).lower().split(" ")
    if len(quote_punc_strip_list) == 0: return ""
    else:
        for word in list(set(quote_punc_strip_list)):
            if word not in stopwords:
                quote_word_list_no_stopwords.append(word)
        return " ".join(random.sample(quote_word_list_no_stopwords, min(num_words, len(quote_word_list_no_stopwords))))


def wrap_nicely(text_to_wrap):
    # Lower starting point for width is longest single word, or 15 whichever is higher
    lower_width = max(15, len(max(text_to_wrap.split(" "), key=len)))
    
    # Initial upper bound is higher of lower bound and half the overall length of the text to wrap
    upper_width = max(int(len(text_to_wrap)/2), lower_width)
    
    # This value is to be updated as we improve our estimate
    best_width = lower_width # assume first one
    
    wrapped_text_list = textwrap.wrap(text=text_to_wrap, width=lower_width)
    shortest_len = len(min(wrapped_text_list, key=len))
    longest_len = len(max(wrapped_text_list, key=len))
    lowest_diff_so_far = longest_len - shortest_len

    for test_width in range(upper_width, lower_width, -1):
        wrapped_text_list = textwrap.wrap(text=text_to_wrap, width=test_width)
        if len(wrapped_text_list) == 2: continue
        shortest_len = len(min(wrapped_text_list, key=len))
        longest_len = len(max(wrapped_text_list, key=len))
        if (longest_len - shortest_len) < lowest_diff_so_far:
            lowest_diff_so_far = longest_len - shortest_len
            best_width = test_width
    
    return textwrap.wrap(text=text_to_wrap, width=best_width)


def get_vid(query_term):
    query = query_term
    size = "small"
    per_page=80
    page=1
    headers = {'Authorization': pexels_api_key}
    search_ref = """https://api.pexels.com/videos/search?query={}&per_page={}&page={}""".format(query, per_page, page)
    search_request = requests.get(search_ref, headers=headers)
    vid_json_from_search_req = json.loads(search_request.content.decode('utf-8'))

    num_vids = len(vid_json_from_search_req['videos'])

    if num_vids == 0:
        st.info("No pexels image ... using default")
        vid = Image.open('grey.png')
        return vid, "#", "#", "#"
    else:
        random_index = random.randint(0,num_vids-1)
        vid_url_overall = """https://api.pexels.com/videos/videos/{}""".format(vid_json_from_search_req['videos'][random_index]['id'])
        vid_request = requests.get(vid_url_overall, headers=headers)
        vid_request_json = json.loads(vid_request.content.decode('utf-8'))

        vid_url = vid_request_json['url']
        vid_author = vid_request_json['user']['name']
        vid_author_url = vid_request_json['user']['url']
        
        # Set vid_file_link to first item
        vid_file_link = vid_request_json['video_files'][0]['link']
        
        # We want to get an SD link, so iterate over video_files to find first one
        for item in vid_request_json['video_files']:
            if item["quality"] == "sd":
                vid_file_link = item['link']
                break

        file_name = 'temp_vid.mp4'
        
        r = requests.get(vid_file_link, stream=True)
        with open(file_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size = 1024*1024):
                if chunk:
                    f.write(chunk)
        
        f = open(file_name, "rb")
        video_bytes = f.read()
        f.close()

        return video_bytes, vid_url, vid_author, vid_author_url


def generate_vid_and_quote(num_words=2):
    quote, author = get_quote()
    query = choose_random_word_from_quote(quote, num_words)
    my_quote_vid, vid_link, vid_author, vid_author_url = get_vid(query)

    file_name = 'temp_vid.mp4'
    f = open(file_name, "wb")
    f.write(my_quote_vid)
    f.close()
    video_path = file_name

    cap = cv2.VideoCapture(video_path)
    max_target_dim = 800

    if cap.isOpened():
        fourcc = cv2.VideoWriter_fourcc('H', '2', '6', '4')
        fps = cap.get(cv2.CAP_PROP_FPS)
        source_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        source_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        source_res = (source_width, source_height)
        
        if source_width > source_height:
            
            if source_width < max_target_dim:
                target_width = source_width
                target_height = source_height
            else:
                target_width = max_target_dim
                target_height = int(source_height * max_target_dim / source_width)
        else:
            if source_height < max_target_dim:
                target_width = source_width
                target_height = source_height
            else:
                target_height = max_target_dim
                target_width = int(source_width * max_target_dim / source_height)
        
        target_res = (target_width, target_height)
        
        out = cv2.VideoWriter('temp_op.mp4', fourcc, fps, target_res)

        max_seconds = 10 # user defined max
        max_frames = fps * max_seconds
        
        txt = Image.new("RGBA", target_res, (255,255,255,0))
        draw = ImageDraw.Draw(txt)
        text = quote

        wrapped_text_list = wrap_nicely(text)
        wrapped_text = "\n".join(wrapped_text_list)
        longest_line = max(wrapped_text_list, key=len)

        # To determine the max font size for the quotation, we set a max width e.g. 80pc
        # We want the longest word including punctuation to fit on one line
        # NB font size is approximately equal to pixel size, so font pt 10 is approx 10px x 10px
        
        max_quote_width_ratio = 0.6
        max_quote_height_ratio = 0.5
        
        # We want the longest word including punctuation to fit on one line
        
        width_to_fill = int(max_quote_width_ratio * target_width)
        height_to_not_overflow = int(max_quote_height_ratio * target_height)
        pixels_per_char_x = int( width_to_fill / len(longest_line))
        
        # Guess font size, then test width in pixels of longest line, then scale to fill
        font_size_x = int(pixels_per_char_x)
        font = ImageFont.truetype('arial.ttf', font_size_x)
        font_size_x = int(font_size_x * width_to_fill / font.getsize(longest_line)[0])
        font = ImageFont.truetype('arial.ttf', font_size_x)

        # Now check the height of the first letters of each line stacked, and if too big, scale back down
        font_rows_height_stacked = 0
        for item in wrapped_text_list:
            font_rows_height_stacked = font_rows_height_stacked + font.getsize(item[0])[1]
        if font_rows_height_stacked > height_to_not_overflow:
            font_size_x = int(font_size_x * height_to_not_overflow / font_rows_height_stacked )
        
        font_attrib = ImageFont.truetype('arial.ttf', 24)

        xclr1, xclr2, xclr3 = 0, 0, 0
        opac = 255
        draw.text(xy=(txt.size[0]/20, txt.size[1]/20), text=wrapped_text, font=font, fill=(255-xclr1,255-xclr2,255-xclr3,opac))
        draw.text(xy=(txt.size[0]/20, txt.size[1]*18/20), text=author, font=font_attrib, fill=(255-xclr1,255-xclr2,255-xclr3,opac))
        
        
        frame = None
        a=0
        frame_count = 0
        while True:
            a=a+1
            frame_count = frame_count + 1
            
            try:
                is_success, frame = cap.read()
            except cv2.error:
                continue
            if not is_success:
                break

            image = frame
            image = cv2.resize(image, target_res)
                    
            applier = ImageEnhance.Brightness(Image.fromarray(image.astype('uint8'), 'RGB').convert("RGBA"))
            PIL_output = Image.alpha_composite(applier.enhance(.5), txt)
            image_output = np.array(PIL_output.convert("RGB"))
            
            out.write(image_output)

            if frame_count >= max_frames: break
            
        out.release()
    cap.release()

    f = open('temp_op.mp4', 'rb')
    my_quote_vid_bytes = f.read()
    f.close()

    return my_quote_vid_bytes, vid_link, vid_author, vid_author_url


def main():
    container = st.container()
    my_quote_vid, vid_link, vid_author, vid_author_url = generate_vid_and_quote()
    container.video(my_quote_vid)
    st.markdown('---')
    if st.button('Generate another'): container.empty()
    st.markdown('---')
    st.markdown('''<small>Video provided by [Pexels](https://www.pexels.com), quotations from various sources.</small>''', unsafe_allow_html = True)
    st.markdown('''<small>This [video]({}) was taken by [{}]({}) on Pexels.</small>'''.format(vid_link, vid_author, vid_author_url), unsafe_allow_html = True)
    st.markdown('---')
    #os.remove('temp_vid.mp4')
    #os.remove('temp_op.mp4')

    return None


if __name__ == "__main__":
    main()
