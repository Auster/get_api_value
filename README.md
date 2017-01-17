GET_API_VALUE.py

Dependencies:
- py-zabbix
- objectpath
- pytz
- pyyaml

Usage:
- From console: 
- $ ./get_api_value.py --app_name datanode --app_host test-run-01.aws.internal --app_port 50075 --conf datanode.jmx.FSDatasetState

From zabbix:
- Item type: External script
- Item: get_api_value["datanode","{HOST.HOST}",{$DATANODE_API_PORT},{$DATANODE_API_USER},{$DATANODE_API_PASSWORD},"datanode.jmx.FSDatasetState"]	
