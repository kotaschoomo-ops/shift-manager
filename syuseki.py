import streamlit as st
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="シフト管理システム", layout="wide")

# --- 1. データベース（Googleスプレッドシート）への接続設定 ---
# セキュリティ設定(Secrets)を参照して接続します
conn = st.connection("gsheets", type=GSheetsConnection)

# データを読み込む関数
def get_data():
    return conn.read(ttl="10s") # 10秒キャッシュ（常に最新に近い状態にする）

# --- 2. サイドバーでの画面切り替え ---
st.sidebar.title("📱 シフト管理システム")
mode = st.sidebar.radio("役割を選択してください", ["【バイト】希望入力", "【職員】シフト管理"])

# --- A. バイト用画面 ---
if mode == "【バイト】希望入力":
    st.title("📝 シフト希望 入力")
    st.write("名前を入力し、希望日を選択して送信してください。")
    
    name = st.text_input("フルネーム")
    
    # 向こう60日の日付を選択肢にする
    today = datetime.date.today()
    date_options = [(today + datetime.timedelta(days=i)).strftime("%Y-%m-%d") for i in range(60)]
    selected_dates = st.multiselect("入れる日を選択（複数可）", date_options)
    
    if st.button("希望を送信する"):
        if name and selected_dates:
            # 既存のデータを取得
            existing_data = get_data()
            
            # 新しいデータを準備
            new_entries = pd.DataFrame([{"名前": name, "日付": d} for d in selected_dates])
            
            # データを合体させて保存
            updated_data = pd.concat([existing_data, new_entries], ignore_index=True).drop_duplicates()
            conn.update(data=updated_data)
            
            st.success(f"{name}さんの希望を保存しました！")
            st.balloons()
        else:
            st.error("名前と日付を正しく入力してください。")

# --- B. 職員用画面 ---
else:
    st.title("🔑 職員用 管理画面")
    
    password = st.sidebar.text_input("管理者パスワード", type="password")
    if password == "staff123": # パスワードは自由に変えてください
        st.success("ログイン成功")
        
        df = get_data()
        
        tab1, tab2 = st.tabs(["📊 リスト表示", "📅 シフト表（Excel風）"])
        
        with tab1:
            st.subheader("登録データ一覧")
            st.dataframe(df, use_container_width=True)
            
            # 特定の行を削除するなどの機能もここに追加可能です
            
        with tab2:
            st.subheader("全体シフト確認表")
            if not df.empty:
                # 名前を縦軸、日付を横軸にして「◯」を入れる表を作る
                matrix = pd.crosstab(df['名前'], df['日付']).replace(1, "◯").replace(0, "")
                st.dataframe(matrix, use_container_width=True)
    else:
        st.warning("パスワードを入力してください。")


