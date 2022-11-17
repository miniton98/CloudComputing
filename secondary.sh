wget https://dev.mysql.com/get/Downloads/MySQL-Cluster-8.0/mysql-cluster-community-data-node_8.0.31-1ubuntu20.04_amd64.deb
sudo apt install libclass-methodmaker-perl
sudo dpkg -i mysql-cluster-community-data-node_8.0.31-1ubuntu20.04_amd64.deb

sudo nano /etc/my.cnf

# private ip of cluster manager

[mysql_cluster]
# Options for NDB Cluster processes:
ndb-connectstring=172.31.1.146 # location of cluster manager

CTRL + O --> ENTER # to save
CTRL + X # to exit

sudo mkdir -p /usr/local/mysql/data

sudo ndbd
pkill -f ndbd

sudo nano /etc/systemd/system/ndbd.service

[Unit]
Description=MySQL NDB Data Node Daemon
After=network.target auditd.service

[Service]
Type=forking
ExecStart=/usr/sbin/ndbd
ExecReload=/bin/kill -HUP $MAINPID
KillMode=process
Restart=on-failure

[Install]
WantedBy=multi-user.target

sudo systemctl daemon-reload
sudo systemctl start ndbd
sudo systemctl enable ndbd

sudo systemctl status ndbd

#maybe add these private ips of the other nodes
#sudo ufw allow from 198.51.100.0
#sudo ufw allow from 198.51.100.2
#sudo ufw allow from 198.51.100.2