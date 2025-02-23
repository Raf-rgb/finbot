import logging
import pandas as pd
import plotly.express as px

from datetime import datetime
from utils.models import MovementType

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

def get_total_movements_by_month(df: pd.DataFrame, movement_type:MovementType) -> pd.DataFrame:
    try:
        df["datetime"] = pd.to_datetime(df["datetime"], format="%Y-%m-%d %H:%M:%S")
        df["month"] = df["datetime"].dt.month
        df["year"]  = df["datetime"].dt.year

        total_expenses_by_month = df[df["movement_type"] == movement_type].groupby(["year", "month"])["amount"].sum().reset_index()
        total_expenses_by_month["month"] = total_expenses_by_month["month"].apply(lambda x: pd.to_datetime(str(x), format="%m").strftime("%B"))

        return total_expenses_by_month
    except Exception as e:
        logging.error(f"Error getting the total expenses by month: {e}")
        return None

def get_current_week_movements(df: pd.DataFrame, movement_type:MovementType) -> float:
    try:
        df["datetime"] = pd.to_datetime(df["datetime"], format="%Y-%m-%d %H:%M:%S")
        current_year  = datetime.now().year
        current_month = datetime.now().month
        current_week  = datetime.now().isocalendar()[1]

        current_week_expenses = df[(df["movement_type"] == movement_type) &
                                    (df["datetime"].dt.year == current_year) &
                                    (df["datetime"].dt.month == current_month) &
                                    (df["datetime"].dt.isocalendar().week == current_week)]["amount"].sum()
        
        return current_week_expenses
    except Exception as e:
        logging.error(f"Error getting the current week expenses: {e}")
        return 0.0

def get_last_week_movements(df: pd.DataFrame, movement_type:MovementType) -> float:
    try:
        df["datetime"] = pd.to_datetime(df["datetime"], format="%Y-%m-%d %H:%M:%S")
        last_week = datetime.now().isocalendar()[1] - 1

        if last_week == 0:
            last_week = 52

        last_week_expenses = df[(df["movement_type"] == movement_type) & (df["datetime"].dt.isocalendar().week == last_week)]["amount"].sum()

        return last_week_expenses
    except Exception as e:
        logging.error(f"Error getting the last week expenses: {e}")
        return 0.0

def get_current_day_movements(df: pd.DataFrame, movement_type:MovementType) -> float:
    try:
        df["datetime"] = pd.to_datetime(df["datetime"], format="%Y-%m-%d %H:%M:%S")
        current_year  = datetime.now().year
        current_month = datetime.now().month
        current_day   = datetime.now().day

        current_day_expenses = df[(df["movement_type"] == movement_type) &
                                  (df["datetime"].dt.year == current_year) &
                                  (df["datetime"].dt.month == current_month) &
                                  (df["datetime"].dt.day == current_day)]["amount"].sum()

        return current_day_expenses
    except Exception as e:
        logging.error(f"Error getting the current day expenses: {e}")
        return 0.0
    
def get_last_day_movements(df: pd.DataFrame, movement_type:MovementType) -> float:
    try:
        df["datetime"] = pd.to_datetime(df["datetime"], format="%Y-%m-%d %H:%M:%S")
        last_day = datetime.now().day - 1

        if last_day == 0:
            last_day = 31

        last_day_expenses = df[(df["movement_type"] == movement_type) & (df["datetime"].dt.day == last_day)]["amount"].sum()

        return last_day_expenses
    except Exception as e:
        logging.error(f"Error getting the last day expenses: {e}")
        return 0.0

def get_last_month_movements(df: pd.DataFrame, movement_type:MovementType) -> float:
    try:
        df["datetime"] = pd.to_datetime(df["datetime"], format="%Y-%m-%d %H:%M:%S")
        last_month = datetime.now().month - 1

        if last_month == 0:
            last_month = 12

        last_month_expenses = df[(df["movement_type"] == movement_type) & (df["datetime"].dt.month == last_month)]["amount"].sum()

        return last_month_expenses
    except Exception as e:
        logging.error(f"Error getting the last month expenses: {e}")
        return 0.0

def get_current_month_movements(df: pd.DataFrame, movement_type:MovementType) -> float:
    try:
        df["datetime"] = pd.to_datetime(df["datetime"], format="%Y-%m-%d %H:%M:%S")
        current_year   = datetime.now().year
        current_month  = datetime.now().month

        current_month_expenses = df[(df["movement_type"] == movement_type) & 
                                    (df["datetime"].dt.year == current_year) & 
                                    (df["datetime"].dt.month == current_month)]["amount"].sum()

        return current_month_expenses
    except Exception as e:
        logging.error(f"Error getting the current month expenses: {e}")
        return 0.0

def plot_line_total_movements_by_month(df: pd.DataFrame, movement_type:MovementType):
    try:
        total_movements_by_month = get_total_movements_by_month(df, movement_type)

        if total_movements_by_month is not None:
            fig = px.line(
                total_movements_by_month,
                x="month",
                y="amount",
                title=f"Total {movement_type.value} by month",
                labels={"amount": "Amount ($)", "month": "Month"},
                color="year"
            )

            return fig
        else:
            return None
    except Exception as e:
        logging.error(f"Error plotting the total movements by month: {e}")
        return None
    
def plot_total_movements_by_month(df: pd.DataFrame, movement_type:MovementType):
    try:
        total_movements_by_month = get_total_movements_by_month(df, movement_type)

        if total_movements_by_month is not None:
            fig = px.bar(
                total_movements_by_month,
                x="month",
                y="amount",
                title=f"Total {movement_type.value} by month",
                labels={"amount": "Amount ($)", "month": "Month"},
                color="year",
                barmode="group"
            )

            return fig
        else:
            return None
    except Exception as e:
        logging.error(f"Error plotting the total movements by month: {e}")
        return None