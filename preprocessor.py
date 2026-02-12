import re
import pandas as pd

def preprocess(data):

    # 🔥 Supports Android + iPhone + 12hr + 24hr formats
    pattern = r'(\d{1,2}/\d{1,2}/\d{2,4},?\s\d{1,2}:\d{2}(?:\s?[APMapm]{2})?)\s-\s'

    matches = re.split(pattern, data)

    # If chat format still not detected
    if len(matches) < 3:
        return pd.DataFrame()

    dates = matches[1::2]
    messages = matches[2::2]

    df = pd.DataFrame({
        'message_date': dates,
        'user_message': messages
    })

    # Clean hidden WhatsApp unicode space
    df['message_date'] = df['message_date'].str.replace('\u202f', ' ', regex=False)

    # Convert to datetime safely
    df['message_date'] = pd.to_datetime(
        df['message_date'],
        dayfirst=True,
        errors='coerce'
    )

    df.rename(columns={'message_date': 'date'}, inplace=True)
    df.dropna(subset=['date'], inplace=True)

    # --------------------------
    # Extract user and message
    # --------------------------
    users = []
    messages = []

    for message in df['user_message']:
        entry = re.split(r'([^:]+):\s', message)

        if len(entry) >= 3:
            users.append(entry[1])
            messages.append(entry[2])
        else:
            users.append('group_notification')
            messages.append(entry[0])

    df['user'] = users
    df['message'] = messages
    df.drop(columns=['user_message'], inplace=True)

    # Ensure string (prevents .str errors)
    df['message'] = df['message'].astype(str).str.strip()

    # --------------------------
    # Time Features
    # --------------------------
    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour.fillna(0).astype(int)
    df['minute'] = df['date'].dt.minute.fillna(0).astype(int)

    # Safe time period (fixes float error)
    df['period'] = df['hour'].apply(lambda x: f"{int(x):02d}-{(int(x)+1)%24:02d}")

    return df






