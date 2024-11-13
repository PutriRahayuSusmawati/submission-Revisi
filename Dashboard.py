import pandas as pd
import streamlit as st
import plotly.express as px
import seaborn as sns

sns.set(style='dark')

def create_daily_orders_df(orders_df):
    # Mengonversi kolom 'order_purchase_timestamp' ke format datetime
    orders_df['order_purchase_timestamp'] = pd.to_datetime(orders_df['order_purchase_timestamp'])

    # Menambahkan kolom tanggal saja untuk mempermudah agregasi harian
    orders_df['order_date'] = orders_df['order_purchase_timestamp'].dt.date

    # Mengelompokkan berdasarkan 'order_date' dan menghitung jumlah pesanan per hari
    daily_orders_df = orders_df.groupby('order_date').agg(
        total_orders=('order_id', 'count'),
        total_order_value=('order_value', 'sum') 
    ).reset_index()

    return daily_orders_df

def create_payment_summary_df(payments_df):
    # Mengelompokkan berdasarkan 'payment_type' dan menghitung frekuensi dan total nilai pembayaran
    payment_summary_df = payments_df.groupby('payment_type').agg(
        payment_count=('payment_value', 'count'),
        total_payment_value=('payment_value', 'sum')
    ).reset_index()

    return payment_summary_df

def create_order_status_summary(orders_df):
    # Mengelompokkan berdasarkan 'order_status' untuk menghitung jumlah pesanan per status
    order_status_summary_df = orders_df['order_status'].value_counts().reset_index()
    order_status_summary_df.columns = ['order_status', 'count']

    return order_status_summary_df

def merge_orders_payments(orders_df, payments_df):
    # Menggabungkan orders_df dan payments_df berdasarkan 'order_id'
    merged_df = pd.merge(orders_df, payments_df, on='order_id', how='inner')
    return merged_df

def create_daily_revenue_df(merged_df):
    # Memfilter data hanya untuk pesanan yang berhasil (status = 'delivered')
    delivered_df = merged_df[merged_df['order_status'] == 'delivered']

    # Mengonversi 'order_purchase_timestamp' ke format datetime
    delivered_df['order_purchase_timestamp'] = pd.to_datetime(delivered_df['order_purchase_timestamp'])

    # Mengelompokkan berdasarkan tanggal dan menghitung total pendapatan harian
    delivered_df['order_date'] = delivered_df['order_purchase_timestamp'].dt.date
    daily_revenue_df = delivered_df.groupby('order_date').agg(
        daily_revenue=('payment_value', 'sum')
    ).reset_index()

    return daily_revenue_df

all_df = pd.read_csv('all_data.csv')
all_df['order_purchase_timestamp'] = pd.to_datetime(all_df['order_purchase_timestamp'])

st.sidebar.image('shop_logo.png', width=150)
st.header('E-Store :sparkles:')

st.sidebar.header("Filter Berdasarkan Tanggal")
start_date = st.sidebar.date_input("Tanggal Mulai", all_df['order_purchase_timestamp'].min().date())
end_date = st.sidebar.date_input("Tanggal Akhir", all_df['order_purchase_timestamp'].max().date())

# Filter data berdasarkan rentang tanggal yang dipilih
filtered_data = all_df[
    (all_df['order_purchase_timestamp'] >= pd.to_datetime(start_date)) &
    (all_df['order_purchase_timestamp'] <= pd.to_datetime(end_date))
]

# Tampilkan data yang sudah difilter untuk pengecekan
st.write("Data yang sudah difilter berdasarkan rentang tanggal:")
st.dataframe(filtered_data)

# Menghitung jumlah order harian
daily_orders_df = filtered_data.groupby(filtered_data['order_purchase_timestamp'].dt.date).size().reset_index(name='order_count')
daily_orders_df.columns = ['order_date', 'order_count']

# Membuat visualisasi jumlah order harian
fig = px.line(daily_orders_df, x='order_date', y='order_count', title='Jumlah Order Harian', labels={'order_date': 'Tanggal', 'order_count': 'Jumlah Order'})

st.title("Dashboard Informasi Jumlah Order Harian")
st.write("Visualisasi jumlah order harian berdasarkan rentang tanggal yang dipilih.")
st.plotly_chart(fig)

st.subheader("Data Jumlah Order Harian")
st.write(daily_orders_df)

st.subheader("Analisis Metode Pembayaran")

# Menampilkan metode pembayaran yang paling sering digunakan
payment_summary = filtered_data['payment_type'].value_counts().reset_index()
payment_summary.columns = ['payment_type', 'count']

fig_payment = px.bar(payment_summary, x='payment_type', y='count', title="Metode Pembayaran Terpopuler")
st.plotly_chart(fig_payment)

# Hubungan metode pembayaran dengan status pesanan
payment_status_summary = filtered_data.groupby(['payment_type', 'order_status']).size().reset_index(name='count')
fig_payment_status = px.bar(payment_status_summary, x='payment_type', y='count', color='order_status',
                            title="Hubungan Metode Pembayaran dengan Status Pesanan")
st.plotly_chart(fig_payment_status)


filtered_data['order_estimated_delivery_date'] = pd.to_datetime(filtered_data['order_estimated_delivery_date'])
filtered_data['order_delivered_customer_date'] = pd.to_datetime(filtered_data['order_delivered_customer_date'])

# Menghitung selisih antara tanggal estimasi dan tanggal pengiriman aktual
filtered_data['delivery_accuracy'] = (filtered_data['order_estimated_delivery_date'] - filtered_data['order_delivered_customer_date']).dt.days

# Filter data untuk enam bulan terakhir
six_months_data = filtered_data[filtered_data['order_purchase_timestamp'] >= (filtered_data['order_purchase_timestamp'].max() - pd.DateOffset(months=6))]

# Hitung rata-rata selisih waktu pengiriman
avg_delivery_accuracy = six_months_data['delivery_accuracy'].mean()
st.metric("Rata-Rata Selisih Waktu Pengiriman (6 Bulan Terakhir)", avg_delivery_accuracy)

filtered_data['order_delivered_customer_date'] = pd.to_datetime(filtered_data['order_delivered_customer_date'])
filtered_data['order_approved_at'] = pd.to_datetime(filtered_data['order_approved_at'])

# Filter data untuk dua tahun terakhir
two_years_data = filtered_data[filtered_data['order_purchase_timestamp'] >= (filtered_data['order_purchase_timestamp'].max() - pd.DateOffset(years=2))]

# Menghitung frekuensi pembelian per pelanggan
customer_purchase_freq = two_years_data.groupby('customer_id').size().reset_index(name='purchase_frequency')

# Menghitung rata-rata waktu pengiriman dalam dua tahun terakhir
avg_delivery_time = (two_years_data['order_delivered_customer_date'] - two_years_data['order_approved_at']).dt.days.mean()

st.write("Rata-Rata Waktu Pengiriman Berdasarkan Frekuensi Pembelian")
st.write(f"Frekuensi Rata-rata: {customer_purchase_freq['purchase_frequency'].mean()}, Waktu Pengiriman Rata-rata: {avg_delivery_time} hari")


# Menghitung kecepatan berdasarkan jenis/metode pembayaran
one_year_data = filtered_data[filtered_data['order_purchase_timestamp'] >= (filtered_data['order_purchase_timestamp'].max() - pd.DateOffset(years=1))]
one_year_data['delivery_time'] = (one_year_data['order_delivered_customer_date'] - one_year_data['order_approved_at']).dt.days
delivery_by_payment = one_year_data.groupby('payment_type')['delivery_time'].mean().reset_index()
fig_delivery = px.bar(delivery_by_payment, x='payment_type', y='delivery_time', title="Kecepatan Pengiriman Berdasarkan Jenis Pembayaran")
st.plotly_chart(fig_delivery)

# Menghitung persentase pengiriman tepat waktu 
one_year_data['on_time'] = one_year_data['order_delivered_customer_date'] <= one_year_data['order_estimated_delivery_date']
on_time_percentage = one_year_data['on_time'].mean() * 100
st.metric("Persentase Pengiriman Tepat Waktu (1 Tahun Terakhir)", f"{on_time_percentage:.2f}%")

# Menghitung nilai pembayaran berdasarkan metode pembayaran
avg_payment_value = filtered_data.groupby('payment_type')['payment_value'].mean().reset_index()
fig_avg_payment = px.bar(avg_payment_value, x='payment_type', y='payment_value', title="Rata-Rata Nilai Pembayaran Berdasarkan Metode Pembayaran")
st.plotly_chart(fig_avg_payment)

# Menghitung rata-rata waktu pengiriman dan persetujuan hinggi diterima
filtered_data['delivery_time'] = (filtered_data['order_delivered_customer_date'] - filtered_data['order_approved_at']).dt.days
avg_delivery_time = filtered_data['delivery_time'].mean()
st.metric("Rata-Rata Waktu Pengiriman (Hari)", avg_delivery_time)

# Analisis RFM (Recency, Frequency, Monetary)
# Menghitung RFM
# Recency dihitung sebagai selisih (dalam hari) antara reference_date dan pembelian terakhir yang dilakukan setiap pelanggan.
# Frequency dihitung sebagai jumlah order_id per pelanggan, menunjukkan berapa kali pelanggan membeli dalam periode analisis.
# Monetary dihitung sebagai total payment_value yang dibelanjakan oleh setiap pelanggan.
import pandas as pd
filtered_data['order_purchase_timestamp'] = pd.to_datetime(filtered_data['order_purchase_timestamp'])
reference_date = filtered_data['order_purchase_timestamp'].max()
rfm_data = filtered_data.groupby('customer_id').agg({
    'order_purchase_timestamp': lambda x: (reference_date - x.max()).days,  # Recency
    'order_id': 'count',  # Frequency
    'payment_value': 'sum'  # Monetary
}).reset_index()
rfm_data.columns = ['customer_id', 'recency', 'frequency', 'monetary']
st.write("Tabel RFM per Pelanggan")
st.dataframe(rfm_data)

# Menghitung Segmentation
# recency menghitung waktu terakhir pelanggan melakukan pembelian
# frequency mengukur berapa kali pelanggan melakukan pembelian dalam periode yang ditentukan
# monetary mengukur total pengeluaran pelanggan dalam periode yang sama.
# RFM_Score menggabungkan skor untuk Recency (R), Frequency (F), dan Monetary (M) menjadi satu skor yang mengidentifikasi kelompok pelanggan berdasarkan perilaku
rfm_data['R_Score'] = pd.cut(rfm_data['recency'], bins=4, labels=[4, 3, 2, 1])
rfm_data['F_Score'] = pd.cut(rfm_data['frequency'], bins=4, labels=[1, 2, 3, 4])
rfm_data['M_Score'] = pd.cut(rfm_data['monetary'], bins=4, labels=[1, 2, 3, 4])
rfm_data['RFM_Score'] = rfm_data['R_Score'].astype(str) + rfm_data['F_Score'].astype(str) + rfm_data['M_Score'].astype(str)
st.write("Segmentasi RFM per Pelanggan")
st.dataframe(rfm_data[['customer_id', 'recency', 'frequency', 'monetary', 'RFM_Score']])

# Menghitung interpretasi segmentasi RFM
# Loyal Customer menghitung pelanggan dengan RFM_Score 444, yang berarti mereka sering berbelanja, baru-baru ini melakukan pembelian, dan memiliki nilai pembelian tinggi
# Potential Loyalist menghitung pelanggan yang baru-baru ini melakukan pembelian dan memiliki frekuensi pembelian yang cukup tinggi, tetapi belum setinggi loyal customer.
# At Risk mengitung pelanggan yang jarang melakukan pembelian dan belum membeli dalam waktu lama.
# Need Attention menghitung pelanggan yang baru-baru ini membeli tetapi memiliki frekuensi yang rendah, sehingga mungkin membutuhkan dorongan untuk lebih sering berbelanja.
def segment_rfm(df):
    if df['RFM_Score'] == '444':
        return 'Loyal Customer'
    elif df['R_Score'] == 4 and df['F_Score'] >= 3:
        return 'Potential Loyalist'
    elif df['R_Score'] >= 3 and df['F_Score'] == 1:
        return 'At Risk'
    elif df['R_Score'] == 1 and df['F_Score'] >= 3:
        return 'Need Attention'
    else:
        return 'Other'

rfm_data['Customer_Segment'] = rfm_data.apply(segment_rfm, axis=1)
st.write("Segmentasi Pelanggan Berdasarkan Skor RFM")
st.dataframe(rfm_data[['customer_id', 'recency', 'frequency', 'monetary', 'RFM_Score', 'Customer_Segment']])
st.write("Distribusi Pelanggan Berdasarkan Segmen")
st.bar_chart(rfm_data['Customer_Segment'].value_counts())