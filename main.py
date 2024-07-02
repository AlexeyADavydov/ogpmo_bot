import os
import telebot
import time
import requests
from channels import OGPMO

from datetime import datetime as dt

from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
token = os.getenv('TOKEN')
bot = telebot.TeleBot(token)

ogpmo_ran = "@ogpmo_ran"


@bot.message_handler(commands=['start'])
def start(message):

    bot.reply_to(
        message,
        "Привет! Я буду репостить посты из одного канала в другой."
    )

    previous_post_datetime = None

    while True:

        for institute in OGPMO:

            url = institute['telegram_url']
            if url == '':
                continue

            previous_post_datetime = institute['latest_post_datetime']
            post_entity = channels(previous_post_datetime, url)
            current_post_datetime = post_entity['datetime']

            post = (
                f'<b>{post_entity["title"]}</b>'
                f'\n\n'
                f'{post_entity["text"]}'
                f'\n\n'
                f'Подробнее – {post_entity["link"]}'
            )

            if (previous_post_datetime != current_post_datetime) and (
                previous_post_datetime == "None"
            ):

                institute['latest_post_datetime'] = current_post_datetime

            elif (dt.fromisoformat(current_post_datetime) >
                  dt.fromisoformat(previous_post_datetime)):

                institute['latest_post_datetime'] = current_post_datetime

                time.sleep(15)

                bot.send_message(
                    ogpmo_ran,
                    post,
                    parse_mode='HTML'
                )
                bot.send_message(
                    message.from_user.id,
                    f"Новый пост {current_post_datetime, url}",
                )
                print(f"Новый пост {current_post_datetime, url}")

        bot.send_message(
            message.from_user.id,
            "Конец цикла парсинга. Следующий будет через 10 минут",
            )
        time.sleep(600)


def channels(previous_post_datetime, url):
    channel = requests.get(url)
    soup = BeautifulSoup(channel.content, 'html.parser')
    posts_all = soup.find_all(
        'div',
        {'class': 'tgme_widget_message_wrap js-widget_message_wrap'}
    )

    if posts_all:

        post_number = -1

        while True:
            try:
                latest_post = posts_all[post_number]

                title = latest_post.find(
                    'div',
                    class_='tgme_widget_message_author'
                ).text.strip()

                text = latest_post.find(
                    'div',
                    class_='tgme_widget_message_text'
                ).text.strip()

                link = latest_post.find(
                    'a',
                    class_='tgme_widget_message_date'
                ).get('href')

                datetime = latest_post.find(
                    'time',
                    class_='time',
                    datetime=True
                )['datetime'].strip()

                post_entity = {
                    'title': title,
                    'text': text,
                    'link': link,
                    'datetime': datetime,
                }

                return post_entity
            except AttributeError:
                post_number -= 1
                if abs(post_number) > len(posts_all):
                    break

        return previous_post_datetime
    else:
        return previous_post_datetime


if __name__ == "__main__":
    bot.polling()
