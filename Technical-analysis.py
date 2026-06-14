import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

def veri_cek(ticker, baslangic, bitis):
    df = yf.download(ticker, start=baslangic, end=bitis)
    if df.empty:
        print("Hata: Geçersiz ticker veya tarih aralığı.")
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    print("Verinin ilk 5 satırı")
    print(df[["Open", "High", "Low", "Close"]].head())
    return df

def ma_hesapla(df,periyot):
    df[f"MA{periyot}"] = df["Close"].rolling(window=periyot).mean()
    return df[f"MA{periyot}"]
def hesapla_rsi(df,periyot=14):
    delta=df["Close"].diff()
    kazan=delta.clip(lower=0)
    kaybet=-delta.clip(upper=0)
    ort_kazanc=kazan.rolling(periyot).mean()
    ort_kaybet=kaybet.rolling(periyot).mean()
    rs= ort_kazanc/ort_kaybet
    rsi=100 - (100/(1+rs))
    return rsi
def hesapla_macd(df):
    df["EMA12"]=df["Close"].ewm(span=12,adjust=False).mean()
    df["EMA26"]=df["Close"].ewm(span=26,adjust=False).mean()
    df["MACD"]=df["EMA12"] - df["EMA26"]
    df["Sinyal2"]= df["MACD"].ewm(span=9, adjust=False).mean()
    df["Histogram"]=df["MACD"] - df["Sinyal2"]
    return df[["MACD","Sinyal2","Histogram"]]
def hesapla_bollinger(df,periyot=20):
    df["BB_Orta"]=df["Close"].rolling(periyot).mean()
    df["BB_std"]=df["Close"].rolling(periyot).std()
    df["BB_ust"]=df["BB_Orta"] + 2*(df["BB_std"])
    df["BB_alt"]=df["BB_Orta"] - 2*(df["BB_std"])
    return df[["BB_ust","BB_Orta","BB_alt"]].round(2)
def golden_cross(df):
    df["MA20"]=df["Close"].rolling(20).mean()
    df["MA50"]=df["Close"].rolling(50).mean()
    df["MA20_ust"]=(df["MA20"]>df["MA50"]).astype(int)
    df["Sinyal"]=df["MA20_ust"].diff()
    al_sinyalleri=df["Sinyal"]==1
    sat_sinyalleri=df["Sinyal"]==-1
    return al_sinyalleri , sat_sinyalleri
def strateji_rsi(df,alt=30,ust=70):
    df["RSI_sinyal"]=hesapla_rsi(df)
    df["RSI_strateji"]=np.where(df["RSI_sinyal"] <alt,"AL",np.where(df["RSI_sinyal"] > ust,"SAT", "TUT"))
    return df[df["RSI_strateji"] != "TUT"][["Close", "RSI_sinyal", "RSI_strateji"]].round(2)
def strateji_macd_crossover(df):
    df["EMA12"] = df["Close"].ewm(span=12, adjust=False).mean()
    df["EMA26"] = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = df["EMA12"] - df["EMA26"]
    df["Sinyal2"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["Macd_ust"] = (df["MACD"] > df["Sinyal2"]).astype(int)
    df["signal"] = df["Macd_ust"].diff()
    al = df["signal"] == 1
    sat = df["signal"] == -1
    return al, sat
def strateji_bollinger(df):
    df["BB_Orta"] = df["Close"].rolling(20).mean()
    df["BB_std"] = df["Close"].rolling(20).std()
    df["BB_ust"] = df["BB_Orta"] + 2 * df["BB_std"]
    df["BB_alt"] = df["BB_Orta"] - 2 * df["BB_std"]
    df["Bollinger_strateji"] = np.where(
        df["Close"] < df["BB_alt"], "AL",
        np.where(df["Close"] > df["BB_ust"], "SAT", "TUT")
    )
    return df[df["Bollinger_strateji"] != "TUT"][["Close", "Bollinger_strateji"]].round(2)
def backtest_calistir(df, pozisyon_sutunu):
    test_df = df.dropna().copy()
    test_df["Gunluk_Getiri"] = test_df["Close"].pct_change()
    test_df["Strateji_Getiri"] = test_df["Gunluk_Getiri"] * test_df[pozisyon_sutunu].shift(1)
    al_tut   = (1 + test_df["Gunluk_Getiri"]).cumprod().iloc[-1]
    strateji = (1 + test_df["Strateji_Getiri"]).cumprod().iloc[-1]
    print(f"Al & Tut  : %{round((al_tut - 1) * 100, 1)}")
    print(f"Strateji  : %{round((strateji - 1) * 100, 1)}")
def goster_golden_cross(df, ticker):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True,
                                    gridspec_kw={'height_ratios': [3, 1]})
    ax1.plot(df.index, df["Close"], label="Fiyat", linewidth=1, alpha=0.8)
    ax1.plot(df.index, df["MA20"], label="MA20", linewidth=1.5)
    ax1.plot(df.index, df["MA50"], label="MA50", linewidth=1.5)
    al = df[df["Sinyal"] == 1]
    sat = df[df["Sinyal"] == -1]
    ax1.scatter(al.index, al["Close"], marker="^", color="green", s=100, label="AL", zorder=5)
    ax1.scatter(sat.index, sat["Close"], marker="v", color="red", s=100, label="SAT", zorder=5)
    ax1.set_title(f"{ticker} — Golden Cross")
    ax1.set_ylabel("Fiyat ($)")
    ax1.legend()
    ax1.grid(alpha=0.3)
    ax2.bar(df.index, df["Volume"], color="gray", alpha=0.5)
    ax2.set_ylabel("Hacim")
    ax2.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{ticker}_golden_cross.png", dpi=150)
    plt.show()

def goster_rsi(df, ticker):
    df["RSI"] = hesapla_rsi(df)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True,
                                    gridspec_kw={'height_ratios': [3, 1]})
    ax1.plot(df.index, df["Close"], label="Fiyat", linewidth=1)
    al = df[df["RSI"] < 30]
    sat = df[df["RSI"] > 70]
    ax1.scatter(al.index, al["Close"], marker="^", color="green", s=100, label="AL (RSI<30)", zorder=5)
    ax1.scatter(sat.index, sat["Close"], marker="v", color="red", s=100, label="SAT (RSI>70)", zorder=5)
    ax1.set_title(f"{ticker} — RSI Stratejisi")
    ax1.set_ylabel("Fiyat ($)")
    ax1.legend()
    ax1.grid(alpha=0.3)
    ax2.plot(df.index, df["RSI"], color="purple", linewidth=1)
    ax2.axhline(70, color="red", linestyle="--", alpha=0.7)
    ax2.axhline(30, color="green", linestyle="--", alpha=0.7)
    ax2.fill_between(df.index, 70, 100, alpha=0.1, color="red")
    ax2.fill_between(df.index, 0, 30, alpha=0.1, color="green")
    ax2.set_ylabel("RSI")
    ax2.set_ylim(0, 100)
    ax2.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{ticker}_rsi.png", dpi=150)
    plt.show()

def goster_macd(df, ticker):
    hesapla_macd(df)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True,
                                    gridspec_kw={'height_ratios': [3, 1]})
    ax1.plot(df.index, df["Close"], label="Fiyat", linewidth=1)
    ax1.set_title(f"{ticker} — MACD")
    ax1.set_ylabel("Fiyat ($)")
    ax1.legend()
    ax1.grid(alpha=0.3)
    ax2.plot(df.index, df["MACD"], label="MACD", linewidth=1.5)
    ax2.plot(df.index, df["Sinyal2"], label="Sinyal", linewidth=1.5)
    colors = ['green' if h >= 0 else 'red' for h in df["Histogram"]]
    ax2.bar(df.index, df["Histogram"], color=colors, alpha=0.7, label="Histogram")
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_ylabel("MACD")
    ax2.legend()
    ax2.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{ticker}_macd.png", dpi=150)
    plt.show()

def goster_bollinger(df, ticker):
    plt.figure(figsize=(14, 6))
    plt.plot(df.index, df["Close"], label="Fiyat", linewidth=1, alpha=0.8)
    plt.plot(df.index, df["BB_Orta"], label="Orta Bant (MA20)", linewidth=1.5)
    plt.plot(df.index, df["BB_ust"], label="Üst Bant", linewidth=1, linestyle="--")
    plt.plot(df.index, df["BB_alt"], label="Alt Bant", linewidth=1, linestyle="--")
    plt.fill_between(df.index, df["BB_ust"], df["BB_alt"], alpha=0.1, color="blue")
    al = df[df["Bollinger_strateji"] == "AL"]
    sat = df[df["Bollinger_strateji"] == "SAT"]
    plt.scatter(al.index, al["Close"], marker="^", color="green", s=100, label="AL", zorder=5)
    plt.scatter(sat.index, sat["Close"], marker="v", color="red", s=100, label="SAT", zorder=5)
    plt.title(f"{ticker} — Bollinger Bantları")
    plt.ylabel("Fiyat ($)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{ticker}_bollinger.png", dpi=150)
    plt.show()

def gosterge_menusu(df, ticker):
    while True:
        print("\n--- GÖSTERGELER ---")
        print("1) MA20")
        print("2) MA50")
        print("3) EMA20")
        print("4) RSI")
        print("5) MACD")
        print("6) Bollinger Bantları")
        print("7) Geri")
        secim = input("Seçim: ")
        if secim == "1":
            print(f"MA20 son değer: {ma_hesapla(df, 20).iloc[-1]:.2f}")
        elif secim == "2":
            print(f"MA50 son değer: {ma_hesapla(df, 50).iloc[-1]:.2f}")
        elif secim == "3":
            ema = df["Close"].ewm(span=20, adjust=False).mean()
            print(f"EMA20 son değer: {ema.iloc[-1]:.2f}")
        elif secim == "4":
            rsi = hesapla_rsi(df)
            son = rsi.iloc[-1]
            yorum = "Aşırı alım" if son > 70 else "Aşırı satım" if son < 30 else "Normal"
            print(f"RSI: {son:.2f} — {yorum}")
        elif secim == "5":
            hesapla_macd(df)
            print(f"MACD  : {df['MACD'].iloc[-1]:.4f}")
            print(f"Sinyal: {df['Sinyal2'].iloc[-1]:.4f}")
        elif secim == "6":
            hesapla_bollinger(df)
            print(f"Üst Bant : {df['BB_ust'].iloc[-1]:.2f}")
            print(f"Orta Bant: {df['BB_Orta'].iloc[-1]:.2f}")
            print(f"Alt Bant : {df['BB_alt'].iloc[-1]:.2f}")
        elif secim == "7":
            break

def strateji_menusu(df, ticker):
    while True:
        print("\n--- STRATEJİLER ---")
        print("1) Golden Cross")
        print("2) RSI Stratejisi")
        print("3) MACD Crossover")
        print("4) Bollinger Band")
        print("5) Geri")
        secim = input("Seçim: ")
        if secim == "1":
            golden_cross(df)
            print(f"AL sinyali: {df['Sinyal'].eq(1).sum()} | SAT sinyali: {df['Sinyal'].eq(-1).sum()}")
            backtest_calistir(df, "MA20_ust")
            goster_golden_cross(df, ticker)
        elif secim == "2":
         strateji_rsi(df)
         df["RSI_pozisyon"] = np.where(df["RSI_sinyal"] < 30, 1, 0)
         print(df[df["RSI_strateji"] != "TUT"][["Close", "RSI_sinyal", "RSI_strateji"]].round(2).to_string())
         backtest_calistir(df, "RSI_pozisyon")
         goster_rsi(df, ticker)
        elif secim == "3":
            strateji_macd_crossover(df)
            print(f"AL sinyali: {df['signal'].eq(1).sum()} | SAT sinyali: {df['signal'].eq(-1).sum()}")
            backtest_calistir(df, "Macd_ust")
            goster_macd(df, ticker)
        elif secim == "4":
         hesapla_bollinger(df)
         strateji_bollinger(df)
         df["BB_pozisyon"] = np.where(df["Close"] < df["BB_alt"], 1, 0)
         print(df[df["Bollinger_strateji"] != "TUT"][["Close", "Bollinger_strateji"]].round(2).to_string())
         backtest_calistir(df, "BB_pozisyon")
         goster_bollinger(df, ticker)
        elif secim == "5":
            break

def ana_menu():
    print("=" * 40)
    print("   TEKNİK ANALİZ ARACI")
    print("=" * 40)
    ticker = input("Ticker: ").upper()
    baslangic = input("Başlangıç tarihi (YYYY-MM-DD): ")
    bitis = input("Bitiş tarihi (YYYY-MM-DD): ")

    df = veri_cek(ticker, baslangic, bitis)
    if df is None:
        return

    guncel = float(df["Close"].iloc[-1])
    print(f"\nAnlık fiyat : {guncel:.2f} $")
    while True:
        print("\n--- ANA MENÜ ---")
        print("1) Göstergeler")
        print("2) Stratejiler")
        print("3) Çıkış")
        secim = input("Seçim: ")
        if secim == "1":
            gosterge_menusu(df, ticker)
        elif secim == "2":
            strateji_menusu(df, ticker)
        elif secim == "3":
            break

if __name__ == "__main__":
    ana_menu()