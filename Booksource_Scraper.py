from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.select import Select
import pandas as pd
import time
import csv
import sys
import numpy as np
import re 

def initialize_bot():

    # Setting up chrome driver for the bot
    chrome_options  = webdriver.ChromeOptions()
    # suppressing output messages from the driver
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    # adding user agents
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chrome_options.add_argument("--incognito")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # running the driver with no browser window
    chrome_options.add_argument('--headless')
    # disabling images rendering 
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.page_load_strategy = 'eager'
    # installing the chrome driver
    driver_path = ChromeDriverManager().install()
    chrome_service = ChromeService(driver_path)
    # configuring the driver
    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    driver.set_page_load_timeout(60)
    driver.maximize_window()

    return driver

def scrape_booksource(path):

    start = time.time()
    print('-'*75)
    print('Scraping booksource.com ...')
    print('-'*75)
    # initialize the web driver
    driver = initialize_bot()

    # initializing the dataframe
    data = pd.DataFrame()

    # if no books links provided then get the links
    if path == '':
        name = 'booksource_data.xlsx'
        # getting the books under each category
        links = []
        nbooks = 0
        homepage = 'https://www.booksource.com/SearchResults.aspx'
        driver.get(homepage)

        # applying the search settings
        print("Applying search filter 'Interest Level/Grade' to 8 - Adult. ")
        divs = wait(driver, 2).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.search-filter__title")))
        for div in divs:
            if 'Interest Level/Grade' in div.get_attribute('textContent'):
                driver.execute_script("arguments[0].click();", div)
                time.sleep(1)
                break

        # Selecting grades from 8 to adult
        menu = wait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//select[@id='BodyContent_fvFilter_ddIntLevelLow']")))
        sel = Select(menu)
        options = wait(menu, 60).until(EC.presence_of_all_elements_located((By.TAG_NAME, "option")))
        for option in options:
            if option.get_attribute('textContent') == '8':
                sel.select_by_visible_text('8')  
                time.sleep(3)
                break        
            
        menu = wait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//select[@id='BodyContent_fvFilter_ddIntLevelHigh']")))
        sel = Select(menu)
        options = wait(menu, 60).until(EC.presence_of_all_elements_located((By.TAG_NAME, "option")))
        for option in options:
            if option.get_attribute('textContent') == 'Adult':
                sel.select_by_visible_text('Adult')  
                time.sleep(3)
                break
        
        # language settings
        print("Applying search filter 'Language' to English ")
        divs = wait(driver, 2).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.search-filter__title")))
        for div in divs:
            if 'Language' in div.get_attribute('textContent'):
                driver.execute_script("arguments[0].click();", div)
                time.sleep(1)
                break

        button = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//input[@id='BodyContent_fvFilter_ucLanguageSearchFilter_rblLanguage_1']")))
        driver.execute_script("arguments[0].click();", button)
        time.sleep(3)     
        print("Applying search filter 'Exclude Bilingual'")
        button = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//input[@id='BodyContent_fvFilter_ucLanguageSearchFilter_RBLBilingual_0']")))
        driver.execute_script("arguments[0].click();", button)
        time.sleep(3)
        print('-'*75)

        nres = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.actual-site"))).get_attribute('textContent').strip().split(' ')[-1]
        print(f'Total search results = {nres}')

        # selecting 50 results per page
        button = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//a[@id='BodyContent_ucPageSizer_myFV_repPageSizes_btnChangePageSize_2']")))
        driver.execute_script("arguments[0].click();", button)
        time.sleep(5)

        while True:          
            # scraping books urls
            titles = wait(driver, 2).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "td.image.first")))
            for title in titles:
                try:
                    nbooks += 1
                    print(f'Scraping the url for book {nbooks}')
                    a = wait(title, 2).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                    link = a.get_attribute('href')
                    links.append(link)
                except Exception as err:
                    print('The below error occurred during the scraping from  booksource.com, retrying ..')
                    print('-'*50)
                    print(err)
                    continue

            # checking the next page
            try:
                button = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//a[@id='BodyContent_ucPager_myFV_btnNextPage']")))
                driver.execute_script("arguments[0].click();", button)
                time.sleep(5)
            except:
                break
                    
        # saving the links to a csv file
        print('-'*75)
        print('Exporting links to a csv file ....')
        with open('booksource_links.csv', 'w', newline='\n', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Link'])
            for row in links:
                writer.writerow([row])

    scraped = []
    if path != '':
        df_links = pd.read_csv(path)
        name = path.split('\\')[-1][:-4]
        name = name + '_data.xlsx'
    else:
        df_links = pd.read_csv('booksource_links.csv')

    links = df_links['Link'].values.tolist()

    try:
        data = pd.read_excel(name)
        scraped = data['Title Link'].values.tolist()
    except:
        pass

    # scraping books details
    print('-'*75)
    print('Scraping Books Info...')
    print('-'*75)
    n = len(links)
    for i, link in enumerate(links):
        try:
            if link in scraped: continue
            driver.get(link)           
            details = {}
            print(f'Scraping the info for book {i+1}\{n}')

            # title and title link
            title_link, title = '', ''              
            try:
                title_link = link
                title = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//span[@id='MainContentHolder_lblTitle']"))).get_attribute('textContent').replace('\n', '').strip().title() 
            except:
                print(f'Warning: failed to scrape the title for book: {link}')               
                
            details['Title'] = title
            details['Title Link'] = title_link                          
            # Author 
            author = ''
            try:
                a = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//a[@id='MainContentHolder_lblauthor']")))
                author = a.get_attribute('textContent').replace('Author:', '').strip()
            except:
                pass
                    
            details['Author'] = author            
             
            # ISBN, ISBN13
            ISBN, ISBN13 = '', ''
            try:
                ISBN = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//span[@id='MainContentHolder_lblISBN']"))).get_attribute('textContent').replace('ISBN-10:', '').strip()
                ISBN13 = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//span[@id='MainContentHolder_lblISBN13']"))).get_attribute('textContent').replace('ISBN-13:', '').strip()
            except:
                pass          
                
            details['ISBN-10'] = ISBN          
            details['ISBN-13'] = ISBN13            
            
            # interest level
            int_lvl = ''
            try:
                int_lvl = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//span[@id='MainContentHolder_lblInterestTop']"))).get_attribute('textContent').replace('Interest Level:', '').strip()
            except:
                pass          
                
            details['Interest Level'] = int_lvl           
                               
            # publisher
            publisher = ''
            try:
                publisher = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//span[@id='MainContentHolder_lblPublisher']"))).get_attribute('textContent').replace('Publisher:', '').strip()
            except:
                pass          
                
            details['Publisher'] = publisher            
            
            # publication date
            date = ''
            try:
                date = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//span[@id='MainContentHolder_lblPubDate']"))).get_attribute('textContent').replace('Publication Date:', '').strip()
            except:
                pass          
                
            details['Publication Date'] = date           
           
            # copywrite
            copywrite = ''
            try:
                copywrite = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//span[@id='MainContentHolder_lblCopyrightDate']"))).get_attribute('textContent').replace('Copyright:', '').strip()
            except:
                pass          
                
            details['Copywrite'] = copywrite             
            
            # page count
            npages = ''
            try:
                npages = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//span[@id='MainContentHolder_lblPageCount']"))).get_attribute('textContent').replace('Page Count:', '').strip()
            except:
                pass          
                
            details['Page Count'] = npages             
            
            # format
            form = ''
            try:
                form = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//div[@id='ProductDetailBinding']"))).get_attribute('textContent').strip()
            except:
                pass          
                
            details['Format'] = form             
            
            # price
            price = ''
            try:
                price = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//span[@id='MainContentHolder_lblYourPriceTop']"))).get_attribute('textContent').replace('$', '').strip()
            except:
                pass          
                
            details['Price'] = price            
            
            # guided reading
            guided = ''
            try:
                guided = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//span[@id='MainContentHolder_LblLevelAZ']"))).get_attribute('textContent').replace('Guided Reading:', '').strip()
            except:
                pass          
                
            details['Guied Reading'] = guided             
            
            # lexile
            lexile = ''
            try:
                lexile = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//span[@id='MainContentHolder_lblLexile']"))).get_attribute('textContent').replace('Lexile:', '').strip()
            except:
                pass          
                
            details['Lexile'] = lexile            
            
            # Accelerated Reader Level
            acc_lvl = ''
            try:
                acc_lvl = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//span[@id='MainContentHolder_LblARlevel']"))).get_attribute('textContent').replace('Accelerated Reader Level:', '').strip()
            except:
                pass          
                
            details['Accelerated Reader Level'] = acc_lvl 
 
            # Accelerated Reader Points
            acc_points = ''
            try:
                acc_points = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//span[@id='MainContentHolder_LblArPoints']"))).get_attribute('textContent').replace('Accelerated Reader Points:', '').strip()
            except:
                pass          
                
            details['Accelerated Reader Points'] = acc_points            
            
            # genre
            genre = ''
            try:
                genre = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//div[@id='MainContentHolder_pnlGenre']"))).get_attribute('textContent').replace('Genre', '').replace('\n', '').replace('*', '').replace('/', ', ').replace(';', ', ').strip()
            except:
                try:
                    genre = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//div[@id='MainContentHolder_pnlBISAC']"))).get_attribute('textContent').replace('BISAC Subjects', '').replace('\n', '').replace('*', '').replace('/', ', ').replace(';', ', ').strip()  
                except:
                    pass
                
            details['Genres'] = genre 
                        
                           
            # appending the output to the datafame       
            data = data.append([details.copy()])
            # saving data to csv file each 100 links
            if np.mod(i+1, 100) == 0:
                print('Outputting scraped data ...')
                data.to_excel(name, index=False)
        except Exception as err:
            print(str(err))
           

    # optional output to excel
    data.to_excel(name, index=False)
    elapsed = round((time.time() - start)/60, 2)
    print('-'*75)
    print(f'booksource.com scraping process completed successfully! Elapsed time {elapsed} mins')
    print('-'*75)
    driver.quit()

    return data

if __name__ == "__main__":
    
    path = ''
    if len(sys.argv) == 2:
        path = sys.argv[1]
    data = scrape_booksource(path)

