import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import mysql.connector
from cryptography.fernet import Fernet
import base64, hashlib, json
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Filter,
    FilterExpression,
    Metric,
    RunReportRequest,
)

@st.cache_data
def load_data(host,user,password):
    config = {
    'user': user,
    'password': password,
    'host': host,
    'database': 'ado_hub',
    'raise_on_warnings': True
    }
    cnx = mysql.connector.connect(**config)
    mycursor = cnx.cursor()

    sql = "SELECT * FROM user_table"
    mycursor.execute(sql)
    results = mycursor.fetchall()

    df1 = pd.DataFrame(results, columns = mycursor.column_names)
    df1 = df1[(df1['is_staff']==False)&(df1['is_superuser']==False)]
    df1 = df1[['id','username','date_joined','pro','last_login','last_interaction']]
    df1 = df1[(df1['date_joined']<df1['last_login'])&(df1['date_joined']<df1['last_interaction'])]

    sql = "SELECT user_id,requested_at,path,remote_addr,host,username_persistent FROM rest_framework_tracking_apirequestlog"
    mycursor.execute(sql)
    results = mycursor.fetchall()

    df2 = pd.DataFrame(results, columns = mycursor.column_names)
    df2 = df2[df2['host'].apply(lambda x: 'localhost' not in x and 'test' not in x)]


    sql = "SELECT * FROM cathoven_api_webhookevents"
    mycursor.execute(sql)
    results = mycursor.fetchall()
    df3 = pd.DataFrame(results, columns = mycursor.column_names)[['webhook_code','order_id','created']]

    sql = "SELECT * FROM cathoven_api_paymenthistory"
    mycursor.execute(sql)
    results = mycursor.fetchall()
    df4 = pd.DataFrame(results, columns = mycursor.column_names)[['order_id','package_id','user_id']]
    df4 = df4[~pd.isnull(df4['user_id'])]

    sql = "SELECT * FROM cathoven_api_package"
    mycursor.execute(sql)
    results = mycursor.fetchall()
    df5 = pd.DataFrame(results, columns = mycursor.column_names)[['id','duration','name']]

    df_pro = df3.merge(df4,how='left',on='order_id').merge(df5,how='left',left_on='package_id',right_on='id')
    df_pro = df_pro[~pd.isnull(df_pro['user_id'])].drop_duplicates()
    mycursor.close()

    return df1, df2, df_pro

st.sidebar.subheader("Credentials")
host = st.sidebar.text_input('host')
user = st.sidebar.text_input('user')
password = st.sidebar.text_input('password',type='password')

if host!='' and user!='' and password!='':
    try:
        df1, df2, df_pro = load_data(host,user,password)
    except Exception as e:
        st.warning(e)
        st.stop()
else:
    st.stop()



@st.cache_data
def get_credentials(password_A):
    encrypted_password_B = 'gAAAAABk4d082reg_muIcxJB9NKMZyE_B9M8xYiU6uNmfdCluzd_x--wX4mG3PyXV8zINM2S6op19wF52PuJAuCgcVDnRFPKn3xPRqhlaCqWlYEPzEnFGclPQHnbEvc4_DUE4n46sSd80_n2m_NzmMlO4V0Zml2_ghGfxS8hJz05Z2C-wnbq0lslSuODua312-sbPTlKu-zNJr4lky-X3r0AXc5XmvUsw76jAgsGPMFuHrQrROGOkGLgF7KBT-rXEmTOUH7PKd7HT1MWvA6T9R6eqwWEFnqHgyg39MT95YFn8h5kH1-8u9lksOwFeD1Qbj9tOOmpJi7zKLDOJOCMDUOfwd7htMUzeu62vEYvlVN6Konk8CknYbyBxVOrO0VW8ikja6FKz5d_sU34y9WTRVafGd3y67079-2Oyql8YFqf8-QC4y2KZopm46eaYV4ixMKTYtHiINph8yB9onvaYwYHKIRAJGtf-FN54_uHhBxkt2mPWASdRmixLcvx-km5_3y7y45dUMdJ7EVmGuVkwAZqCvkuCsUsxllppXg0a8yZT9EKTCXFzaV7RfE_uECPk--XPLKm1piIdcZpAxYgBloLUO1HMdq7jlrYNw_Mmt8D1RlQQ9XjZwtVGTmzOT2B0ZxibplBqE0ZAK7tCrYJSTY4yJ9SI7DvWk4AGzMW5DUXrthMGLx1WTB-rsVElz4F-ubC_JgTCRJdBX5kBQDEjbpYzG4j0Mm-ycQOuo7QbumBOa1uGfeytceGeIkcVv1iHgo3cfz7arjvcY15sUd9q4U93fq0wDkYg16Wd4cHhdwDUT05TKiGjA7_iYSa9K3Y_mCHfyD6TG-5ToKCGm8lnOkkWOwjRFCnrRZH8g2fYgmgEECJpxjZ0pZgoajhyAo7yhyx2faPCU2Y-MooUDe5GFcrQ57hX_AgkwxRB0rPeLUrx3jwH9oUJz56jhqrTT4gsq67WYnCAiGNtZ585tAfAGgTZp_N9u6dO9OzJiMcdIOMFHWjNkxT-QFgxt8Bh3_LvYSqfetTXOeHQuSt8cC8kU-_jKTJ_Y4Z3wGZ_D56a4hVfqDQmvYjnc74lA00_mlzPElBHVDrOCYp3EJUc5ZEjybRxDGd3tTwy4viBQSxDd__uKdcFz0W7ODaJKcX4AqIdXZDN_UGqYJdNodHYSFqLH7LlNvJ9Pzx7-giiK22bmY6Xgi68AKsnpE1YdNQ7UimSEZFOMsYaLBjvADPSry0vgy3qxbmNFb-k2_DcEA5evXw7JJR4rjpZtC50IGDzSj1qciculujZibMJLy96PyP-xRn8T703QujhVhWJk7oqw77XHRwsoajju4AIgkTC8NNks5R4WWn3sk4omLbdB7shzvBRFIAH5EdplNTYHBSBkLlsE6OaKs_G2q3RUnHj7uHTUd6hAKndKaRQynvPvKv_BbyCOU9nFYNO9jC7jirFPD__nXK-h_xmWehXYJIK8abyN7hxvyz3uxnPrIqkURUIvbfK86Cg8-yXGgu9P6fUvOSug6Sz9EETa_pDvjhBeYja9Xgv7gSYRf3brkobCtu-ASn83y3spYjDna1CL7Z_PyIwLJ1_DEzD6mc5a0_Pnoqz8p5N6O6_H8wVszjQaT95fEcZOoqo0AzKEyZu-pQayYDHZx2kEJx4W9M9F-zBiZdja8538IbDABNvDj6YJtzhRW64NyE1NABKNSQDLxpQZl373yhWJNR03ZxvryKE5illeKDdGYf8eUg7_V2P__kgv2Z_rWUR0pHGvX7OffnI1GjEVQc_bjtlrrpeY3870qPZWc5ZWIFRTATZa63jhpP857qy07BtZ2dxaL4ZIT1b05E8_ydnk1makGkwHh_hbhGe4kNZG0Zy_yEyW5Rrsdg3LNa-guu3XfXAyXr-jGusvoka-rUkciBRt9KuzrSG8zEervn0w-ISISXWjbZUgSRGddKogbULp_M5ykEI4LRaS8jMvom3lnEIhctcK9M1B07KQC5x_F9JNwRWytrE5UJEZ8qdMbT5lHyZzuHFiVr_d2JF2K2MppXV_U495jQkjkm69EBqhhTN3-WQPYnYbQwe0ZCITO1Q9j3Gt4tgV0m36JyIYfwpYnGBiPS2pl3dk7lfAnbHNFYxqlcnuARWf5_6BD1vLpFuZtae5Y4huanU-WCKfMOr8aBY9ZsFzbMGGwV7n2bcZfV4SIeBGIGP_mRLuiaf6Pn3Omrfn_zrP4oGVBRszo-Vd58AJRYL28_IPDU6-nQ9zvEiGDvpm95uEkcu0u7jrlzT0M8qfriQm_e-t7dSdTe51BJdSZJnNOiGn0Gi-nfhKEN_wKGimh_FbZVON2dY1dl75xRMJgZNhWyPbHISikwlkTQhbg9_CrucLT8uL2ROvqfzIh9kU56laFEShhX8k9aE3VcLROjxCFQUs1ocTscIfQGrHdsLNlCjPBgzXO_WjuBnpjc7OZSUS-t4d6xVVTeYxuiNFUi1JGw2787_Led8h7Ll9OjdcQbHOpxskKqXjl3IOCdupGnxONtZ8GwubMy1-c76OwvW-124ibeoya4F2bgj_QVMjgkEhKEKzoX2750hS0Q37PIqnqQTeVELCsYHxOc0taX67PnbwPAzW16YpZC6DiYmfoHFjLoX6myctOQSgpyevvlxwLoMUNEFk4U96JPmnMX3EZmB3qGKe-XP3eWtX-myFCuNKyvyRqJjbBPHrSb5CjhtJmUe8t7ShUnMxtKyRYL6KkDTefDlWcBFOmwJ3xxlHKoTV4GE6t0LT9YYktL1jivyKEWtAECSVF_K0dvqPsV2nR9H3tsuKGO-LwSzThkCrQQL5gXGyAikUfVQxMtjmrR3nOE48Pe8xnDdO4nbc6c9M3iWjsF2Uz_D5ouoAN1lkpSzFk1l_J3wWg-x_KELxXuG8YIgCJoDTnfh7THTeTQxkD7WyV0idcQuHnUzpx1b7uSW691SUDUPYjjS70RrYL4brACSNlu-PGULv8_IEqbk1v2X9-8vGT6AkkNizw4mRlIRooDo6eLb5EFLDUopiu_cIJaqXbC3dvVAhwewiOkSzPQBUUoNf8Az5vAULHA3DbA0yXP41QUl_a-AJJXzGckcPvQYueR01HpCcCe0NR_h3ur4-H-Eu5OrRsHnojxGX4hrfnW_vTAsOpBiBnjR_9lSK2u6FNPQVt6ZRChVkoQ2TtwsMWNhNAuQOOkUHeMPF2FtWo8KxaAuim_lFM9nxdpxM8SnaUM0AQeMmBg1mj1ZDTJXZK3dS6aoHv0pmCK7lv7sRoKqzgWOmxY5kxxfTQk5VzggwgAfiFKoQT49A=='.encode()
    hlib = hashlib.md5()
    hlib.update(password_A.encode())
    encoded_password = base64.urlsafe_b64encode(hlib.hexdigest().encode('latin-1'))
    cipher_suite = Fernet(encoded_password)
    return cipher_suite.decrypt(encrypted_password_B).decode()




st.sidebar.divider()
st.sidebar.subheader("Settings")

reactivation_settings_expander = st.sidebar.expander("Reactivation window size (days)")
reactivation_settings_expander.caption("Reactivated users: active in period A, inactive in period I, and then active again in period R.")
reactivation_settings_expander.caption("0: same as chosen time frame")
reactivation_settings_expander.caption("-1: indefinite")
previous_active_period = reactivation_settings_expander.number_input("Previous active period (A)",value=0,min_value=-1,max_value=90,step=1,key="previous_active_period")
inactive_period = reactivation_settings_expander.number_input("Inactive period (I)",value=0,min_value=0,max_value=90,step=1,key="inactive_period")
reactive_period = reactivation_settings_expander.number_input("Reactive period (R)",value=0,min_value=0,max_value=1,step=1,key="reactive_period")

resurrection_settings_expander = st.sidebar.expander("Resurrection window size (days)")
resurrection_settings_expander.caption("Resurrected users: inactive for more than I days, and then active again in period R.")
resurrection_settings_expander.caption("0: same as chosen time frame")
dormant_period = resurrection_settings_expander.number_input("Inactive period threshold (I)",value=30,min_value=0,max_value=90,step=1,key="dormant_period")
resurrect_period = resurrection_settings_expander.number_input("Resurrect period (R)",value=0,min_value=0,max_value=1,step=1,key="resurrect_period")


churning_settings_expander = st.sidebar.expander("Churning window size (days)")
churning_settings_expander.caption("Churned users: inactive for more than I days")
churning_threshold = churning_settings_expander.number_input("Churning threshold (I)",value=30,min_value=1,max_value=90,step=1,key="churning_threshold")


trend_settings_expander = st.sidebar.expander("Trends")
show_trends = trend_settings_expander.checkbox("Show trends",value=True,key="show_trends")
if show_trends:
    trend_settings_expander.write("Window size")
    daily_window_size = trend_settings_expander.number_input("Daily",value=7,min_value=2,max_value=30,step=1,key="daily_window_size")
    weekly_window_size = trend_settings_expander.number_input("Weekly",value=6,min_value=2,max_value=12,step=1,key="weekly_window_size")
    biweekly_window_size = trend_settings_expander.number_input("Bi-weekly",value=4,min_value=2,max_value=12,step=1,key="biweekly_window_size")
    monthly_window_size = trend_settings_expander.number_input("Monthly",value=3,min_value=2,max_value=12,step=1,key="monthly_window_size")


@st.cache_data
def visitors(dates):
    password_B = get_credentials(host+user+password)
    client = BetaAnalyticsDataClient().from_service_account_info(json.loads(password_B))

    date_ranges = []
    for date in dates:
        date_ranges.append(DateRange(start_date=date[0], end_date=date[1]))

    values = []

    for i in range(int((len(date_ranges)-1)//4+1)):

        request = RunReportRequest(
            property=f"properties/294609234",
            dimensions=[Dimension(name="eventName")],
            metrics=[Metric(name="totalUsers")],
            date_ranges=date_ranges[i*4:(i+1)*4],
            dimension_filter=FilterExpression(
                filter=Filter(
                    field_name="eventName",
                    string_filter=Filter.StringFilter(value="first_visit"),
                )
            ),
        )
        response = client.run_report(request)

        values += [row.metric_values[-1].value for row in response.rows]

    return np.array(list(reversed(values)))


@st.cache_data
def trial_users(dates):
    counts = []
    for date in dates:
        date = pd.to_datetime(np.array(date))
        trial_user_ids = set(df2[(df2['username_persistent']=='Anonymous')&(df2['requested_at'].dt.normalize()>=date[0])&(df2['requested_at'].dt.normalize()<=date[1])&(df2['path']!='/')]['remote_addr'].values)
        counts.append(len(trial_user_ids))
    return np.array(counts)

@st.cache_data
def new_users(dates):
    counts = []
    ids = []
    for date in dates:
        date = pd.to_datetime(np.array(date))
        temp = df1[(df1['date_joined'].dt.normalize()>=date[0])&(df1['date_joined'].dt.normalize()<=date[1])]
        ids.append(set(temp['id'].values))
        counts.append(len(temp))
    return np.array(counts), ids

@st.cache_data
def registered_users(dates):
    dates = pd.to_datetime(np.array(dates))
    counts = []
    for date in dates:
        counts.append(len(df1[df1['date_joined'].dt.normalize()<=date]))
    return np.array(counts)

@st.cache_data
def subscription_users(dates):
    dates = pd.to_datetime(dates)
    return len(df1[df1['pro']==True])

@st.cache_data
def new_subscription_users(dates, duration=0):
    df_temp = df_pro[df_pro['webhook_code']=='BILLING.SUBSCRIPTION.ACTIVATED'].drop_duplicates()
    counts = []
    ids = []
    for date in dates:
        date = pd.to_datetime(np.array(date))
        if duration==0:
            temp = df_temp[(df_temp['created'].dt.normalize()>=date[0])&(df_temp['created'].dt.normalize()<=date[1])]
        else:
            temp = df_temp[(df_temp['created'].dt.normalize()>=date[0])&(df_temp['created'].dt.normalize()<=date[1])&(df_temp['duration']==duration)]
        ids.append(set(temp['user_id'].values))
        counts.append(len(temp))
    return np.array(counts), ids

@st.cache_data
def active_users(dates, among=None):
    df2_temp = df2[df2['username_persistent']!='Anonymous'].copy()
    df2_temp['requested_at'] = df2_temp['requested_at'].dt.normalize()
    #df2_temp = df2_temp[df2_temp['requested_at']>=pd.to_datetime(dates[0][0])-pd.Timedelta(days=31)]
    df2_temp = df2_temp.drop_duplicates(['user_id','requested_at'])
    #df2_temp['requested_at'] = df2_temp['requested_at'].apply(lambda x:x.strftime('%Y-%m-%d'))
    #if among is not None:
    #    df2_temp = df2_temp[df2_temp['user_id'].apply(lambda x: x in among)]

    counts = []
    ids = []
    for i, date in enumerate(dates):
        date = pd.to_datetime(np.array(date))
        active_user_ids = set(df2_temp[(df2_temp['requested_at']>=date[0])&(df2_temp['requested_at']<=date[1])]['user_id'].values)
        if among is not None:
            active_user_ids = active_user_ids.intersection(among[i])
        # count = 0
        # date_range = set([x.strftime('%Y-%m-%d') for x in pd.date_range(start=date[0], end=date[1], freq='D')])
        # for _,g in df2_temp.groupby('user_id'):
        #     if len(date_range.intersection(set(g['requested_at'].values)))>0:
        #         count += 1
        # counts.append(count)
        ids.append(active_user_ids)
        counts.append(len(active_user_ids))

    return np.array(counts), ids


@st.cache_data
def continuous_active_users(dates, unit, n, among=None):
    df2_temp = df2[df2['username_persistent']!='Anonymous'].copy()
    df2_temp['requested_at'] = df2_temp['requested_at'].dt.normalize()
    #df2_temp = df2_temp[df2_temp['requested_at']>=pd.to_datetime(dates[0][0])-pd.Timedelta(days=31)]
    df2_temp = df2_temp.drop_duplicates(['user_id','requested_at'])
    #df2_temp['requested_at'] = df2_temp['requested_at'].apply(lambda x:x.strftime('%Y-%m-%d'))
    #if among is not None:
    #    df2_temp = df2_temp[df2_temp['user_id'].apply(lambda x: x in among)]

    if unit=='Day':
        unit = 1
    elif unit=='Week':
        unit = 7
    else:
        unit = 30

    counts = []
    ids = []
    already_included = set()
    for date in dates:
        date = pd.to_datetime(np.array(date))
        continuous_user_ids = set()
        for day in pd.date_range(start=date[0], end=date[1], freq='D'):
            temp = []
            for i in range(n):
                temp.append(set(df2_temp[(df2_temp['requested_at']>day-pd.Timedelta(days=unit*(i+1)))&(df2_temp['requested_at']<=day-pd.Timedelta(days=unit*i))]['user_id'].values))
            continuous_user_ids = continuous_user_ids.union(set.intersection(*temp))
            
        continuous_user_ids = continuous_user_ids-already_included
        counts.append(len(continuous_user_ids))
        ids.append(continuous_user_ids)
        already_included = already_included.union(continuous_user_ids)
    return np.array(counts), ids

@st.cache_data
def churned_users(dates, churning_threshold=30):
    counts = []
    ids = []

    already_churned = set()
    date0 = pd.to_datetime(np.array(dates[0]))
    length = pd.Timedelta(days=(date0[1]-date0[0]).days+1)
    for day in pd.date_range(start=date0[0]-length, end=date0[1]-length, freq='D'):
        already_churned = already_churned.union(set(df1[df1['last_login'].dt.normalize()<day-pd.Timedelta(days=churning_threshold)]['id'].values))
    
    for date in dates:
        date = pd.to_datetime(np.array(date))
        churned_user_ids = set()
        for day in pd.date_range(start=date[0], end=date[1], freq='D'):
            churned_user_ids = churned_user_ids.union(set(df1[df1['last_login'].dt.normalize()<day-pd.Timedelta(days=churning_threshold)]['id'].values))
        churned_user_ids = churned_user_ids-already_churned
        counts.append(len(churned_user_ids))
        ids.append(churned_user_ids)
        already_churned = already_churned.union(churned_user_ids)
    return np.array(counts), ids

@st.cache_data
def rurr(dates):
    df2_temp = df2[df2['username_persistent']!='Anonymous'].copy()
    df2_temp['requested_at'] = df2_temp['requested_at'].dt.normalize()
    #df2_temp = df2_temp[df2_temp['requested_at']>=pd.to_datetime(dates[0][0])-pd.Timedelta(days=31)]
    df2_temp = df2_temp.drop_duplicates(['user_id','requested_at'])
    
    rurrs = []
    for date in dates:
        date = pd.to_datetime(np.array(date))
        freq = (date[1]-date[0]).days+1

        reactivated_user_count = 0
        return_reactivated_user_count = 0
        for _,g in df2_temp.groupby('user_id'):
            if len(g[(g['requested_at']>=date[0]-pd.Timedelta(days=freq))&(g['requested_at']<=date[1]-pd.Timedelta(days=freq))])==0:
                continue
            if len(g[(g['requested_at']>=date[0]-pd.Timedelta(days=freq*2))&(g['requested_at']<=date[1]-pd.Timedelta(days=freq*2))])>0:
                continue
            if len(g[g['requested_at']<date[1]-pd.Timedelta(days=freq*2)])==0:
                continue
            reactivated_user_count += 1
            if len(g[(g['requested_at']>=date[0])&(g['requested_at']<=date[1])])>0:
                return_reactivated_user_count += 1
        if reactivated_user_count==0:
            rurrs.append(0)
        else:
            rurrs.append(return_reactivated_user_count/reactivated_user_count)
    return np.array(rurrs)

@st.cache_data
def get_reactivated_users(dates, reactive_period=0, inactive_period=0, previous_active_period=0):
    df2_temp = df2[df2['username_persistent']!='Anonymous'].copy()
    df2_temp['requested_at'] = df2_temp['requested_at'].dt.normalize()
    #df2_temp = df2_temp[df2_temp['requested_at']>=pd.to_datetime(dates[0][0])-pd.Timedelta(days=31)]
    df2_temp = df2_temp.drop_duplicates(['user_id','requested_at'])
    
    reactivated_users = []
    for date in dates:
        date = pd.to_datetime(np.array(date))
        if reactive_period == 0:
            reactive_period = (date[1]-date[0]).days+1
        if inactive_period == 0:
            inactive_period = (date[1]-date[0]).days+1
        if previous_active_period == 0:
            previous_active_period = (date[1]-date[0]).days+1

        reactivated_user_set = set()
        if reactive_period==1:
            for day in pd.date_range(start=date[0], end=date[1], freq='D'):
                active_this_period = set(df2_temp[df2_temp['requested_at']==day]['user_id'].values)
                active_previous_period = set(df2_temp[((df2_temp['requested_at']>=day-pd.Timedelta(days=inactive_period))&(df2_temp['requested_at']<day))]['user_id'].values)
                if previous_active_period == -1:
                    active_before_previous_period = set(df2_temp[df2_temp['requested_at']<day-pd.Timedelta(days=inactive_period)]['user_id'].values)
                else:
                    active_before_previous_period = set(df2_temp[(df2_temp['requested_at']>=day-pd.Timedelta(days=inactive_period+previous_active_period))&(df2_temp['requested_at']<day-pd.Timedelta(days=inactive_period))]['user_id'].values)
        else:
            active_this_period = set(df2_temp[(df2_temp['requested_at']>=date[0])&(df2_temp['requested_at']<=date[1])]['user_id'].values)
            active_previous_period = set(df2_temp[((df2_temp['requested_at']>=date[0]-pd.Timedelta(days=inactive_period))&(df2_temp['requested_at']<=date[1]-pd.Timedelta(days=inactive_period)))]['user_id'].values)
            if previous_active_period == -1:
                active_before_previous_period = set(df2_temp[df2_temp['requested_at']<date[0]-pd.Timedelta(days=inactive_period)]['user_id'].values)
            else:
                active_before_previous_period = set(df2_temp[(df2_temp['requested_at']>=date[0]-pd.Timedelta(days=inactive_period+previous_active_period))&(df2_temp['requested_at']<date[0]-pd.Timedelta(days=inactive_period))]['user_id'].values)
        reactivated_user_set = reactivated_user_set.union((active_this_period-active_previous_period).intersection(active_before_previous_period))
        reactivated_users.append(reactivated_user_set)
    return reactivated_users


@st.cache_data
def engagement_rate(dates):
    return active_users(dates)[0]/registered_users([date[1] for date in dates])

@st.cache_data
def activation_rate(dates):
    new_user_counts, new_user_ids = new_users(dates)
    return active_users(dates, new_user_ids)[0]/new_user_counts

@st.cache_data
def moving_average(arr, window_size=0):
    if window_size<=1:
        return arr
    numbers_series = pd.Series(arr)
    windows = numbers_series.rolling(window_size)
    moving_averages = windows.mean()
    moving_averages_list = moving_averages.tolist()
    final_list = np.array(moving_averages_list[window_size - 1:])
    return final_list

def get_dates(start,end,freq):
    if freq=='Daily':
        date_range_end = pd.date_range(start=start, end=end, freq='D')
        date_range_start = date_range_end
    elif freq=='Weekly':
        date_range_end = pd.date_range(start=start, end=end, freq='W-SUN')
        date_range_start = [x-pd.Timedelta(days=6) for x in date_range_end]
    elif freq=='Bi-weekly':
        date_range_end = pd.date_range(start=start, end=end, freq='2W-SUN')
        date_range_start = [x-pd.Timedelta(days=13) for x in date_range_end]
    else:
        date_range_end = pd.date_range(start=start, end=end, freq='M')
        date_range_start = pd.to_datetime(date_range_end.to_numpy().astype('datetime64[M]'))

    date_range_start_str = np.array([x.strftime('%Y-%m-%d') for x in date_range_start])
    date_range_end_str = np.array([x.strftime('%Y-%m-%d') for x in date_range_end])
    date_range_str = np.array(list(zip(date_range_start_str,date_range_end_str)))
    return date_range_start, date_range_end, date_range_str


default_to = pd.to_datetime((pd.Timestamp.today()-pd.Timedelta(days=2)).date())
default_from = default_to-pd.Timedelta(days=63)


au_expander = st.expander("Active Users")
au_col1, au_col2, au_col3 = au_expander.columns(3)
au_from = au_col1.date_input(label="From",value=default_from,key='au_from')
au_to = au_col2.date_input(label="To",value=default_to,key='au_to')
au_freq = au_col3.selectbox('Time frame',('Daily', 'Weekly', 'Bi-weekly', 'Monthly'),index=1,key='au_freq')
au_yrange = au_expander.slider("Y-axis range", value=(0, 500), min_value=0, max_value=2000, step=100, key='au_yrange')

date_range_start, date_range_end, date_range_str = get_dates(au_from,au_to,au_freq)
active_user_counts = active_users(date_range_str)[0]

fig = go.Figure()

if au_freq=='Daily':
    x = [x.strftime('%b-%d %a') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=active_user_counts, name='DAU'))
    fig.update_layout(xaxis_title='Day',yaxis_title='Active Users')
elif au_freq=='Weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=active_user_counts, name='WAU'))
    fig.update_layout(xaxis_title='Week',yaxis_title='Active Users')
elif au_freq=='Bi-weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=active_user_counts, name='2WAU'))
    fig.update_layout(xaxis_title='Bi-week',yaxis_title='Active Users')
else:
    x = [x.strftime('%Y %b') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=active_user_counts, name='MAU'))
    fig.update_layout(xaxis_title='Month',yaxis_title='Active Users')

if show_trends:
    if au_freq=='Daily':
        extra_range_start, extra_range_end, extra_range_str = get_dates(au_from-pd.Timedelta(days=daily_window_size-1),au_from,au_freq)
        active_user_trend = moving_average(list(active_users(extra_range_str)[0])+list(active_user_counts),window_size=daily_window_size)[-len(active_user_counts):]
    elif au_freq=='Weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(au_from-pd.Timedelta(days=(weekly_window_size-1)*7),au_from,au_freq)
        active_user_trend = moving_average(list(active_users(extra_range_str)[0])+list(active_user_counts),window_size=weekly_window_size)[-len(active_user_counts):]
    elif au_freq=='Bi-weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(au_from-pd.Timedelta(days=(biweekly_window_size-1)*14),au_from,au_freq)
        active_user_trend = moving_average(list(active_users(extra_range_str)[0])+list(active_user_counts),window_size=biweekly_window_size)[-len(active_user_counts):]
    else:
        extra_range_start, extra_range_end, extra_range_str = get_dates(au_from-pd.Timedelta(days=(monthly_window_size-1)*31),au_from,au_freq)
        active_user_trend = moving_average(list(active_users(extra_range_str)[0])+list(active_user_counts),window_size=monthly_window_size)[-len(active_user_counts):]
    fig.add_trace(go.Scatter(x=x, y=active_user_trend, name='Trend', line=dict(color='firebrick', dash='dash')))

fig.update_layout(legend=dict(yanchor="top",y=1.2,xanchor="left",x=0.01))
fig.update_yaxes(range=au_yrange)
au_expander.plotly_chart(fig, use_container_width=True)





cau_expander = st.expander("Continuous Active Users")
cau_col1, cau_col2, cau_col3 = cau_expander.columns(3)
cau_from = cau_col1.date_input(label="From",value=default_from,key='cau_from')
cau_to = cau_col2.date_input(label="To",value=default_to,key='cau_to')
cau_freq = cau_col3.selectbox('Time frame',('Daily', 'Weekly', 'Bi-weekly', 'Monthly'),index=1,key='cau_freq')

cau_col5, cau_col6 = cau_expander.columns(2)
cau_n = cau_col5.number_input('Continuous #', value=2,min_value=2, max_value=30, step=1, key='cau_n')
cau_unit = cau_col6.selectbox('Time unit',('Day', 'Week', 'Month'),index=1,key='cau_unit')
cau_yrange = cau_expander.slider("Y-axis range", value=(0, 200), min_value=0, max_value=1000, step=10, key='cau_yrange')

date_range_start, date_range_end, date_range_str = get_dates(cau_from,cau_to,cau_freq)
cau = continuous_active_users(date_range_str,cau_unit,cau_n)[0]

fig = go.Figure()
if cau_freq=='Daily':
    x = [x.strftime('%b-%d %a') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=cau, name='Daily Continuous Active Users'))
    fig.update_layout(xaxis_title='Day',yaxis_title='Continuous Active Users')
elif cau_freq=='Weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=cau, name='Weekly Continuous Active Users'))
    fig.update_layout(xaxis_title='Week',yaxis_title='Continuous Active Users')
elif cau_freq=='Bi-weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=cau, name='Bi-weekly Continuous Active Users'))
    fig.update_layout(xaxis_title='Bi-week',yaxis_title='Continuous Active Users')
else:
    x = [x.strftime('%Y %b') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=cau, name='Monthly Continuous Active Users'))
    fig.update_layout(xaxis_title='Month',yaxis_title='Continuous Active Users')

if show_trends:
    if cau_freq=='Daily':
        extra_range_start, extra_range_end, extra_range_str = get_dates(cau_from-pd.Timedelta(days=daily_window_size-1),cau_from,cau_freq)
        cau_trend = moving_average(list(continuous_active_users(extra_range_str,cau_unit,cau_n)[0])+list(cau),window_size=daily_window_size)[-len(cau):]
    elif cau_freq=='Weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(cau_from-pd.Timedelta(days=(weekly_window_size-1)*7),cau_from,cau_freq)
        cau_trend = moving_average(list(continuous_active_users(extra_range_str,cau_unit,cau_n)[0])+list(cau),window_size=weekly_window_size)[-len(cau):]
    elif cau_freq=='Bi-weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(cau_from-pd.Timedelta(days=(biweekly_window_size-1)*14),cau_from,cau_freq)
        cau_trend = moving_average(list(continuous_active_users(extra_range_str,cau_unit,cau_n)[0])+list(cau),window_size=biweekly_window_size)[-len(cau):]
    else:
        extra_range_start, extra_range_end, extra_range_str = get_dates(cau_from-pd.Timedelta(days=(monthly_window_size-1)*31),cau_from,cau_freq)
        cau_trend = moving_average(list(continuous_active_users(extra_range_str,cau_unit,cau_n)[0])+list(cau),window_size=monthly_window_size)[-len(cau):]
    fig.add_trace(go.Scatter(x=x, y=cau_trend, name='Trend', line=dict(color='firebrick', dash='dash')))

fig.update_layout(legend=dict(yanchor="top",y=1.2,xanchor="left",x=0.01))
fig.update_yaxes(range=cau_yrange)
cau_expander.plotly_chart(fig, use_container_width=True)




cu_expander = st.expander("Churned Users")
cu_col1, cu_col2, cu_col3 = cu_expander.columns(3)
cu_from = cu_col1.date_input(label="From",value=default_from,key='cu_from')
cu_to = cu_col2.date_input(label="To",value=default_to,key='cu_to')
cu_freq = cu_col3.selectbox('Time frame',('Daily', 'Weekly', 'Bi-weekly', 'Monthly'),index=1,key='cu_freq')
cu_yrange = cu_expander.slider("Y-axis range", value=(0, 500), min_value=0, max_value=1000, step=50, key='cu_yrange')

date_range_start, date_range_end, date_range_str = get_dates(cu_from,cu_to,cu_freq)
churned_user_counts = churned_users(date_range_str,churning_threshold)[0]

fig = go.Figure()
if cu_freq=='Daily':
    x = [x.strftime('%b-%d %a') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=churned_user_counts, name='Daily Churned Users'))
    fig.update_layout(xaxis_title='Day',yaxis_title='Churned Users')
elif cu_freq=='Weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=churned_user_counts, name='Weekly Churned Users'))
    fig.update_layout(xaxis_title='Week',yaxis_title='Churned Users')
elif cu_freq=='Bi-weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=churned_user_counts, name='Bi-weekly Churned Users'))
    fig.update_layout(xaxis_title='Bi-week',yaxis_title='Churned Users')
else:
    x = [x.strftime('%Y %b') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=churned_user_counts, name='Monthly Churned Users'))
    fig.update_layout(xaxis_title='Month',yaxis_title='Churned Users')

if show_trends:
    if cu_freq=='Daily':
        extra_range_start, extra_range_end, extra_range_str = get_dates(cu_from-pd.Timedelta(days=daily_window_size-1),cu_from,cu_freq)
        churned_users_trend = moving_average(list(churned_users(extra_range_str,churning_threshold)[0])+list(churned_user_counts),window_size=daily_window_size)[-len(churned_user_counts):]
    elif cu_freq=='Weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(cu_from-pd.Timedelta(days=(weekly_window_size-1)*7),cu_from,cu_freq)
        churned_users_trend = moving_average(list(churned_users(extra_range_str,churning_threshold)[0])+list(churned_user_counts),window_size=weekly_window_size)[-len(churned_user_counts):]
    elif cu_freq=='Bi-weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(cu_from-pd.Timedelta(days=(biweekly_window_size-1)*14),cu_from,cu_freq)
        churned_users_trend = moving_average(list(churned_users(extra_range_str,churning_threshold)[0])+list(churned_user_counts),window_size=biweekly_window_size)[-len(churned_user_counts):]
    else:
        extra_range_start, extra_range_end, extra_range_str = get_dates(cu_from-pd.Timedelta(days=(monthly_window_size-1)*31),cu_from,cu_freq)
        churned_users_trend = moving_average(list(churned_users(extra_range_str,churning_threshold)[0])+list(churned_user_counts),window_size=monthly_window_size)[-len(churned_user_counts):]
    fig.add_trace(go.Scatter(x=x, y=churned_users_trend, name='Trend', line=dict(color='firebrick', dash='dash')))

fig.update_layout(legend=dict(yanchor="top",y=1.2,xanchor="left",x=0.01))
fig.update_yaxes(range=cu_yrange)
cu_expander.plotly_chart(fig, use_container_width=True)



nsu_expander = st.expander("New Subscription Users")
nsu_col1, nsu_col2, nsu_col3, nsu_col4 = nsu_expander.columns(4)
nsu_from = nsu_col1.date_input(label="From",value=default_from,key='nsu_from')
nsu_to = nsu_col2.date_input(label="To",value=default_to,key='nsu_to')
nsu_freq = nsu_col3.selectbox('Time frame',('Daily', 'Weekly', 'Bi-weekly', 'Monthly'),index=1,key='nsu_freq')
nsu_duration = nsu_col4.selectbox('Subscription length',('1 month', '6 month', '12 month', 'All length'),index=3,key='nsu_duration')
nsu_yrange = nsu_expander.slider("Y-axis range", value=(0, 10), min_value=0, max_value=100, step=5, key='nsu_yrange')

date_range_start, date_range_end, date_range_str = get_dates(nsu_from,nsu_to,nsu_freq)

if nsu_duration=='1 month':
    duration = 1
elif nsu_duration=='6 month':
    duration = 6
elif nsu_duration=='12 month':
    duration = 12
else:
    duration = 0
nsu = new_subscription_users(date_range_str,duration)[0]

fig = go.Figure()
if nsu_freq=='Daily':
    x = [x.strftime('%b-%d %a') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=nsu, name=f'New Subscription Users ({nsu_duration})'))
    fig.update_layout(xaxis_title='Day',yaxis_title="New Subscription Users")
elif nsu_freq=='Weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=nsu, name=f'New Subscription Users ({nsu_duration})'))
    fig.update_layout(xaxis_title='Week',yaxis_title="New Subscription Users")
elif nsu_freq=='Bi-weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=nsu, name=f'New Subscription Users ({nsu_duration})'))
    fig.update_layout(xaxis_title='bi-week',yaxis_title="New Subscription Users")
else:
    x = [x.strftime('%Y %b') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=nsu, name=f'New Subscription Users ({nsu_duration})'))
    fig.update_layout(xaxis_title='Month',yaxis_title="New Subscription Users")


if show_trends:
    if nsu_freq=='Daily':
        extra_range_start, extra_range_end, extra_range_str = get_dates(nsu_from-pd.Timedelta(days=daily_window_size-1),nsu_from,nsu_freq)
        nsu_trend = moving_average(list(new_subscription_users(extra_range_str,duration)[0])+list(nsu),window_size=daily_window_size)[-len(nsu):]
    elif nsu_freq=='Weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(nsu_from-pd.Timedelta(days=(weekly_window_size-1)*7),nsu_from,nsu_freq)
        nsu_trend = moving_average(list(new_subscription_users(extra_range_str,duration)[0])+list(nsu),window_size=weekly_window_size)[-len(nsu):]
    elif nsu_freq=='Bi-weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(nsu_from-pd.Timedelta(days=(biweekly_window_size-1)*14),nsu_from,nsu_freq)
        nsu_trend = moving_average(list(new_subscription_users(extra_range_str,duration)[0])+list(nsu),window_size=biweekly_window_size)[-len(nsu):]
    else:
        extra_range_start, extra_range_end, extra_range_str = get_dates(nsu_from-pd.Timedelta(days=(monthly_window_size-1)*31),nsu_from,nsu_freq)
        nsu_trend = moving_average(list(new_subscription_users(extra_range_str,duration)[0])+list(nsu),window_size=monthly_window_size)[-len(nsu):]
    fig.add_trace(go.Scatter(x=x, y=nsu_trend, name='Trend', line=dict(color='firebrick', dash='dash')))

fig.update_layout(legend=dict(yanchor="top",y=1.2,xanchor="left",x=0.01))
fig.update_yaxes(range=nsu_yrange)
nsu_expander.plotly_chart(fig, use_container_width=True)



nu_expander = st.expander("New Users")
nu_col1, nu_col2, nu_col3 = nu_expander.columns(3)
nu_from = nu_col1.date_input(label="From",value=default_from,key='nu_from')
nu_to = nu_col2.date_input(label="To",value=default_to,key='nu_to')
nu_freq = nu_col3.selectbox('Time frame',('Daily', 'Weekly', 'Bi-weekly', 'Monthly'),index=1,key='nu_freq')
nu_yrange = nu_expander.slider("Y-axis range", value=(0, 500), min_value=0, max_value=2000, step=50, key='nu_yrange')

date_range_start, date_range_end, date_range_str = get_dates(nu_from,nu_to,nu_freq)
new_user_counts = new_users(date_range_str)[0]

fig = go.Figure()
if nu_freq=='Daily':
    x = [x.strftime('%b-%d %a') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=new_user_counts, name='DNU'))
    fig.update_layout(xaxis_title='Day',yaxis_title='New Users')
elif nu_freq=='Weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=new_user_counts, name='WNU'))
    fig.update_layout(xaxis_title='Week',yaxis_title='New Users')
elif nu_freq=='Bi-weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=new_user_counts, name='WNU'))
    fig.update_layout(xaxis_title='Bi-week',yaxis_title='New Users')
else:
    x = [x.strftime('%Y %b') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=new_user_counts, name='WNU'))
    fig.update_layout(xaxis_title='Month',yaxis_title='New Users')

if show_trends:
    if nu_freq=='Daily':
        extra_range_start, extra_range_end, extra_range_str = get_dates(nu_from-pd.Timedelta(days=daily_window_size-1),nu_from,nu_freq)
        new_user_trend = moving_average(list(new_users(extra_range_str)[0])+list(new_user_counts),window_size=daily_window_size)[-len(new_user_counts):]
    elif nu_freq=='Weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(nu_from-pd.Timedelta(days=(weekly_window_size-1)*7),nu_from,nu_freq)
        new_user_trend = moving_average(list(new_users(extra_range_str)[0])+list(new_user_counts),window_size=weekly_window_size)[-len(new_user_counts):]
    elif nu_freq=='Bi-weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(nu_from-pd.Timedelta(days=(biweekly_window_size-1)*14),nu_from,nu_freq)
        new_user_trend = moving_average(list(new_users(extra_range_str)[0])+list(new_user_counts),window_size=biweekly_window_size)[-len(new_user_counts):]
    else:
        extra_range_start, extra_range_end, extra_range_str = get_dates(nu_from-pd.Timedelta(days=(monthly_window_size-1)*31),nu_from,nu_freq)
        new_user_trend = moving_average(list(new_users(extra_range_str)[0])+list(new_user_counts),window_size=monthly_window_size)[-len(new_user_counts):]
    fig.add_trace(go.Scatter(x=x, y=new_user_trend, name='Trend', line=dict(color='firebrick', dash='dash')))

fig.update_layout(legend=dict(yanchor="top",y=1.2,xanchor="left",x=0.01))
fig.update_yaxes(range=nu_yrange)
nu_expander.plotly_chart(fig, use_container_width=True)




rau_expander = st.expander("Reactivated Users")
rau_col1, rau_col2, rau_col3 = rau_expander.columns(3)
rau_from = rau_col1.date_input(label="From",value=default_from,key='rau_from')
rau_to = rau_col2.date_input(label="To",value=default_to,key='rau_to')
rau_freq = rau_col3.selectbox('Time frame',('Daily', 'Weekly', 'Bi-weekly', 'Monthly'),index=1,key='rau_freq')
rau_yrange = rau_expander.slider("Y-axis range", value=(0, 50), min_value=0, max_value=200, step=10, key='rau_yrange')

date_range_start, date_range_end, date_range_str = get_dates(rau_from,rau_to,rau_freq)
reactivated_user_counts = np.array([len(x) for x in get_reactivated_users(date_range_str, reactive_period, inactive_period, previous_active_period)])

fig = go.Figure()
if rau_freq=='Daily':
    x = [x.strftime('%b-%d %a') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=reactivated_user_counts, name='Reactivated Users'))
    fig.update_layout(xaxis_title='Day',yaxis_title='Reactivated Users')
elif rau_freq=='Weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=reactivated_user_counts, name='Reactivated Users'))
    fig.update_layout(xaxis_title='Week',yaxis_title='Reactivated Users')
elif rau_freq=='Bi-weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=reactivated_user_counts, name='Reactivated Users'))
    fig.update_layout(xaxis_title='Bi-week',yaxis_title='Reactivated Users')
else:
    x = [x.strftime('%Y %b') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=reactivated_user_counts, name='Reactivated Users'))
    fig.update_layout(xaxis_title='Month',yaxis_title='Reactivated Users')

if show_trends:
    if rau_freq=='Daily':
        extra_range_start, extra_range_end, extra_range_str = get_dates(rau_from-pd.Timedelta(days=daily_window_size-1),rau_from,rau_freq)
        reactivated_user_trend = moving_average([len(x) for x in get_reactivated_users(extra_range_str, reactive_period, inactive_period, previous_active_period)]+list(reactivated_user_counts),window_size=daily_window_size)[-len(reactivated_user_counts):]
    elif rau_freq=='Weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(rau_from-pd.Timedelta(days=(weekly_window_size-1)*7),rau_from,rau_freq)
        reactivated_user_trend = moving_average([len(x) for x in get_reactivated_users(extra_range_str, reactive_period, inactive_period, previous_active_period)]+list(reactivated_user_counts),window_size=weekly_window_size)[-len(reactivated_user_counts):]
    elif rau_freq=='Bi-weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(rau_from-pd.Timedelta(days=(biweekly_window_size-1)*14),rau_from,rau_freq)
        reactivated_user_trend = moving_average([len(x) for x in get_reactivated_users(extra_range_str, reactive_period, inactive_period, previous_active_period)]+list(reactivated_user_counts),window_size=biweekly_window_size)[-len(reactivated_user_counts):]
    else:
        extra_range_start, extra_range_end, extra_range_str = get_dates(rau_from-pd.Timedelta(days=(monthly_window_size-1)*31),rau_from,rau_freq)
        reactivated_user_trend = moving_average([len(x) for x in get_reactivated_users(extra_range_str, reactive_period, inactive_period, previous_active_period)]+list(reactivated_user_counts),window_size=monthly_window_size)[-len(reactivated_user_counts):]
    fig.add_trace(go.Scatter(x=x, y=reactivated_user_trend, name='Trend', line=dict(color='firebrick', dash='dash')))

fig.update_layout(legend=dict(yanchor="top",y=1.2,xanchor="left",x=0.01))
fig.update_yaxes(range=rau_yrange)
rau_expander.plotly_chart(fig, use_container_width=True)




rsu_expander = st.expander("Resurrected Users")
rsu_col1, rsu_col2, rsu_col3 = rsu_expander.columns(3)
rsu_from = rsu_col1.date_input(label="From",value=default_from,key='rsu_from')
rsu_to = rsu_col2.date_input(label="To",value=default_to,key='rsu_to')
rsu_freq = rsu_col3.selectbox('Time frame',('Daily', 'Weekly', 'Bi-weekly', 'Monthly'),index=1,key='rsu_freq')
rsu_yrange = rsu_expander.slider("Y-axis range", value=(0, 50), min_value=0, max_value=200, step=10, key='rsu_yrange')

date_range_start, date_range_end, date_range_str = get_dates(rsu_from,rsu_to,rsu_freq)
reactivated_user_counts = np.array([len(x) for x in get_reactivated_users(date_range_str,reactive_period=resurrect_period,inactive_period=dormant_period,previous_active_period=-1)])

fig = go.Figure()
if rsu_freq=='Daily':
    x = [x.strftime('%b-%d %a') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=reactivated_user_counts, name='Daily Resurrected Users'))
    fig.update_layout(xaxis_title='Day',yaxis_title='Resurrected Users')
elif rsu_freq=='Weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=reactivated_user_counts, name='Weekly Resurrected Users'))
    fig.update_layout(xaxis_title='Week',yaxis_title='Resurrected Users')
elif rsu_freq=='Bi-weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=reactivated_user_counts, name='Bi-weekly Resurrected Users'))
    fig.update_layout(xaxis_title='Bi-week',yaxis_title='Resurrected Users')
else:
    x = [x.strftime('%Y %b') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=reactivated_user_counts, name='Monthly Resurrected Users'))
    fig.update_layout(xaxis_title='Month',yaxis_title='Resurrected Users')

if show_trends:
    if rsu_freq=='Daily':
        extra_range_start, extra_range_end, extra_range_str = get_dates(rsu_from-pd.Timedelta(days=daily_window_size-1),rsu_from,rsu_freq)
        reactivated_user_trend = moving_average([len(x) for x in get_reactivated_users(extra_range_str,reactive_period=resurrect_period,inactive_period=dormant_period,previous_active_period=-1)]+list(reactivated_user_counts),window_size=daily_window_size)[-len(reactivated_user_counts):]
    elif rsu_freq=='Weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(rsu_from-pd.Timedelta(days=(weekly_window_size-1)*7),rsu_from,rsu_freq)
        reactivated_user_trend = moving_average([len(x) for x in get_reactivated_users(extra_range_str,reactive_period=resurrect_period,inactive_period=dormant_period,previous_active_period=-1)]+list(reactivated_user_counts),window_size=weekly_window_size)[-len(reactivated_user_counts):]
    elif rsu_freq=='Bi-weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(rsu_from-pd.Timedelta(days=(biweekly_window_size-1)*14),rsu_from,rsu_freq)
        reactivated_user_trend = moving_average([len(x) for x in get_reactivated_users(extra_range_str,reactive_period=resurrect_period,inactive_period=dormant_period,previous_active_period=-1)]+list(reactivated_user_counts),window_size=biweekly_window_size)[-len(reactivated_user_counts):]
    else:
        extra_range_start, extra_range_end, extra_range_str = get_dates(rsu_from-pd.Timedelta(days=(monthly_window_size-1)*31),rsu_from,rsu_freq)
        reactivated_user_trend = moving_average([len(x) for x in get_reactivated_users(extra_range_str,reactive_period=resurrect_period,inactive_period=dormant_period,previous_active_period=-1)]+list(reactivated_user_counts),window_size=monthly_window_size)[-len(reactivated_user_counts):]
    fig.add_trace(go.Scatter(x=x, y=reactivated_user_trend, name='Trend', line=dict(color='firebrick', dash='dash')))

fig.update_layout(legend=dict(yanchor="top",y=1.2,xanchor="left",x=0.01))
fig.update_yaxes(range=rsu_yrange)
rsu_expander.plotly_chart(fig, use_container_width=True)







tu_expander = st.expander("Trial Users")
tu_col1, tu_col2, tu_col3 = tu_expander.columns(3)
tu_from = tu_col1.date_input(label="From",value=default_from,key='tu_from')
tu_to = tu_col2.date_input(label="To",value=default_to,key='tu_to')
tu_freq = tu_col3.selectbox('Time frame',('Daily', 'Weekly', 'Bi-weekly', 'Monthly'),index=1,key='tu_freq')
tu_yrange = tu_expander.slider("Y-axis range", value=(0, 1000), min_value=0, max_value=4000, step=50, key='tu_yrange')

date_range_start, date_range_end, date_range_str = get_dates(tu_from,tu_to,tu_freq)
trial_user_counts = trial_users(date_range_str)

fig = go.Figure()
if tu_freq=='Daily':
    x = [x.strftime('%b-%d %a') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=trial_user_counts, name='Daily Trial Users'))
    fig.update_layout(xaxis_title='Day',yaxis_title='Trial Users')
elif tu_freq=='Weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=trial_user_counts, name='Weekly Trial Users'))
    fig.update_layout(xaxis_title='Week',yaxis_title='Trial Users')
elif tu_freq=='Bi-weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=trial_user_counts, name='Bi-weekly Trial Users'))
    fig.update_layout(xaxis_title='Bi-week',yaxis_title='Trial Users')
else:
    x = [x.strftime('%Y %b') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=trial_user_counts, name='Monthly Trial Users'))
    fig.update_layout(xaxis_title='Month',yaxis_title='Trial Users')

if show_trends:
    if tu_freq=='Daily':
        extra_range_start, extra_range_end, extra_range_str = get_dates(tu_from-pd.Timedelta(days=daily_window_size-1),tu_from,tu_freq)
        trial_user_trend = moving_average(list(trial_users(extra_range_str))+list(trial_user_counts),window_size=daily_window_size)[-len(trial_user_counts):]
    elif tu_freq=='Weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(tu_from-pd.Timedelta(days=(weekly_window_size-1)*7),tu_from,tu_freq)
        trial_user_trend = moving_average(list(trial_users(extra_range_str))+list(trial_user_counts),window_size=weekly_window_size)[-len(trial_user_counts):]
    elif tu_freq=='Bi-weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(tu_from-pd.Timedelta(days=(biweekly_window_size-1)*14),tu_from,tu_freq)
        trial_user_trend = moving_average(list(trial_users(extra_range_str))+list(trial_user_counts),window_size=biweekly_window_size)[-len(trial_user_counts):]
    else:
        extra_range_start, extra_range_end, extra_range_str = get_dates(tu_from-pd.Timedelta(days=(monthly_window_size-1)*31),tu_from,tu_freq)
        trial_user_trend = moving_average(list(trial_users(extra_range_str))+list(trial_user_counts),window_size=monthly_window_size)[-len(trial_user_counts):]
    fig.add_trace(go.Scatter(x=x, y=trial_user_trend, name='Trend', line=dict(color='firebrick', dash='dash')))

fig.update_layout(legend=dict(yanchor="top",y=1.2,xanchor="left",x=0.01))
fig.update_yaxes(range=tu_yrange)
tu_expander.plotly_chart(fig, use_container_width=True)




vu_expander = st.expander("Visitors")
vu_col1, vu_col2, vu_col3 = vu_expander.columns(3)
vu_from = vu_col1.date_input(label="From",value=default_from,key='vu_from')
vu_to = vu_col2.date_input(label="To",value=default_to,key='vu_to')
vu_freq = vu_col3.selectbox('Time frame',('Daily', 'Weekly', 'Bi-weekly', 'Monthly'),index=1,key='vu_freq')
vu_yrange = vu_expander.slider("Y-axis range", value=(0, 500), min_value=0, max_value=10000, step=50, key='vu_yrange')

date_range_start, date_range_end, date_range_str = get_dates(vu_from,vu_to,vu_freq)

vu = visitors(date_range_str)

fig = go.Figure()
if vu_freq=='Daily':
    x = [x.strftime('%b-%d %a') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=vu, name=f'Daily Visitors'))
    fig.update_layout(xaxis_title='Day',yaxis_title="Visitors")
elif vu_freq=='Weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=vu, name=f'Weekly Visitors'))
    fig.update_layout(xaxis_title='Week',yaxis_title="Visitors")
elif vu_freq=='Bi-weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=vu, name=f'Bi-weekly Visitors'))
    fig.update_layout(xaxis_title='bi-week',yaxis_title="Visitors")
else:
    x = [x.strftime('%Y %b') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=vu, name=f'Monthly Visitors'))
    fig.update_layout(xaxis_title='Month',yaxis_title="Visitors")


if show_trends:
    if vu_freq=='Daily':
        extra_range_start, extra_range_end, extra_range_str = get_dates(vu_from-pd.Timedelta(days=daily_window_size-1),vu_from,vu_freq)
        vu_trend = moving_average(list(visitors(extra_range_str))+list(vu),window_size=daily_window_size)[-len(vu):]
    elif vu_freq=='Weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(vu_from-pd.Timedelta(days=(weekly_window_size-1)*7),vu_from,vu_freq)
        vu_trend = moving_average(list(visitors(extra_range_str))+list(vu),window_size=weekly_window_size)[-len(vu):]
    elif vu_freq=='Bi-weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(vu_from-pd.Timedelta(days=(biweekly_window_size-1)*14),vu_from,vu_freq)
        vu_trend = moving_average(list(visitors(extra_range_str))+list(vu),window_size=biweekly_window_size)[-len(vu):]
    else:
        extra_range_start, extra_range_end, extra_range_str = get_dates(vu_from-pd.Timedelta(days=(monthly_window_size-1)*31),vu_from,vu_freq)
        vu_trend = moving_average(list(visitors(extra_range_str))+list(vu),window_size=monthly_window_size)[-len(vu):]
    fig.add_trace(go.Scatter(x=x, y=vu_trend, name='Trend', line=dict(color='firebrick', dash='dash')))

fig.update_layout(legend=dict(yanchor="top",y=1.2,xanchor="left",x=0.01))
fig.update_yaxes(range=vu_yrange)
vu_expander.plotly_chart(fig, use_container_width=True)





st.divider()


ar_expander = st.expander("Activation Rate")
ar_expander.write("New users who are active / New users")
ar_col1, ar_col2, ar_col3 = ar_expander.columns(3)
ar_from = ar_col1.date_input(label="From",value=default_from,key='ar_from')
ar_to = ar_col2.date_input(label="To",value=default_to,key='ar_to')
ar_freq = ar_col3.selectbox('Time frame',('Daily', 'Weekly', 'Bi-weekly', 'Monthly'),index=1,key='ar_freq')
ar_yrange = ar_expander.slider("Y-axis range", value=(0, 100), min_value=0, max_value=100, step=5, key='ar_yrange')

date_range_start, date_range_end, date_range_str = get_dates(ar_from,ar_to,ar_freq)
ar = np.round(activation_rate(date_range_str)*100,2)

fig = go.Figure()
if ar_freq=='Daily':
    x = [x.strftime('%b-%d %a') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=ar, name='Daily Activation Rate (%)'))
    fig.update_layout(xaxis_title='Day',yaxis_title='Activation Rate (%)')
elif ar_freq=='Weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=ar, name='Weekly Activation Rate (%)'))
    fig.update_layout(xaxis_title='Week',yaxis_title='Activation Rate (%)')
elif ar_freq=='Bi-weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=ar, name='Bi-weekly Activation Rate (%)'))
    fig.update_layout(xaxis_title='Bi-week',yaxis_title='Activation Rate (%)')
else:
    x = [x.strftime('%Y %b') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=ar, name='Monthly Activation Rate (%)'))
    fig.update_layout(xaxis_title='Month',yaxis_title='Activation Rate (%)')

if show_trends:
    if ar_freq=='Daily':
        extra_range_start, extra_range_end, extra_range_str = get_dates(ar_from-pd.Timedelta(days=daily_window_size-1),ar_from,ar_freq)
        extra_ar = np.round(activation_rate(extra_range_str)*100,2)
        ar_trend = moving_average(list(extra_ar)+list(ar),window_size=daily_window_size)[-len(ar):]
    elif ar_freq=='Weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(ar_from-pd.Timedelta(days=(weekly_window_size-1)*7),ar_from,ar_freq)
        extra_ar = np.round(activation_rate(extra_range_str)*100,2)
        ar_trend = moving_average(list(extra_ar)+list(ar),window_size=weekly_window_size)[-len(ar):]
    elif ar_freq=='Bi-weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(ar_from-pd.Timedelta(days=(biweekly_window_size-1)*14),ar_from,ar_freq)
        extra_ar = np.round(activation_rate(extra_range_str)*100,2)
        ar_trend = moving_average(list(extra_ar)+list(ar),window_size=biweekly_window_size)[-len(ar):]
    else:
        extra_range_start, extra_range_end, extra_range_str = get_dates(ar_from-pd.Timedelta(days=(monthly_window_size-1)*31),ar_from,ar_freq)
        extra_ar = np.round(activation_rate(extra_range_str)*100,2)
        ar_trend = moving_average(list(extra_ar)+list(ar),window_size=monthly_window_size)[-len(ar):]
    fig.add_trace(go.Scatter(x=x, y=ar_trend, name='Trend', line=dict(color='firebrick', dash='dash')))

fig.update_layout(legend=dict(yanchor="top",y=1.2,xanchor="left",x=0.01))
fig.update_yaxes(range=ar_yrange)
ar_expander.plotly_chart(fig, use_container_width=True)





er_expander = st.expander("Engagement Rate")
er_expander.write("Active users / All users")
er_col1, er_col2, er_col3 = er_expander.columns(3)
er_from = er_col1.date_input(label="From",value=default_from,key='er_from')
er_to = er_col2.date_input(label="To",value=default_to,key='er_to')
er_freq = er_col3.selectbox('Time frame',('Daily', 'Weekly', 'Bi-weekly', 'Monthly'),index=1,key='er_freq')
er_yrange = er_expander.slider("Y-axis range", value=(0, 50), min_value=0, max_value=100, step=5, key='er_yrange')

date_range_start, date_range_end, date_range_str = get_dates(er_from,er_to,er_freq)
er = np.round(engagement_rate(date_range_str)*100,2)

fig = go.Figure()
if er_freq=='Daily':
    x = [x.strftime('%b-%d %a') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=er, name='Daily Engagement Rate (%)'))
    fig.update_layout(xaxis_title='Day',yaxis_title='Engagement Rate (%)')
elif er_freq=='Weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=er, name='Weekly Engagement Rate (%)'))
    fig.update_layout(xaxis_title='Week',yaxis_title='Engagement Rate (%)')
elif er_freq=='Bi-weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=er, name='Bi-weekly Engagement Rate (%)'))
    fig.update_layout(xaxis_title='Bi-week',yaxis_title='Engagement Rate (%)')
else:
    x = [x.strftime('%Y %b') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=er, name='Monthly Engagement Rate (%)'))
    fig.update_layout(xaxis_title='Month',yaxis_title='Engagement Rate (%)')

if show_trends:
    if er_freq=='Daily':
        extra_range_start, extra_range_end, extra_range_str = get_dates(er_from-pd.Timedelta(days=daily_window_size-1),er_from,er_freq)
        extra_er = np.round(engagement_rate(extra_range_str)*100,2)
        er_trend = moving_average(list(extra_er)+list(er),window_size=daily_window_size)[-len(er):]
    elif er_freq=='Weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(er_from-pd.Timedelta(days=(weekly_window_size-1)*7),er_from,er_freq)
        extra_er = np.round(engagement_rate(extra_range_str)*100,2)
        er_trend = moving_average(list(extra_er)+list(er),window_size=weekly_window_size)[-len(er):]
    elif er_freq=='Bi-weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(er_from-pd.Timedelta(days=(biweekly_window_size-1)*14),er_from,er_freq)
        extra_er = np.round(engagement_rate(extra_range_str)*100,2)
        er_trend = moving_average(list(extra_er)+list(er),window_size=biweekly_window_size)[-len(er):]
    else:
        extra_range_start, extra_range_end, extra_range_str = get_dates(er_from-pd.Timedelta(days=(monthly_window_size-1)*31),er_from,er_freq)
        extra_er = np.round(engagement_rate(extra_range_str)*100,2)
        er_trend = moving_average(list(extra_er)+list(er_expander),window_size=monthly_window_size)[-len(er):]
    fig.add_trace(go.Scatter(x=x, y=er_trend, name='Trend', line=dict(color='firebrick', dash='dash')))

fig.update_layout(legend=dict(yanchor="top",y=1.2,xanchor="left",x=0.01))
fig.update_yaxes(range=er_yrange)
er_expander.plotly_chart(fig, use_container_width=True)





rgr_expander = st.expander("Registration Rate")
rgr_expander.write("Trial Users / New users")
rgr_col1, rgr_col2, rgr_col3 = rgr_expander.columns(3)
rgr_from = rgr_col1.date_input(label="From",value=default_from,key='rgr_from')
rgr_to = rgr_col2.date_input(label="To",value=default_to,key='rgr_to')
rgr_freq = rgr_col3.selectbox('Time frame',('Daily', 'Weekly', 'Bi-weekly', 'Monthly'),index=1,key='rgr_freq')
rgr_yrange = rgr_expander.slider("Y-axis range", value=(0, 100), min_value=0, max_value=100, step=5, key='rgr_yrange')

date_range_start, date_range_end, date_range_str = get_dates(rgr_from,rgr_to,rgr_freq)
rgr = np.round((new_users(date_range_str)[0]/trial_users(date_range_str))*100,2)

fig = go.Figure()
if rgr_freq=='Daily':
    x = [x.strftime('%b-%d %a') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=rgr, name='Daily Activation Rate (%)'))
    fig.update_layout(xaxis_title='Day',yaxis_title='Activation Rate (%)')
elif rgr_freq=='Weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=rgr, name='Weekly Activation Rate (%)'))
    fig.update_layout(xaxis_title='Week',yaxis_title='Activation Rate (%)')
elif rgr_freq=='Bi-weekly':
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=rgr, name='Bi-weekly Activation Rate (%)'))
    fig.update_layout(xaxis_title='Bi-week',yaxis_title='Activation Rate (%)')
else:
    x = [x.strftime('%Y %b') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=rgr, name='Monthly Activation Rate (%)'))
    fig.update_layout(xaxis_title='Month',yaxis_title='Activation Rate (%)')

if show_trends:
    if rgr_freq=='Daily':
        extra_range_start, extra_range_end, extra_range_str = get_dates(rgr_from-pd.Timedelta(days=daily_window_size-1),rgr_from,rgr_freq)
        extra_rgr = np.round((new_users(extra_range_str)[0]/trial_users(extra_range_str))*100,2)
        rgr_trend = moving_average(list(extra_rgr)+list(rgr),window_size=daily_window_size)[-len(rgr):]
    elif rgr_freq=='Weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(rgr_from-pd.Timedelta(days=(weekly_window_size-1)*7),rgr_from,rgr_freq)
        extra_rgr = np.round((new_users(extra_range_str)[0]/trial_users(extra_range_str))*100,2)
        rgr_trend = moving_average(list(extra_rgr)+list(rgr),window_size=weekly_window_size)[-len(rgr):]
    elif rgr_freq=='Bi-weekly':
        extra_range_start, extra_range_end, extra_range_str = get_dates(rgr_from-pd.Timedelta(days=(biweekly_window_size-1)*14),rgr_from,rgr_freq)
        extra_rgr = np.round((new_users(extra_range_str)[0]/trial_users(extra_range_str))*100,2)
        rgr_trend = moving_average(list(extra_rgr)+list(rgr),window_size=biweekly_window_size)[-len(rgr):]
    else:
        extra_range_start, extra_range_end, extra_range_str = get_dates(rgr_from-pd.Timedelta(days=(monthly_window_size-1)*31),rgr_from,rgr_freq)
        extra_rgr = np.round((new_users(extra_range_str)[0]/trial_users(extra_range_str))*100,2)
        rgr_trend = moving_average(list(extra_rgr)+list(rgr),window_size=monthly_window_size)[-len(rgr):]
    fig.add_trace(go.Scatter(x=x, y=rgr_trend, name='Trend', line=dict(color='firebrick', dash='dash')))

fig.update_layout(legend=dict(yanchor="top",y=1.2,xanchor="left",x=0.01))
fig.update_yaxes(range=rgr_yrange)
rgr_expander.plotly_chart(fig, use_container_width=True)





stickiness_expander = st.expander("Stickiness")
stickiness_expander.write("DAU/MAU or WAU/MAU")
stickiness_col1, stickiness_col2, stickiness_col3 = stickiness_expander.columns(3)
stickiness_from = stickiness_col1.date_input(label="From",value=default_from,key='stickiness_from')
stickiness_to = stickiness_col2.date_input(label="To",value=default_to,key='stickiness_to')
stickiness_freq = stickiness_col3.selectbox('Time frame',('Daily', 'Weekly'),index=1,key='stickiness_freq')
stickiness_yrange = stickiness_expander.slider("Y-axis range", value=(0, 100), min_value=0, max_value=100, step=5, key='stickiness_yrange')

date_range_start, date_range_end, date_range_str = get_dates(stickiness_from,stickiness_to,stickiness_freq)
month_range_start = [end-pd.Timedelta(days=29) for end in date_range_end]
month_range_start_str = np.array([x.strftime('%Y-%m-%d') for x in month_range_start])
month_range_end_str = np.array([x.strftime('%Y-%m-%d') for x in date_range_end])
month_range_str = np.array(list(zip(month_range_start_str,month_range_end_str)))
mau = active_users(month_range_str)[0]
au = active_users(date_range_str)[0]
stickiness = np.round(au/mau*100,2)

fig = go.Figure()
if stickiness_freq=='Daily':
    x = [x.strftime('%b-%d %a') for x in date_range_end]
    fig.add_trace(go.Scatter(x=x, y=stickiness, name='DAU/MAU (%)'))
    fig.update_layout(xaxis_title='Day',yaxis_title='DAU/MAU (%)')
else:
    x = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
    fig.add_trace(go.Scatter(x=x, y=stickiness, name='WAU/MAU (%)'))
    fig.update_layout(xaxis_title='Week',yaxis_title='WAU/MAU (%)')

if show_trends:
    if stickiness_freq=='Daily':
        extra_range_start, extra_range_end, extra_range_str = get_dates(stickiness_from-pd.Timedelta(days=daily_window_size-1),stickiness_from,stickiness_freq)
        extra_month_range_start = [end-pd.Timedelta(days=29) for end in extra_range_end]
        extra_month_range_start_str = np.array([x.strftime('%Y-%m-%d') for x in extra_month_range_start])
        extra_month_range_end_str = np.array([x.strftime('%Y-%m-%d') for x in extra_range_end])
        extra_month_range_str = np.array(list(zip(extra_month_range_start_str,extra_month_range_end_str)))
        extra_mau = active_users(extra_month_range_str)[0]
        extra_au = active_users(extra_range_str)[0]
        extra_stickiness = np.round(extra_au/extra_mau*100,2)
        stickiness_trend = moving_average(list(extra_stickiness)+list(stickiness),window_size=daily_window_size)[-len(stickiness):]
    else:
        extra_range_start, extra_range_end, extra_range_str = get_dates(stickiness_from-pd.Timedelta(days=(weekly_window_size-1)*7),stickiness_from,stickiness_freq)
        extra_month_range_start = [end-pd.Timedelta(days=29) for end in extra_range_end]
        extra_month_range_start_str = np.array([x.strftime('%Y-%m-%d') for x in extra_month_range_start])
        extra_month_range_end_str = np.array([x.strftime('%Y-%m-%d') for x in extra_range_end])
        extra_month_range_str = np.array(list(zip(extra_month_range_start_str,extra_month_range_end_str)))
        extra_mau = active_users(extra_month_range_str)[0]
        extra_au = active_users(extra_range_str)[0]
        extra_stickiness = np.round(extra_au/extra_mau*100,2)
        stickiness_trend = moving_average(list(extra_stickiness)+list(stickiness),window_size=weekly_window_size)[-len(stickiness):]
    fig.add_trace(go.Scatter(x=x, y=stickiness_trend, name='Trend', line=dict(color='firebrick', dash='dash')))

fig.update_layout(legend=dict(yanchor="top",y=1.2,xanchor="left",x=0.01))
fig.update_yaxes(range=stickiness_yrange)
stickiness_expander.plotly_chart(fig, use_container_width=True)



st.divider()


funnel_expander = st.expander("Funnel")
funnel_col1, funnel_col2 = funnel_expander.columns(2)
funnel_from = funnel_col1.date_input(label="From",value=default_from,key='funnel_from')
funnel_to = funnel_col2.date_input(label="To",value=default_to,key='funnel_to')

visitor_count = visitors([[funnel_from.strftime('%Y-%m-%d'),funnel_to.strftime('%Y-%m-%d')]])
trial_user_count = trial_users([[funnel_from.strftime('%Y-%m-%d'),funnel_to.strftime('%Y-%m-%d')]])
new_user_count, new_user_ids = new_users([[funnel_from.strftime('%Y-%m-%d'),funnel_to.strftime('%Y-%m-%d')]])
new_active_user_count, _ = active_users([[funnel_from.strftime('%Y-%m-%d'),funnel_to.strftime('%Y-%m-%d')]],new_user_ids)
subscription_user_count, _ = new_subscription_users([[funnel_from.strftime('%Y-%m-%d'),funnel_to.strftime('%Y-%m-%d')]])

fig = go.Figure(go.Funnel(
    y = ["Visitors","Trial Users", "New Users", "New Active Users", "New Subscription Users"],
    x = [visitor_count[0],trial_user_count[0], new_user_count[0], new_active_user_count[0], subscription_user_count[0]],
    textinfo = "value+percent initial",hoverinfo="x+y+percent initial+percent previous",texttemplate='+%{x:.2f}'))

funnel_expander.plotly_chart(fig, use_container_width=True)






st.divider()

curr_expander = st.expander("CURR")
curr_expander.write("Current user retention rate")
curr_col1, curr_col2, curr_col3 = curr_expander.columns(3)
curr_freq = curr_col3.selectbox('Time frame',('Daily','Weekly', 'Bi-weekly', 'Monthly'), index=1, key='curr_freq')
curr_from = curr_col1.date_input(label="From",value=default_from,key='curr_from')
curr_to = curr_col2.date_input(label="To",value=default_to,key='curr_to')
date_range_start, date_range_end, date_range_str = get_dates(curr_from,curr_to,curr_freq)

data = []
raw_numbers = []
for i in range(len(date_range_str)):
    date = pd.to_datetime(np.array(date_range_str[i]))
    current_user_ids = set(df2[(df2['username_persistent']!='Anonymous')&(df2['requested_at'].dt.normalize()>=date[0])&(df2['requested_at'].dt.normalize()<=date[1])]['user_id'])
    raw_numbers.append(len(current_user_ids))
    l = np.array(active_users(date_range_str[i:],[current_user_ids]*len(date_range_str))[0])
    l = list(np.round(l/len(current_user_ids),4)*100)
    data.append(l+[np.nan]*(len(date_range_str)-len(l)))
#data.append([1]+[np.nan]*(len(date_range_str)-1))
data = np.array(data)

if curr_freq=='Daily':
    y = [x.strftime('%b-%d %a') + f'        {raw_numbers[i]}'  for i,x in enumerate(date_range_end)]
elif curr_freq=='Weekly' or curr_freq=='Bi-weekly':
    y = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') + f'        {raw_numbers[i]}'  for i,x in enumerate(zip(date_range_start,date_range_end))]
else:
    y = [x.strftime('%Y %b') + f'        {raw_numbers[i]}'  for i,x in enumerate(date_range_end)]
fig = px.imshow(data,
                labels=dict(x="Period", y="Date", color="Retention Rate (%)"),
                y=y,
                color_continuous_scale='rdylgn'
               )
fig.update_xaxes(side="top")

annotations = []
for i in range(len(date_range_str)):
    for j in range(len(date_range_str)):
        if not np.isnan(data[i, j]):
            if 70>data[i, j]>30:
                annotations.append(dict(x=j, y=i, text=f"{data[i, j]:.1f}%", showarrow=False, font=dict(color="black")))
            else:
                annotations.append(dict(x=j, y=i, text=f"{data[i, j]:.1f}%", showarrow=False, font=dict(color="white")))

fig.update_layout(annotations=annotations)

curr_expander.plotly_chart(fig, use_container_width=True)





nurr_expander = st.expander("NURR")
nurr_expander.write("New active user retention rate")
nurr_col1, nurr_col2, nurr_col3 = nurr_expander.columns(3)
nurr_freq = nurr_col3.selectbox('Time frame',('Daily','Weekly', 'Bi-weekly', 'Monthly'), index=1, key='nurr_freq')
nurr_from = nurr_col1.date_input(label="From",value=default_from,key='nurr_from')
nurr_to = nurr_col2.date_input(label="To",value=default_to,key='nurr_to')
date_range_start, date_range_end, date_range_str = get_dates(nurr_from,nurr_to,nurr_freq)

data = []
raw_numbers = []
for i in range(len(date_range_str)):
    date = pd.to_datetime(np.array(date_range_str[i]))
    new_user_ids = set(df1[(df1['date_joined'].dt.normalize()>=date[0])&(df1['date_joined'].dt.normalize()<=date[1])]['id'].values)
    new_active_user_counts, new_active_user_ids = active_users([date_range_str[i]],[new_user_ids])
    raw_numbers.append(new_active_user_counts[0])
    l = list(np.round(active_users(date_range_str[i:],[new_active_user_ids[0]]*len(date_range_str))[0]/new_active_user_counts[0],4)*100)
    data.append(l+[np.nan]*(len(date_range_str)-len(l)))
data = np.array(data)

if nurr_freq=='Daily':
    y = [x.strftime('%b-%d %a') + f'        {raw_numbers[i]}'  for i,x in enumerate(date_range_end)]
elif nurr_freq=='Weekly' or nurr_freq=='Bi-weekly':
    y = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') + f'        {raw_numbers[i]}'  for i,x in enumerate(zip(date_range_start,date_range_end))]
else:
    y = [x.strftime('%Y %b') + f'        {raw_numbers[i]}'  for i,x in enumerate(date_range_end)]
fig = px.imshow(data,
                labels=dict(x="Period", y="Date", color="Retention Rate (%)"),
                y=y,
                color_continuous_scale='rdylgn'
               )
fig.update_xaxes(side="top")

# Customize the annotations to include percentage sign
annotations = []
for i in range(len(date_range_str)):
    for j in range(len(date_range_str)):
        if not np.isnan(data[i, j]):
            if 70>data[i, j]>30:
                annotations.append(dict(x=j, y=i, text=f"{data[i, j]:.1f}%", showarrow=False, font=dict(color="black")))
            else:
                annotations.append(dict(x=j, y=i, text=f"{data[i, j]:.1f}%", showarrow=False, font=dict(color="white")))

fig.update_layout(annotations=annotations)

nurr_expander.plotly_chart(fig, use_container_width=True)




# rurr_expander = st.expander("RURR")
# rurr_expander.write("reactivated user retention rate")
# rurr_col1, rurr_col2, rurr_col3 = rurr_expander.columns(3)
# rurr_freq = rurr_col3.selectbox('Time frame',('Weekly', 'Bi-weekly', 'Monthly'), key='rurr_freq')
# rurr_from = rurr_col1.date_input(label="From",value=default_from,key='rurr_from')
# rurr_to = rurr_col2.date_input(label="To",value=default_to,key='rurr_to')
# rurr_yrange = stickiness_expander.slider("Y-axis range", value=(0, 100), min_value=0, max_value=100, step=5, key='rurr_yrange')

# date_range_start, date_range_end, date_range_str = get_dates(rurr_from,rurr_to,rurr_freq)

# temp = pd.DataFrame({'rurr':np.round(rurr(date_range_str)*100,2)})

# if rurr_freq=='Weekly':
#     temp['date'] = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
#     fig = px.line(temp, x="date", y='rurr', labels={'date':'Week', 'rurr':'RURR (%)'},markers=True)
# elif rurr_freq=='Bi-weekly':
#     temp['date'] = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') for x in zip(date_range_start,date_range_end)]
#     fig = px.line(temp, x="date", y='rurr', labels={'date':'Bi-week', 'rurr':'RURR (%)'},markers=True)
# elif rurr_freq=='Monthly':
#     temp['date'] = [x.strftime('%Y %b') for x in date_range_end]
#     fig = px.line(temp, x="date", y='rurr', labels={'date':'Month', 'rurr':'RURR (%)'},markers=True)

# fig.update_yaxes(range=stickiness_yrange)

# rurr_expander.plotly_chart(fig, use_container_width=True)


rurr_expander = st.expander("RURR")
rurr_expander.write("Reactivated user retention rate")
rurr_col1, rurr_col2, rurr_col3 = rurr_expander.columns(3)
rurr_freq = rurr_col3.selectbox('Time frame',('Daily','Weekly', 'Bi-weekly', 'Monthly'), index=1, key='rurr_freq')
rurr_from = rurr_col1.date_input(label="From",value=default_from,key='rurr_from')
rurr_to = rurr_col2.date_input(label="To",value=default_to,key='rurr_to')
date_range_start, date_range_end, date_range_str = get_dates(rurr_from,rurr_to,rurr_freq)

reactivated_user_ids = get_reactivated_users(date_range_str, reactive_period, inactive_period, previous_active_period)

data = []
for i in range(len(date_range_str)):
    active_user_counts = active_users(date_range_str[i:],[reactivated_user_ids[i]]*len(date_range_str))[0]
    l = list(np.round(active_user_counts/len(reactivated_user_ids[i]),4)*100)
    data.append(l+[np.nan]*(len(date_range_str)-len(l)))
data = np.array(data)

if rurr_freq=='Daily':
    y = [x.strftime('%b-%d %a') + f'        {raw_numbers[i]}'  for i,x in enumerate(date_range_end)]
elif rurr_freq=='Weekly' or rurr_freq=='Bi-weekly':
    y = [x[0].strftime('%b %d')+"-"+x[1].strftime('%b %d') + f'        {len(reactivated_user_ids[i])}' for i, x in enumerate(zip(date_range_start,date_range_end))]
else:
    y = [x.strftime('%Y %b') + f'        {len(reactivated_user_ids[i])}' for i, x in enumerate(date_range_end)]
fig = px.imshow(data,
                labels=dict(x="Period", y="Date", color="Retention Rate (%)"),
                y=y,
                color_continuous_scale='rdylgn'
               )
fig.update_xaxes(side="top")

annotations = []
for i in range(len(date_range_str)):
    for j in range(len(date_range_str)):
        if not np.isnan(data[i, j]):
            if 70>data[i, j]>30:
                annotations.append(dict(x=j, y=i, text=f"{data[i, j]:.1f}%", showarrow=False, font=dict(color="black")))
            else:
                annotations.append(dict(x=j, y=i, text=f"{data[i, j]:.1f}%", showarrow=False, font=dict(color="white")))

fig.update_layout(annotations=annotations)

rurr_expander.plotly_chart(fig, use_container_width=True)
