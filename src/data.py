from typing import Any, Union

import pandas as pd
from pandas import DataFrame
from pandas.io.parsers import TextFileReader


def read_hack_rf_sweep_file(path):
    # Nicely formats the hackrf data
    data = pd.read_csv(path, header=None)
    num_rows, num_cols = data.shape

    # sets the header values for a hackrf_sweep csv
    col_names = ["date", "time", "hz_low", "hz_high", "bin_width",
                 "num_samples"]
    col_names += ["db_%d" % i for i in range(num_cols - len(col_names))]

    data.columns = col_names

    # appends new column to the end as the average db reading per bin in range
    readings = data.loc[:, "db_0":]
    data["db_avg"] = readings.mean(axis=1)

    return data


def read_hack_rf_sweep_file_and_merge(path):
    # Nicely formats the hackrf data
    data: pd.DataFrame = pd.read_csv(path, header=None)
    # fast method for indexing by datetime

    # Index everything by date+time
    datetime = pd.DatetimeIndex(lookup(data[0] + data[1]))
    data = data.set_index(datetime)
    data[0] = datetime
    num_rows, num_cols = data.shape

    # Group according to datetime timestamp
    grouped = data.groupby(data.index)
    temp_df = pd.DataFrame()
    min_freq = data[2].min()
    max_freq = data[3].max()
    for name, group in grouped:  # merge same timestamp into one row
        temp_df[name] = group.iloc[:, 6:].stack().values
    temp_df: pd.DataFrame = temp_df.T  # transpose because it came out the other way
    num_bins = temp_df.shape[1]
    bin_size = (max_freq - min_freq) / num_bins  # in hz
    # set col name to min freq for each sample i.e. sample starting at 2400000000 hz
    temp_df.columns = [int((min_freq + x * bin_size)) for x in range(0, num_bins)]

    # # sets the header values for a hackrf_sweep csv
    # col_names = ["datetime", "hz_low", "hz_high", "bin_width",
    #              "num_samples"]
    # # col_names += ["db_%d" % i for i in range(num_cols - len(col_names))]
    #
    # col_names += ["db_%d" % i for i in range(num_cols - len(col_names))]
    #
    # data.columns = col_names
    #
    # # appends new column to the end as the average db reading per bin in range
    # readings = data.loc[:, "db_0":]
    # data["db_avg"] = readings.mean(axis=1)

    return temp_df


def get_average_activity(data):
    # Requires a hackrf data frame (as returned by read_hack_rf_sweep_file) and
    # will average the bins and readings across the entire time it was recorded
    db_readings = data.loc[:, "hz_low":]
    return db_readings.groupby("hz_low", as_index=False).mean()


def lookup(s):
    """
    https://stackoverflow.com/questions/29882573/pandas-slow-date-conversion
    This is an extremely fast approach to datetime parsing.
    For large data, the same dates are often repeated. Rather than
    re-parse these, we store all unique dates, parse them, and
    use a lookup to convert all dates.
    """
    dates = {date: pd.to_datetime(date) for date in s.unique()}
    return s.map(dates)


if __name__ == "__main__":
    print("Example of reading in 25 meter data")
    print("==================================")
    sample_data = read_hack_rf_sweep_file_and_merge("../data/25_meters.csv")
    # sample_data = read_hack_rf_sweep_file("../data/25_meters.csv")
    print(sample_data.head(5))

    # print("\nAveraged readings in a file")
    # print("==================================")
    # print(get_average_activity(sample_data).head(5))
    # print(get_average_activity(sample_data).head(5))
