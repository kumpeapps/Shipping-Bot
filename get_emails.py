"""Fetch Emails from mech_shippingbot"""
import setup # pylint: disable=unused-import, wrong-import-order
from typing import Optional
from imap_tools import MailBox, AND
import mysql.connector
from params import Params
from pitney_ship import scrape_pitneyship


def parse_data(message: dict) -> dict:
    """Parse message data into dict"""
    parsed_data = {}
    if message.from_ == 'no-reply@sendpro360.pitneybowes.com':
        parsed_data = scrape_pitneyship(message.html)
        if message.subject == "[PitneyShip] Package Shipped":
            parsed_data['status'] = "shipped"
            parsed_data['flow_status'] = "processing"
        elif message.subject == "[PitneyShip] Package Delivered":
            parsed_data['status'] = "delivered"
            parsed_data['flow_status'] = "rejected"
        elif message.subject == "Shipment Delivered":
            parsed_data['status'] = "delivered"
            parsed_data['flow_status'] = "rejected"
        else:
            parsed_data['status'] = "unknown"
            parsed_data['flow_status'] = "rejected"
    else:
        parsed_data['flow_status'] = "rejected"
    parsed_data['uid'] = message.uid
    parsed_data['from'] = message.from_
    parsed_data['to'] = message.to
    parsed_data['subject'] = message.subject
    return parsed_data


def process_email(messages: list):
    """Process parsed email data"""
    message_data = []
    processed_data = []
    for message in messages:
        if message['flow_status'] == 'processing':
            order_id = get_order_number(message)
            message['order_id'] = order_id
            if message['order_id'] is not None:
                message_data.append(message)
            else:
                message['flow_status'] = 'processed'
                processed_data.append(message)
        else:
            processed_data.append(message)
    mark_flow_status(processed_data)
    upload_data(messages)


def mark_flow_status(messages: list):
    """Mark email as processed or rejected"""
    creds = Params.Email.dict()
    with MailBox(creds['server']).login(creds['email'], creds['password']) as mailbox:
        for message in messages:
            if message is not None:
                mailbox.flag(message['uid'], message['flow_status'], True)


def fetch_emails():
    """Fetch shippingbot emails"""
    creds = Params.Email.dict()
    with MailBox(creds['server']).login(creds['email'], creds['password']) as mailbox:
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
        database=Params.SQL.database
    )
    if message['status'] == 'shipped':
        status_check = 2
    elif message['status'] == 'delivered':
        status_check = 3
    customer = message['customer']
    address = message['street_address']
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
        autocommit=False

    )
    for message in messages:
        if message['flow_status'] == 'processing':
            cursor = mydb.cursor(buffered= True)
            sql = """INSERT INTO `BOT_Data`.`shippingbot__trackingdata`
                    (`tracking_number`,
                    `street_address`,
                    `courier`,
                    `order_system`,
                    `order_number`,
                    `shipping_status`,
                    `expected_delivery`,
                    `customer_name`,
                    `bot_status`,
                    `email_from`,
                    `email_to`)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE shipping_status = %s, bot_status = %s, last_updated = now()"""
            values = (
                message['tracking_id'],
                message['street_address'],
                message['courier'],
                'ACC',
                message['order_id'],
                message['status'],
                message['estimated_delivery'],
                message['customer'],
                message['flow_status'],
                message['from'],
                ''.join(message['to']),
                message['status'],
                message['flow_status']
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
    mydb = mysql.connector.connect(
        host=Params.SQL.server,
        user=Params.SQL.username,
        password=Params.SQL.password,
        database=Params.SQL.database,
        autocommit=False

    )

    for message in messages:
        if message['status'] == 'shipped':
            status_id = 3
        elif message['status'] == 'delivered':
            status_id = 18
        if message['flow_status'] == 'processing':
            cursor = mydb.cursor(buffered= True)
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
                message['order_id'],
                status_id,
                f"""Marked as {message['status']} by ShippingBot. {message['courier']}
                Tracking ID: {message['tracking_id']}"""
                )
            cursor.execute(sql, values)
            sql2 = f"""UPDATE `Web_ACC_Shopping`.orders
                    SET
                        order_status_id = {status_id},
                        date_modified = now()
                    WHERE 1=1
                        AND order_id = {message['order_id']} """
            cursor.execute(sql2)
            message['flow_status'] = 'processed'
            message_data.append(message)
        else:
            message_data.append(message)
    mydb.commit()
    mydb.close()
    upload_data(message_data, False)
    mark_flow_status(message_data)

if __name__ == "__main__":
    fetch_emails()
