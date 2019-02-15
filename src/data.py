import os

import pandas as pd


# # Original functions -- just commented these out so i didn't get confused.
# def read_hack_rf_sweep_file(path):
#     # Nicely formats the hackrf data
#     data = pd.read_csv(path, header=None)
#     num_rows, num_cols = data.shape
#
#     # sets the header values for a hackrf_sweep csv
#     col_names = ["date", "time", "hz_low", "hz_high", "bin_width",
#                  "num_samples"]
#     col_names += ["db_%d" % i for i in range(num_cols - len(col_names))]
#
#     data.columns = col_names
#
#     # appends new column to the end as the average db reading per bin in range
#     readings = data.loc[:, "db_0":]
#     data["db_avg"] = readings.mean(axis=1)
#
#     return data
#
#
# def get_average_activity(data):
#     # Requires a hackrf data frame (as returned by read_hack_rf_sweep_file) and
#     # will average the bins and readings across the entire time it was recorded
#     db_readings = data.loc[:, "hz_low":]
#     return db_readings.groupby("hz_low", as_index=False).mean()


def dt_lookup(s):
    """
    Helper func. This is an extremely fast approach to datetime parsing.
    For large data, the same dates are often repeated. Rather than
    re-parse these, we store all unique dates, parse them, and
    use a lookup to convert all dates.

    https://stackoverflow.com/questions/29882573/pandas-slow-date-conversion
    """
    return s.map({date: pd.to_datetime(date) for date in s.unique()})


def read_hackrf_sweep_file_and_merge(path):
    """
    Takes in the path to an output file from hackrf_sweep. hackrf_sweep spreads the output of a single sweep over
    multiple lines. This combines those lines. So that:
    - one row is one whole sweep (180 bins)
    - row indexed by datetime timestamp
    - columns (ie bins) are floor(starting_bin_freq_hz)

    With current hackrf_sweep settings, this yields a dataframe with 180 rows

    :param path: filepath_or_buffer : str, path object, or file-like object
    :return: pd.DataFrame
    """
    # Nicely formats the hackrf hackrf_df
    hackrf_df: pd.DataFrame = pd.read_csv(path, header=None)

    # Index everything by date+time
    datetime = pd.DatetimeIndex(dt_lookup(hackrf_df[0] + hackrf_df[1]))
    hackrf_df = hackrf_df.set_index(datetime)
    hackrf_df[0] = datetime

    # Group according to datetime timestamp
    grouped = hackrf_df.groupby(hackrf_df.index)
    merged_df = pd.DataFrame()
    min_freq = hackrf_df[2].min()
    max_freq = hackrf_df[3].max()
    for name, group in grouped:  # merge same timestamp into one row
        try:
            merged_df[name] = group.iloc[:, 6:].stack().values
        except ValueError:
            # Error occurs when we get fewer rows than expected because of hackrf_sweep terminating
            print("Got incorrect number of rows... discarding timestamp %s (ok if only a few of these)" % name)
    merged_df: pd.DataFrame = merged_df.T  # swap rows/cols because it came out the other way
    num_bins = merged_df.shape[1]
    bin_size = (max_freq - min_freq) / num_bins  # in hz
    # set col name to min freq for each sample i.e. sample starting at 2400000000 hz
    merged_df.columns = [int((min_freq + x * bin_size)) for x in range(0, num_bins)]

    return merged_df


def get_mean_db_by_bin(df: pd.DataFrame):
    """
    Takes all the sweep data from the input dataframe as returned by read_hackrf_sweep_file_and_merge
    and gets the average db for each bin.
    Returns as a pandas Series

    :param df: pd.DataFrame from experiment in question
    :return: pd.Series of average
    """
    return df.mean(axis=0)


if __name__ == "__main__":
    filename = "../../Drone-Data-Collection/data/2019.02.15_dji/2019.02.15.25_meters_dji.csv"
    # filename = "../../Drone-Data-Collection/data/2019.02.01_chi/2019.02.01.25_meters_chi.csv"
    # filename = "../data/25_meters.csv"
    print("Working in %s" % os.getcwd())
    print("Using file %s" % filename)
    print("Example of reading in 25 meter data")
    print("==================================")
    sample_data = read_hackrf_sweep_file_and_merge(filename)
    # sample_data = read_hackrf_sweep_file("../data/25_meters.csv")
    print(sample_data.head(5))

    # print("\nAveraged readings in a file")
    # print("==================================")
    # print(get_average_activity(sample_data).head(5))
    # print(get_average_activity(sample_data).head(5))
