import requests
from bs4 import BeautifulSoup
from fake_headers import Headers
import re
import json
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import itertools

HOST = "https://hh.ru/"
SEARCH = f"{HOST}search/vacancy?text=python&area=1&area=2"


def get_headers():
    header = Headers(
        browser="chrome",  # Generate only Chrome UA
        os="win",  # Generate ony Windows platform
        headers=True,  # generate misc headers
    )
    headers_data = header.generate()
    return headers_data


def get_text(url):
    return requests.get(url, headers=get_headers()).text


def get_next_page_link(soup):
    next_page_link_div = soup.find("div", class_="pager")
    next_page_link_a = next_page_link_div.find("a", class_="bloko-button")
    next_page_link = next_page_link_a["href"]
    return next_page_link


def get_link_from_vacancy(some_link_soup):
    div_vacancy_list_tag = some_link_soup.find("div", id="a11y-main-content")
    vacancies = div_vacancy_list_tag.find_all("div", class_="serp-item")
    len(vacancies)
    vacancies_list = []
    for vacancy in vacancies:
        a_tag = vacancy.find("a", class_="serp-item__title")
        link = a_tag["href"]
        vacancies_list.append({"link": link})
    return vacancies_list


def find_all_vacancies():
    main_html = get_text(SEARCH)
    main_soup = BeautifulSoup(main_html, "lxml")
    count_pages_block_div = main_soup.find("div", class_="pager")
    count_pages_block_span = count_pages_block_div.find_all("span")
    find_count = count_pages_block_span[-3]
    count_pages = int(find_count.text)
    res = []
    for page in range(count_pages):
        search_pages = f"{SEARCH}&page={page}"
        next_page_html = get_text(search_pages)
        next_page_soup = BeautifulSoup(next_page_html, "lxml")
        res.append(get_link_from_vacancy(next_page_soup))
    return res


def wait_element(driver, delay_seconds=1, by=By.TAG_NAME, value=None):
    return WebDriverWait(driver, delay_seconds).until(
        expected_conditions.presence_of_element_located((by, value))
    )


def selenium_search():
    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.get(SEARCH)

    vacancy_data = find_all_vacancies()
    vacancy_data = list(itertools.chain(*vacancy_data))
    vacancy_data_new = []
    for vacancy_dict in vacancy_data:
        driver.get(vacancy_dict["link"])
        vacancy_description_text = driver.find_element(
            By.CLASS_NAME, "vacancy-description"
        ).text
        pattern = r"Django|Flask"
        research = re.findall(pattern, vacancy_description_text, re.IGNORECASE)
        if research:
            try:
                wait_element(
                    driver,
                    2,
                    by=By.XPATH,
                    value="//div/div[3]/div[1]/div/div/div/div/div/div[1]/div[1]/div/div[1]/div[2]",
                )
                wait_element(driver, 2, by=By.CLASS_NAME, value="vacancy-company-name")
                wait_element(
                    driver,
                    2,
                    by=By.XPATH,
                    value="//div/div[3]/div[1]/div/div/div/div/div/div[2]/div/div[1]/div/div/div/a/span",
                )
                wait_element(
                    driver,
                    2,
                    by=By.XPATH,
                    value="//div/div[3]/div[1]/div/div/div/div/div/div[2]/div/div[1]/div/div/div/p",
                )
            except TimeoutException:
                pass

            try:
                vacancy_salary_fork = driver.find_element(
                    By.XPATH,
                    "//div/div[3]/div[1]/div/div/div/div/div/div[1]/div[1]/div/div[1]/div[2]",
                ).text
            except Exception:
                vacancy_salary_fork = "ЗП не указана"

            vacancy_company_name = driver.find_element(
                By.CLASS_NAME, "vacancy-company-name"
            ).text
            try:
                city = driver.find_element(
                    By.XPATH,
                    "//div/div[3]/div[1]/div/div/div/div/div/div[2]/div/div[1]/div/div/div/a/span",
                ).text
            except Exception:
                city = "Город не указан"

            try:
                city_alternative = driver.find_element(
                    By.XPATH,
                    "//div/div[3]/div[1]/div/div/div/div/div/div[2]/div/div[1]/div/div/div/p",
                ).text
            except Exception:
                city_alternative = ""

            vacancy_data_new.append(
                {
                    "salary_fork": vacancy_salary_fork,
                    "city": city,
                    "company_name": vacancy_company_name,
                    "link": vacancy_dict["link"],
                    "city_alternative": city_alternative,
                }
            )
    driver.quit()
    return vacancy_data_new


def write_to_json(data):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return print("data.json was created")


def read_json(file):
    with open(file, encoding="utf-8") as f:
        data = json.load(f)
    return data


if __name__ == "__main__":
    main_html = get_text(SEARCH)
    main_soup = BeautifulSoup(main_html, "lxml")
    get_link_from_vacancy(main_soup)
    data = selenium_search()
    write_to_json(data)
    data = read_json("data.json")
    print(len(data))
