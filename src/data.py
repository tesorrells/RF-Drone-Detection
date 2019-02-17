import os
from typing import List
import pandas as pd

from sklearn.model_selection import train_test_split


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


def read_hackrf_sweep_file_and_merge(path) -> pd.DataFrame:
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


def get_mean_by_bin(df: pd.DataFrame) -> pd.Series:
    """
    Takes all the sweep data from the input dataframe as returned by read_hackrf_sweep_file_and_merge
    and gets the average db for each bin.
    Returns as a pandas Series

    :param df: pd.DataFrame from experiment in question
    :return: pd.Series of average
    """
    return df.mean(axis=0)

def get_train_test_data(positive: List, negative: List, testSize=0.2):
    """
    Takes in string or list of string paths to data files for both positive and
    negative examples of our hackrf_sweep data and returns a train and test
    split of inputs and their labels


    :param positive: the list files containing positive examples
    :param negative: the list of files containing negative examples
    returns a four tuple of x_train, x_test, y_train, y_test
    """
    # 1 for positive examples (drones flying) and 0 for just random noise
    labels = [1.0, 0.0]

    labeled_data = pd.DataFrame()
    for files, label in zip([positive, negative], labels):
        for filename in files:
            new_data = read_hackrf_sweep_file_and_merge(filename)
            new_data['label'] = label
            labeled_data = labeled_data.append(new_data)

    
    labels = labeled_data['label']
    inputs = labeled_data.drop('label', axis=1)
    return train_test_split(inputs, labels, test_size=testSize)

if __name__ == "__main__":
    drone_filename = "../data/2019.02.15_dji/2019.02.15.25_meters_dji.csv"
    noise_filename = "../data/2019.02.15_dji/2019.02.15.bg_after_25_meters_dji.csv"
    

    # filename = "../data/25_meters.csv"
    print("Working in %s" % os.getcwd())
    print("Using file %s" % drone_filename)
    print("Example of reading in 25 meter dji data")
    print("=======================================")
    sample_data = read_hackrf_sweep_file_and_merge(drone_filename)
    sample_data.info()  # just print out some info about the dataframe
    print("---------------------------------------")
    print(sample_data.head(5))
    print("=======================================")
    print("\nExample of getting avg for each bin (pandas Series):")
    print("=======================================")
    avg_by_bin = get_mean_by_bin(sample_data)
    print("Shape: %s" % avg_by_bin.shape)
    print("---------------------------------------")
    print(avg_by_bin.head(4))
    print("\t...")
    print(avg_by_bin.tail(4))
    print("=======================================")
    print("\n Creating a split of our positive and negative examples for use in learning models: ")
    x_train, x_test, y_train, y_test = get_train_test_data(positive=[drone_filename], negative=[noise_filename])
    print("Training examples: " + str(x_train.head()) + "\nTraining Labels: " + str(y_train.head()))
    
    pass
