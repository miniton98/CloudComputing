# setup mysql
wget https://downloads.mysql.com/archives/get/p/14/file/mysql-cluster_7.6.23-1ubuntu18.04_amd64.deb-bundle.tar
sudo mkdir install
sudo tar -xvf mysql-cluster_7.6.23-1ubuntu18.04_amd64.deb-bundle.tar -C install/

cd install
sudo apt update
yes | sudo apt install libaio1 libmecab2
# asks for password
yes | sudo dpkg -i *.deb
# must be run manually
sudo nano /etc/mysql/my.cnf
[mysqld]
# Options for mysqld process:
ndbcluster                      # run NDB storage engine

[mysql_cluster]
# Options for NDB Cluster processes:
ndb-connectstring=172.31.11.201  # location of management server

# instructions on how to save written data using nano commands
# CtRL + O
# Enter
# CTRL + X

sudo systemctl restart mysql
sudo systemctl enable mysql

#check that everything works correctly
cd ~
mysql -u root -p
SHOW ENGINE NDB STATUS \G

ndb_mgm
show

# Sakila download
#some issues with unzip download
sudo wget http://downloads.mysql.com/docs/sakila-db.zip
sudo apt update
yes | sudo apt --fix-broken install
sudo apt install unzip
sudo unzip sakila-db.zip -d "/tmp/"
#sudo mysql -e "SOURCE /tmp/sakila-db/sakila-schema.sql;" -p
#sudo mysql -e "SOURCE /tmp/sakila-db/sakila-data.sql;" -p

# run these in the mysql bash
# MySQL installation
mysql -u root -p
SOURCE /tmp/sakila-db/sakila-schema.sql;
SOURCE /tmp/sakila-db/sakila-data.sql;
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
FLUSH PRIVILEGES;
CREATE USER 'victor'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES on sakila.* TO 'victor'@'localhost';

#this based on which user etc
# Sysbench installation and benchmarking
yes | sudo apt-get install sysbench
# Prepare
sudo chmod ugo+rwx ~
sysbench oltp_read_write --db-driver=mysql --mysql-user=victor --mysql_password=password --mysql-db=sakila --tables=6 --table-size=100000  prepare
sysbench oltp_read_write --db-driver=mysql --mysql-user=victor --mysql_password=password --mysql-db=sakila --tables=6 --table-size=100000 --threads=6 --time=60  run > Cluster.txt
cat Cluster.txt
