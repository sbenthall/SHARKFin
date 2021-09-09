import pandas as pd
import re

data = pd.read_csv("004-64-2178-3-grid-study-all_records.csv")

mean_re = re.compile("\('aLvl_mean', 'CRRA\: (\d.\d+), DiscFac\: (\d.\d+)'\)")
std_re = re.compile("\('aLvl_std', 'CRRA\: (\d.\d+), DiscFac\: (\d.\d+)'\)")

data['row'] = data.index

mean_data = data.melt(
    id_vars=['row','attention', 'p1', 'p2', 'dividend_ror','ror_volatility'],
    value_vars=[
        "('aLvl_mean', 'CRRA: 3.33, DiscFac: 0.95')",
        "('aLvl_mean', 'CRRA: 3.33, DiscFac: 0.97')",
        "('aLvl_mean', 'CRRA: 6.0, DiscFac: 0.95')",
        "('aLvl_mean', 'CRRA: 6.0, DiscFac: 0.97')",
        "('aLvl_mean', 'CRRA: 8.67, DiscFac: 0.95')",
        "('aLvl_mean', 'CRRA: 8.67, DiscFac: 0.97')"],
    var_name='pop_class',
    value_name='aLvl_mean'
)

mean_data['CRRA'] = mean_data['pop_class'].apply(lambda x : float(mean_re.match(x)[1]))
mean_data['DiscFac'] = mean_data['pop_class'].apply(lambda x : float(mean_re.match(x)[2]))
mean_data.drop("pop_class", axis=1, inplace=True)

std_data = data.melt(
    id_vars=['row','attention', 'p1', 'p2', 'dividend_ror'],
    value_vars=[
        "('aLvl_std', 'CRRA: 3.33, DiscFac: 0.95')",
        "('aLvl_std', 'CRRA: 3.33, DiscFac: 0.97')",
        "('aLvl_std', 'CRRA: 6.0, DiscFac: 0.95')",
        "('aLvl_std', 'CRRA: 6.0, DiscFac: 0.97')",
        "('aLvl_std', 'CRRA: 8.67, DiscFac: 0.95')",
        "('aLvl_std', 'CRRA: 8.67, DiscFac: 0.97')"],
    var_name='pop_class',
    value_name='aLvl_std'
)

std_data['CRRA'] = std_data['pop_class'].apply(lambda x : float(std_re.match(x)[1]))
std_data['DiscFac'] = std_data['pop_class'].apply(lambda x : float(std_re.match(x)[2]))
std_data.drop("pop_class", axis=1, inplace=True)

all_data = pd.merge(mean_data, std_data,
                    on = [
                        "row", 
                        "attention", 
                        "p1", 
                        "p2", 
                        "dividend_ror", 
                        "CRRA", 
                        "DiscFac"
                    ])


all_data.to_csv("004-64-2178-3-grid-study-all_records_long.csv")
