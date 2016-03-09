# gis-code-challenge

## Task
Imagine you are a Software Developer at ally and you are presented that data. Your task is to derive bus stop locations from the data.

* 1. Develop an algorithm in Python that processes the data.
* 2. Visualise your results in a web map.

## asumptions
To create a minimum data quality check we select only data points within a region around a street and with a speed equals 0.

## Steps
* First we will filter the data (as mentioned above!)
* create a [DBSCAN](http://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html) result dataset 
* project resulting cluster centers to streets 



