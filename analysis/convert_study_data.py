import pandas as pd
import re
import argparse
from functools import reduce

parser = argparse.ArgumentParser()
parser.add_argument('fname', help='the filename to convert')
args = parser.parse_args()

data = pd.read_csv(args.fname)

mean_re = re.compile("\('aLvl_mean', 'CRRA\: (\d.\d+), DiscFac\: (\d.\d+)'\)")
std_re = re.compile("\('aLvl_std', 'CRRA\: (\d.\d+), DiscFac\: (\d.\d+)'\)")
mnrm_mean_re = re.compile("\('mNrm_ratio_StE_mean', 'CRRA\: (\d.\d+), DiscFac\: (\d.\d+)'\)")
mnrm_std_re = re.compile("\('mNrm_ratio_StE_std', 'CRRA\: (\d.\d+), DiscFac\: (\d.\d+)'\)")

data['row'] = data.index

mean_data = data.melt(
    id_vars=['row','attention', 'p1', 'p2', 'dividend_ror','ror_volatility', 'dollars_per_hark_money_unit'],
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
    id_vars=['row','attention', 'p1', 'p2', 'dividend_ror', 'dollars_per_hark_money_unit'],
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

mnrm_ratio_ste_mean = data.melt(
    id_vars=['row','attention', 'p1', 'p2', 'dividend_ror', 'dollars_per_hark_money_unit'],
    value_vars=[
        "('mNrm_ratio_StE_mean', 'CRRA: 3.33, DiscFac: 0.95')",
        "('mNrm_ratio_StE_mean', 'CRRA: 3.33, DiscFac: 0.97')",
        "('mNrm_ratio_StE_mean', 'CRRA: 6.0, DiscFac: 0.95')",
        "('mNrm_ratio_StE_mean', 'CRRA: 6.0, DiscFac: 0.97')",
        "('mNrm_ratio_StE_mean', 'CRRA: 8.67, DiscFac: 0.95')",
        "('mNrm_ratio_StE_mean', 'CRRA: 8.67, DiscFac: 0.97')"],
    var_name='pop_class',
    value_name='mNrm_ratio_StE_mean'

)

mnrm_ratio_ste_mean['CRRA'] = mnrm_ratio_ste_mean['pop_class'].apply(lambda x : float(mnrm_mean_re.match(x)[1]))
mnrm_ratio_ste_mean['DiscFac'] = mnrm_ratio_ste_mean['pop_class'].apply(lambda x : float(mnrm_mean_re.match(x)[2]))
mnrm_ratio_ste_mean.drop("pop_class", axis=1, inplace=True)

mnrm_ratio_ste_std = data.melt(
    id_vars=['row','attention', 'p1', 'p2', 'dividend_ror', 'dollars_per_hark_money_unit'],
    value_vars=[
        "('mNrm_ratio_StE_std', 'CRRA: 3.33, DiscFac: 0.95')",
        "('mNrm_ratio_StE_std', 'CRRA: 3.33, DiscFac: 0.97')",
        "('mNrm_ratio_StE_std', 'CRRA: 6.0, DiscFac: 0.95')",
        "('mNrm_ratio_StE_std', 'CRRA: 6.0, DiscFac: 0.97')",
        "('mNrm_ratio_StE_std', 'CRRA: 8.67, DiscFac: 0.95')",
        "('mNrm_ratio_StE_std', 'CRRA: 8.67, DiscFac: 0.97')"],
    var_name='pop_class',
    value_name='mNrm_ratio_StE_std'
)

mnrm_ratio_ste_std['CRRA'] = mnrm_ratio_ste_std['pop_class'].apply(lambda x : float(mnrm_std_re.match(x)[1]))
mnrm_ratio_ste_std['DiscFac'] = mnrm_ratio_ste_std['pop_class'].apply(lambda x : float(mnrm_std_re.match(x)[2]))
mnrm_ratio_ste_std.drop("pop_class", axis=1, inplace=True)


dfs = [mean_data, std_data, mnrm_ratio_ste_mean, mnrm_ratio_ste_std]

all_data = reduce(lambda  left,right: pd.merge(left,right,on = [
                        "row", 
                        "attention", 
                        "p1", 
                        "p2", 
                        "dividend_ror", 
                        "CRRA", 
                        "DiscFac",
                        "dollars_per_hark_money_unit"
                    ]), dfs)


all_data.to_csv(f'{args.fname.replace(".csv", "")}-long.csv')
