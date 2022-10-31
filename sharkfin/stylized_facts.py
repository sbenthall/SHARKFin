### reference: 
# [1]: Measures of Skewness and Kurtosis, Engineering Statistics Handbook
# https://www.itl.nist.gov/div898/handbook/eda/section3/eda35b.htm
#
# [2]: Durbin Watson Statistic, CFI
# https://corporatefinanceinstitute.com/resources/knowledge/other/durbin-watson-statistic/


### Dependency:
# 1. numpy
# 2. sklearn


import numpy as np
from sklearn import linear_model


def Skewness(x):

    """
    Skewness(x)

    Calculate the skewness of a one-dimensional numpy array (x). 

    """

    assert x.ndim == 1 or (x.ndim == 2 and x.shape[1] == 1)

    num = np.sum( (x - np.mean(x)) ** 3)
    den = len(x) * np.std(x) ** 3 
    return num / den 


def Kurtosis(x):

    """
    Kurtosis(x)

    Calculate the skewness of a one-dimensional numpy array (x). 

    """

    assert x.ndim == 1 or (x.ndim == 2 and x.shape[1] == 1)

    num = np.sum( (x - np.mean(x)) ** 4)
    den = len(x) * np.std(x) ** 4 
    return num / den 


def DW_test(x): # Durbin Watson test

    """
    DW_test(x)

    Perform the Durbin-Watson test for a one-dimensional numpy array (x). 

    """

    assert x.ndim == 1 or (x.ndim == 2 and x.shape[1] == 1)

    indexing = np.arange(0, len(x), 1).reshape(-1,1)
    x = x.reshape(-1,1)
    
    reg = linear_model.LinearRegression()
    reg.fit(indexing, x)
    
    pred = reg.coef_ * indexing + reg.intercept_
    
    num = 0
    den = 0

    for i in range(len(pred) - 1):
        num += ((pred[i+1] - x[i+1]) - (pred[i] - x[i]))**2
        den += (pred[i+1] - x[i+1])**2
    
    return (num / den)[0]