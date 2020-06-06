from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import json
import os
from bs4 import BeautifulSoup
import re
import time
import configparser


# These texts depend of facebook language.
# These are for Portuguese. Change that for the language you're using
TXT_COMMENT = "comentário"
TXT_COMMENT_LIST = ["Comentário", "Resposta ao comentário"]
TXT_SEE_PREVIOUS_COMMENTS = "Ver comentários anteriores"


browser = None
loggedIn = False

REACTION_LIKE_TAG = {
    "sx_0b1925": "Like",
    "sx_54deb1": "Love",
    "sx_3aa2da": "Hug",
    "sx_64365a": "Haha",
    "sx_786626": "Wow",
    "sx_f08bd7": "Sad",
    "sx_49c2cb": "Grr",
}

posts_data = {}

def login():
    global loggedIn
    global browser

    if loggedIn:
        return

    if browser is None:
        browser = webdriver.Firefox()

    print ("Logging in to Facebook...")

    cookieFile = os.path.join(os.path.dirname(__file__), "cookies.json")

    try:
        browser.get('https://www.facebook.com/')#find the username field and enter the email example@yahoo.com.
    except:
        return
    username = browser.find_elements_by_css_selector("input[name=email]")
    username[0].send_keys(USER_NAME)#find the password field and enter the password password.
    password = browser.find_elements_by_css_selector("input[name=pass]")
    password[0].send_keys(PASSWORD)#find the login button and click it.
    loginButton = browser.find_elements_by_css_selector("input[type=submit]")
    loginButton[0].click()

    cookies = browser.get_cookies()

    loggedIn = True

    with open (cookieFile, "w") as f:
        s = json.dumps(cookies, indent=4, sort_keys=True)
        f.write(s)

    print ("Done logging in!")

def load_group_page():
    page = 'download/group_page.html'
    if not os.path.isfile(page):
        login()
        print("Downloading group page")
        try:
            browser.get('https://www.facebook.com/groups/%s/'% GROUP_ID)
        except:
            return ""

        # Roll the page a few times to download more posts
        html = browser.find_element_by_tag_name('html')
        rollCount = NUMBER_PAGE_ROLL_DOWNS
        for i in range(rollCount):
            print ("Rolling page %d of %d..." %  (i+1, rollCount))
            html.send_keys(Keys.END)
            time.sleep(WAIT_FOR_PAGE_UPDATE_AFTER_ROLL_DOWN)

        with open(page, 'wb') as f:
            f.write(browser.page_source.encode("utf-8"))
            f.close()

    with open(page, encoding='utf8') as f:
        html = BeautifulSoup(f, "html.parser")

    return html


def get_list_of_posts():
    posts_file = "data/posts.txt"
    if not os.path.isfile(posts_file):
        post_link = "https://www.facebook.com/groups/%s/permalink/" % (GROUP_ID)
        html = str(load_group_page())
        links = []

        for match in re.finditer(post_link, html):
            end = html[match.end():].index('/')
            link = html[match.end():match.end() + end]
            if link not in links:
                links.append(link)

        with open(posts_file, "w") as f:
            for link in links:
                f.write("%s\n" % link)
    else:
        with open(posts_file) as f:
            links = f.readlines()
            links = [l.strip() for l in links if l.strip() != ""]

    print ("%d posts found" % len(links))
    return links

def download_post(post, idx, num_posts, force_click_comments=False):
    page = 'download/post_%s.html' % post
    post_link = "https://www.facebook.com/groups/%s/permalink/%s/" % (GROUP_ID, post)
    if not os.path.isfile(page) or force_click_comments:
        login()
        print("Downloading post %d/%d:%s" % (idx + 1, num_posts, post))
        try:
            browser.get(post_link)
        except:
            return

        all_expanded = False
        while not all_expanded:
            try:
                links = browser.find_elements_by_partial_link_text(TXT_SEE_PREVIOUS_COMMENTS)
                if len(links) > 0:
                    print("\tExpanding comments. May repeat if too much comments")
            except:
                links = []
            if len(links) > 0:
                for link in links:
                    try:
                        #browser.execute_script("arguments[0].scrollIntoView(true);", link)
                        #time.sleep(WAIT_FOR_PAGE_UPDATE_AFTER_CLICK_VER_MAIS)
                        try:
                            link.click()
                        except:
                            #print("click")
                            try:
                                browser.execute_script("arguments[0].scrollIntoView(true);", link)
                                time.sleep(WAIT_FOR_PAGE_UPDATE_AFTER_CLICK_VER_MAIS)
                                link.click()
                            except:
                                pass
                    except:
                        pass # print("Error click")
            else:
                all_expanded = True

        time.sleep(2)

        if force_click_comments:
            try:
                links = browser.find_elements_by_partial_link_text(TXT_COMMENT)
                print("\tForcefully expanding %d 'coments' links..." % (len(links)))
            except:
                links = []
            for link in links:
                try:
                    link.click()
                except:
                    try:
                        browser.execute_script("arguments[0].scrollIntoView(true);", link)
                        time.sleep(WAIT_FOR_PAGE_UPDATE_AFTER_CLICK_VER_MAIS)
                        link.click()
                    except:
                        pass
                time.sleep(WAIT_FOR_PAGE_UPDATE_AFTER_CLICK_VER_MAIS)


        try:
            links = browser.find_elements_by_partial_link_text("Ver mais")
            print("\tExpanding %d 'See more' links..." % (len(links)))
        except:
            links = []
        for link in links:
            try:
                #browser.execute_script("arguments[0].scrollIntoView(true);", link)
                #time.sleep(WAIT_FOR_PAGE_UPDATE_AFTER_CLICK_VER_MAIS)
                try:
                    link.click()
                except:
                    try:
                        browser.execute_script("arguments[0].scrollIntoView(true);", link)
                        time.sleep(WAIT_FOR_PAGE_UPDATE_AFTER_CLICK_VER_MAIS)
                        link.click()
                    except:
                        pass
                time.sleep(WAIT_FOR_PAGE_UPDATE_AFTER_CLICK_VER_MAIS)
            except:
                print("\t\tError click")
        with open(page, 'wb') as f:
            f.write(browser.page_source.encode("utf-8"))
            f.close()

    with open(page, encoding='utf8') as f:
        html = BeautifulSoup(f, "html.parser")

    return html

def decode_url_reaction(post, url_reaction):
    folder = "download/%s" % (post)
    os.makedirs(folder, exist_ok=True)
    page=url_reaction[:url_reaction.rfind("&")]
    page=page[page.index("=")+1:]
    page = "%s/%s.html" % (folder, page)

    reactions = {}
    if os.path.isfile(page):
        with open(page, encoding='utf8') as f:
            html = BeautifulSoup(f, "html.parser")
    else:
        login()
        print(" (Downloading reactions...)", end='')
        try:
            browser.get("https://www.facebook.com%s" % (url_reaction))
        except:
            return reactions
        with open(page, 'wb') as f:
            f.write(browser.page_source.encode("utf-8"))
            f.close()
        html = BeautifulSoup(browser.page_source.encode("utf-8"), "html.parser")

    for reaction_div in html.findAll("div", {"class": "_2ar2"}):
        react_person = reaction_div.find("img")['aria-label']
        tags = reaction_div.findAll("i", {"data-testid":"ufiReactionsIconsTestId"})[0]["class"]
        reaction_tag = tags[-1] # The last one
        try:
            reaction = REACTION_LIKE_TAG[reaction_tag]
        except:
            print ("Unkown reaction tag in", url_reaction, end='')
            reaction = reaction_tag

        reactions[react_person] = reaction

    return reactions

def decode_post(html, post, idx, num_posts):
    global posts_data

    print("Decoding post %d/%d:%s" % (idx + 1, num_posts, post))
    try:
        if "header" in posts_data[post]:
            if "body" in posts_data[post]["header"]:
                print ("Skipping. Already parsed!")
                return
    except:
        pass # post not present in the file. Need to be processed anyway

    if not post in posts_data:
        posts_data[post] = {"log":[], "header": {}}
    if not "header" in posts_data[post]:
        posts_data[post]["header"] = {}

    posts_data[post]["header"]["post_image_alt"] = []

    try:
        post_header_div = html.find("div", {"class":"_6a _5u5j _6b"})
    except:
        post_header_div = None
    if post_header_div:
        try:
            a = post_header_div.find("a")
            posts_data[post]["header"]["author"] = a.text
            date = post_header_div.find("abbr", {"class":"_5ptz"})
            posts_data[post]["header"]["utime"] = date['data-utime']
            posts_data[post]["header"]["date_str"] = date.text
        except:
            pass
    try:
        post_text_div = html.find("div", {"id":"js_8"})
        posts_data[post]["header"]["text"] = post_text_div.text
    except:
        pass

    try:
        text = html.find("div", {"data-testid":"post_message"}).text
        print (text[:78])
        post_body = [text]
    except:
        print ("< UNDETECTED BODY TEXT >")
        post_body = []

    # Post contain text. Lets see if there are images too
    try:
        mtm = html.find("div", {"class":"mtm"})
        body_images = mtm.findAll("img")
    except:
        body_images = []
    for img in body_images:
        try:
            post_body.append(img["src"])
            try:
                img_alt = img['alt']
            except:
                img_alt = None
            posts_data[post]["header"]["post_image_alt"].append(img_alt)
            print ("< FOUND BODY IMAGE >")
        except:
            pass

    posts_data[post]["header"]["body"] = post_body

    if not "comments" in posts_data[post]:
        posts_data[post]["comments"] = []
        try:
            comments_divs = html.findAll("div", {"aria-label": TXT_COMMENT_LIST} )
        except:
            comments_divs = []

        if len(comments_divs) == 0:
            print ("No comments found. Re-downloading the post with forcefull comment expanding...")
            html = download_post(post, idx, num_posts, force_click_comments=True)
            try:
                comments_divs = html.findAll("div", {"aria-label": TXT_COMMENT_LIST} )
            except:
                comments_divs = []

        #comments_divs = [] # temporario
        total_comments = len(comments_divs)
        print("\tDownloading and analyzing %d comments" % (total_comments))

        for idx, comment_div in enumerate(comments_divs):
            commend_div_str = str(comment_div)

            img_alt = None
            commenter = comment_div.find("img", alt=True)['alt']

            #strip comment text
            comment = []
            try:
                comment_text = comment_div.findAll("span", {"class": "_3l3x"})[0].text
                partial_comment = comment_text[:17]
                comment.append(comment_text)
            except:
                comment_text = ""
                partial_comment = ""
                comment.append(comment_text)
                pass

            try:
                # check if comment also has image
                # if more than one image is found, the comment image shall be
                # the last one (The first is the commenter profile pic,
                # the second (if exist) may be the commenter shield (admin,
                # new member 'hand' icon, etc)
                comment_imgs = comment_div.findAll("img", alt=True)
                if len(comment_imgs) > 1:
                    comment_img = comment_imgs[-1]['src']
                    comment.append(comment_img)
                    img_alt = comment_imgs[-1]['alt']
                    if comment_text == "":
                        partial_comment = "<IMG>"
                    else:
                        partial_comment += " + <IMG>"
                else:
                    partial_comment += " <PURE TEXT>"
            except:
                pass

            if len(comment) == 0:
                log = "Comment %d not detected - all empty" % (idx)
                posts_data[post]["log"].append(log)
                continue

            if (len(comment) == 1) and (comment[0] == ""):
                # nao detectou comentario
                log = "Comment %d not detected - text empty" % (idx)
                posts_data[post]["log"].append(log)
                continue

            print ("\t%d/%d %s: %s" % (idx+1, total_comments, commenter, partial_comment),end='')

            try:
                pos = commend_div_str.index('"/ufi/reaction/profile/browser/?ft_ent_identifier=')
            except:
                print (" (No likes)")
                pos = -1

            if pos >= 0:
                url_reaction = commend_div_str[pos + 1:]
                try:
                    pos = url_reaction.index('" ')
                    url_reaction = url_reaction[:pos]
                    reactions = decode_url_reaction(post, url_reaction)
                    print("")
                except:
                    print (" (Not found end of reaction URL)")
                    pos = -1

            if pos < 0:
                reactions = {}

            posts_data[post]["comments"].append({
                "commenter": commenter,
                "comment": comment,
                "img_alt": img_alt,
                "reactions": reactions
            })
    else: # if not ccomments in posts_data
        print ("\tData file already contains this post comments. Skipping parsing...")

def download_all_posts():
    global posts_data

    data_file = "data/extracted_data.json"
    if os.path.isfile(data_file):
        with open(data_file, "r") as f:
            posts_data = json.load(f)

    # if post is present in this file it will be deleted from
    # data_file to force being processed again
    again_file = "data/process_again.txt"
    if os.path.isfile(again_file):
        with open(again_file) as f:
            reprocess = f.readlines()
            reprocess = [l.strip() for l in reprocess if l.strip() != ""]
    else:
        reprocess = []

    key_list = list( posts_data.keys() )
    for post in key_list:
        if post in reprocess:
            print ("Deleting to reprocess: %s" % post)
            del (posts_data[post])

    if len(reprocess) == 0:
        posts = get_list_of_posts()
    else:
        posts = reprocess

    for idx, post in enumerate(posts):
            html = download_post(post, idx, len(posts))
            decode_post(html, post, idx, len(posts))

            #update data file after each post to prevent data los
            with open (data_file, "w") as f:
                s = json.dumps(posts_data, indent=4, sort_keys=True)
                f.write(s)

#-------------------------------------------------------------------------------

config = configparser.ConfigParser()
config.read('config.ini')
try:
    USER_NAME = config['authentication']['username']
except:
    print ("Error: Entry 'username' not found in config.ini")

try:
    PASSWORD = config['authentication']['password']
except:
    print ("Error: Entry 'password' not found in config.ini")

try:
    GROUP_ID = config['authentication']['group_id']
except:
    print ("Error: Entry 'group_id' not found in config.ini")


try:
    NUMBER_PAGE_ROLL_DOWNS = config['limits']['NUMBER_PAGE_ROLL_DOWNS']
except:
    NUMBER_PAGE_ROLL_DOWNS = 1

try:
    WAIT_FOR_PAGE_UPDATE_AFTER_ROLL_DOWN = config['limits']['WAIT_FOR_PAGE_UPDATE_AFTER_ROLL_DOWN']
except:
    WAIT_FOR_PAGE_UPDATE_AFTER_ROLL_DOWN = 5

try:
    WAIT_FOR_PAGE_UPDATE_AFTER_CLICK_VER_MAIS = config['limits']['WAIT_FOR_PAGE_UPDATE_AFTER_CLICK_VER_MAIS']
except:
    WAIT_FOR_PAGE_UPDATE_AFTER_CLICK_VER_MAIS = 0.5


os.makedirs("download", exist_ok=True)
os.makedirs("data", exist_ok=True)
download_all_posts()

