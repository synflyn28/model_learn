import argparse
from datetime import datetime, timedelta
import logging

import numpy as np
import pandas as pd
from sklearn.ensemble import AdaBoostRegressor, BaggingRegressor, ExtraTreesRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsRegressor
from sklearn.svm import SVR
import xarray as xr

# ----------------------------------------------------------------------------------------------------------------------
# set up a basic, global _logger which will write to the console as standard error
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d  %H:%M:%S')
_logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------------------------------------------------------
def train_test_linear(x_train,
                      y_train,
                      x_test,
                      y_test):
    """
    Train and test a number of regression models using a train/test split of single dataset, and log/report scores.

    :param x_train:
    :param y_train:
    :param x_test:
    :param y_test:
    :return: None
    """

    # create and train a linear regression model
    model = LinearRegression()
    model.fit(x_train, y_train)
    score = model.score(x_test, y_test)
    _logger.info("LRM score: {result}".format(result=score))

    # create and train a ridge regression model
    model = Ridge()
    model.fit(x_train, y_train)
    score = model.score(x_test, y_test)
    _logger.info("Ridge score: {result}".format(result=score))

    # create and train a random forest regression model
    for trees in [3, 10, 20, 100, 250]:
        model = RandomForestRegressor(n_estimators=trees)
        model.fit(x_train, y_train)
        score = model.score(x_test, y_test)
        _logger.info("Random Forest (trees={t}) score: {result}".format(t=trees, result=score))

    # create and train a K-neighbors regression model
    for k in [1, 3, 5, 10, 20]:
        model = KNeighborsRegressor(n_neighbors=k)
        model.fit(x_train, y_train)
        score = model.score(x_test, y_test)
        _logger.info("K-Neighbors (k={k}) score: {result}".format(k=k, result=score))

    # # create and train an Ada boost regression model, trying various estimators and learning rate parameters
    # for estimators in [1, 3, 5, 10, 20]:
    #     for rate in [0.01, 0.1, 1, 5, 12]:
    #         model = AdaBoostRegressor(n_estimators=estimators, learning_rate=rate)
    #         model.fit(x_train, y_train)
    #         score = model.score(x_test, y_test)
    #         _logger.info("Ada Boost (estimators={n}, learning rate={r}) score: {result}".format(n=estimators,
    #                                                                                             r=rate,
    #                                                                                             result=score))

    # # create and train a bagging regression model
    # model = BaggingRegressor()
    # model.fit(x_train, y_train)
    # score = model.score(x_test, y_test)
    # _logger.info("Bagging score: {result}".format(result=score))

    # create and train an extra trees regression model
    for trees in [3, 6, 10, 20]:
        model = ExtraTreesRegressor(n_estimators=trees)
        model.fit(x_train, y_train)
        score = model.score(x_test, y_test)
        _logger.info("Extra Trees (trees={t}) score: {result}".format(t=trees, result=score))

    # create and train a support vector regression model with an linear kernel
    model = SVR(kernel='linear', C=1e3)
    model.fit(x_train.flatten(), y_train.flatten())
    score = model.score(x_test, y_test)
    _logger.info("SVR (linear) score: {result}".format(result=score))

    # create and train a support vector regression model with a polynomial kernel
    model = SVR(kernel='poly', C=1e3, degree=2)
    model.fit(x_train, y_train)
    score = model.score(x_test, y_test)
    _logger.info("SVR (polynomial) score: {result}".format(result=score))

    # create and train a support vector regression model with an RBF kernel
    model = SVR(kernel='rbf', C=1e3, gamma=0.1)
    model.fit(x_train, y_train)
    score = model.score(x_test, y_test)
    _logger.info("SVR (RBF) score: {result}".format(result=score))


# ----------------------------------------------------------------------------------------------------------------------
def extract_timestamps(ds,
                       initial_year,
                       initial_month,
                       initial_day):

    # Cook up an initial datetime object based on our specified initial date.
    initial = datetime(initial_year, initial_month, initial_day)

    # Create an array of datetime objects from the time values (assumed to be in units of days since the inital date).
    times = ds.variables['time'].values
    datetimes = np.empty(shape=times.shape, dtype='datetime64[m]')
    for i in range(datetimes.size):
        datetimes[i] = initial + timedelta(days=times[i])

    # Put the array into a Series and return it.
    return pd.Series(datetimes)


# ----------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    """
    This module is used to showcase ML modeling of the climate using scikit-learn, using NCAR CAM files as input.
    """

    try:

        # parse the command line arguments
        parser = argparse.ArgumentParser()
        parser.add_argument("--input_flows",
                            help="NetCDF file containing flow variables",
                            nargs='*',
                            required=True)
        parser.add_argument("--input_tendencies",
                            help="NetCDF file containing time tendency forcing variables",
                            nargs='*',
                            required=True)
        args = parser.parse_args()

        # open the features (flows) and labels (tendencies) as xarray DataSets
        ds_features = xr.open_mfdataset(args.input_flows)
        ds_labels = xr.open_mfdataset(args.input_tendencies)

        # confirm that we have datasets that match on the time dimension/coordinate
        if (ds_features.variables['time'].values != ds_labels.variables['time'].values).any():
            _logger.info('ERROR: Non-matching time values')
        else:
            _logger.info("OK: time values match as expected")

        # # TODO get initial year, month, and day from the datasets
        # init_year = 2000
        # init_month = 12
        # init_day = 27
        # timestamps = extract_timestamps(ds_features, init_year, init_month, init_day)

        # put features dataset values into a pandas DataFrame
        ps = pd.Series(ds_features.variables['PS'].values[:, :, :].flatten())
        t = pd.Series(ds_features.variables['T'].values[:, 0, :, :].flatten())
        u = pd.Series(ds_features.variables['U'].values[:, 0, :, :].flatten())
        v = pd.Series(ds_features.variables['V'].values[:, 0, :, :].flatten())
        df_features = pd.DataFrame({'PS': ps,
                                    'T': t,
                                    'U': u,
                                    'V': v})
        df_features.index.rename('index', inplace=True)

        # put labels dataset values into a pandas DataFrame
        pttend = pd.Series(ds_labels.variables['PTTEND'].values[:, 0, :, :].flatten())
        putend = pd.Series(ds_labels.variables['PUTEND'].values[:, 0, :, :].flatten())
        pvtend = pd.Series(ds_labels.variables['PVTEND'].values[:, 0, :, :].flatten())
        df_labels = pd.DataFrame({'PTTEND': pttend,
                                  'PUTEND': putend,
                                  'PVTEND': pvtend})
        df_labels.index.rename('index', inplace=True)

        # split the data into training and testing datasets
        train_x, test_x, train_y, test_y = train_test_split(df_features,
                                                            df_labels,
                                                            test_size=0.25,
                                                            random_state=4)

        # perform modeling using linear regression models
        _logger.info("Model results for PS, T, U, and V")
        train_test_linear(train_x, train_y, test_x, test_y)

        # add the non-linear forcing mechanism variables
        df_features['PRECL'] = pd.Series(ds_features.variables['PRECL'].values[:, :, :].flatten())
        df_features['Q'] = pd.Series(ds_features.variables['Q'].values[:, :, :].flatten())
        df_labels['PTEQ'] = pd.Series(ds_labels.variables['PTEQ'].values[:, 0, :, :].flatten())

        # split the data into training and testing datasets
        train_x, test_x, train_y, test_y = train_test_split(df_features,
                                                            df_labels,
                                                            test_size=0.25,
                                                            random_state=4)

        # perform modeling using linear regression models
        _logger.info("Model results for PS, T, U, V, PRECL, and Q")
        train_test_linear(train_x, train_y, test_x, test_y)

        # trim the DataFrames down to only the non-linear forcing mechanism variables
        df_features = df_features['PRECL', 'Q']
        df_labels = df_labels['PTEQ']

        # split the data into training and testing datasets
        train_x, test_x, train_y, test_y = train_test_split(df_features,
                                                            df_labels,
                                                            test_size=0.25,
                                                            random_state=4)

    except Exception as ex:

        _logger.exception('Failed to complete', exc_info=True)
        raise
