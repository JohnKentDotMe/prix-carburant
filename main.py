# coding:utf-8
import requests
import os
from configparser import ConfigParser
import certifi
import urllib3
from zipfile import ZipFile
from datetime import datetime
import xml.etree.ElementTree as ET
from lxml import html
import sqlite3
from sqlite3 import Error


####
# Main file function

class prix_carburant():

    def pub_date(self):
        d = datetime.now()
        date_v = "{:%Y-%m-%d %H:%M:%S}".format(d)
        return date_v

    def transform_date(self, input_date):
        date_splited = input_date.split('/')
        new_date = '20' + date_splited[2] + '-' + date_splited[1] + '-' + date_splited[0]
        return new_date

###
# Initialization of values
    def __init__(self):
        print('[i] Initializing values...', end='')
        self.section = 'prix-carburant'
        self.site = 'https://www.prix-carburants.gouv.fr/'
        self.url_open_data = 'https://donnees.roulez-eco.fr/opendata/instantane'
        self.cur_dir = os.getcwd()
        self.pc_folder = '/PC_folder/'
        self.zip_file = '-open_data.zip'
        self.xml_file = 'PrixCarburants_instantane.xml'
        self.pdv = '78170002'
        self.inscrire = self.site + 'internaute/inscrire'
        self.login_check = self.site + 'internaute/login_check'
        self.fav = 'https://www.prix-carburants.gouv.fr/internaute/'
        self.gas_type = ('E85', 'Diesel', 'GPLc', 'SP95', 'SP95-E10', 'SP98')
        self.sqlite_base = 'db.sqlite3'
        self.sql_create_pump_table = """ CREATE TABLE IF NOT EXISTS pump (
                                        id integer PRIMARY KEY,
                                        pump_id text NOT NULL,
                                        name text NOT NULL,
                                        brand text,
                                        address text,
                                        location text
                                    );"""
        self.sql_create_pump_data_table = """CREATE TABLE IF NOT EXISTS pumpdata (
                                    id integer PRIMARY KEY,
                                    name text NOT NULL,
                                    gas_type text NOT NULL,
                                    price float,
                                    update_date text NOT NULL,
                                    pub_date text NOT NULL,
                                    FOREIGN KEY (pump_id) REFERENCES projects (id)
                                );"""
        

        print("OK")

###
# Global functions
    def read_config(self):
        """ Read database configuration file and return a dictionary object
        :param filename: name of the configuration file
        :param section: section of database configuration
        :return: a dictionary of database parameters
        """
        # create parser and read ini configuration file
        filename = self.cur_dir + '/config.ini'
        parser = ConfigParser()
        parser.read(filename)

        # get section, default to mysql
        self.db = {}
        if parser.has_section(self.section):
            items = parser.items(self.section)
            for item in items:
                self.db[item[0]] = item[1]
        else:
            raise Exception('{0} not found in the {1} file'.format(self.section, filename))

    def is_alive(self, site):
        '''function to ckeck if the site is alive'''

        print("[i] Reaching site...",end='')
        http = urllib3.PoolManager(
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where())
        r = http.request('GET',site)

        if r.status == 200:
            print("OK (" + site +")")
        else:
            raise Exception('Error {0}: {1}'.format(r.status,r.exception.RequestException))

        r.release_conn()

###
# Database functions

    def is_db_exist(self):
        if os.path.isfile(self.db):
            print("[i] DB file found!")
        else:
            print("[!] DB file not found. Start creating 'db.sqlite3' file")
            try:
                conn = sqlite3.connect(self.sqlite_base)
                print(sqlite3.version)
                return conn
            except Error as e:
                print(e)
            finally:
                conn.close()
        return None

    def create_table(self, conn, create_table_sql):
        try:
            c = conn.cursor()
            c.execute(create_table_sql)
        except Error as e:
            print(e)

    def request_db(self, buffer):

        conn = sqlite3.connect(self.sqlite_base)
        conn.isolation_level = None
        c = conn.cursor()

        #print(' Executing:', buffer)

        if sqlite3.complete_statement(buffer):
            try:
                buffer = buffer.strip()
                c.execute(buffer)

                if buffer.lstrip().upper().startswith("SELECT"):
                    fetch_all = c.fetchall()

                    if len(fetch_all) > 0:
                        conn.close()
                        return fetch_all
                    else:
                        conn.close()
                        return [(-1,)]
                else:
                    conn.close()

            except sqlite3.Error as e:
                print("An error occurred:", e.args[0])
        else:
            print('Buffer statement not complete!')

    def insert_many_to_pompedata(self, data):
        try:
            conn = sqlite3.connect(self.sqlite_base)
            conn.isolation_level = None
            c = conn.cursor()
            c.executemany('INSERT INTO prixcarburant_pompedata(pompe_gas_type,pompe_gas_price,pompe_gas_update,pub_date,pompe_id_f_id) VALUES (?,?,?,?,?)', data)
            conn.close()

        except sqlite3.Error as e:
            print("An error occurred:", e.args[0])

###
# Open data functions EXPERIMENTAL

    def download_data(self):
        "download data from https://donnees.roulez-eco.fr/opendata/instantane"
        print("[i] Downloading file...", end= ' ')

        self.zip_file = self.cur_dir + self.pc_folder + self.pub_date() + self.zip_file

        http = urllib3.PoolManager(
            cert_reqs='CERT_REQUIRED',
            ca_certs=certifi.where())
        r = http.request('GET', self.url_open_data, preload_content=False)

        if r.status == 200:
            with open(self.zip_file, 'wb') as out:
                while True:
                    data = r.read()
                    if not data:
                        break
                    out.write(data)
                    print("OK")
        else:
            raise Exception('Error {0}: {1}'.format(r.status, r.exception.RequestException))

        r.release_conn()

    def unzip(self):
        "unzip the downloaded file"

        print("[i] UnZipping file...", end='')
        with ZipFile(self.zip_file) as myzip:
            myzip.extractall(path=self.cur_dir + self.pc_folder)
            print("OK")

    def xml_parser(self):
        "convert xml file to json"
        print("[i] Converting XML file to DICT...",end='')
        self.xml_file = self.cur_dir + self.pc_folder + self.xml_file

        with open(self.xml_file, "rb"):  # notice the "rb" mode
            self.dict_data = ET.parse(self.xml_file)
            self.root = self.dict_data.getroot()

        print("OK")

    def extract_xml_info(self):
        for pdv in self.root.findall('pdv'):
            if pdv.get('id') == self.pdv:
                print("Ville: " + pdv.find('ville').text)
                for info in pdv.findall('prix'):
                    if info.get('nom') == "SP98":
                        print(info.get('nom') + ": " + info.get('valeur'))

###
# Account connexion and bookmark reading

    def get_token(self):
        print('[i] Get token for authentification...', end='')
        self.session_request = requests.session()
        self.r = self.session_request.get(self.inscrire)

        if self.r.status_code == 200:
            self.page = self.r.text #Gather html page content

            self.page_parser = html.fromstring(self.page) #Initiale parser for html page
            self.token = str(list(set(self.page_parser.xpath("//input[@name='_csrf_token']/@value")))[0]) #Gather token from page parsed
            print('OK')

        else:
            raise Exception('Error {0}: {1}'.format(self.r.status_code, self.r.raise_for_status()))

    def connect_with_session(self):

        print('[i] Logging...', end='')
        # Construct payload for connection
        self.payload = {
            '_username': str(self.db['username']),
            '_password': str(self.db['password']),
            '_csrf_token': self.token,
            '_submit' : 'Se connecter'
        }

        # Initialize cookie file/management

        self.r = self.session_request.post(self.login_check, data=self.payload, headers=dict(referer=self.inscrire))

        if self.r.status_code == 200:

            self.r = self.session_request.get(self.fav, headers=dict(referer=self.fav))

            if self.r.status_code == 200:
                self.page = self.r.text
                self.page_parser = html.fromstring(self.page)  # Initiale parser for html page

                self.is_connected = self.page_parser.xpath('//h2')
                if self.is_connected[0].text == 'Bienvenue sur votre espace personnel':
                    print('OK')

            else:
                print("Cannot reach Fav page" + str(self.r.status_code))
        else:
            print("Cannot connect: " + str(self.r.status_code))

    def parse_fav(self):

        print('[i] Gathering gas price...',end='')
        self.r = self.session_request.get(self.fav, headers = dict(referer = self.fav))

        if self.r.status_code == 200:
            self.page = self.r.text
            self.page_parser = html.fromstring(self.page)
            print('OK')

            #print('[i] Listing favs:')
            count = 0

            # Parsing webpage and create json db

            self.json_data = {}

            for tr in self.page_parser.xpath('//*[@id="tab_resultat"]/tbody/tr[@class="data" or @class="data clair"]'):
                #//*[@id="tab_resultat"]/tbody
                #print(tr)
                
                #print('Fav n°',count)

                id = tr.get('id')
                title = tr.xpath('td[1]/div[1]/div[1]/span[1]/strong//text()')[0]
                name, brand = title.split(' | ')
                address = tr.xpath('td[1]/div[1]/div[1]/span[2]//text()')[0]
                location = tr.xpath('td[1]/div[1]/div[1]/span[3]//text()')[0]
                gazole_price = tr.xpath('td[2]/span[1]/strong//text()')[0] if tr.xpath('td[2]/span[1]/strong//text()') else None
                gazole_date = tr.xpath('td[2]/span[2]//text()')[0] if tr.xpath('td[2]/span[2]//text()') else None
                sp98_price = tr.xpath('td[3]/span[1]/strong//text()')[0] if tr.xpath('td[3]/span[1]/strong//text()') else None
                sp98_date = tr.xpath('td[3]/span[2]//text()')[0] if tr.xpath('td[3]/span[2]//text()') else None
                sp95_e10_price = tr.xpath('td[4]/span[1]/strong//text()')[0] if tr.xpath('td[4]/span[1]/strong//text()') else None
                sp95_e10_date = tr.xpath('td[4]/span[2]//text()')[0] if tr.xpath('td[4]/span[2]//text()') else None
                sp95_price = tr.xpath('td[5]/span[1]/strong//text()')[0] if tr.xpath('td[5]/span[1]/strong//text()') else None
                sp95_date = tr.xpath('td[5]/span[2]//text()')[0] if tr.xpath('td[5]/span[2]//text()') else None
                gpl_price = tr.xpath('td[6]/span[1]/strong//text()')[0] if tr.xpath('td[6]/span[1]/strong//text()') else None
                gpl_date = tr.xpath('td[6]/span[2]//text()')[0] if tr.xpath('td[6]/span[2]//text()') else None
                e85_price = tr.xpath('td[7]/span[1]/strong//text()')[0] if tr.xpath('td[7]/span[1]/strong//text()') else None
                e85_date = tr.xpath('td[7]/span[2]//text()')[0] if tr.xpath('td[7]/span[2]//text()') else None
             
                #print(id, name, brand, address, location, gazole_price, gazole_date, sp98_price, sp98_date, sp95_e10_price, sp95_e10_date, sp95_price, sp95_date, gpl_price, gpl_date, e85_price, e85_date)
                self.json_data["fav"+str(count)] = {}
                self.json_data["fav"+str(count)]["id"] = id
                self.json_data["fav"+str(count)]["data"] = {
                    "name": name,
                    "brand": brand,
                    "address": address,
                    "location": location,
                    "gas_price": {
                        "gazole": {
                            "price": gazole_price,
                            "date": gazole_date},
                        "sp98": {
                            "price": sp98_price,
                            "date": sp98_date},
                        "sp95_e10": {
                            "price": sp95_e10_price,
                            "date": sp95_e10_date},
                        "sp95": {
                            "price": sp95_price,
                            "date": sp95_date},
                        "gpl": {
                            "price": gpl_price,
                            "date": gpl_date},
                        "e85": {
                            "price": e85_price,
                            "date": e85_date}
                    }
                }

                count += 1

        return self.json_data

###
# Run it

    def run(self):
        self.read_config()
        #self.is_alive(self.url_open_data)
        #self.download_data()
        #self.unzip()
        #self.xml_parser()
        #self.extract_xml_info()
        self.get_token()
        self.connect_with_session()
        self.parse_fav()


if __name__ == '__main__':
    prix_carburant().run()