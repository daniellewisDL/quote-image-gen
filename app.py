import streamlit as st
import requests
import json
import pandas as pd
from os import environ, path
import base64

# For Heroku
if 'sandbox_client_id' in environ:
    sandbox_client_id = environ['sandbox_client_id']
    sandbox_client_secret = environ['sandbox_client_secret']
    live_client_id = environ['live_client_id']
    live_client_secret = environ['live_client_secret']
    passphrase = environ['passphrase']
else:
    sandbox_client_id = st.secrets["sandbox_client_id"]
    sandbox_client_secret = st.secrets["sandbox_client_secret"]
    live_client_id = st.secrets["live_client_id"]
    live_client_secret = st.secrets["live_client_secret"]
    passphrase = st.secrets["passphrase"]

sandbox_headers = {
    'ClientID': sandbox_client_id,
    'ClientSecret': sandbox_client_secret,
    'Accept-Language': 'en-HK'
}

live_headers = {
    'ClientID': live_client_id,
    'ClientSecret': live_client_secret,
    'Accept-Language': 'en-HK'
}

sandbox_domain_url="https://developer.hsbc.com.hk/sandbox/open-banking/v1.0/"
live_domain_url = "https://api.hsbc.com.hk/live/open-banking/v1.0/"

api_addresses = [
        'Choose...',
        'atms',
        'branches',
        'personal-foreign-exchange-rates',
        'business-integrated-accounts',
        'commercial-cards',
        'commercial-secured-lending',
        'commercial-unsecured-lending',
        'personal-all-in-one-and-savings-accounts',
        'personal-credit-cards',
        'personal-current-accounts',
        'personal-foreign-currency-accounts',
        'personal-mortgages',
        'personal-secured-loans',
        'personal-unsecured-loans',
        'time-deposit-accounts'
]


# Thanks to GokulNC for this code snippet
@st.cache(allow_output_mutation=True)
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

@st.cache(allow_output_mutation=True)
def get_img_with_href(local_img_path, target_url):
    img_format = path.splitext(local_img_path)[-1].replace('.', '')
    bin_str = get_base64_of_bin_file(local_img_path)
    html_code = f'''
        <a href="{target_url}" target="_blank">
            <img src="data:image/{img_format};base64,{bin_str}" />
        </a>'''
    return html_code


def visualise(api_name, response_json, pretty_json):
    
    if api_name=='atms':
        st.subheader("HSBC HK ATM locations")
        geo_list = []
        for atm in response_json["data"][0]["Brand"][0]["ATM"]:
            geo_list.append([float(atm["ATMAddress"]["LatitudeDescription"]),float(atm["ATMAddress"]["LongitudeDescription"])])
        geo_pandas = pd.DataFrame(geo_list, columns = ["latitude", "longitude"])
        st.map(geo_pandas)
        
    elif api_name=='branches':
        st.subheader("HSBC HK branch locations")
        geo_list = []
        for branch in response_json["data"][0]["Brand"][0]["Branch"]:
            geo_list.append([float(branch["BranchAddress"]["LatitudeDescription"]),float(branch["BranchAddress"]["LongitudeDescription"])])
        geo_pandas = pd.DataFrame(geo_list, columns = ["latitude", "longitude"])
        st.map(geo_pandas)

    elif api_name=='personal-foreign-exchange-rates':
        st.subheader("Banknote exchange rates against HKD")
        pfx_list = []
        col1, col2 = st.columns(2)
        for rate in response_json["data"][0]["Brand"][0]["ExchangeRateType"][0]["ExchangeRate"][0]["ExchangeRateTierBand"]:
            pfx_list.append(rate)
            col1.metric(rate["CurrencyCode"]+" bank buy rate", rate["BankBuyRate"])
            col2.metric(rate["CurrencyCode"]+" bank sell rate", rate["BankSellRate"])

    elif api_name=='business-integrated-accounts': st.write("...")
    elif api_name=='commercial-cards': st.write("...")
    elif api_name=='commercial-secured-lending': st.write("...")
    elif api_name=='commercial-unsecured-lending': st.write("...")
    elif api_name=='personal-all-in-one-and-savings-accounts': st.write("...")
    elif api_name=='personal-credit-cards': st.write("...")
    elif api_name=='personal-current-accounts': st.write("...")
    elif api_name=='personal-foreign-currency-accounts': st.write("...")
    elif api_name=='personal-mortgages': st.write("...")
    elif api_name=='personal-secured-loans': st.write("...")
    elif api_name=='personal-unsecured-loans': st.write("...")
    elif api_name=='time-deposit-accounts': st.write("...")

    st.write("First {} characters of the JSON response".format(len(pretty_json)))
    st.code(pretty_json, language='json')

    return None

def main():
    st.header("HSBC HK Developer API explorer")
    st.markdown("""[HSBC HK developer portal](https://developer.hsbc.com.hk/#/home)""", unsafe_allow_html=True)
    st.markdown("""<small>Simple app to explore HSBC HK product information APIs</small>""", unsafe_allow_html=True)
    st.markdown('---')
    sandbox_or_live = st.radio('Choose sandbox or live APIs', ['Sandbox', 'Live'])
    chosen_api = st.selectbox('Choose which API to poll', api_addresses)
    if sandbox_or_live == 'Live':
        headers = live_headers
        domain_url = live_domain_url+chosen_api
    else:
        headers = sandbox_headers
        domain_url = sandbox_domain_url+chosen_api

    st.markdown('---')

    if chosen_api != 'Choose...':
        response = requests.get(domain_url, headers=headers)
        st.write(response)
        json_response = response.json()
        pretty_response = json.dumps(response.json(), indent=4)
        first_n_chars = 6000
        if len(pretty_response)<first_n_chars: first_n_chars=len(pretty_response)
        visualise(chosen_api, json_response, pretty_response[:first_n_chars])
    else:
        st.write('When you choose an API, details of the response will be displayed here...')    

    st.markdown('---')
    png_html = get_img_with_href('GitHub-Mark-32px.png', 'https://github.com/daniellewisDL/hsbc-hk-api-explorer')
    st.markdown(png_html, unsafe_allow_html=True)
    png_html = get_img_with_href('GitHub-Mark-Light-32px.png', 'https://github.com/daniellewisDL/hsbc-hk-api-explorer')
    st.markdown(png_html, unsafe_allow_html=True)
    
    return None


if __name__ == "__main__":
    password_attempt = st.text_input('Enter passphrase', type='password')
    if password_attempt != passphrase:
        st.stop()
    else:
        main()
    
# End

