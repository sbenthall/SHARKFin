import azure.storage.fileshare as fs
import asyncio
import re
import os
import json
import pandas as pd

conn_str = 'DefaultEndpointsProtocol=https;AccountName=sbsimulationdata;AccountKey=JD7dU19DXZ1TBAGRZYhCEod344kS2sSnFP2IL7ReFqZAhEwnvEn9LHdjq32Q0yj2eAcMQwNBSc4N+AStQHZQNQ==;EndpointSuffix=core.windows.net'

def download(fname, dirname='chum_results', share_name='sharkfin-ammps-fs'):
	file_client = fs.ShareFileClient.from_connection_string(
		conn_str=conn_str,
		share_name=share_name,
		file_path=fname)

	if not os.path.isdir(dirname):
		os.mkdir(dirname)

	with open(f'{dirname}/{fname}', 'wb+') as file_handle:
		data = file_client.download_file()
		data.readinto(file_handle)

def list_files(share_name='sharkfin-ammps-fs'):
	file_list_json = os.popen("az storage file list --share-name sharkfin-ammps-fs --connection-string 'DefaultEndpointsProtocol=https;AccountName=sbsimulationdata;AccountKey=JD7dU19DXZ1TBAGRZYhCEod344kS2sSnFP2IL7ReFqZAhEwnvEn9LHdjq32Q0yj2eAcMQwNBSc4N+AStQHZQNQ==;EndpointSuffix=core.windows.net'").read()
	file_info = json.loads(file_list_json)
	names = [item['name'] for item in file_info]

	return names

if __name__ == '__main__':
	regex = 'chum-\d+-\d+-\d+-\d+_data.csv'
	pattern = re.compile(regex)

	for fname in list_files():
		if pattern.search(fname):
			print(f'downloading {fname}')
			download(fname)

	final_df = pd.DataFrame()

	for fname in os.listdir('chum_results'):
		df = pd.read_csv(f'chum_results/{fname}')
		final_df = final_df.append(df.iloc[-1], ignore_index=True)

	final_df.to_csv('chum_results_run_1.csv')




	
