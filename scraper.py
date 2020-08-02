from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


PATH = '/usr/local/bin/chromedriver'

with open('500ecomm.txt') as file:
    for line in file.readlines():

        # Open webdriver and with it the website
        driver = webdriver.Chrome(PATH)
        driver.get(line)
        

        try:
            # Wait until body is loaded
            body = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'body'))
            )
            # wait for pup-ups to load
            driver.implicitly_wait(3)
            # find all textboxes in the page
            emails = body.find_elements_by_xpath("//input[@type='text' or @type='email']")
            for email in emails:
                # find the most immediate div ancestor of textbox
                ancestor = email.find_element_by_xpath("./ancestor::div[1]")
                # check whether the source code has 'email'
                inner = ancestor.get_attribute("innerHTML")
                if 'email' in inner or 'Email' in inner:
                    try:
                        # submit the email id to the field
                        email.click()
                        email.send_keys('synctestinternalgrr1@yahoo.com', Keys.RETURN)
                        email.submit()
                    except:
                        continue
                
        except Exception as e: 
            print(e)
        
        # This following block confirms from the user if the script was able to subscribe. If yes then add the site to the list
        print('Enter: ')
        ans = input()
        if ans == 'y':
            print("appending to file")
            with open('ecomm_sub.txt', 'a') as ecomm:
                ecomm.write("\n")
                ecomm.write(line)
        driver.quit()

        # Use this method to eliminate any user interference, but accuracy drops by 25%
        # inner_body = body.get_attribute('innerHTML')
        # if 'Thanks' in inner or 'Thank you' in inner or 'subscribed' in inner or 'successfully' in inner:
        #    with open('ecomm_sub.txt', 'a') as ecomm:
        #        ecomm.write("\n")
        #        ecomm.write(line) 


    