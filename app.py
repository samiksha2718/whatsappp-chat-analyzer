# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
from urlextract import URLExtract
from collections import Counter
import emoji
from textblob import TextBlob
import re
from datetime import datetime
import time

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="WhatsApp Chat Analyzer Pro", layout="wide")

# ---------------- DARK/LIGHT MODE ----------------
dark_mode = st.checkbox("Dark Mode 🌙", value=False)

if dark_mode:
    primary_bg = "#111111"
    secondary_bg = "#1f1f1f"
    text_color = "white"
    wc_bg_color = "black"
else:
    primary_bg = "#f5f5f5"
    secondary_bg = "#ffffff"
    text_color = "black"
    wc_bg_color = "white"

# ---------------- CSS ----------------
st.markdown(f"""
<style>
body {{
    background-image: url("https://images.unsplash.com/photo-1517836357463-d25dfeac3438?auto=format&fit=crop&w=1470&q=80");
    background-size: cover;
    background-attachment: fixed;
    color: {text_color};
}}
.main-box {{
    background-color: rgba(34, 139, 34, 0.85);
    border-radius: 20px;
    padding: 25px;
    margin-bottom: 20px;
}}
.metric-card {{
    background-color: {secondary_bg};
    color: {text_color};
    padding: 20px;
    border-radius: 20px;
    text-align: center;
    box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
}}
@keyframes bounce {{
    0%, 100% {{ transform: translateY(0); }}
    50% {{ transform: translateY(-10px); }}
}}
</style>
""", unsafe_allow_html=True)

# ---------------- MAIN DASHBOARD ----------------
st.markdown('<div class="main-box">', unsafe_allow_html=True)
st.title("📊 WhatsApp Chat Analyzer Pro")

# ---------------- REAL-TIME CLOCK ----------------
clock = st.empty()

def display_clock():
    now = datetime.now().strftime("%A, %B %d, %Y | %I:%M:%S %p")
    clock.markdown(f"<h4 style='color:{text_color}'>🕒 {now}</h4>", unsafe_allow_html=True)

display_clock()  # initial display

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader("Upload WhatsApp Chat (.txt)", type=["txt"])
if not uploaded_file:
    st.stop()

# ---------------- PREPROCESS ----------------
def preprocess(data):
    pattern = r'(\d{1,2}/\d{1,2}/\d{2,4},?\s\d{1,2}:\d{2}(?:\s?[APMapm]{2})?)\s-\s'
    matches = re.split(pattern, data)
    if len(matches) < 3: return pd.DataFrame()
    dates = matches[1::2]
    messages = matches[2::2]
    df = pd.DataFrame({'message_date': dates, 'user_message': messages})
    df['message_date'] = df['message_date'].str.replace('\u202f',' ', regex=False)
    df['message_date'] = pd.to_datetime(df['message_date'], dayfirst=True, errors='coerce')
    df.rename(columns={'message_date':'date'}, inplace=True)
    df.dropna(subset=['date'], inplace=True)
    users, msgs = [], []
    for msg in df['user_message']:
        entry = re.split(r'([^:]+):\s', msg)
        if len(entry)>=3: users.append(entry[1]); msgs.append(entry[2])
        else: users.append('group_notification'); msgs.append(entry[0])
    df['user'] = users
    df['message'] = pd.Series(msgs).astype(str).str.strip()
    df.drop(columns=['user_message'], inplace=True)
    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour.fillna(0).astype(int)
    df['minute'] = df['date'].dt.minute.fillna(0).astype(int)
    df['period'] = df['hour'].apply(lambda x: f"{x:02d}-{(x+1)%24:02d}")
    return df

data = uploaded_file.getvalue().decode("utf-8")
df = preprocess(data)
if df.empty:
    st.error("Invalid chat format!")
    st.stop()

st.success("Chat Loaded Successfully!")

# ---------------- USER SELECTION ----------------
user_list = df['user'].unique().tolist()
user_list.sort()
user_list.insert(0,"Overall")
selected_user = st.selectbox("Show Analysis For:", user_list)

# ---------------- STATISTICS ----------------
extract = URLExtract()

def fetch_stats(selected_user, df):
    if selected_user!="Overall": df=df[df['user']==selected_user]
    num_msgs = df.shape[0]
    words = sum(len(str(msg).split()) for msg in df['message'])
    media = df[df['message'].str.contains('Media', na=False)].shape[0]
    links = sum(len(extract.find_urls(str(msg))) for msg in df['message'])
    return num_msgs, words, media, links

num_msgs,num_words,media_count,link_count = fetch_stats(selected_user, df)
emoji_count = len([c for msg in df['message'] for c in msg if c in emoji.EMOJI_DATA])

metrics = [
    {"label":"Messages", "value":num_msgs, "icon":"💬"},
    {"label":"Words", "value":num_words, "icon":"📝"},
    {"label":"Media", "value":media_count, "icon":"📸"},
    {"label":"Links", "value":link_count, "icon":"🔗"},
    {"label":"Emojis", "value":emoji_count, "icon":"😀"}
]

cols = st.columns(len(metrics))
for i, m in enumerate(metrics):
    cols[i].markdown(f"""
        <div class="metric-card">
            <div style="font-size:40px; animation:bounce 1s infinite">{m['icon']}</div>
            <h3>{m['value']}</h3>
            <p>{m['label']}</p>
        </div>
    """, unsafe_allow_html=True)

# ---------------- MOST ACTIVE USERS ----------------
if selected_user=="Overall":
    st.subheader("👑 Most Active Users")
    user_counts = df['user'].value_counts().head()
    percent_df = ((df['user'].value_counts()/df.shape[0])*100).round(2).reset_index()
    percent_df.columns = ['name','percent']
    fig = px.bar(x=user_counts.index, y=user_counts.values, text=user_counts.values, color=user_counts.values,
                 color_continuous_scale='viridis')
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(percent_df)

# ---------------- MONTHLY TIMELINE ----------------
st.subheader("📅 Monthly Timeline")
timeline = df.groupby(['year','month_num','month']).count()['message'].reset_index()
timeline['time'] = timeline['month']+"-"+timeline['year'].astype(str)
fig = px.line(timeline, x='time', y='message', markers=True)
st.plotly_chart(fig, use_container_width=True)

# ---------------- DAILY TIMELINE ----------------
st.subheader("📅 Daily Timeline")
daily = df.groupby('only_date').count()['message'].reset_index()
fig = px.line(daily, x='only_date', y='message', markers=True)
st.plotly_chart(fig, use_container_width=True)

# ---------------- ACTIVITY HEATMAP ----------------
st.subheader("🔥 Activity Heatmap")
heatmap = df.pivot_table(index='day_name', columns='period', values='message', aggfunc='count').fillna(0)
days_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
heatmap = heatmap.reindex(days_order)
fig = px.imshow(heatmap, text_auto=True, aspect="auto", color_continuous_scale='viridis')
st.plotly_chart(fig, use_container_width=True)

# ---------------- WORDCLOUD ----------------
st.subheader("☁ WordCloud")
try:
    with open('stop_hinglish.txt','r',encoding='utf-8') as f: stop_words=f.read().split()
except: stop_words=[]
temp = df[df['user']!='group_notification']
temp = temp[~df['message'].str.contains('Media', na=False)]
if not temp.empty:
    temp['message'] = temp['message'].apply(lambda x: " ".join([w for w in x.lower().split() if w not in stop_words]))
    wc = WordCloud(width=600, height=400, background_color=wc_bg_color).generate(temp['message'].str.cat(sep=" "))
    st.image(wc.to_array())
else:
    st.write("No text data for wordcloud.")

# ---------------- EMOJI ANALYSIS ----------------
st.subheader("😀 Emoji Analysis")
emojis_list = [c for msg in df['message'] for c in msg if c in emoji.EMOJI_DATA]
if emojis_list:
    emoji_df = pd.DataFrame(Counter(emojis_list).most_common(20), columns=['emoji','count'])
    fig = px.bar(emoji_df, x='count', y='emoji', orientation='h', text='count', color='count', color_continuous_scale='viridis')
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(emoji_df)
else:
    st.write("No emojis found.")

# ---------------- SENTIMENT ----------------
st.subheader("🤖 Sentiment Analysis")
df['sentiment'] = df['message'].apply(lambda x: TextBlob(str(x)).sentiment.polarity)
fig = px.histogram(df, x='sentiment', nbins=20, color_discrete_sequence=['green'])
st.plotly_chart(fig, use_container_width=True)

# ---------------- DOWNLOAD ----------------
st.subheader("⬇ Download Analysis CSV")
stats_df = pd.DataFrame({
    "Total Messages":[num_msgs],
    "Total Words":[num_words],
    "Media Messages":[media_count],
    "Links Shared":[link_count],
    "Total Emojis":[emoji_count],
    "Positive Messages":[(df['sentiment']>0).sum()],
    "Negative Messages":[(df['sentiment']<0).sum()],
    "Neutral Messages":[(df['sentiment']==0).sum()]
})
st.download_button("Download CSV", stats_df.to_csv(index=False), file_name="chat_analysis.csv", mime="text/csv")

st.markdown('</div>', unsafe_allow_html=True)






















