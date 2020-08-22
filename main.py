# E-mail notifications about extremely changes currency rate
# RUR / USD rate
# Python 3.8., PEP 8

# Imports
import os
import yahoo_fin.stock_info as si
import pandas as pd
from datetime import datetime
import smtplib
import time
import logging

# Mimes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class Currency:
    """Notifications about extremely changes currency"""

    def __init__(self, difference, step):
        self.difference = difference
        self.step = step

    def get_currency(self):
        """Returning exchange rate from Yahoo Fin"""

        # Logging errors
        logging.basicConfig(
            level=logging.DEBUG,
            filename='myapp.log',
            format='%(asctime)s %(levelname)s:%(message)s'
        )
        logger = logging.getLogger(__name__)

        try:
            currency = si.get_live_price('USDRUB=X')
        except BaseException as e:
            logging.error(e)
            time.sleep(self.step)
            self.get_currency()

        return float(currency)

    def save_currency(self):
        """Saving current currency into DB"""

        data_base = pd.read_csv('data_base.csv')
        currency = self.get_currency()
        data_base = data_base.append(
            pd.Series((float(currency),
                       datetime.now().strftime('%d/%m/%Y-%H:%M')),
                      index=['currency', 'datetime']),
            ignore_index=True
        )

        data_base.to_csv('data_base.csv', index=False)

    def send_mail(self, text):
        """Sending mail alert about extremely changes currency"""

        # ==================== Account ======================

        addr_from = os.environ.get('WORK_EMAIL')
        password = os.environ.get('WORK_EMAIL_PASS')
        addr_to = os.environ.get('MY_EMAIL')

        msg = MIMEMultipart()
        msg['From'] = addr_from
        msg['To'] = addr_to
        msg['Subject'] = 'Обменный курс RUR/USD изменился'

        body = text
        msg.attach(MIMEText(body, 'plain'))

        # =============== Mail Server Settings ===============

        print('Connecting to server...')
        server = smtplib.SMTP_SSL(os.environ.get('WORK_SMTP'), 465)
        print('Login...')
        server.login(addr_from, password)
        print('Logged in and ready to send...')
        server.send_message(msg)
        server.quit()
        print('Done and quit')

        # ======================== END ========================

    def check_currency(self):
        """Check changes currency"""

        df = pd.read_csv('data_base.csv')

        # Meaning last bids for 3 days
        currency_take_one = df.tail(12)['currency'].mean()
        currency_take_one = round(currency_take_one, 2)
        print('Mean currency:', currency_take_one)
        # Live bid
        self.save_currency()
        df_updated = pd.read_csv('data_base.csv')
        currency_take_two = df_updated.tail(1)['currency'].mean()
        currency_take_two = round(currency_take_two, 2)
        print('Bid for comparisons:', currency_take_two)

        if currency_take_two >= currency_take_one + self.difference:
            self.send_mail(
                f'''[Курс RUR/USD вырос на {round((currency_take_two / currency_take_one -1) * 100, 2)}%] \n
                    Средний курс за 3 дн: {currency_take_one}, Текущий: {currency_take_two}'''
            )
        elif currency_take_two <= currency_take_one - self.difference:
            self.send_mail(
                f'''[Курс RUR/USD снизился на {round((currency_take_one / currency_take_two) * 100, 2)}%] \n
                  Средний курс за 3 дн: {currency_take_one}, Текущий: {currency_take_two}'''
            )
        else:
            pass


if __name__ == '__main__':
    while True:
        step = 21600  # Time between requests in sec
        currency = Currency(0.8, step)  # Exchange rate difference in native value
        currency.check_currency()
        print('Sleep, min:', step / 60)
        time.sleep(step)
