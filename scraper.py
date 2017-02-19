
# coding: utf-8

# In[ ]:

from selenium import webdriver
import random
import time
from bs4 import BeautifulSoup
import os
import csv
import datetime
from send_email import send_email
import glob


def sift_chars(fname_str):
    '''
    ensures filename is legal, replaces all with hyphens
    '''
    
    illegal_chars = "%><!`&*‘|{}?“=\/:@'" + '"'
    
    for c in illegal_chars:
        fname_str = fname_str.replace(c, "-")
        
    return fname_str


def login_to_pacer(login_user, login_password, dl_directory):
    '''
    simply logs into the pacer system for any court
    '''
    # setup driver
    chrome_profile = webdriver.ChromeOptions()
    profile = {
        "download.default_directory": dl_directory,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.plugins_disabled": ["Chrome PDF Viewer"]}
    chrome_profile.add_experimental_option("prefs", profile)
    driver = webdriver.Chrome(chrome_options=chrome_profile)

    # login to pacer website
    login_url = "https://pacer.login.uscourts.gov/csologin/login.jsf"
    driver.get(login_url)
    driver.find_element_by_name("login:loginName").send_keys(login_user)
    driver.find_element_by_name("login:password").send_keys(login_password)
    driver.find_element_by_name('login:fbtnLogin').click()

    time.sleep(random.randint(1,3))

    return driver


def get_docket_rows(driver, case_num, year, court_perl):
    '''
    goes to specific court perl script and extracts docket rows for specific case.
    can be used for main case and associated cases
    '''

    # execute if not getting rows for associated cases
    if case_num != False:
        # Western District Texas Court, start loop for cases here
        driver.get(court_perl)
        driver.find_element_by_name("case_num").clear()
        driver.find_element_by_name("case_num").send_keys(case_num)
        driver.find_element_by_id('case_number_find_button_0').click()

        # wait until case is found and number is changed
        count = 0
        while driver.find_element_by_name(
                "case_num").get_attribute('value') == case_num:
            time.sleep(1)
            count += 1
            if count > 30:
                break

    time.sleep(random.randint(1,3))  # case has been found, proceed

    driver.find_element_by_name("date_from").clear()
    driver.find_element_by_name("date_from").send_keys("01/01/1990")
    driver.find_element_by_name("date_to").clear()
    driver.find_element_by_name("date_to").send_keys(
        datetime.date.today().strftime("%m/%d/%Y"))
    
    time.sleep(random.randint(1,3))
    driver.find_element_by_name('button1').click()

    # get source to get docket info
    docket_source = str(driver.page_source)
    soup = BeautifulSoup(docket_source, 'lxml')
    

    
    # set start for row, will change if scrape was interrupted
    row_start = 0

    # get associated cases if main case
    if case_num != False:
        
        with open(district + "/" + je_id + "/" + je_id + "_data.csv", 'r', encoding="utf-8") as f:
            reader = csv.reader(f)
            data = list(reader)
        
        if len(data) == 1: 
            get_associated_cases(soup)
            # save docket source if main case
            with open(district + "/" + je_id + "/" + str(je_id) + ".html", "w", encoding="utf-8") as f:
                f.write(docket_source)
            
        else:
            row_start = len(data) - 1

    docket_rows = []
    for i in range(len(soup.findAll("table")) - 5):
        # table is broken up to sets of 100 rows, don't want first 4 or last
        ind = i + 4
        docket_table = soup.findAll("table")[ind]
        docket_headers = ("Filing Date", "#", "Docket Text")

        # get table info in dict
        for row in docket_table.findAll("tr"):
            row_data = []
            for i, column in enumerate(row.findAll("td")):
                if i == 0:
                    row_data.append(column.text)
                elif i == 2:
                    cell_urls = {}
                    urls = column.findAll("a")
                    for u in urls:
                        cell_urls[u.text.strip()] = u.get("href")
                        
                    row_data.append((column.text.strip(), cell_urls))
                        
                elif i > 2:
                    row_data.append(column.text.strip())

            if len(row_data) > 0:
                docket_rows.append(tuple(row_data))

    return docket_rows[row_start:]


def process_link(link_str, base_url, district, already_scraped, adversary=False, dock_num=False):
    '''
    takes any links to documents, and downloads them into file structure
    '''

    if link_str.startswith("https://"):
        pass
    else:
        link_str = base_url + link_str

    driver.get(link_str)
    f_paths = []

    if "Multiple Documents" in str(driver.page_source):
        soup = BeautifulSoup(str(driver.page_source), 'lxml')
        doc_table = soup.findAll("tr")
        for r in doc_table:
            if "href" in str(r):
                tds = r.findAll("td")
                doc_url = tds[0].a["href"]
                dl_id = doc_url.split("/")[-1]
                if dl_id not in already_scraped:
                    if doc_url.startswith("https://"):
                        driver.get(doc_url)
                        driver.find_element_by_xpath(
                            '//*[@id="cmecfMainContent"]/form/input').click()
                    else:
                        doc_url = base_url + doc_url
                        driver.get(doc_url)
                        driver.find_element_by_xpath(
                            '//*[@id="cmecfMainContent"]/form/input').click()

                    file_name = tds[2].text
                    new_name = sift_chars(file_name.strip()) + ".pdf"

                    # if not associated case
                    # create file structure
                    if adversary == False:
                        if not os.path.exists(
                                district + "/" + je_id + "/" + docket_number):
                            os.makedirs(
                                district + "/" + je_id + "/" + docket_number)

                        new_path = district + "/" + je_id + "/" + docket_number + "/" + new_name
                        
                    else:
                        if not os.path.exists(
                                district + "/" + je_id + "/associated/" + adversary + "/" + dock_num):
                            os.makedirs(
                                district + "/" + je_id + "/associated/" + adversary + "/" + dock_num)

                        new_path = district + "/" + je_id + "/associated/" + adversary + "/" + dock_num + "/" + new_name

                        
                    # wait for file to download
                    counter = 0
                    while len(glob.glob("*.pdf")) == 0:
                        time.sleep(1)
                        counter += 1
                        if counter > 500:
                            break
                    try:
                        download_name = glob.glob("*.pdf")[0]
                        os.rename(download_name, new_path)
                    
                    except:
                        if "Restricted Web Site" in str(driver.page_source):
                            new_path = "RESTRICTED"
                    
                    already_scraped.append(dl_id)
                    f_paths.append(new_path)


    else:
        soup = BeautifulSoup(str(driver.page_source), 'lxml')
        
        valid_id = True
        # try, some downloads restricted
        try:
            dl_id = soup.find("form")["action"].split("/")[-1]
            
        except:
            valid_id = False
        
        if valid_id == True:
            if dl_id not in already_scraped:
                
                try:
                    driver.find_element_by_xpath(
                        '//*[@id="cmecfMainContent"]/form/input').click()
                except:
                    valid_id == False
                    
                if valid_id == True:

                    # create file structure
                    if adversary == False:
                        if not os.path.exists(
                                district + "/" + je_id + "/" + docket_number):
                            os.makedirs(
                                district + "/" + je_id + "/" + docket_number)

                        new_path = district + "/" + je_id + "/" + docket_number + "/Main Document.pdf"

                    else:
                        if not os.path.exists(
                                district + "/" + je_id + "/associated/" + adversary + "/" + dock_num):
                            os.makedirs(
                                district + "/" + je_id + "/associated/" + adversary + "/" + dock_num)

                        new_path = district + "/" + je_id + "/associated/" + adversary + "/" + dock_num + "/Main Document.pdf"

                    # wait for file to download
                    counter = 0
                    while len(glob.glob("*.pdf")) == 0:
                        time.sleep(1)
                        counter += 1
                        if counter > 500:
                            break

                    try:
                        download_name = glob.glob("*.pdf")[0]
                        os.rename(download_name, new_path)
                    
                    except:
                        if "Restricted Web Site" in str(driver.page_source):
                            new_path = "RESTRICTED"
                            
                    already_scraped.append(dl_id)
                    f_paths.append(new_path)
                    
                else:
                    f_paths.append("Restricted")
                
        else:
            f_paths.append("Restricted")

    return (f_paths, already_scraped)


def get_associated_cases(soup):

    ass_cases_ext = soup.findAll("div", {"class": "noprint"})[1].find("a")["href"]
    driver.get(base_url + ass_cases_ext)
    soup = BeautifulSoup(str(driver.page_source), "lxml")
    
    assoc_rows = soup.find("table").findAll("tr")
    
    if not os.path.exists(district + "/" + je_id + "/" + "associated"):
        os.makedirs(district + "/" + je_id + "/" + "associated")
        
    with open(district + "/" + je_id + "/" + str(je_id) + "_associated_cases.html", "w", encoding="utf-8") as f:
        f.write(str(driver.page_source))
    
    # if interrupted start from where last row
    if os.path.exists(str(district) + "/" + str(je_id) + "/" + str(je_id) + '_associated_cases.csv'):
        with open(str(district) + "/" + str(je_id) + "/" + str(je_id) + '_associated_cases.csv', 'r', encoding="utf-8") as f:
            reader = csv.reader(f)
            data = list(reader)
            
        assoc_rows = assoc_rows[len(data)-1:]
        
    else:
        with open(str(district) + "/" + str(je_id) + "/" + str(je_id) + '_associated_cases.csv', 'a', encoding="utf-8") as f:
            w = csv.writer(f, delimiter=',')
            header = ("je_id", "Related Case No", "Caption", "Type", "Judge", "Plaintiff", "Defendant", "Plaintiff Lawyer", "Defendant Lawyer", "Date Filed", "Date Terminated", "Nature of Suit")
            w.writerow(header)

    for row in assoc_rows: # CHANGE FOR FULL
        columns = row.findAll("td")
        if len(columns) > 0:

            case_ext = columns[1].find("a")["href"]
            case_num = columns[1].find("a").text
            caption = ' '.join(columns[1].text.split()[1:])
            case_type = columns[2].text

            row_to_write = (je_id, case_num, caption, case_type)

            with open(str(district) + "/" + str(je_id) + "/" + str(je_id) + '_associated_cases.csv', 'a', encoding="utf-8") as f:
                w = csv.writer(f, delimiter=',')
                w.writerow(row_to_write)

            driver.get(base_url + case_ext) 

            docket_rows = get_docket_rows(
                driver=driver,
                case_num=False,
                year=False,
                court_perl=False)
            
            if not os.path.exists(
                    district + "/" + je_id + "/associated/" + case_num):
                os.makedirs(
                    district + "/" + je_id + "/associated/" + case_num)

            with open(district + "/" + je_id + "/associated/" + case_num + "/" + str(case_num) + ".html", "w", encoding="utf-8") as f:
                f.write(str(driver.page_source))
                
            if os.path.exists(district + "/" + je_id + "/associated/" + str(case_num) + "/" + 'assoc_data.csv'):
                with open(district + "/" + je_id + "/associated/" + str(case_num) + "/" + 'assoc_data.csv', 'r', encoding="utf-8") as f:
                    reader = csv.reader(f)
                    data = list(reader)
                    
                docket_rows = docket_rows[len(data)-1:]
                
            else:
                with open(district + "/" + je_id + "/associated/" + str(case_num) + "/" + 'assoc_data.csv', 'a', encoding="utf-8") as f:
                    w = csv.writer(f, delimiter=',')
                    header = ("je_id","case_num","docket_text","docket_number","docket_date","file_link","[lawfirm1]","[lawyers1]","[lawfirm2]","[lawyers2]","[lawfirm3]","[lawyers3]","[moving party]","[motion caption]")
                    w.writerow(header)

            for row in docket_rows:  # just 20 rows CHANGE FOR FULL
                docket_date = row[0]
                docket_text = row[2].strip()
                if len(row[1]) > 1 and len(row[1][0]) > 0 and row[1][0][0].isdigit():
                    docket_number = row[1][0].split()[0]
                    
                else:
                    with open(district + "/" + je_id + "/associated/" + str(case_num) + "/" + 'assoc_data.csv', 'r', encoding="utf-8") as f:
                        reader = csv.reader(f)
                        temp_data = list(reader)
                    docket_number = temp_data[-1][-3]

                already_scraped = []
                paths = []
                for c in row:
                    if len(c) > 1 and isinstance(c[1], dict) and len(c[1]) > 0:
                        for k in c[1].keys():
                            url = c[1][k]
                            res = process_link(
                                link_str=url,
                                base_url=base_url,
                                district=district,
                                already_scraped=already_scraped,
                                dock_num = docket_number,
                                adversary=case_num)
                            file_paths = res[0]
                            if len(file_paths) > 0:
                                already_scraped = res[1]
                                paths.extend(file_paths)

                            time.sleep(random.randint(1,3))  # wait after each link call

                csv_row = [
                    je_id,
                    case_num,
                    docket_text,
                    docket_number,
                    docket_date,
                    "; ".join(paths)]
                scraped_data[district].append(csv_row)

                with open(district + "/" + je_id + "/associated/" + str(case_num) + "/" + 'assoc_data.csv', 'a', encoding="utf-8") as f:
                    w = csv.writer(f, delimiter=',')
                    w.writerow(csv_row)
                    
        time.sleep(random.randint(1,3))


# In[ ]:

# main program
# for case num info
with open('dataset.csv', 'r', encoding="utf-8") as f:
    reader = csv.reader(f)
    data = list(reader)
    
with open('distlogin.csv', 'r', encoding="utf-8") as f:
    reader = csv.reader(f)
    distlogin_csv = list(reader)
    
with open('completed', 'r') as f:
    completed_cases = f.read().split('\n')
    
email_address = distlogin_csv[0][0]
email_password = distlogin_csv[0][1]
dl_directory = distlogin_csv[0][2]
district = distlogin_csv[1][0]

# change for each district
dist_data = [x for x in data if x[-2] == district]
district = ''.join(district.split())

distlogin = {}

for r in distlogin_csv[1:]:
    distlogin[district] = {"login": r[1],
                       "pw": r[2],
                       "base_url": r[3]}

# prepare and loop
scraped_data = {}
scraped_data[district] = []

if not os.path.exists(district):
    os.makedirs(district)

driver = login_to_pacer(login_user=distlogin[district]["login"], login_password=distlogin[district]["pw"], dl_directory=dl_directory)

for case in dist_data:  # just two cases CHANGE FOR FULL
    
    print(datetime.datetime.time(datetime.datetime.now()))
    
    company = case[0]
    je_id = case[1]
    case_num = case[2]
    petition_date = case[3]
    year = case[6]
    
    if je_id not in completed_cases:
    
        send_email(email_address, email_password, email_address, "New Case", "JEID" + str(je_id))

        if not os.path.exists(district + "/" + je_id):
            os.makedirs(district + "/" + je_id)

        if not os.path.exists(district + "/" + je_id + "/" + je_id + "_data.csv"):
            # for output data
            with open(district + "/" + je_id + "/" + je_id + "_data.csv", 'w', encoding="utf-8") as f:
                w = csv.writer(f, delimiter=',')
                header = ("Company","je_id","petition_date","casenum","xdistfiled","docket_text","docket_number","docket_date","file_link","[lawfirm1]","[lawyers1]","[lawfirm2]","[lawyers2]","[lawfirm3]","[lawyers3]","[moving party]","[motion caption]")
                w.writerow(header)

        # change for each district
        base_url = distlogin[district]["base_url"]
        court_perl = base_url + "/cgi-bin/DktRpt.pl"
        docket_rows = get_docket_rows(
            driver=driver,
            case_num=case_num,
            year=year,
            court_perl=court_perl)

        for row in docket_rows:  # just 20 rows CHANGE FOR FULL
            docket_date = row[0]
            docket_text = row[2].strip()
            if len(row[1]) > 1 and len(row[1][0]) > 0 and row[1][0][0].isdigit():
                docket_number = row[1][0].split()[0]
            else:
                with open(district + "/" + je_id + "/" + je_id + "_data.csv", 'r', encoding="utf-8") as f:
                    reader = csv.reader(f)
                    temp_data = list(reader)
                docket_number = temp_data[-1][-3]

            already_scraped = []
            paths = []
            for c in row:
                if len(c) > 1 and isinstance(c[1], dict) and len(c[1]) > 0:
                    for k in c[1].keys():
                        url = c[1][k]
                        res = process_link(
                            link_str=url,
                            base_url=base_url,
                            district=district,
                            already_scraped=already_scraped)
                        file_paths = res[0]
                        if len(file_paths) > 0:
                            already_scraped = res[1]
                            paths.extend(file_paths)

                        time.sleep(random.randint(1,3))  # wait after each link call

            csv_row = [
                company,
                je_id,
                petition_date,
                case_num,
                district,
                docket_text,
                docket_number,
                docket_date,
                "; ".join(paths)]
            scraped_data[district].append(csv_row)

            with open(district + "/" + je_id + "/" + je_id + "_data.csv", 'a', encoding="utf-8") as f:
                w = csv.writer(f, delimiter=',')
                w.writerow(csv_row)
                
        with open('completed', 'a') as f:
            f.write('\n' + je_id)

send_email(email_address, email_password, email_address, "Finished", "Done scraping." + str(je_id))
print(datetime.datetime.time(datetime.datetime.now()))


# In[ ]:



