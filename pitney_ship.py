"""PitneyShip Email Scripts"""
import setup # pylint: disable=unused-import, wrong-import-order
from bs4 import BeautifulSoup

def scrape_pitneyship(file):
    """Scrape and parse PitneyShip email"""
    soup = BeautifulSoup(file, 'html.parser')
    for br_tag in soup.find_all("br"):
        br_tag.replace_with("\n")
    th_data = soup.find_all('th')
    tracking_id = th_data[18].text.splitlines()[2].replace(" =20", "")
    estimated_delivery = th_data[20].text.replace("  ", "").splitlines()[1]
    courier = th_data[22].text.replace(" ", "").splitlines()[1]
    address_block = th_data[26].text.replace("  ", "").replace("MO=", "")
    customer = address_block.splitlines()[1]
    street_address = address_block.splitlines()[2]
    return {
        "tracking_id": tracking_id,
        "estimated_delivery": estimated_delivery,
        "courier": courier,
        "customer": customer,
        "street_address": street_address,
        "system": "ACC"
        }
