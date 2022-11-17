

wget https://dev.mysql.com/get/Downloads/MySQL-Cluster-8.0/mysql-cluster-community-management-server_8.0.31-1ubuntu20.04_amd64.deb
sudo dpkg -i mysql-cluster-community-management-server_8.0.31-1ubuntu20.04_amd64.deb
sudo mkdir /var/lib/mysql-cluster

sudo nano /var/lib/mysql-cluster/config.ini

#use private ip adresses
"""
[ndbd default]
# Options affecting ndbd processes on all data nodes:
NoOfReplicas=1	# Number of replicas

[ndb_mgmd]
# Management process options:
hostname=172.31.1.146 # Hostname of the manager

datadir=/var/lib/mysql-cluster 	# Directory for the log files

[ndbd]
hostname=172.31.12.52 # Hostname/IP of the first data node
NodeId=2			# Node ID for this data node
datadir=/usr/local/mysql/data	# Remote directory for the data files

[ndbd]
hostname=172.31.6.248 # Hostname/IP of the second data node
NodeId=3			# Node ID for this data node
datadir=/usr/local/mysql/data	# Remote directory for the data files

[ndbd]
hostname=172.31.9.252 # Hostname/IP of the second data node
NodeId=4			# Node ID for this data node
datadir=/usr/local/mysql/data	# Remote directory for the data files

[mysqld]
# SQL node options:
hostname=172.31.1.146 # In our case the MySQL server/client is on the same Droplet as the cluster manager"""

#CTRL + O --> ENTER # to save
#CTRL + X # to exit

sudo ndb_mgmd -f /var/lib/mysql-cluster/config.ini
sudo pkill -f ndb_mgmd

sudo nano /etc/systemd/system/ndb_mgmd.service

   """ [Unit]
    Description=MySQL NDB Cluster Management Server
    After=network.target auditd.service

    [Service]
    Type=forking
    ExecStart=/usr/sbin/ndb_mgmd -f /var/lib/mysql-cluster/config.ini
    ExecReload=/bin/kill -HUP $MAINPID
    KillMode=process
    Restart=on-failure

    [Install]
    WantedBy=multi-user.target"""

sudo systemctl daemon-reload
sudo systemctl start ndb_mgmd
sudo systemctl enable ndb_mgmd
sudo systemctl status ndb_mgmd


#maybe add these
#sudo ufw allow from 198.51.100.0
#sudo ufw allow from 198.51.100.1
#sudo ufw allow from 198.51.100.2


# setup mysql

wget https://dev.mysql.com/get/Downloads/MySQL-Cluster-8.0/mysql-cluster_8.0.31-1ubuntu20.04_amd64.deb-bundle.tar
sudo mkdir install
sudo tar -xvf mysql-cluster_8.0.31-1ubuntu20.04_amd64.deb-bundle.tar -C install/

cd install
# asks for password etc
yes | sudo apt install libaio1 libmecab2
yes | sudo dpkg -i *.deb
yes | sudo apt-get install -f

sudo nano /etc/mysql/my.cnf


    # add management server private ip
    """[mysqld]
    # Options for mysqld process:
    ndbcluster                      # run NDB storage engine

    [mysql_cluster]
    # Options for NDB Cluster processes:
    ndb-connectstring=172.31.1.146  # location of management server"""


sudo systemctl restart mysql

# maybe run this
#sudo systemctl enable mysql


# Sakila download
sudo wget http://downloads.mysql.com/docs/sakila-db.zip
sudo apt install unzip
sudo unzip sakila-db.zip -d "/tmp/"
sudo mysql -e "SOURCE /tmp/sakila-db/sakila-schema.sql;"
sudo mysql -e "SOURCE /tmp/sakila-db/sakila-data.sql;"

#consider this try manually

# MySQL installation
sudo mysql -e "UPDATE mysql.user SET Password=PASSWORD('admin') WHERE User='root';"
sudo mysql -e "DELETE FROM mysql.user WHERE User='';"
sudo mysql -e "DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');"
sudo mysql -e "DROP DATABASE test"
sudo mysql -e "FLUSH PRIVILEGES;"
sudo mysql -e "CREATE USER 'victor'@'localhost' IDENTIFIED BY 'password';"
sudo mysql -e "GRANT ALL PRIVILEGES on sakila.* TO 'victor'@'localhost';"

#this based on which user etc
# Sysbench installation and benchmarking
yes | sudo apt-get install sysbench
# Prepare
sysbench --db-driver=mysql --mysql-user=victor --mysql_password=password --mysql-db=sakila --tables=6 --table-size=200 /usr/share/sysbench/oltp_read_write.lua prepare
sysbench --db-driver=mysql --mysql-user=victor --mysql_password=password --mysql-db=sakila --tables=6 --table-size=200 --threads=6 --time=60 /usr/share/sysbench/oltp_read_write.lua run > SA.txt

