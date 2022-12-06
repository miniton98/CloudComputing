# install and setup mysql
# perform benchmarking using sysbench
cd install
sudo apt update
yes | sudo apt install libaio1 libmecab2
# asks for password, insert desired password
yes | sudo dpkg -i *.deb

# must be run manually, for some reason
#insert private IP of manager node
sudo nano /etc/mysql/my.cnf

[mysqld]
# Options for mysqld process:
ndbcluster                      # run NDB storage engine

[mysql_cluster]
# Options for NDB Cluster processes:
ndb-connectstring=172.31.14.186  # location of management server

# instructions on how to save written data using nano commands
# CtRL + O
# Enter
# CTRL + X

sudo systemctl restart mysql
sudo systemctl enable mysql
cd ~

#check that everything works correctly
#checking from cluster manager shell
ndb_mgm
show
# exit to close shell

# run these in the mysql bash
# checking from mysql shell that it is correctly set up
# MySQL set up
mysql -u root -p
SHOW ENGINE NDB STATUS \G
SOURCE /tmp/sakila-db/sakila-schema.sql;
SOURCE /tmp/sakila-db/sakila-data.sql;
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
FLUSH PRIVILEGES;
CREATE USER 'victor'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES on sakila.* TO 'victor'@'localhost';
# exit to close shell

# Sysbench benchmarking
sudo chmod ugo+rwx ~
sysbench oltp_read_write --db-driver=mysql --mysql-user=victor --mysql_password=password --mysql-db=sakila --tables=6 --table-size=100000  prepare
sysbench oltp_read_write --db-driver=mysql --mysql-user=victor --mysql_password=password --mysql-db=sakila --tables=6 --table-size=100000 --threads=6 --time=60  run > Cluster.txt
cat Cluster.txt
