import pandas as pd



def read_hack_rf_sweep_file(path):
    # Nicely formats the hackrf data
    data = pd.read_csv(path, header=None)
    num_rows, num_cols = data.shape


    # sets the header values for a hackrf_sweep csv
    col_names = ["date", "time", "hz_low", "hz_high", "bin_width",
            "num_samples"]
    col_names += ["db_%d"%i for i in range(num_cols - len(col_names))]

    data.columns = col_names

    # appends new column to the end as the average db reading per bin in range
    readings = data.loc[:, "db_0":]
    data["db_avg"] = readings.mean(axis=1)

    return data


def get_average_activity(data):
    # Requires a hackrf data fram (as returned by read_hack_rf_sweep_file) and
    # will average the bins and readings across the entire time it was recorded
    db_readings = data.loc[:, "hz_low":]
    return db_readings.groupby("hz_low", as_index=False).mean()



print("Example of reading in 25 meter data")
print("==================================")
sample_data = read_hack_rf_sweep_file("../data/25_meters.csv")
print(sample_data.head(5))


print("\nAveraged readings in a file")
print("==================================")
print(get_average_activity(sample_data).head(5))
