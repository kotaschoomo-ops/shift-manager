import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials
from streamlit_calendar import calendar

st.set_page_config(page_title="シフト管理システム", layout="wide")

# ===== Google接続 =====
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=scope
)

client = gspread.authorize(creds)

# 🔽 スプレッドシートを開く処理を「キャッシュ」する
@st.cache_resource
def get_spreadsheet(url):
    return client.open_by_url(url)

# 🔽 あなたのスプレッドシートURL
target_url = "https://docs.google.com/spreadsheets/d/1DG1aCJxiw6AEW7O383KKntimnxg_oV4uyecwPtGvx5E/edit?usp=sharing"

spreadsheet = get_spreadsheet(target_url)
sheet = spreadsheet.sheet1


# ===== データ取得 =====
# @st.cache_data を追加して、10秒間はGoogleに聞かずに手元のデータを使うようにします
@st.cache_data(ttl=10) 
def get_data():
    # 1. 全データを取得
    all_values = sheet.get_all_values()
    
    # 2. データが全くない、またはヘッダーしかない場合の処理
    if len(all_values) <= 1:
        return pd.DataFrame(columns=["名前", "日付"])
    
    # 3. データがある場合は、1行目をヘッダーとして読み込む
    return pd.DataFrame(all_values[1:], columns=all_values[0])


# ===== サイドバー =====
st.sidebar.title("📱 シフト管理システム")
mode = st.sidebar.radio("役割を選択してください", ["【バイト】希望入力", "【職員】シフト管理"])


# ===== バイト画面 =====
if mode == "【バイト】希望入力":
    st.title("📝 シフト希望 入力")

    name = st.text_input("フルネーム")

    # --- ここからカレンダー修正（記憶保持モード） ---
    st.write("カレンダーをタップして、**「入れる日」**をすべて選択してください。")

# 1. 記憶（セッション状態）の初期化
    if "selected_dates_list" not in st.session_state:
        st.session_state.selected_dates_list = []

# 2. カレンダーを表示
    today = datetime.date.today()
    picked_date = st.date_input(
        "日付を1つずつ選んで追加してください",
        value=None,  # 常に空で表示させる
        min_value=today,
        max_value=today + datetime.timedelta(days=60),
        label_visibility="collapsed"
    )

# 3. 日付がクリックされたら、リストに追加（既にあるなら削除）
    if picked_date:
        date_str = picked_date.strftime("%Y-%m-%d")
    if date_str not in st.session_state.selected_dates_list:
        st.session_state.selected_dates_list.append(date_str)
    else:
        st.session_state.selected_dates_list.remove(date_str)
    
    # 選択後にカレンダーをリセットするために一度再実行
    st.rerun()

# 4. 現在選ばれている日を表示
    if st.session_state.selected_dates_list:
        selected_dates = sorted(st.session_state.selected_dates_list) # 保存用変数
        st.info(f"✅ 選択中: {len(selected_dates)}日間")
    
    # 選んだ日をタグのように表示し、間違えたら消せるようにする
        cols = st.columns(3)
        for i, d in enumerate(selected_dates):
            if cols[i % 3].button(f"🗑️ {d}", key=f"del_{d}"):
                st.session_state.selected_dates_list.remove(d)
                st.rerun()
    else:
        selected_dates = []
        st.warning("まだ日付が選択されていません。")

# 5. 全リセットボタン
    if st.button("選択をすべてクリア"):
        st.session_state.selected_dates_list = []
        st.rerun()
# --- ここまで ---
        else:
            st.error("名前と日付を入力してください。")


# ===== 職員画面 =====
else:
    st.title("🔑 職員用 管理画面")

    password = st.sidebar.text_input("管理者パスワード", type="password")

    if password == "staff123":
        st.success("ログイン成功")

        df = get_data()

        tab1, tab2 = st.tabs(["📊 リスト表示", "📅 シフト表（Excel風）"])

        with tab1:
            if not df.empty:
                # 1. 削除用のチェックボックス列を追加
                df.insert(0, "選択", False)
                
                # 2. 編集可能なテーブル（Data Editor）を表示
                # ※ 元の st.dataframe ではなく st.data_editor を使います
                edited_df = st.data_editor(
                    df,
                    column_config={"選択": st.column_config.CheckboxColumn(required=True)},
                    disabled=["名前", "日付"], # 名前と日付は直接編集できないようにガード
                    hide_index=True,
                    use_container_width=True
                )

                # 3. 「選択」にチェックが入った行だけを抽出
                rows_to_delete = edited_df[edited_df["選択"] == True]

                if not rows_to_delete.empty:
                    if st.button("🔴 選択した行を削除する"):
                        # チェックがついていない行（＝残したいデータ）だけを抽出して保存
                        remaining_df = edited_df[edited_df["選択"] == False].drop(columns=["選択"])
                        
                        sheet.clear()
                        sheet.append_row(["名前", "日付"])
                        if not remaining_df.empty:
                            sheet.append_rows(remaining_df.values.tolist())
                        
                        st.success("選択したデータを削除しました！")
                        st.rerun() # 画面を更新して削除を反映
            else:
                st.info("現在、登録されているデータはありません。")

        with tab2:
            if not df.empty:
                matrix = pd.crosstab(df["名前"], df["日付"]).replace(1, "◯")
                st.dataframe(matrix, use_container_width=True)

    else:
        st.warning("パスワードを入力してください。")




























