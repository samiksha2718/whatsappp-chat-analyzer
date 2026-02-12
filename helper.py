from urlextract import URLExtract
from wordcloud import WordCloud
import pandas as pd
from collections import Counter
import emoji

extract = URLExtract()

def fetch_stats(selected_user, df):

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    num_messages = df.shape[0]

    words = []
    for message in df['message']:
        words.extend(str(message).split())

    num_media_messages = df[df['message'].astype(str).str.contains('Media', na=False)].shape[0]

    links = []
    for message in df['message']:
        links.extend(extract.find_urls(str(message)))

    return num_messages, len(words), num_media_messages, len(links)


def most_busy_users(df):

    x = df['user'].value_counts().head()

    percent_df = (
        (df['user'].value_counts() / df.shape[0]) * 100
    ).round(2).reset_index()

    percent_df.columns = ['name', 'percent']

    return x, percent_df


def create_wordcloud(selected_user, df):

    with open('stop_hinglish.txt', 'r', encoding='utf-8') as f:
        stop_words = f.read().split()

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    temp = df[df['user'] != 'group_notification']
    temp = temp[~temp['message'].astype(str).str.contains('Media', na=False)]

    if temp.empty:
        return None

    def remove_stop_words(message):
        return " ".join(
            word for word in str(message).lower().split()
            if word not in stop_words
        )

    temp = temp.copy()
    temp['message'] = temp['message'].apply(remove_stop_words)

    wc = WordCloud(width=600, height=600, background_color='white')
    return wc.generate(temp['message'].str.cat(sep=" "))


def most_common_words(selected_user, df):

    with open('stop_hinglish.txt', 'r', encoding='utf-8') as f:
        stop_words = f.read().split()

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    temp = df[df['user'] != 'group_notification']
    temp = temp[~temp['message'].astype(str).str.contains('Media', na=False)]

    words = []
    for message in temp['message']:
        for word in str(message).lower().split():
            if word not in stop_words:
                words.append(word)

    if len(words) == 0:
        return pd.DataFrame(columns=['word', 'count'])

    most_common_df = pd.DataFrame(Counter(words).most_common(20))
    most_common_df.columns = ['word', 'count']

    return most_common_df


def emoji_helper(selected_user, df):

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    emojis = []

    for message in df['message']:
        for char in str(message):
            if char in emoji.EMOJI_DATA:
                emojis.append(char)

    if len(emojis) == 0:
        return pd.DataFrame(columns=['emoji', 'count'])

    emoji_df = pd.DataFrame(Counter(emojis).most_common())
    emoji_df.columns = ['emoji', 'count']

    return emoji_df


def monthly_timeline(selected_user, df):

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    timeline = df.groupby(['year', 'month_num', 'month']).count()['message'].reset_index()
    timeline['time'] = timeline['month'] + "-" + timeline['year'].astype(str)

    return timeline


def daily_timeline(selected_user, df):

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    return df.groupby('only_date').count()['message'].reset_index()


def week_activity_map(selected_user, df):

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    return df['day_name'].value_counts()


def month_activity_map(selected_user, df):

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    return df['month'].value_counts()


def activity_heatmap(selected_user, df):

    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    heatmap = df.pivot_table(
        index='day_name',
        columns='period',
        values='message',
        aggfunc='count'
    ).fillna(0)

    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap = heatmap.reindex(days_order)

    return heatmap.fillna(0)

















