# %%
# imports
import json
import re
import requests
import os
import time

from bs4 import BeautifulSoup
from rich import print

# %%
# parameters
# custom headers to mimic browser
headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:48.0) Gecko/20100101 Firefox/48.0",}

# search url, append with url_num to access a specific page of items
astro_ph_url_base = r"https://arxiv.org/search/advanced?advanced=&terms-0-operator=AND&terms-0-term=&terms-0-field=title&classification-physics=y&classification-physics_archives=astro-ph&classification-include_cross_list=include&date-year=&date-filter_by=date_range&date-from_date=2022-07&date-to_date=&date-date_type=submitted_date&abstracts=show&size=200&order=-announced_date_first&start="

# %%
# scrape the website for its articles and get a list with title and link
def recursive_page_scrape(base_url: str, url_num: int = 0, interval_timer: int = 10, do_outputs: bool = False,
                          articles_list: list = [], already_failed: bool = False, recursed: bool = False):
    # reset articles list at the start of the function
    if not recursed: articles_list = []

    # the program should always give an output, http responses fail sometimes
    try:
        # make initial request
        request = requests.get(astro_ph_url_base + str(url_num), headers=headers)

        # build base soup
        soup = BeautifulSoup(request.content, "html.parser")

        # get a list of the article results
        articles = soup.find_all("li", {"class": "arxiv-result"})

        # only parse articles if there are any otherwise return the full list
        if len(articles) <= 0: return articles_list

        # iterate over list of articles
        for article in articles:
            # get data from html tag
            title = article.find("p", {"class": "title"}).text.strip()
            pdf_link = [l["href"] for l in article.find_all("a") if "pdf" in l.text]

            # skip article if no pdf links are present
            if len(pdf_link) != 1: continue

            # extract single link and append results to list
            pdf_link = pdf_link[0]
            articles_list.append((title, pdf_link))

        # recurse and call back with incremented url_num
        if do_outputs: print(f"Page scraped from {url_num} to {url_num + len(articles)} results. Scraping resumes after {interval_timer} second sleep.")
        time.sleep(interval_timer)
        return recursive_page_scrape(base_url=base_url,
                                     url_num=url_num+len(articles),
                                     interval_timer=interval_timer,
                                     do_outputs=do_outputs,
                                     articles_list=articles_list,
                                     already_failed=already_failed,
                                     recursed=True)
    except Exception as e:
        # recall the code with a already_failed flag set to true, if it fails twice kill it
        if do_outputs: print(f"Exiting due to exception {e}.")
        return articles_list

# %%
# get the list of articles
print("Scraping articles.")
articles = recursive_page_scrape(base_url=astro_ph_url_base, do_outputs=False, interval_timer=0)
print(f"Scraped {len(articles)} articles.")

# %%
# save the list of articles to a file
# first the list has to be made into a dict, the key will just be the number of the article
saved_articles_dict = [{num: {"title": art[0], "link": art[1]}} for num, art in enumerate(articles)]
print(f"{len(saved_articles_dict)} articles saved.")
# print(json.dumps(saved_articles_dict))

# open/make a new file to dump to
with open("articles_list.json", "w+") as writer: json.dump(saved_articles_dict, writer)

# %%
# create and save into a folder
article_folder = "Articles"
os.makedirs(article_folder, exist_ok=True)

# download and save all articles
for number, article in enumerate(articles):
    # define a new title
    new_title = re.sub(r"\$\\.*{([^}]*)}\$", r"\g<1>", str(article[0])).replace(" ", "_").replace("$", "") + ".pdf"

    # download pdf
    r = requests.get(article[1], stream=True)
    with open(os.path.join(article_folder, new_title), "wb") as download: download.write(r.content)

    # report
    print(f"{number}: Downloaded {new_title}")

# %%



