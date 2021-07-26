import os, uuid
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__

import json
import pandas as pd


# CONFIGURATION

# Retrieve the connection string for use with the application. The storage
# connection string is stored in an environment variable on the machine
# running the application called AZURE_STORAGE_CONNECTION_STRING. If the environment variable is
# created after the application is launched in a console or with Visual Studio,
# the shell or application needs to be closed and reloaded to take the
# environment variable into account.
connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')

# Create a unique name for the container
container_name = "simulationlogs"


#####################

# Create the BlobServiceClient object which will be used to create a container client
blob_service_client = BlobServiceClient.from_connection_string(connect_str)

# Create the container
container_client = blob_service_client.get_container_client(container_name)

# For TEST: Create a file in the local data directory to upload and download
local_file_name = str(uuid.uuid4()) + ".txt"

def test_file(local_path = "."):
    upload_file_path = os.path.join(local_path, local_file_name)
    # Write text to the file
    file = open(upload_file_path, 'w')
    file.write("Hello, World!")
    file.close()
  
def upload_file(
        file_name,
        local_path = ".",
        local_file_name = None
):
    # Create a local directory to hold blob data
    upload_file_path = os.path.join(
        local_path,
        file_name
        if local_file_name is None
        else local_file_name
    )

    # Create a blob client using the local file name as the name for the blob
    blob_client = blob_service_client.get_blob_client(
        container=container_name,
        blob=file_name
    )

    print("\nUploading to Azure Storage as blob:\n\t" + upload_file_path)

    # Upload the created file
    with open(upload_file_path, "rb") as data:
        blob_client.upload_blob(data)

def list_blobs():
    print("\nListing blobs...")

    # List the blobs in the container
    blob_list = container_client.list_blobs()
    for blob in blob_list:
        print("\t" + blob.name)

def dataframe_to_blob(df, path, filename):
    local_path = os.path.join(path, filename)
    df.to_csv(local_path)
    print(f"\nUploading to Azure Storage as blob:\n\t{local_path}")
    upload_file(filename, local_path = path)
    os.remove(local_path)

def json_to_blob(js, path, filename):
    local_path = os.path.join(path, filename)
    with open(local_path, 'w') as json_file:
        json.dump(js, json_file)
    print(f"\nUploading to Azure Storage as blob:\n\t{local_path}")
    upload_file(filename, local_path = path)
    os.remove(local_path)
