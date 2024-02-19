import csv
import json
import os
import random
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, wait
import multiprocessing as mp
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException,
                                        TimeoutException)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm

#Idea generale
# 1) Carico un CSV contenente nomenewsgroup,annopartenza
# 2) Per ogni anno, comincio lo scraping dal 01-01-anno al 31-12-anno
# 3) Salvo il file con i link in nomenewsgroup/lista_anno.csv






def click_next_page(driver, f):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    pagina_iniziale = driver.pagina
    
    try:
        # Wait for the next button to be clickable
        next_button = driver.find_element(By.XPATH, '//div[@role="button" and @aria-label="Next page"]')
        driver.execute_script("arguments[0].scrollIntoView();", next_button)
        driver.execute_script("arguments[0].click();", next_button)
        # Wait for the page to load
        if "--verbose" in sys.argv:
            print("Cliccato su prossima pagina")
        loaded= False
        while not loaded:
            time.sleep(random.uniform(0, 0.5))
            loaded = driver.execute_script("return document.readyState == 'complete'")
        driver.pagina += 1  # Increment page counter here
        
    except (TimeoutException, StaleElementReferenceException):
        if "--verbose" in sys.argv:
            print("C'è stato un problema nel caricare la prossima pagina")
        # Check if page changed
        if driver.pagina== pagina_iniziale:
            if "--verbose" in sys.argv:
                print("Non è cambiata la pagina, riprovo")
            click_next_page(driver, f)
        pass




def scrape_month(group,year,month,f, driver):
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
    url = f"{base_url}{group}/search?q=after%3A{year}-{month_string}-01%20before%3A{next_year}-{next_month_string}-01"

    driver.get(url)
    time.sleep(1)


    total_links = set()
    skip_to_nextpage = False
    while flag==0:
        time.sleep(random.uniform(0, 0.5))
        
        # Se c'è scritto "Content unavailable" nella pagina, dà errore
        if "Content unavailable" in driver.page_source:
            
            print(f"\nContent unavailable - skipping group {group}")
            driver.quit()
            raise ValueError(f"Content unavailable - Skipping group {group}")
        
        try:
            # Find all links containing '/g/it.discussioni.auto/c' in href attribute
            links = driver.find_elements(By.XPATH, f'//a[contains(@href, "/g/{group}/c")]')
            # Deduplicate results
            unique_links = set(link.get_attribute('href') for link in links)
            if "--verbose" in sys.argv:
                print(f"Pagina {driver.pagina} trovati {len(unique_links)} link")

            if driver.pagina==0:
                unique_first_links=unique_links
                
                # Salvo i link

            if driver.pagina>=1:
                # compare overlap between the new links and the ones in the first page
                overlap = unique_links.intersection(unique_first_links)                
                # flag=1 if the overlap is more than half the links in the page + 1
                if len(overlap) > (len(unique_links) / 2 + 1):
                    if "--verbose" in sys.argv:
                        print("Più della metà dei link sono ripetuti, passiamo al mese successivo")
                    flag = 1
            # Skippo la pagina se vuota
            if len(unique_links) == 0:
                if "--verbose" in sys.argv:
                    print("Pagina vuota, passo al mese successivo")
                flag = 1     
            
            # Se la pagina ha meno di 4 link, passo alla prossima
            if len(unique_links) < 4:
                if "--verbose" in sys.argv:
                    print("Pagina con meno di 4 link, passo al mese successivo")
                flag = 1

            skip_to_nextpage= True

    
        except StaleElementReferenceException:
            if "--verbose" in sys.argv:
                print("StaleElementReferenceException")
            # Check if page is loading
            skip_to_nextpage= False

            if driver.execute_script("return document.readyState") != "complete":
                wait = WebDriverWait(driver, 2)  # Wait for page to load
                wait.until(EC.presence_of_element_located((By.ID, "some_element_id")))
            else:
                # Page is loaded, continue with the rest of the code
                continue
        finally:
            # add the links to the set and click next page if done with the current one
            if skip_to_nextpage:
                total_links.update(unique_links)
                click_next_page(driver, f)
        
        
    if flag==1:
        if "--verbose" in sys.argv:
            print("Salvo i link e passo al mese successivo")
        for link in total_links:
                f.write(f"{link},{year},{month}\n")
        if "--verbose" in sys.argv:
            print(f"Salvato n link: {len(total_links)}")
            print(f"Finito con il mese {year}-{month}")
    
        






    

def scrape_year(group, year, f, driver):
    #Nuovo approccio: provo mese per mese
    for month in tqdm(range(1, 13), desc=f"Scraping {group} in {year}", position=(mp.current_process().pid)*2):
        scrape_month(group, year, month, f, driver)


# Usage example:
# Call the scrape_links function with the newsgroup and year
# scrape_links("your_newsgroup_here", your_year_here)



def scrape_group(group):
    # Prepare the Firefox browser
    options = webdriver.FirefoxOptions()
    
    # make it headless if not specified
    if not "--not-headless" in sys.argv:
        options.add_argument("-headless") 
    
    #options.add_argument("-profile") # non so a cosa serva
    driver = webdriver.Firefox(options=options)
    
    if "--verbose" in sys.argv:
        print(f"Scraping {group}")
        
    # give error if the file already exists
    if os.path.exists(f"results/lista_link_{group}.csv"):
        print(f"\n File results/lista_link_{group}.csv already exists. Skipping {group}")
        raise ValueError(f"File results/lista_link_{group}.csv already exists. Skipping {group}")        
    # Open a new file to write the links
    f = open(f"results/lista_link_{group}.csv", "w")
    f.write("link,anno,mese\n")
            # Extract newsgroup and year from the link
            # Scrape the group between 1995 and 2024
    for year in tqdm(range(1991, 2024), desc=f"Scraping {group} between 1991 and 2024", position=(mp.current_process().pid)*2-1):
        if "--verbose" in sys.argv:
            print(f"Scraping {group} in {year}")
        scrape_year(group, year, f, driver)
    if "--verbose" in sys.argv:
        print(f"Finished scraping {group}")
    f.close()
    driver.quit()

# main 
if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise ValueError("Please provide the filepath of the file feed as a command line argument.")
    
    feed_filepath = sys.argv[1]
    
    # check if the results folder exists
    if not os.path.exists("results"):
        os.makedirs("results")

    groups = []
    with open(feed_filepath, "r") as feed_file:
        for line in feed_file:
            group = line.strip()
            groups.append(group)
            
        with mp.Pool() as pool:
            print("Inizio scraping")
            pool.map(scrape_group, groups)
                
          
            
            

    print("Scraping terminato. Chiudo il browser")
    
    
