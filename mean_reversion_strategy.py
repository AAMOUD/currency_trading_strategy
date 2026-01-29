import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt

def calc_sharpe(returns):
    if np.std(returns) == 0 or len(returns[returns != 0]) == 0:
        return 0
    return np.mean(returns) / np.std(returns)

def load_and_prepare(filepath, col_name):
    df = pd.read_csv(filepath, index_col='Date', parse_dates=True)
    df.columns = [col_name]
    df.dropna(inplace=True)
    df['Delta'] = df[col_name].diff()
    df['Lag'] = df[col_name].shift(1)
    df.dropna(inplace=True)
    return df

def test_mean_reversion(data):
    X = sm.add_constant(data['Lag'])
    y = data['Delta']
    model = sm.OLS(y, X).fit()
    return model.params['const'], model.params['Lag'], model.tvalues['Lag']

def run_strategy(data, window=80, t_crit=-1, beta_min=None):
    returns = []
    for t in range(window, len(data) - 1):
        sample = data.iloc[t-window:t]
        alpha_hat, beta_hat, t_stat = test_mean_reversion(sample)
        
        signal_col = data.columns[0]
        expected_change = alpha_hat + beta_hat * data.iloc[t][signal_col]
        
        if (alpha_hat > 0) and (beta_hat < 0) and (t_stat < t_crit):
            if beta_min is None or beta_hat < beta_min:
                ret = data.iloc[t+1]['Delta'] if expected_change > 0 else -data.iloc[t+1]['Delta']
            else:
                ret = 0
        else:
            ret = 0
        
        returns.append(ret)
    
    return np.array(returns)

def save_chart(returns, title, filename):
    portfolio = np.cumprod(1 + returns)
    plt.figure(figsize=(10, 6))
    plt.plot(portfolio)
    plt.title(title)
    plt.xlabel("Trading Days")
    plt.ylabel("Portfolio Value")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"outputs/{filename}", dpi=150)
    plt.close()

def print_results(name, returns):
    num_trades = np.count_nonzero(returns)
    win_rate = np.sum(returns > 0) / num_trades * 100 if num_trades > 0 else 0
    sharpe = calc_sharpe(returns)
    
    portfolio = np.cumprod(1 + returns)
    cum_max = np.maximum.accumulate(portfolio)
    drawdown = (portfolio - cum_max) / cum_max
    max_drawdown = drawdown.min()
    
    print(f"\n{name}:")
    print(f"  Sharpe: {sharpe:.3f}")
    print(f"  Trades: {num_trades}/{len(returns)} days ({100*num_trades/len(returns):.1f}%)")
    if num_trades > 0:
        print(f"  Win Rate: {win_rate:.1f}%")
    print(f"  Max Drawdown: {max_drawdown:.2%}")

print("\n=== EUR/USD ===")
eurusd = load_and_prepare('data/eurusd_data.csv', 'EURUSD')

alpha, beta, tstat = test_mean_reversion(eurusd)
print(f"\nMean Reversion Test:")
print(f"  Alpha: {alpha:.6f}, Beta: {beta:.6f}, t-stat: {tstat:.2f}")
print(f"  Signal: {'Detected' if beta < 0 and tstat < -1 else 'Weak'}")

returns_baseline = run_strategy(eurusd, t_crit=-1)
returns_improved = run_strategy(eurusd, t_crit=-1.5)

save_chart(returns_baseline, "EUR/USD", "baseline_performance.png")
print_results("Baseline (t < -1)", returns_baseline)
print_results("Improved (t < -1.5)", returns_improved)

# Compare both strategies
portfolio_baseline = np.cumprod(1 + returns_baseline)
portfolio_improved = np.cumprod(1 + returns_improved)
plt.figure(figsize=(12, 6))
plt.plot(portfolio_baseline, label="Baseline (t < -1)", linewidth=1.5)
plt.plot(portfolio_improved, label="Improved (t < -1.5)", linewidth=1.5)
plt.legend()
plt.title("EUR/USD: Strategy Comparison")
plt.xlabel("Trading Days")
plt.ylabel("Portfolio Value")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("outputs/strategy_comparison.png", dpi=150)
plt.close()
print("  Comparison saved: outputs/strategy_comparison.png")

print("\n=== GBP/USD ===")
gbpusd = load_and_prepare('data/gbpusd_data.csv', 'GBPUSD')

alpha, beta, tstat = test_mean_reversion(gbpusd)
print(f"\nMean Reversion Test:")
print(f"  Alpha: {alpha:.6f}, Beta: {beta:.6f}, t-stat: {tstat:.2f}")
print(f"  Signal: {'Detected' if beta < 0 and tstat < -1 else 'Weak'}")

returns_gbp = run_strategy(gbpusd)
save_chart(returns_gbp, "GBP/USD", "gbpusd_performance.png")
print_results("GBP/USD", returns_gbp)

print("\n=== USD/JPY ===")
usdjpy = load_and_prepare('data/usdjpy_data.csv', 'USDJPY')

alpha, beta, tstat = test_mean_reversion(usdjpy)
print(f"\nMean Reversion Test:")
print(f"  Alpha: {alpha:.6f}, Beta: {beta:.6f}, t-stat: {tstat:.2f}")
print(f"  Signal: {'Detected' if beta < 0 and tstat < -1 else 'NOT TRADEABLE'}")

returns_jpy = run_strategy(usdjpy, t_crit=-2.0, beta_min=-0.002)
save_chart(returns_jpy, "USD/JPY", "usdjpy_performance.png")
print_results("USD/JPY", returns_jpy)
print("  Note: Insufficient mean reversion signal - use with caution")

print("\nDone!")
