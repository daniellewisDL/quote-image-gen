from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import requests
from io import BytesIO
import random
import json
import string
import textwrap
import pandas as pd
import streamlit as st
from os import environ

# For Heroku
pexels_api_key = environ['pexels_api_key']

# For share.streamlit.io
pexels_api_key = st.secrets["pexels_api_key"]

# standard list of stopwords to remove

stopwords1 = {'ourselves', 'hers', 'between', 'yourself', 'but', 'again', 'there',
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

stopwords = {''}

@st.cache
def get_quote_data():
    quote_df = pd.read_csv('consol.csv')
    quote_df = quote_df.drop(quote_df[quote_df.len_quote > 120].index)
    return quote_df

def get_quote():
    my_quote_data = get_quote_data()
    
    # Give a 1 in 10 chance of a vegan related quotation
    
    if random.randint(0,9) == 0:
        sampled_quote = my_quote_data[my_quote_data['Category']=="vegan"].sample(n=1)
    else:
        sampled_quote = my_quote_data[my_quote_data['Category']=="inspirational"].sample(n=1)
        #sampled_quote = my_quote_data.sample(n=1)
    
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



def get_img(query_term):

    query = query_term + " random"
    per_page=80
    pexels_colors = ['red', 'orange', 'yellow', 'green', 'turquoise', 'blue', 'violet', 'pink', 'brown', 'black', 'gray', 'white', '']
    color_req = random.choice(pexels_colors)
    page=1
    headers = {'Authorization': pexels_api_key}

    search_ref = """https://api.pexels.com/v1/search?query={}&per_page={}&color={}&page={}""".format(query, per_page, color_req, page)
    search_request = requests.get(search_ref, headers=headers)
    img_json_from_search_req = json.loads(search_request.content.decode('utf-8'))

    num_images = len(img_json_from_search_req['photos'])

    if num_images == 0:
        st.info("No pexels image ... using default")
        img = Image.open('grey.png')
        return img, "#", "#", "#"
    else:
        random_index = random.randint(0,num_images-1)
        img_url = img_json_from_search_req['photos'][random_index]['src']['large']
        img_request = requests.get(img_url, headers=headers)
        img = Image.open(BytesIO(img_request.content))
        return img, img_json_from_search_req['photos'][random_index]['src']['original'], img_json_from_search_req['photos'][random_index]['photographer'], img_json_from_search_req['photos'][random_index]['photographer_url']

def wrap_nicely(text_to_wrap, aspect_ratio):
    # TODO - buiding aspect ratio functionality
    
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

def gen_text_wrapped_image(size, quote, author=""):

    # Create new image of size as Pexels returned image, with a transparency channel of 0
    text_wrapped_image = Image.new("RGBA", size, (255,255,255,0))
    
    draw = ImageDraw.Draw(text_wrapped_image)
    text = quote

    wrapped_text_list = wrap_nicely(text, round(size[0]/size[1],2))
    wrapped_text = "\n".join(wrapped_text_list)
    longest_line = max(wrapped_text_list, key=len)

    # To determine the max font size for the quotation, we set a max width e.g. 80pc
    # We want the longest word including punctuation to fit on one line
    # NB font size is approximately equal to pixel size, so font pt 10 is approx 10px x 10px
    
    max_quote_width_ratio = 0.6
    max_quote_height_ratio = 0.5
    
    # We want the longest word including punctuation to fit on one line
    
    width_to_fill = int(max_quote_width_ratio * size[0])
    height_to_not_overflow = int(max_quote_height_ratio * size[1])
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
    font = ImageFont.truetype('arial.ttf', font_size_x)

    # Generate font size for the attribution
    max_attrib_ratio_height = 0.05
    max_attrib_ratio_width = 0.9
    font_size_for_attrib = 24 # Guess at 24
    font_attrib = ImageFont.truetype('arial.ttf', 24)
    font_size_for_attrib = int(font_size_for_attrib * max_attrib_ratio_height / (font_attrib.getsize(author)[1] / size[1]))
    font_attrib = ImageFont.truetype('arial.ttf', font_size_for_attrib)
    if font_attrib.getsize(author)[0] > (max_attrib_ratio_width * size[0]):
        font_size_for_attrib = int((font_size_for_attrib * max_attrib_ratio_width) / (font_attrib.getsize(author)[0] / size[0]))
    font_attrib = ImageFont.truetype('arial.ttf', font_size_for_attrib)

    xclr1, xclr2, xclr3 = 0, 0, 0
    opac = 255
    draw.text(xy=(text_wrapped_image.size[0]/20, text_wrapped_image.size[1]/20), text=wrapped_text, font=font, fill=(255-xclr1,255-xclr2,255-xclr3,opac))
    draw.text(xy=(text_wrapped_image.size[0]/20, text_wrapped_image.size[1]*18/20), text=author, font=font_attrib, fill=(255-xclr1,255-xclr2,255-xclr3,opac))

    return text_wrapped_image


def generate_image_and_quote(num_words=3):
    
    # Request a quote from consol.csv according to the topic_to_obtain
    quote, author = get_quote()

    # Choose two (or num_words) random words from the quote
    query = choose_random_word_from_quote(quote, num_words)

    # Obtain an image on the basis of the query
    my_quote_image, photo_link, photo_author, photographer_url = get_img(query)

    # Generate an image of the same size, with transparent background, and text wrapped
    text_wrapped_image = gen_text_wrapped_image(my_quote_image.size, quote, author)

    # Specify a brightness modifier for the image
    applier = ImageEnhance.Brightness(my_quote_image.convert("RGBA"))
    
    # Composite the final image from the quote image darkened slightly, and the text wrapped image
    final_image = Image.alpha_composite(applier.enhance(.7), text_wrapped_image)
    
    return final_image, photo_link, photo_author, photographer_url



def main():
    container = st.container()
    image, photo_link, photographer, photographer_url = generate_image_and_quote()
    container.image(image)
    if st.button('Generate another'): container.empty()
    st.markdown('---')
    st.markdown('''<small>Photos provided by [Pexels](https://www.pexels.com), quotations from various sources.</small>''', unsafe_allow_html = True)
    st.markdown('''<small>This [photo]({}) was taken by [{}]({}) on Pexels.</small>'''.format(photo_link, photographer, photographer_url), unsafe_allow_html = True)
    st.markdown('---')

    return None


if __name__ == "__main__":
    main()
