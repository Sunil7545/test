from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import StaleElementReferenceException
from collections import OrderedDict
from bs4 import BeautifulSoup
import json
import time
import datetime
import logging.config
import pandas as pd
from decouple import config

logging.config.fileConfig(config('LOGFILE_CONF'), defaults={'logfilename': config('LOGFILE_PATH')}, disable_existing_loggers=False)
logger = logging.getLogger(__name__)

logger.info("Logger Initialized")

options = Options()

main_url_count = 0

start_time = time.time()

main_urls_file = config('MAIN_URLS_PATH')

df = pd.read_csv(main_urls_file)

main_url_list = df['URL']

# loop for main urls
# range(len(main_url_list))
for j in list(range(len(main_url_list))):

    options.headless = True

    driver = webdriver.Firefox(options=options, executable_path=config('GECODRIVER_PATH'))

    logger.info("Headless Firefox Initialized for main url %s" %str(j+1))

    url = main_url_list[j]

    status = df['STATUS'][j]

    # Check the status in the dataframe (csv file) if 0 it goes ahead else status is 1 and the url is already scrapped
    if status == 0:

        main_url_count = main_url_count + 1

        logger.info("Entering Main url nr %d = %s" % (main_url_count, url))

        main_dict = OrderedDict()

        driver.get(url)

        WebDriverWait(driver, 3)

        counter = 0

        # loop for learn more information of each main url
        for i in list(range(1, 101)):

            try:
                # results is a temporary dictionary where it collects all the information of each learn_more url
                results = OrderedDict()

                counter = counter + 1

                logger.info("Learn more url count for each url in main url = %d" % i)

                xpath = '//*[@id="c15413"]/div/section/div[4]/section[' + str(i) + ']/a'

                # print("XPATH = ", xpath)

                link = driver.find_element_by_xpath(xpath)

                time.sleep(10)

                first_learn_more_click = link.click()

                # WebDriverWait(driver, 5)

                first_page_soup = BeautifulSoup(driver.page_source, 'html.parser')

                course_name = first_page_soup.find('h1').text

                print('Course Name = ', course_name)

                # OVERVIEW SECTION START

                overview = OrderedDict()

                overview['course_name'] = course_name

                for ul_tag in first_page_soup.find_all('ul', {'class': 'info list-inline'}):

                    for li_tag in ul_tag.find_all('li'):
                        field = li_tag.find('span', {'class': 'title'}).text
                        value = li_tag.find('span', {'class': 'status'}).text.strip()

                        overview[field] = value

                # Store the overview results immediately
                results['overview_info'] = overview

                # with open("overview.json", "w") as f:
                #     json.dump(overview, f, ensure_ascii=False, indent=4)

                # OVERVIEW SECTION END

                # FIELD OF STUDY SECTION START

                field_of_study = OrderedDict()

                for fos in first_page_soup.find_all('li', {'id': 'acc-sgbez'}):

                    for ul_tag in fos.find_all('ul', {'class': 'info'}):

                        for li_tag in ul_tag.find_all('li'):

                            field = li_tag.find('span', {'class': 'title'})
                            value = li_tag.find('span', {'class': 'status'})

                            if field and value is not None:
                                fl_text = field.text
                                val_text = value.text.strip()

                                field_of_study[fl_text] = [val_text]

                results['field_of_study_info'] = field_of_study

                # FIELD OF STUDY SECTION END

                # ADMISSION REQUIREMENTS SECTION START

                admission_requirements = OrderedDict()

                language_req = []

                for admission_reqs in first_page_soup.find_all('li', {'id': 'acc-zulassungsvoraussetzungen'}):

                    for ul_tag in admission_reqs.find_all('ul', {'class': 'info'}):

                        for li_tag in ul_tag.find_all('li'):

                            if li_tag.string is not None:
                                language_req.append(li_tag.string)

                            admission_requirements['language_requirements'] = language_req

                            field = li_tag.find('span', {'class': 'title'})
                            value = li_tag.find('span', {'class': 'status'})

                            if field and value is not None:
                                fl_text = field.text
                                val_text = value.text.strip()

                                admission_requirements[fl_text] = val_text

                results['admission_reqs_info'] = admission_requirements

                # ADMISSION REQUIREMENTS SECTION END

                # DEADLINES SECTION START

                dates_and_deadlines = OrderedDict()

                for deadlines in first_page_soup.find_all('li', {'id': 'acc-fristen_termine'}):

                    for ul_tag in deadlines.find_all('ul', {'class': 'info'}):

                        for li_tag in ul_tag.find_all('li'):

                            field = li_tag.find('span', {'class': 'title'})
                            value = li_tag.find('span', {'class': 'status'})

                            if field and value is not None:
                                fl_text = field.text
                                val_text = value.text.strip()

                                dates_and_deadlines[fl_text] = val_text

                results['deadlines_info'] = dates_and_deadlines

                # DEADLINES SECTION END

                # TUITION FEES SECTION START

                tuition_fees = OrderedDict()

                fees_links = []

                fees_text = []

                for fees in first_page_soup.find_all('li', {'id': 'acc-studienbeitrag'}):

                    for ul_tag in fees.find_all('ul', {'class': 'info'}):

                        for li_tag in ul_tag.find_all('li'):

                            field = li_tag.find('span', {'class': 'title'})
                            value = li_tag.find('span', {'class': 'status'})

                            if field and value is not None:
                                fl_text = field.text

                                # Tuition fees sometime contains links and sometime fee is given in text so split it into fee_text and
                                #
                                # fee_links

                                if fl_text == "Tuition fee":
                                    fee_text = value.text.strip()
                                    fees_text.append(fee_text)

                                    tuition_fees['fee_text'] = fees_text

                                    val_links = li_tag.find_all('a')
                                    for links in val_links:
                                        fees_links.append(links['href'])
                                        tuition_fees['fee_links'] = fees_links
                                else:

                                    val_text = value.text.strip()
                                    tuition_fees[fl_text] = val_text

                results['tuition_fees_info'] = tuition_fees

                # TUITION FEES SECTION END

                # CONTACT DETAILS SECTION START

                contact_details = OrderedDict()

                for contact in first_page_soup.find_all('li', {'id': 'acc-kontakte_ansprechpartner'}):

                    for ul_tag in contact.find_all('ul', {'class': 'info'}):

                        sub_heading = ""

                        for li_tag in ul_tag.find_all('li'):

                            field_sub_heading = li_tag.find('span', {'class': 'title sub-heading'})

                            if field_sub_heading is not None:
                                # print("SUB HEADING TEXT = ", field_sub_heading.text.lstrip())
                                sub_heading = field_sub_heading.text.lstrip()
                                contact_details[sub_heading] = {}

                            field = li_tag.find('span', {'class': 'title'})
                            value = li_tag.find('span', {'class': 'status'})

                            if field and value is not None:

                                fl_text = field.text
                                val_text = value.text.strip()

                                contact_details[sub_heading][fl_text] = val_text

                            # if field is None:
                            #     fl_text = "href"
                            #     href = li_tag.find('a')
                            #     # print("FLTEXT = ", fl_text.lstrip())
                            #
                            #     if href is not None:
                            #         contact_details[sub_heading]["website"] = href['href']
                                    # print(href['href'])
                                    # print(href['title'])

                                # print("FL TEXT = ", fl_text)
                                # print("VAL TEXT = ", val_text)
                                # contact_details[field_sub_heading.text][fl_text] = val_text

                results['contact_info'] = contact_details

                # CONTACT DETAILS SECTION END

                # print("RESULTS = ", results)

                key_main_dict = "main_url_" + str(main_url_count) + "_UNIVERSITY_" + str(counter)

                # the information collected in the results dict is fed into the main dict
                # which is then written to the csv file

                main_dict[key_main_dict] = results

                driver.back()

                WebDriverWait(driver, 3)

            except Exception as e:
                # YOU MAY GET StaleElementReferenceException
                logger.error(e)

        utc_date_time = datetime.datetime.utcnow()

        utc_date_time.strftime("%Y-%m-%d %H:%M:%S")

        file_name = config('DATA_PATH')+"complete_info_main_url_with_time_stamp" + str(utc_date_time) + ".json"

        with open(file_name, "w") as f:
            json.dump(main_dict, f, ensure_ascii=False, indent=4)

        if counter == 100:

            df['URL'][j] = url

            df['STATUS'][j] = 1

            df['TIMESTAMP'][j] = utc_date_time

            df['FILENAME'][j] = file_name

            df.to_csv(main_urls_file, mode='w', index=False)
        else:
            df['URL'][j] = url

            df['STATUS'][j] = 2

            df['TIMESTAMP'][j] = utc_date_time

            df['FILENAME'][j] = file_name

            df.to_csv(main_urls_file, mode='w', index=False)

            logger.error("Scrapping failed for the url %s" % url)
            logger.error("Only partial information wrote to the json file")
            logger.error("Restart the script")

    else:
        logger.info("Information already scrapped for the url")
        logger.info(url)
        logger.info(status)

    driver.quit()

end_time = time.time()

logger.info("================== Execution Time =======================")
logger.info("Total time = %f seconds" % (end_time-start_time))
logger.info("=========================================================")


