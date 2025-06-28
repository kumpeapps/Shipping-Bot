"""Fetch Emails from mech_shippingbot"""

import setup  # pylint: disable=unused-import, wrong-import-order
import sys
import signal
from typing import Optional
import time
from imap_tools import MailBox, AND
import schedule
import requests
from loguru import logger
import mysql.connector
import pymysql
from params import Params
from pirate_ship import scrape_pirateship

shutdown = False


def parse_data(message: dict) -> dict:
    """Parse message data into dict"""
    parsed_data = {}
    if (
        message.from_ == "no-reply@sendpro360.pitneybowes.com"
        or message.from_ == "no-reply@pb.com"
    ):
        if (
            message.subject == "[PitneyShip] Package Shipped"
            or message.subject == "A shipment from Angela Kumpe is on its way"
        ):
            # parsed_data = scrape_pitneyship(message.html)
            # parsed_data["status"] = "shipped"
            # parsed_data["flow_status"] = "processing"
            parsed_data["status"] = "unknown"
            parsed_data["flow_status"] = "rejected"
        elif (
            message.subject == "[PitneyShip] Package Delivered"
            or message.subject == "Shipment Delivered"
        ):
            parsed_data["status"] = "delivered"
            parsed_data["flow_status"] = "rejected"
        elif message.subject == "Shipment Delivered":
            parsed_data["status"] = "delivered"
            parsed_data["flow_status"] = "rejected"
        else:
            parsed_data["status"] = "unknown"
            parsed_data["flow_status"] = "rejected"
    elif message.from_ in ("helpdesk@kumpeapps.com", "sales@kumpe3d.com"):
        parsed_data = scrape_pirateship(message.html, "Kumpe3D")
        parsed_data["status"] = "shipped"
        parsed_data["flow_status"] = "processing"
    else:
        parsed_data["flow_status"] = "rejected"
    parsed_data["uid"] = message.uid
    parsed_data["from"] = message.from_
    parsed_data["to"] = message.to
    parsed_data["subject"] = message.subject
    return parsed_data


def process_email(messages: list):
    """Process parsed email data"""
    message_data = []
    processed_data = []
    for message in messages:
        if message["flow_status"] == "processing" and message["system"] == "Kumpe3D":
            if message["order_id"] is not None:
                message_data.append(message)
            else:
                message["flow_status"] = "rejected"
                processed_data.append(message)
        elif message["flow_status"] == "processing" and message["system"] == "ACC":
            order_id = get_order_number(message)
            message["order_id"] = order_id
            if message["order_id"] is not None:
                message_data.append(message)
            else:
                message["flow_status"] = "processed"
                processed_data.append(message)
        else:
            processed_data.append(message)
    mark_flow_status(processed_data)
    upload_data(message_data)


def mark_flow_status(messages: list):
    """Mark email as processed or rejected"""
    creds = Params.Email.dict()
    with MailBox(creds["server"]).login(creds["email"], creds["password"]) as mailbox:
        for message in messages:
            if message is not None:
                mailbox.flag(message["uid"], message["flow_status"], True)


def fetch_emails():
    """Fetch shippingbot emails"""
    creds = Params.Email.dict()
    with MailBox(creds["server"]).login(creds["email"], creds["password"]) as mailbox:
        messages = []
        for msg in mailbox.fetch(AND(no_keyword=["processed", "rejected"])):
            message = parse_data(msg)
            messages.append(message)
        process_email(messages)


def get_order_number(message: dict) -> Optional[int]:
    """Attempt to find order number"""
    mydb = mysql.connector.connect(
        host=Params.SQL.server,
        user=Params.SQL.username,
        password=Params.SQL.password,
        database=Params.SQL.database,
    )
    if message["status"] == "shipped":
        status_check = 2
    elif message["status"] == "delivered":
        status_check = 3
    # customer = message['customer']
    address = message["street_address"]
    cursor = mydb.cursor()
    sql = """SELECT
                order_id
            FROM
                BOT_Data.vw_shippingbut__accorders
                WHERE 1=1
                    AND order_status_id = %s
                    AND (shipping_address = %s OR shipping_company = %s)"""
    values = (status_check, address, address)
    cursor.execute(sql, values)
    order_id = cursor.fetchone()
    if order_id is not None:
        order_id = order_id[0]
    mydb.close()
    return order_id


def upload_data(messages: list, initial_upload: bool = True):
    """Upload Tracking Data"""
    message_data = []
    mydb = mysql.connector.connect(
        host=Params.SQL.server,
        user=Params.SQL.username,
        password=Params.SQL.password,
        database=Params.SQL.database,
        autocommit=False,
    )
    for message in messages:
        if message["flow_status"] == "processing":
            cursor = mydb.cursor(buffered=True)
            sql = """INSERT INTO `BOT_Data`.`shippingbot__trackingdata`
                    (`tracking_number`,
                    `street_address`,
                    `courier`,
                    `order_system`,
                    `order_number`,
                    `shipping_status`,
                    `customer_name`,
                    `bot_status`,
                    `email_from`,
                    `email_to`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE shipping_status = %s, bot_status = %s, last_updated = now()"""
            values = (
                message["tracking_id"],
                message["street_address"],
                message["courier"],
                "ACC",
                message["order_id"],
                message["status"],
                message["customer"],
                message["flow_status"],
                message["from"],
                "".join(message["to"]),
                message["status"],
                message["flow_status"],
            )
            cursor.execute(sql, values)
            message_data.append(message)
        else:
            message_data.append(message)
    mydb.commit()
    mydb.close()
    if initial_upload:
        mark_order_shipped(message_data)


def mark_order_shipped(messages: list):
    """Mark Orders as Shipped"""
    message_data = []

    for message in messages:
        if message["system"] == "ACC":
            message_data.append(process_acc(message))
        elif message["system"] == "Kumpe3D":
            message_data.append(process_k3d(message))
    upload_data(message_data, False)
    mark_flow_status(message_data)


def process_acc(message):
    """Process A Creative Collection Tracking"""
    mydb = mysql.connector.connect(
        host=Params.SQL.server,
        user=Params.SQL.username,
        password=Params.SQL.password,
        database=Params.SQL.database,
        autocommit=False,
    )
    if message["status"] == "shipped":
        status_id = 3
    elif message["status"] == "delivered":
        status_id = 18
    if message["flow_status"] == "processing":
        cursor = mydb.cursor(buffered=True)
        sql = """INSERT INTO `Web_ACC_Shopping`.order_history
                    (
                    order_id
                    ,order_status_id
                    ,notify
                    ,comment
                    ,date_added
                    ,date_modified
                    )
            VALUES (%s, %s, 1, %s, now(), now())"""
        values = (
            message["order_id"],
            status_id,
            f"""Marked as {message['status']} by ShippingBot. {message['courier']}
                Tracking ID: {message['tracking_id']}""",
        )
        cursor.execute(sql, values)
        sql2 = f"""UPDATE `Web_ACC_Shopping`.orders
                    SET
                        order_status_id = {status_id},
                        date_modified = now()
                    WHERE 1=1
                        AND order_id = {message['order_id']} """
        cursor.execute(sql2)
        message["flow_status"] = "processed"
        mydb.commit()
        mydb.close()
        return message
    else:
        return message


def process_k3d(message):
    """Process Kumpe3D Tracking"""
    sql_params = Params.SQL
    db = pymysql.connect(
        db="Web_3dprints",
        user=sql_params.username,
        passwd=sql_params.password,
        host=sql_params.server,
        port=3306,
    )
    cursor = db.cursor(pymysql.cursors.DictCursor)
    if message["flow_status"] == "processing":
        try:
            order_id = message["order_id"]
            tracking_id = message["tracking_id"]
            courier = message["courier"]
            sql = """SELECT * FROM `Web_3dprints`.`orders` WHERE idorders = %s"""
            cursor.execute(sql, (order_id))
            order = cursor.fetchone()
            current_status = order["status_id"]
            transaction_id = order["paypal_capture_id"]
            new_status = 14
            if current_status == 11 or current_status == 12:
                new_status = 12
            sql = "UPDATE `Web_3dprints`.`orders` SET `status_id` = %s WHERE idorders = %s"
            sql2 = "UPDATE `Web_3dprints`.`orders__shipments` SET `shipped` = 1 WHERE idorders = %s"
            cursor.execute(sql, (new_status, order_id))
            db.commit()
            cursor.execute(sql2, (order_id))
            sql = """INSERT INTO `Web_3dprints`.`orders__history`
                        (`idorders`,
                        `status_id`,
                        `notes`,
                        `updated_by`)
                    VALUES
                        (%s, %s, "Order shipped", "ShippingBot");"""
            cursor.execute(sql, (order_id, new_status))
            sql = """INSERT INTO `Web_3dprints`.`orders__tracking`
                        (`idorders`,
                        `courier`,
                        `tracking_number`,
                        `tracking_status`)
                    VALUES
                        (%s, %s, %s, "Shipped");"""
            cursor.execute(sql, (order_id, courier, tracking_id))
            db.commit()
            db.close()
            auth = authenticate()
            token = auth["access_token"]
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            }

            if transaction_id is not None:
                data = (
                    '{ "trackers": [ { "transaction_id": "'
                    + transaction_id
                    + '", "tracking_number": "'
                    + tracking_id
                    + '", "status": "SHIPPED", "carrier": "'
                    + message["courier"]
                    + '", "shipment_direction": "FORWARD" }] }'
                )

                requests.post(
                    "https://api-m.paypal.com/v1/shipping/trackers-batch",
                    headers=headers,
                    data=data,
                    timeout=30,
                )
        finally:
            message["flow_status"] = "processed"
            return message
    else:
        message["flow_status"] = "processed"
        return message


def authenticate() -> dict:
    """Authenticate to Get Bearer Token"""
    data = {
        "grant_type": "client_credentials",
    }

    response = requests.post(
        "https://api-m.paypal.com/v1/oauth2/token",
        data=data,
        auth=(Params.PayPal.client_id, Params.PayPal.secret),
        timeout=30,
    )
    return response.json()


def handle_shutdown(signum, _):
    """Handle graceful shutdown on signal"""
    global shutdown # pylint: disable=global-statement
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown = True


if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    logger.info("Initializing Shipping Bot")
    schedule.every().hour.do(fetch_emails)
    while not shutdown:
        schedule.run_pending()
        time.sleep(20)  # Sleep for 20 seconds before checking again
    logger.info("Shipping Bot stopped.")
