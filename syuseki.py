import streamlit as st
import pandas as pd
import datetime
# 💡 追加：書き込みに必要な部品
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. 設定（スプレッドシートのURLを貼る）
# ==========================================
SHEET_URL = "ここにコピーしたスプレッドシートのURLを貼ってください"
CSV_URL = SHEET_URL.split("/edit")[0] + "/export?format=csv"
ADMIN_PASSWORD = "staff123" 

# データの読み込み
def load_data():
    try:
        df = pd.read_csv(CSV_URL)
        df['日付'] = df['日付'].astype(str)
        return df
    except:
        return pd.DataFrame(columns=["名前", "日付"])

st.set_page_config(page_title="シフト管理システム", layout="wide")

if 'submit_count' not in st.session_state:
    st.session_state.submit_count = 0

# サイドバー
with st.sidebar:
    st.title("📱 メニュー")
    mode = st.radio("役割を選択してください", ["【バイト】希望入力", "【職員】シフト管理"])

df = load_data()

# ==========================================
# A. バイト用（希望入力）
# ==========================================
if mode == "【バイト】希望入力":
    st.title("📝 シフト希望 入力画面")
    
    input_name = st.text_input("名前（フルネーム）", key=f"n_{st.session_state.submit_count}")
    
    today = datetime.date.today()
    date_options = [(today + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(60)]
    input_dates = st.multiselect("入れる日を選択", options=date_options, key=f"d_{st.session_state.submit_count}")
    
    if st.button("希望を送信する"):
        if input_name and input_dates:
            # --- ここから書き換え ---
            try:
                # スプレッドシートへの接続を確立
                conn = st.connection("gsheets", type=GSheetsConnection)
                
                # 新しいデータを作成
                new_data = pd.DataFrame([[input_name, d] for d in input_dates], columns=["名前", "日付"])
                
                # 既存のデータ（df）と新しいデータを合体させて保存
                updated_df = pd.concat([df, new_data], ignore_index=True).drop_duplicates()
                
                # スプレッドシートを更新
                conn.update(spreadsheet=SHEET_URL, data=updated_df)
                
                st.success(f"{input_name}さんの希望をスプレッドシートに保存しました！")
                st.session_state.submit_count += 1
                st.rerun()
            except Exception as e:
                st.error(f"保存に失敗しました。Secretsの設定を確認してください。エラー内容: {e}")
            # --- ここまで書き換え ---
        else:
            st.error("名前と日付を入力してください。")

# ==========================================
# B. 職員用（シフト管理）
# ==========================================
else:
    st.title("🔑 職員専用 管理画面")
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        pw = st.text_input("パスワード", type="password")
        if st.button("ログイン"):
            if pw == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.rerun()
    else:
        if st.button("🔒 ログアウト"):
            st.session_state.logged_in = False
            st.rerun()

        st.markdown("---")
        tab1, tab2 = st.tabs(["📊 現在のデータ", "📅 シフト表"])
        with tab1:
            st.dataframe(df, use_container_width=True)
        with tab2:
            if not df.empty:
                matrix = pd.crosstab(df['名前'], df['日付']).replace(1, "◯").replace(0, "×")
                st.dataframe(matrix)

