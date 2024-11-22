import requests
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import argparse

def fetch_ethereum_tvl():
    """
    Fetch historical TVL data for Ethereum from Llama.fi API
    Returns processed TVL data with dates and values
    """
    url = "https://api.llama.fi/v2/historicalChainTvl/Ethereum"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        processed_data = []
        
        for entry in data:
            date = datetime.fromtimestamp(entry['date'])
            tvl = round(float(entry['tvl']), 2)
            processed_data.append({
                'date': date,
                'tvl': tvl
            })
        
        return processed_data
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def filter_data_by_months(data, months):
    """Filter data for the last N months"""
    if not data:
        return []
    
    cutoff_date = datetime.now() - timedelta(days=30 * months)
    return [d for d in data if d['date'] >= cutoff_date]

def get_display_interval(months, data_length):
    """
    Determine the display interval based on the time period:
    3 months: daily (interval=1)
    6 months: every 3 days (interval=3)
    12 months: weekly (interval=7)
    """
    if months == 3:
        return 1, "Daily"
    elif months == 6:
        return 3, "Every 3 Days"
    else:  # 12 months
        return 7, "Weekly"

def plot_tvl_data(data, months):
    """Create a plot of TVL data"""
    dates = [entry['date'] for entry in data]
    tvl_values = [entry['tvl'] / 1e9 for entry in data]  # Convert to billions
    
    plt.figure(figsize=(15, 8))
    plt.plot(dates, tvl_values, 'b-', linewidth=2)
    
    # Determine interval type for title
    _, interval_type = get_display_interval(months, len(data))
    plt.title(f'Ethereum TVL - Last {months} Months ({interval_type} Data)', fontsize=14, pad=20)
    
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('TVL (Billion USD)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    
    # Format y-axis with billion USD
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:.2f}B'))
    
    # Add data points
    plt.plot(dates, tvl_values, 'bo', markersize=4)
    
    # Enhance the layout
    plt.tight_layout()
    
    # Save plot with high DPI for better quality
    plt.savefig(f'eth_tvl_{months}m.png', dpi=300, bbox_inches='tight')
    plt.close()

def display_data(data, months):
    """Display TVL data in table format with appropriate intervals"""
    interval_days, interval_type = get_display_interval(months, len(data))
    
    print(f"\nEthereum TVL - Last {months} Months ({interval_type} Data)")
    print("Date\t\t\tTVL (USD)\t\tChange")
    print("-" * 65)
    
    # Filter data based on interval
    filtered_data = []
    last_date = data[-1]['date']
    current_date = data[0]['date']
    
    while current_date <= last_date:
        # Find the closest data point to current_date
        closest_entry = min(data, key=lambda x: abs(x['date'] - current_date))
        if abs((closest_entry['date'] - current_date).days) <= 1:  # Within 1 day tolerance
            filtered_data.append(closest_entry)
        current_date += timedelta(days=interval_days)
    
    # Display data with percentage changes
    for i in range(len(filtered_data)):
        entry = filtered_data[i]
        date_str = entry['date'].strftime('%Y-%m-%d')
        tvl = entry['tvl']
        
        # Calculate percentage change from previous entry
        if i > 0:
            prev_tvl = filtered_data[i-1]['tvl']
            change_pct = ((tvl - prev_tvl) / prev_tvl) * 100
            change_str = f"{change_pct:+.2f}%"
        else:
            change_str = "---"
        
        print(f"{date_str}\t${tvl:,.2f}\t{change_str}")

def main():
    parser = argparse.ArgumentParser(
        description="""
Ethereum TVL Analysis Tool
Displays Total Value Locked (TVL) data with different time intervals:
- 3 months: Daily data points
- 6 months: Every 3 days data points
- 12 months: Weekly data points
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py 3    # Show daily data for the last 3 months
  python3 main.py 6    # Show 3-day interval data for the last 6 months
  python3 main.py 12   # Show weekly data for the last 12 months
        """
    )
    
    parser.add_argument(
        'months',
        type=int,
        choices=[3, 6, 12],
        metavar='MONTHS',
        help='Number of months to analyze: 3 (daily), 6 (3-day intervals), or 12 (weekly)'
    )
    
    if len(plt.get_fignums()) > 0:
        plt.close('all')
    
    try:
        args = parser.parse_args()
    except SystemExit:
        return

    print(f"Fetching Ethereum TVL data for the last {args.months} months...")
    
    # Fetch and process data
    all_data = fetch_ethereum_tvl()
    if all_data:
        filtered_data = filter_data_by_months(all_data, args.months)
        filtered_data.sort(key=lambda x: x['date'])  # Ensure chronological order
        
        # Display table data
        display_data(filtered_data, args.months)
        
        # Create and save plot
        plot_tvl_data(filtered_data, args.months)
        print(f"\nPlot saved as 'eth_tvl_{args.months}m.png'")

if __name__ == "__main__":
    main()
