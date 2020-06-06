# facebook_group_scrapper
A python script to download all posts, comments, reactions and images from a Facebook group

##How to use
Follow these steps
1. Rename the file 'config.default.ini' to 'config.ini'
1. Edit this file to include your Facebook username and password
1. Also set in this file the GROUP_ID of the group you want to download. It's just the number 'XXXXX' in https://www.facebook.com/groups/XXXXX/
1. Execute the script 'download_facebook_group_data.py'
1. Be patient. Depending on the number of posts to download it may take days to finish
1. Extracted data will be placed at 'data/extracted_data.json'
1. The 'download' folder is temporary. You can delete it after the scrapping job finishes

##Dependencies
This script requires:
*. Python 3.8
*. [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/#installing-beautiful-soup)
*. [Selenium](https://selenium-python.readthedocs.io/installation.html)

