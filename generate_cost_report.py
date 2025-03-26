#!/usr/bin/env python3
import os
import json
import csv
from datetime import datetime, timedelta
from collections import defaultdict
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def get_date_from_filename(filename):
    """Extract date from filename like 2025-03-26.json"""
    return filename.split('.')[0]

def load_orders_from_dir(directory):
    """Load all orders from JSON files in a directory"""
    all_orders = []
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return all_orders
    
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, 'r') as f:
                    orders = json.load(f)
                    if isinstance(orders, list):
                        all_orders.extend(orders)
                    else:
                        print(f"Warning: {file_path} doesn't contain a list")
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    return all_orders

def create_cost_plots(df, output_dir='reports'):
    """Create visualizations of cost data"""
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Set the style
    plt.style.use('ggplot')
    
    # 1. Daily costs stacked bar chart
    plt.figure(figsize=(14, 8))
    df.plot(
        x='date',
        y=['printful_cost', 'printify_cost', 'burger_cost'],
        kind='bar',
        stacked=True,
        title='Daily Costs by Platform',
        color=['#3498db', '#e74c3c', '#2ecc71'],
        figsize=(14, 8)
    )
    plt.xlabel('Date')
    plt.ylabel('Cost ($)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/daily_costs_by_platform.png')
    
    # 2. Platform cost comparison pie chart
    plt.figure(figsize=(10, 10))
    platform_totals = [
        df['printful_cost'].sum(),
        df['printify_cost'].sum(),
        df['burger_cost'].sum()
    ]
    plt.pie(
        platform_totals,
        labels=['Printful', 'Printify', 'Burger Prints'],
        autopct='%1.1f%%',
        startangle=90,
        colors=['#3498db', '#e74c3c', '#2ecc71']
    )
    plt.axis('equal')
    plt.title('Cost Distribution by Platform')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/platform_cost_distribution.png')
    
    # 3. Trend line for total costs
    plt.figure(figsize=(14, 8))
    # Convert date to datetime and sort
    df['date_dt'] = pd.to_datetime(df['date'])
    df = df.sort_values('date_dt')
    
    # Calculate 7-day moving average
    df['7day_avg'] = df['total'].rolling(window=7, min_periods=1).mean()
    
    plt.plot(df['date_dt'], df['total'], marker='o', linestyle='-', color='#3498db', alpha=0.7, label='Daily Total')
    plt.plot(df['date_dt'], df['7day_avg'], linestyle='-', linewidth=3, color='#e74c3c', label='7-Day Moving Avg')
    
    plt.title('Daily Total Cost Trend')
    plt.xlabel('Date')
    plt.ylabel('Total Cost ($)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/total_cost_trend.png')
    
    print(f"Visualizations saved to {output_dir}/ directory")

def analyze_data(df):
    """Perform detailed data analysis"""
    # Basic statistics
    stats = {
        'total_days': len(df),
        'total_cost': df['total'].sum(),
        'avg_daily_cost': df['total'].mean(),
        'max_daily_cost': df['total'].max(),
        'max_cost_date': df.loc[df['total'].idxmax(), 'date'],
        'min_daily_cost': df['total'].min(),
        'min_cost_date': df.loc[df['total'].idxmin(), 'date'],
        'printful_total': df['printful_cost'].sum(),
        'printful_avg': df['printful_cost'].mean(),
        'printify_total': df['printify_cost'].sum(),
        'printify_avg': df['printify_cost'].mean(),
        'burger_total': df['burger_cost'].sum(),
        'burger_avg': df['burger_cost'].mean(),
    }
    
    # Calculate platform percentages
    total = stats['total_cost']
    stats['printful_pct'] = (stats['printful_total'] / total) * 100
    stats['printify_pct'] = (stats['printify_total'] / total) * 100
    stats['burger_pct'] = (stats['burger_total'] / total) * 100
    
    # Weekly analysis if we have enough data
    if len(df) >= 7:
        # Convert date to datetime if it's not already
        if 'date_dt' not in df.columns:
            df['date_dt'] = pd.to_datetime(df['date'])
        
        # Get the most recent week
        most_recent_date = df['date_dt'].max()
        week_ago = most_recent_date - timedelta(days=7)
        last_week_df = df[df['date_dt'] > week_ago]
        
        stats['last_week_total'] = last_week_df['total'].sum()
        stats['last_week_avg'] = last_week_df['total'].mean()
    
    return stats

def generate_report(df, stats, output_dir='reports'):
    """Generate a detailed text report"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    report_file = f"{output_dir}/cost_analysis_report.txt"
    
    with open(report_file, 'w') as f:
        f.write("========================================\n")
        f.write("          COST ANALYSIS REPORT          \n")
        f.write("========================================\n\n")
        
        f.write("OVERALL SUMMARY\n")
        f.write("--------------\n")
        f.write(f"Total Days Analyzed: {stats['total_days']}\n")
        f.write(f"Total Cost: ${stats['total_cost']:.2f}\n")
        f.write(f"Average Daily Cost: ${stats['avg_daily_cost']:.2f}\n")
        f.write(f"Highest Daily Cost: ${stats['max_daily_cost']:.2f} on {stats['max_cost_date']}\n")
        f.write(f"Lowest Daily Cost: ${stats['min_daily_cost']:.2f} on {stats['min_cost_date']}\n\n")
        
        f.write("PLATFORM BREAKDOWN\n")
        f.write("-----------------\n")
        f.write(f"Printful Total: ${stats['printful_total']:.2f} ({stats['printful_pct']:.1f}%)\n")
        f.write(f"Printful Average Daily: ${stats['printful_avg']:.2f}\n\n")
        
        f.write(f"Printify Total: ${stats['printify_total']:.2f} ({stats['printify_pct']:.1f}%)\n")
        f.write(f"Printify Average Daily: ${stats['printify_avg']:.2f}\n\n")
        
        f.write(f"Burger Prints Total: ${stats['burger_total']:.2f} ({stats['burger_pct']:.1f}%)\n")
        f.write(f"Burger Prints Average Daily: ${stats['burger_avg']:.2f}\n\n")
        
        if 'last_week_total' in stats:
            f.write("RECENT TRENDS\n")
            f.write("-------------\n")
            f.write(f"Last 7 Days Total: ${stats['last_week_total']:.2f}\n")
            f.write(f"Last 7 Days Average: ${stats['last_week_avg']:.2f}\n\n")
        
        f.write("TOP 5 HIGHEST COST DAYS\n")
        f.write("----------------------\n")
        top_days = df.sort_values('total', ascending=False).head(5)
        for _, row in top_days.iterrows():
            f.write(f"{row['date']}: ${row['total']:.2f} (Printful: ${row['printful_cost']:.2f}, "
                   f"Printify: ${row['printify_cost']:.2f}, Burger: ${row['burger_cost']:.2f})\n")
        
    print(f"Analysis report saved to {report_file}")
    
    return report_file

def main():
    base_dir = "data/orders"
    output_dir = "reports"
    
    # Define platform directories
    printful_dir = os.path.join(base_dir, "printful")
    printify_dir = os.path.join(base_dir, "printify")
    burger_dir = os.path.join(base_dir, "burger_prints")
    
    # Load orders from each platform
    printful_orders = load_orders_from_dir(printful_dir)
    printify_orders = load_orders_from_dir(printify_dir)
    burger_orders = load_orders_from_dir(burger_dir)
    
    print(f"Loaded {len(printful_orders)} orders from Printful")
    print(f"Loaded {len(printify_orders)} orders from Printify")
    print(f"Loaded {len(burger_orders)} orders from Burger Prints")
    
    # Group orders by date
    daily_costs = defaultdict(lambda: {"printful_cost": 0, "printify_cost": 0, "burger_cost": 0, "total": 0})
    
    # Process Printful orders
    for order in printful_orders:
        # Get date part from order_date
        date_str = order.get("order_date", "").split(" ")[0] if order.get("order_date") else None
        if date_str:
            final_price = float(order.get("final_price", 0))
            daily_costs[date_str]["printful_cost"] += final_price
            daily_costs[date_str]["total"] += final_price
    
    # Process Printify orders
    for order in printify_orders:
        date_str = order.get("order_date", "").split(" ")[0] if order.get("order_date") else None
        if date_str:
            final_price = float(order.get("final_price", 0))
            daily_costs[date_str]["printify_cost"] += final_price
            daily_costs[date_str]["total"] += final_price
    
    # Process Burger Prints orders
    for order in burger_orders:
        date_str = order.get("order_date", "").split(" ")[0] if order.get("order_date") else None
        if date_str:
            final_price = float(order.get("final_price", 0))
            daily_costs[date_str]["burger_cost"] += final_price
            daily_costs[date_str]["total"] += final_price
    
    # Convert to DataFrame for easier analysis
    data = []
    for date, costs in daily_costs.items():
        row = {"date": date}
        row.update(costs)
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Sort by date
    df = df.sort_values('date')
    
    # Create CSV file
    output_file = os.path.join(output_dir, "daily_platform_costs.csv")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    df.to_csv(output_file, index=False)
    print(f"CSV report generated: {output_file}")
    
    # Generate visualizations
    create_cost_plots(df, output_dir)
    
    # Analyze and report
    stats = analyze_data(df)
    report_file = generate_report(df, stats, output_dir)
    
    # Print summary to console
    print(f"\nSummary:")
    print(f"Total Printful cost: ${stats['printful_total']:.2f} ({stats['printful_pct']:.1f}%)")
    print(f"Total Printify cost: ${stats['printify_total']:.2f} ({stats['printify_pct']:.1f}%)")
    print(f"Total Burger Prints cost: ${stats['burger_total']:.2f} ({stats['burger_pct']:.1f}%)")
    print(f"Grand total: ${stats['total_cost']:.2f}")
    print(f"\nDetailed report and visualizations saved to {output_dir}/ directory")

if __name__ == "__main__":
    main() 