import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time, random
from bs4 import BeautifulSoup
import csv
import re
import os
from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
import json
import csv

#Idea generale
# 1) Carico un CSV contenente nomenewsgroup,annopartenza
# 2) Per ogni anno, comincio lo scraping dal 01-01-anno al 31-12-anno
# 3) Salvo il file con i link in nomenewsgroup/lista_anno.csv



from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium import webdriver
import sys





def click_next_page(driver, f):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    try:
        # Wait for the next button to be clickable
        next_button = driver.find_element(By.XPATH, '//div[@role="button" and @aria-label="Next page"]')
        driver.execute_script("arguments[0].scrollIntoView();", next_button)
        driver.execute_script("arguments[0].click();", next_button)
        driver.pagina += 1  # Increment page counter here
    except (TimeoutException, StaleElementReferenceException):
        print("C'è stato un problema nel caricare la prossima pagina")
        pass
    is_loading = driver.execute_script("return document.readyState != 'complete'")
    while is_loading:
        # Wait for a short interval between 0 and 1 seconds
        time.sleep(random.uniform(0, 1))
        is_loading = driver.execute_script("return document.readyState != 'complete'")



def scrape_month(newsgroup,year,month,f, driver):
   #inizializzo i contatori
    driver.pagina = 0
    flag = 0
    base_url = "https://groups.google.com/g/"
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    # Verifica se i mesi necessitano dello zero iniziale
    month_string = str(month) if month >= 10 else f"0{month}"
    next_month_string = str(next_month) if next_month >= 10 else f"0{next_month}"

    # Formatta l'URL utilizzando le variabili appena calcolate
    url = f"{base_url}{newsgroup}/search?q=after%3A{year}-{month_string}-01%20before%3A{next_year}-{next_month_string}-01"

    driver.get(url)
    time.sleep(1)

    #Salvo la data e il titolo  del primo messaggio, in modo da evitare un loop infinito se Google Groups decide di ritornare a mostrare da capo i messaggi
    #<div class="tRlaM">28/02/1998</div> contiene la data
    #t17a0d contiene il titolo
    #QUESTO METODO NON HA FUNZIONATO
   # try:
        # Find the div with class UGgcDd
        #div_element = driver.find_element(By.CLASS_NAME, "ReSblb")

        # Find the first element with class "tRlaM" inside the div
        #first_tRlaM_element = div_element.find_elements(By.CLASS_NAME, "kOkyJc")[0]
        #data_primo_messaggio_text = first_tRlaM_element.text

        # Find the first element with class "t17a0d" inside the div
        #first_t17a0d_element = div_element.find_elements(By.CLASS_NAME, "o1DPKc")[0]
        #testo_primo_messaggio_text = first_t17a0d_element.text
        
        # Find the first element with class "ZLl54" inside the div
        #first_a_element = div_element.find_elements(By.CLASS_NAME, "ZLl54")[0]

        # Get the href attribute of the a element
        #href_primo_messaggio = first_a_element.get_attribute("href")
        
        #print(f"primo: {href_primo_messaggio},{data_primo_messaggio_text}")
    #except (NoSuchElementException, IndexError):
        # Handle cases where the div or elements are not found
        #pass
    #ALTRO METODO: SALVO I LINK DELLA PRIMA PAGINA E VERIFICO CHE NON SI RIPETANO. MENO AFFIDABILE

    while flag == 0:
        # Primo test: risultati di ricerca finiti
        try:
            isittheend_element = driver.find_element(By.CLASS_NAME, "ReSblb")
            isittheend_text = isittheend_element.text
            if isittheend_text == "Try another search":
                # this is the end, my only friend
                flag = 1
        except NoSuchElementException:
            # Element not found, continue with the rest of the code
            pass

        #Secondo test: siamo a una pagina diversa da 0 ma ricompaiono i messaggi che erano a pagina 0
       # try:
            # Find the div with class UGgcDd
            #div_element = driver.find_element(By.CLASS_NAME, "ReSblb")

            # Find the first element with class "tRlaM" inside the div
           # first_tRlaM_element = div_element.find_elements(By.CLASS_NAME, "kOkyJc")[0]
           # data_messaggio_text = first_tRlaM_element.text

            # Find the first element with class "t17a0d" inside the div
            #first_t17a0d_element = div_element.find_elements(By.CLASS_NAME, "o1DPKc")[0]
            #testo_messaggio_text = first_t17a0d_element.text
            # Find the first element with class "ZLl54" inside the div
           # first_a_element = div_element.find_elements(By.CLASS_NAME, "ZLl54")[0]

            # Get the href attribute of the a element
            #href_messaggio = first_a_element.get_attribute("href")
           # print(f"ulteriore: {href_messaggio},{data_messaggio_text}")

       # except (NoSuchElementException, IndexError):
            # Handle cases where the div or elements are not found
           # pass

        #if pagina>0 and data_messaggio_text==data_primo_messaggio_text and href_messaggio==href_primo_messaggio:
           # print(f"Messaggio {href_primo_messaggio} del {data_primo_messaggio_text} già apparsa; esco dal ciclo")
           # flag=1
           # break

        # Attempt to fetch the links, retrying in case of StaleElementReferenceException
        while True:
            time.sleep(random.uniform(0, 0.5))
            try:
                # Find all links containing '/g/it.discussioni.auto/c' in href attribute
                links = driver.find_elements(By.XPATH, f'//a[contains(@href, "/g/{group}/c")]')
                # Deduplicate results
                unique_links = set(link.get_attribute('href') for link in links)
                if driver.pagina==0:
                    unique_first_links=unique_links
                    print("Ho memorizzato i primi link")
                    for link in unique_first_links:
                        print(link)
                    # Skippo la pagina se vuota
                    if len(unique_links) == 0:
                        flag = 1
                        print("Pagina vuota, passo al mese successivo")
                        break
                    # Salvo i link
                    for link in unique_links:
                        f.write(f"{link},{year},{month},{driver.pagina}\n")
                if driver.pagina>=1:
                    for link in unique_links:
                        if link in unique_first_links:
                            print(f"Link {link} già presente, esco dal ciclo")
                            flag = 1
                            break
                        else:
                            f.write(f"{link},{year},{month},{driver.pagina}\n")
                if flag==1:
                    print("Ho trovato un link già presente, passiamo al mese successivo")
                    break
                break
            except StaleElementReferenceException:
                # Check if page is loading
                if driver.execute_script("return document.readyState") != "complete":
                    wait = WebDriverWait(driver, 2)  # Wait for page to load
                    wait.until(EC.presence_of_element_located((By.ID, "some_element_id")))
                else:
                    # Page is loaded, continue with the rest of the code
                    continue
            
        


            
        click_next_page(driver, f)
            






    

def scrape_year(newsgroup, year, f, driver):
    #Nuovo approccio: provo mese per mese
    for month in range(1,13,1):
        scrape_month(newsgroup,year,month,f, driver)


# Usage example:
# Call the scrape_links function with the newsgroup and year
# scrape_links("your_newsgroup_here", your_year_here)


# main 
if __name__ == "__main__":
    if len(sys.argv) < 1:
        print("Please provide the filepath of the file feed as a command line argument.")
        sys.exit(1)
    
    feed_filepath = sys.argv[1]
    
    options = webdriver.FirefoxOptions()
    #options.add_argument("-profile") # non so a cosa serva
    driver = webdriver.Firefox(options=options)
    # open file
    
    
    with open(feed_filepath, "r") as feed_file:
        for line in feed_file:
            group = line.strip()
            f = open(f"lista_link_{group}.csv", "a")
            f.write("link,anno,mese,pagina\n")
            # Extract newsgroup and year from the link
            # Scrape the group between 1995 and 2024
            for year in range(1995, 2025):
                scrape_year(group, year, f, driver)
    
    f.close()
    driver.quit()
