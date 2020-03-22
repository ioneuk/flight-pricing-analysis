from typing import List

import holidays
import pandas as pd
from pandas import DataFrame
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import LabelEncoder


class DateTransformer(BaseEstimator, TransformerMixin):
    def __init__(self) -> None:
        return

    def fit(self) -> DataFrame:
        return self

    def transform(self, x: DataFrame) -> DataFrame:
        x.loc[:, "measure_date"] = pd.to_datetime(pd.to_datetime(x["date_time"]).dt.date)
        x.loc[:, "departure_date"] = pd.to_datetime(pd.to_datetime(x["departure_date_time"]).dt.date)
        x.loc[:, "departure_hour"] = pd.to_datetime(x["departure_date_time"]).dt.hour
        x.loc[:, "departure_minute"] = pd.to_datetime(x["departure_date_time"]).dt.minute
        x.loc[:, "arrival_date"] = pd.to_datetime(pd.to_datetime(x["arrival_date_time"]).dt.date)
        x.loc[:, "arrival_hour"] = pd.to_datetime(x["arrival_date_time"]).dt.hour
        x.loc[:, "arrival_minute"] = pd.to_datetime(x["arrival_date_time"]).dt.minute

        ua_holidays = []
        for date in holidays.CountryHoliday("UA", prov=None, years=[2020]).items():
            ua_holidays.append(str(date[0]))

        x.loc[:, "is_holiday"] = [1 if str(val).split()[0] in ua_holidays else 0 for val in x["departure_date"]]

        x.loc[:, "days_left_to_departure"] = (x["departure_date"] - x["measure_date"]).transform(lambda x: x.dt.days)
        del x["departure_date_time"]
        del x["arrival_date_time"]
        return x

    def fit_transform(self, x: DataFrame, y: DataFrame = None) -> DataFrame:
        return self.fit().transform(x)


class MultiColumnLabelEncoder(BaseEstimator, TransformerMixin):
    def __init__(self, columns: List[str] = []) -> None:
        self.columns = columns

    def fit(self) -> DataFrame:
        return self

    def transform(self, df: DataFrame) -> DataFrame:
        output = df.copy()
        if self.columns is not None:
            for col in self.columns:
                output[col] = LabelEncoder().fit_transform(output[col].astype(str))
                output[col] = output[col].astype("category")
        return output


class ColumnSelector(BaseEstimator, TransformerMixin):
    def __init__(self, columns: List[str] = []) -> None:
        self.columns = columns

    def fit(self) -> DataFrame:
        return self

    def transform(self, x: DataFrame) -> DataFrame:
        if self.columns is not None:
            return x[self.columns]
        return x

    def fit_transform(self, x: DataFrame, y: DataFrame = None) -> DataFrame:
        return self.fit().transform(x, y)
