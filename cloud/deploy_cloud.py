import os
import random
'''
Spins up simulations with the parameter grid specified in chum_config{i}.yaml, 
which should already be uploaded to "sharkfin-ammps-fs" in "sbsimulationdata"


parameter in "range" should equal the number of configs created for the simulation run. Currently there are 666 config files uploaded.
'''

for i in range(666):
	print(i)

	os.system(f"az container create \
		--resource-group ammps-sims \
		--name chum-multi-test1 \
		--image mesalasnano/ammps_sharkfin:chum-slim-multi \
		--restart-policy never \
		--registry-login-server index.docker.io \
		--registry-username DOCKERHUB_USERNAME \
		--registry-password DOCKERHUB_PASSWORD \
		--vnet ammps-sims-vnet \
		--subnet sharkfin-ammps \
		--memory 3 \
		-e SIMCONFIGPATH='output/chum_config{i}.yaml' \
		--ports 5672 \
		--azure-file-volume-account-key AZURE_FS_ACCOUNT_KEY \
		--azure-file-volume-account-name sbsimulationdata \
		--azure-file-volume-mount-path /usr/simulation/output \
		--azure-file-volume-share-name sharkfin-ammps-fs")

'''
Command
    az container create : Create a container group.

Arguments
    --resource-group -g   [Required] : Name of resource group. You can configure the default group
                                       using `az configure --defaults group=<name>`.
    --command-line                   : The command line to run when the container is started, e.g.
                                       '/bin/bash -c myscript.sh'.
    --cpu                            : The required number of CPU cores of the containers, accurate
                                       to one decimal place.  Default: 1.
    --dns-name-label                 : The dns name label for container group with public IP.
    --environment-variables -e       : A list of environment variable for the container. Space-
                                       separated values in 'key=value' format.
    --file -f                        : The path to the input file.
    --image                          : The container image name.
    --ip-address                     : The IP address type of the container group.  Allowed values:
                                       Private, Public.
    --location -l                    : Location. Values from: `az account list-locations`. You can
                                       configure the default location using `az configure --defaults
                                       location=<location>`.
    --memory                         : The required memory of the containers in GB, accurate to one
                                       decimal place.  Default: 1.5.
    --name -n                        : The name of the container group.
    --no-wait                        : Do not wait for the long-running operation to finish.
    --os-type                        : The OS type of the containers.  Allowed values: Linux,
                                       Windows.  Default: Linux.
    --ports                          : A list of ports to open. Space-separated list of ports.
                                       Default: [80].
    --protocol                       : The network protocol to use.  Allowed values: TCP, UDP.
    --restart-policy                 : Restart policy for all containers within the container group.
                                       Allowed values: Always, Never, OnFailure.  Default: Always.
    --secrets                        : Space-separated secrets in 'key=value' format.
    --secrets-mount-path             : The path within the container where the secrets volume should
                                       be mounted. Must not contain colon ':'.
    --secure-environment-variables   : A list of secure environment variable for the container.
                                       Space-separated values in 'key=value' format.
    --zone                           : The zone to place the container group.

Azure File Volume Arguments
    --azure-file-volume-account-key  : The storage account access key used to access the Azure File
                                       share.
    --azure-file-volume-account-name : The name of the storage account that contains the Azure File
                                       share.
    --azure-file-volume-mount-path   : The path within the container where the azure file volume
                                       should be mounted. Must not contain colon ':'.
    --azure-file-volume-share-name   : The name of the Azure File share to be mounted as a volume.

Git Repo Volume Arguments
    --gitrepo-dir                    : The target directory path in the git repository. Must not
                                       contain '..'.  Default: ..
    --gitrepo-mount-path             : The path within the container where the git repo volume
                                       should be mounted. Must not contain colon ':'.
    --gitrepo-revision               : The commit hash for the specified revision.
    --gitrepo-url                    : The URL of a git repository to be mounted as a volume.

Image Registry Arguments
    --acr-identity                   : The identity with access to the container registry.
    --registry-login-server          : The container image registry login server.
    --registry-password              : The password to log in container image registry server.
    --registry-username              : The username to log in container image registry server.

Log Analytics Arguments
    --log-analytics-workspace        : The Log Analytics workspace name or id. Use the current
                                       subscription or use --subscription flag to set the desired
                                       subscription.
    --log-analytics-workspace-key    : The Log Analytics workspace key.

Managed Service Identity Arguments
    --assign-identity                : Space-separated list of assigned identities. Assigned
                                       identities are either user assigned identities (resource IDs)
                                       and / or the system assigned identity ('[system]'). See
                                       examples for more info.
    --role                           : Role name or id the system assigned identity will have.
                                       Default: Contributor.
    --scope                          : Scope that the system assigned identity can access.

Network Arguments
    --subnet                         : The name of the subnet when creating a new VNET or
                                       referencing an existing one. Can also reference an existing
                                       subnet by ID.
    --subnet-address-prefix          : The subnet IP address prefix to use when creating a new VNET
                                       in CIDR format.  Default: 10.0.0.0/24.
    --vnet                           : The name of the VNET when creating a new one or referencing
                                       an existing one. Can also reference an existing vnet by ID.
                                       This allows using vnets from other resource groups.
    --vnet-address-prefix            : The IP address prefix to use when creating a new VNET in CIDR
                                       format.  Default: 10.0.0.0/16.

Global Arguments
    --debug                          : Increase logging verbosity to show all debug logs.
    --help -h                        : Show this help message and exit.
    --only-show-errors               : Only show errors, suppressing warnings.
    --output -o                      : Output format.  Allowed values: json, jsonc, none, table,
                                       tsv, yaml, yamlc.  Default: json.
    --query                          : JMESPath query string. See http://jmespath.org/ for more
                                       information and examples.
    --subscription                   : Name or ID of subscription. You can configure the default
                                       subscription using `az account set -s NAME_OR_ID`.
    --verbose                        : Increase logging verbosity. Use --debug for full debug logs.
'''