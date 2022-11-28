#use for manual insert
#sudo nano /var/lib/mysql-cluster/config.ini
sudo chmod ugo+rwx /var/lib/mysql-cluster
#use private ip adresses
sudo cat <<EOF >/var/lib/mysql-cluster/config.ini
[ndbd default]
# Options affecting ndbd processes on all data nodes:
NoOfReplicas=1	# Number of replicas

[ndb_mgmd]
# Management process options:
hostname=172.31.11.201 # Hostname of the manager
datadir=/var/lib/mysql-cluster 	# Directory for the log files

[ndbd]
hostname=172.31.14.98 # Hostname/IP of the first data node
NodeId=2			# Node ID for this data node
datadir=/usr/local/mysql/data	# Remote directory for the data files

[ndbd]
hostname=172.31.2.161 # Hostname/IP of the second data node
NodeId=3			# Node ID for this data node
datadir=/usr/local/mysql/data	# Remote directory for the data files

[ndbd]
hostname=172.31.6.225 # Hostname/IP of the third data node
NodeId=4			# Node ID for this data node
datadir=/usr/local/mysql/data	# Remote directory for the data files

[mysqld]
# SQL node options:
hostname=172.31.11.201 # In our case the MySQL server/client is on the same Droplet as the cluster manager
EOF
sudo ndb_mgmd -f /var/lib/mysql-cluster/config.ini
sudo pkill -f ndb_mgmd
#sudo nano /etc/systemd/system/ndb_mgmd.service
sudo chmod ugo+rwx /etc/systemd/system
sudo cat <<EOF >/etc/systemd/system/ndb_mgmd.service
[Unit]
Description=MySQL NDB Cluster Management Server
After=network.target auditd.service

[Service]
Type=forking
ExecStart=/usr/sbin/ndb_mgmd -f /var/lib/mysql-cluster/config.ini
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable ndb_mgmd
sudo systemctl start ndb_mgmd
sudo systemctl status ndb_mgmd

