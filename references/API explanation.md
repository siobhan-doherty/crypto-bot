# Binance Klines (Candlesticks) 

## What is a Candlestick?

A **candlestick** (or “candle”) is a simple drawing that tells you how the price of something (like Bitcoin) changed in a period (for example, one day).
Imagine you want to know what happened to the price of a toy every day — not every minute, but just the most important points.

A candlestick shows:

* The price when the day started (open)
* The highest price reached (high)
* The lowest price (low)
* The price when the day ended (close)

A candlestick looks like a little candle with a body and wicks (like this):

```
High
  |
  |   -----
  |  |     |   <-- The "body" (from open to close)
  |  |     |
  |   -----
  |
Low
```

* If the price goes up, the candle is usually green.
* If the price goes down, it’s red.

If you put many candlesticks together, you can see the ups and downs — it’s like watching a cartoon of the market!

---

## Column-by-Column Explanation

Below, you’ll find a table of what each column from the Binance API means, explained simply.

| Column Name                      | What It Means (Simple)                                     | Example Value            |
| -------------------------------- | ---------------------------------------------------------- | ------------------------ |
| **Open time**                    | When the period starts. (Like: “Monday, 9 AM”)             | 2024-05-31 00:00:00      |
| **Open**                         | Price at the start of the period.                          | 10000.00                 |
| **High**                         | Highest price during the period.                           | 10500.00                 |
| **Low**                          | Lowest price during the period.                            | 9800.00                  |
| **Close**                        | Price at the end of the period.                            | 10200.00                 |
| **Volume**                       | How much of the asset (like Bitcoin) was traded.           | 3.5 (means 3.5 Bitcoins) |
| **Close time**                   | When the period ends. (Like: “Monday, 11:59 PM”)           | 2024-05-31 23:59:59      |
| **Quote asset volume**           | How much money (in USDT, for example) was traded in total. | 35000.00                 |
| **Number of trades**             | How many trades (buys/sells) happened.                     | 1250                     |
| **Taker buy base asset volume**  | Amount of the asset bought at the market price.            | 1.7                      |
| **Taker buy quote asset volume** | Amount of money used to buy at market price.               | 17000.00                 |
| **Ignore**                       | You can skip this. It’s always zero.                       | 0                        |
| **Symbol**                       | Which asset pair these numbers are for (like BTCUSDT).     | BTCUSDT                  |

---

## What Are Technical Indicators?

**Technical indicators** are like “math tools” or “formulas” that traders use to help them decide when to buy or sell.

### Most Common Indicators (Explained Simply)

#### 1. **Moving Average**

* **What is it?**
  The average price over the last “n” days.
* **Why use it?**
  It helps you see if the price is mostly going up or down, ignoring crazy jumps.
* **Example:**
  If prices on Monday, Tuesday, Wednesday are 10, 12, 14,
  the 3-day moving average on Wednesday is (10 + 12 + 14) / 3 = **12**.

#### 2. **RSI (Relative Strength Index)**

* **What is it?**
  A score from 0 to 100 that tells you if the price went up a lot (maybe too much) or down a lot (maybe too much).
* **Why use it?**
  To spot when the market might change direction.
* **Example:**
  If RSI is above 70, maybe price will soon go down.
  If RSI is below 30, maybe price will soon go up.

#### 3. **MACD (Moving Average Convergence Divergence)**

* **What is it?**
  A tool that compares two moving averages and draws two lines. When these lines cross, it might be a signal to buy or sell.
* **Why use it?**
  To spot changes in the market’s direction.
* **Example:**
  If the MACD line goes above the “signal line,” that might mean it’s time to buy.

---

## What Can You Do With Binance Klines Data?

With the columns above, you can:

* **Draw candlestick charts** to see the price history.
* **Calculate indicators** (like moving average, RSI, MACD).
* **Analyze volatility** (how wild price changes are).
* **Track trading volume** (how many people are buying/selling).
* **Build rules for alerts** (for example, “If price falls more than 5% in a day, show a warning”).

---

## Example: Simple Moving Average in Python

Suppose you have daily closing prices:

```python
import pandas as pd

# Example data
data = {'Close': [10, 12, 14, 13, 15]}
df = pd.DataFrame(data)

# Calculate 3-day moving average
df['MA3'] = df['Close'].rolling(window=3).mean()

print(df)
```

**Output:**

|   | Close | MA3  |
| - | ----- | ---- |
| 0 | 10    | NaN  |
| 1 | 12    | NaN  |
| 2 | 14    | 12.0 |
| 3 | 13    | 13.0 |
| 4 | 15    | 14.0 |

The “MA3” column only shows values starting from the third row (since you need three numbers to make the average).
