#sudo nano /etc/my.cnf
# private ip of cluster manager
sudo chmod ugo+rwx /etc
sudo cat <<EOF >/etc/my.cnf
[mysql_cluster]
# Options for NDB Cluster processes:
ndb-connectstring=172.31.9.144 # location of cluster manager
EOF
sudo mkdir -p /usr/local/mysql/data
sudo ndbd
sudo pkill -f ndbd
#sudo nano /etc/systemd/system/ndbd.service
sudo chmod ugo+rwx /etc/systemd/system
sudo cat <<EOF >/etc/systemd/system/ndbd.service
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
EOF
sudo systemctl daemon-reload
sudo systemctl enable ndbd
sudo systemctl start ndbd
sudo systemctl status ndbd
