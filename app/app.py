import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import pooling
import os

# Page config
st.set_page_config(
    page_title="股票投资分析系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection pool
@st.cache_resource
def init_connection_pool():
    dbconfig = {
        "host": os.getenv("DB_HOST", "localhost"),
        "user": os.getenv("DB_USER", "stockuser"),
        "password": os.getenv("DB_PASSWORD", "stockpass123"),
        "database": os.getenv("DB_NAME", "stock_db"),
        "pool_name": "mypool",
        "pool_size": 5
    }
    pool = pooling.MySQLConnectionPool(**dbconfig)
    return pool

pool = init_connection_pool()

def get_db_connection():
    return pool.get_connection()

# Authentication functions
def verify_password(username, password):
    """Verify user credentials"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", 
                   (username, password))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def login_form():
    """Display login form"""
    with st.form("login_form"):
        st.markdown("### 登录")
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")
        submitted = st.form_submit_button("登录")
        
        if submitted:
            if username and password:
                user = verify_password(username, password)
                if user:
                    st.session_state['authenticated'] = True
                    st.session_state['username'] = user['username']
                    st.session_state['name'] = user['name']
                    st.rerun()
                else:
                    st.error("用户名或密码错误")
            else:
                st.warning("请输入用户名和密码")

# Load stock data
@st.cache_data(ttl=300)
def load_stock_data():
    """Load all stock data from database"""
    conn = get_db_connection()
    query = """
    SELECT stock_code, date, open_price, close_price, high_price, low_price, volume
    FROM stock_data
    ORDER BY stock_code, date
    """
    df = pd.read_sql(query, conn)
    conn.close()
    df['date'] = pd.to_datetime(df['date'])
    return df

# Calculate returns
def calculate_returns(prices):
    """Calculate daily returns"""
    return prices.pct_change().dropna()

# Calculate cumulative returns
def calculate_cumulative_returns(returns):
    """Calculate cumulative returns"""
    return (1 + returns).cumprod() - 1

# Calculate maximum drawdown
def calculate_max_drawdown(prices):
    """Calculate maximum drawdown"""
    cumulative = (prices / prices.iloc[0])
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    return drawdown.min()

# Calculate Sharpe ratio
def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    """Calculate Sharpe ratio (annualized)"""
    excess_returns = returns - risk_free_rate / 252
    if excess_returns.std() == 0:
        return 0
    return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

# Calculate statistics
def calculate_statistics(df, stock_code=None):
    """Calculate all statistics for a stock or portfolio"""
    if stock_code:
        data = df[df['stock_code'] == stock_code].copy()
        prices = data.set_index('date')['close_price']
    else:
        # Portfolio: equal weight
        portfolio_data = df.pivot_table(
            index='date', 
            columns='stock_code', 
            values='close_price'
        )
        prices = portfolio_data.mean(axis=1)
    
    returns = calculate_returns(prices)
    
    # Current year
    current_year = datetime.now().year
    ytd_mask = returns.index.year == current_year
    ytd_returns = returns[ytd_mask]
    
    # Monthly returns
    monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
    
    stats = {
        '日均收益率': f"{returns.mean() * 100:.3f}%",
        '月均收益率': f"{monthly_returns.mean() * 100:.2f}%",
        '今年以来收益率': f"{calculate_cumulative_returns(ytd_returns).iloc[-1] * 100:.2f}%" if len(ytd_returns) > 0 else "0.00%",
        '历史累计收益率': f"{calculate_cumulative_returns(returns).iloc[-1] * 100:.2f}%",
        '最大回撤': f"{calculate_max_drawdown(prices) * 100:.2f}%",
        '夏普比率': f"{calculate_sharpe_ratio(returns):.2f}"
    }
    
    return stats, prices

# Main app
def main():
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    
    # Authentication
    if not st.session_state['authenticated']:
        login_form()
        st.info('默认用户：admin, user1, user2；密码：password123')
    else:
        # Sidebar
        with st.sidebar:
            st.write(f'欢迎 *{st.session_state["name"]}*')
            if st.button('退出登录'):
                st.session_state['authenticated'] = False
                st.session_state['username'] = None
                st.session_state['name'] = None
                st.rerun()
            st.divider()
            
            # Navigation
            page = st.radio(
                "导航",
                ["📊 概览", "📈 个股分析", "💼 投资组合分析"]
            )
        
        # Load data
        df = load_stock_data()
        stock_codes = df['stock_code'].unique()
        
        if page == "📊 概览":
            st.title("📊 股票投资分析系统")
            st.markdown("### 系统概览")
            
            # Display latest data
            latest_date = df['date'].max()
            st.info(f"数据更新至: {latest_date.strftime('%Y-%m-%d')}")
            
            # Stock list
            st.markdown("### 股票列表")
            latest_prices = df[df['date'] == latest_date][['stock_code', 'close_price']]
            
            # Add previous close for change calculation
            prev_date = df[df['date'] < latest_date]['date'].max()
            prev_prices = df[df['date'] == prev_date][['stock_code', 'close_price']]
            prev_prices.columns = ['stock_code', 'prev_close']
            
            summary = pd.merge(latest_prices, prev_prices, on='stock_code')
            summary['涨跌幅'] = (summary['close_price'] - summary['prev_close']) / summary['prev_close'] * 100
            summary.columns = ['股票代码', '最新价格', '昨收价格', '涨跌幅(%)']
            
            st.dataframe(
                summary.style.format({
                    '最新价格': '${:.2f}',
                    '昨收价格': '${:.2f}',
                    '涨跌幅(%)': '{:.2f}%'
                }).applymap(
                    lambda x: 'color: red' if x < 0 else 'color: green',
                    subset=['涨跌幅(%)']
                ),
                use_container_width=True
            )
            
        elif page == "📈 个股分析":
            st.title("📈 个股分析")
            
            selected_stock = st.selectbox("选择股票", stock_codes)
            
            if selected_stock:
                stats, prices = calculate_statistics(df, selected_stock)
                
                # Display statistics
                st.markdown(f"### {selected_stock} 统计指标")
                cols = st.columns(3)
                for i, (key, value) in enumerate(stats.items()):
                    cols[i % 3].metric(key, value)
                
                # Price chart
                st.markdown("### 价格走势图")
                stock_data = df[df['stock_code'] == selected_stock].sort_values('date')
                
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=stock_data['date'],
                    open=stock_data['open_price'],
                    high=stock_data['high_price'],
                    low=stock_data['low_price'],
                    close=stock_data['close_price'],
                    name=selected_stock
                ))
                
                fig.update_layout(
                    title=f"{selected_stock} K线图",
                    yaxis_title="价格 ($)",
                    xaxis_title="日期",
                    height=500,
                    xaxis_rangeslider_visible=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Volume chart
                fig_volume = px.bar(
                    stock_data,
                    x='date',
                    y='volume',
                    title=f"{selected_stock} 成交量"
                )
                fig_volume.update_layout(height=300)
                st.plotly_chart(fig_volume, use_container_width=True)
                
        elif page == "💼 投资组合分析":
            st.title("💼 投资组合分析")
            st.markdown("假设5只股票平均持有的投资组合")
            
            # Portfolio statistics
            stats, portfolio_prices = calculate_statistics(df)
            
            st.markdown("### 投资组合统计指标")
            cols = st.columns(3)
            for i, (key, value) in enumerate(stats.items()):
                cols[i % 3].metric(key, value)
            
            # Portfolio performance chart
            st.markdown("### 投资组合历史走势")
            
            # Calculate portfolio value
            portfolio_df = pd.DataFrame({
                'date': portfolio_prices.index,
                'portfolio_value': portfolio_prices.values
            })
            
            # Normalize to 100
            portfolio_df['normalized_value'] = (portfolio_df['portfolio_value'] / portfolio_df['portfolio_value'].iloc[0]) * 100
            
            fig = px.line(
                portfolio_df,
                x='date',
                y='normalized_value',
                title='投资组合净值走势（起始值=100）',
                labels={'normalized_value': '净值', 'date': '日期'}
            )
            
            fig.update_layout(height=500)
            fig.update_traces(line_color='#1f77b4', line_width=2)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Individual stock contribution
            st.markdown("### 个股表现对比")
            
            comparison_data = []
            for stock in stock_codes:
                _, stock_prices = calculate_statistics(df, stock)
                normalized = (stock_prices / stock_prices.iloc[0]) * 100
                for date, value in normalized.items():
                    comparison_data.append({
                        'date': date,
                        'stock_code': stock,
                        'normalized_value': value
                    })
            
            comparison_df = pd.DataFrame(comparison_data)
            
            fig_comparison = px.line(
                comparison_df,
                x='date',
                y='normalized_value',
                color='stock_code',
                title='个股净值走势对比（起始值=100）',
                labels={'normalized_value': '净值', 'date': '日期', 'stock_code': '股票代码'}
            )
            
            fig_comparison.update_layout(height=500)
            st.plotly_chart(fig_comparison, use_container_width=True)
            
            # Weight allocation (equal weight)
            st.markdown("### 持仓配置")
            weight_df = pd.DataFrame({
                '股票代码': stock_codes,
                '权重': [20.0] * len(stock_codes)
            })
            
            fig_pie = px.pie(
                weight_df,
                values='权重',
                names='股票代码',
                title='投资组合权重分配'
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)

if __name__ == "__main__":
    main()