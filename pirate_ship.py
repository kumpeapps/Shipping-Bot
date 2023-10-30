"""PirateShip Email Scripts"""
import setup # pylint: disable=unused-import, wrong-import-order
from bs4 import BeautifulSoup

def scrape_pirateship(file):
    """Scrape and parse PitneyShip email"""
    soup = BeautifulSoup(file, 'html.parser')
    system = "Kumpe3D"
    shipping_method = soup.find(id="courier").text
    if shipping_method == "Ground Advantage":
        courier = "USPS"
    elif shipping_method == "Priority Mail":
        courier = "USPS"
    elif "UPS" in shipping_method:
        courier = "UPS"
    else:
        courier = "PITNEY_BOWES"
    order_id = soup.find(id="order_number").text
    tracking_id = soup.find("a", {"class": "tracking-link"}).text
    return {
        "tracking_id": tracking_id,
        "estimated_delivery": "null",
        "courier": courier,
        "customer": "",
        "street_address": "",
        "order_id": order_id,
        "system": system
        }
    