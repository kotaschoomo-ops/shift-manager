import streamlit as st
import pandas as pd
import datetime
import gspread
from google.oauth2.service_account import Credentials

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

# 🔽 あなたのスプレッドシートURL
target_url = "https://docs.google.com/spreadsheets/d/1DG1aCJxiw6AEW7O383KKntimnxg_oV4uyecwPtGvx5E/edit?usp=sharing"

spreadsheet = client.open_by_url(target_url)
sheet = spreadsheet.sheet1


# ===== データ取得 =====
def get_data():
    # 1. 全データを取得
    all_values = sheet.get_all_values()
    
    # 2. データが全くない、またはヘッダーしかない場合の処理
    if len(all_values) <= 1:
        # データが空でも「名前」と「日付」という列だけ持った空の表を作る
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

    today = datetime.date.today()
    date_options = [
        (today + datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(60)
    ]

    selected_dates = st.multiselect("入れる日を選択（複数可）", date_options)

    # 送信ボタンの中の処理
    if st.button("希望を送信する"):
        if name and selected_dates:
            existing_data = get_data()

        # 【追加】今入力された「名前」と一致する行を、既存データから除外する
            existing_data = existing_data[existing_data["名前"] != name]

            new_entries = pd.DataFrame(
                [{"名前": name, "日付": d} for d in selected_dates]
            )

            updated_data = pd.concat(
                [existing_data, new_entries],
                ignore_index=True
            ).drop_duplicates()

            # シートに保存
            sheet.clear()
            sheet.append_row(["名前", "日付"])  # ヘッダー
            sheet.append_rows(updated_data.values.tolist())

            st.success(f"{name}さんの希望を保存しました！")
            st.balloons()
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















