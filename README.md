# CloudComputing

This is a repository for the final assignments in LOG8415 Advanced cloud computing concepts at Polytechnique montreal.

The directory contains 2 python scripts, one for a stand alone benchmarking and another for the cluster setup.
The shell scripts are used to set up the MySQL cluster.

## Instructions to run the scripts
This section provides a step-by-step instruction to run the implementations with ease.
The Stand alone implementation is fully automatic.
The cluster requires some manual steps.

##### Stand alone MySQL set-up
1. Download the AWS Command Line Interface and install it
2. Learner Lap >> AWS Details >> AWS CLI Show
3. Execute aws configure in the command line
4. Copy and paste the suiting credentials from step 2 and region=us-east-1; output=json
5. Unzip the compressed project file to your location of choice
6. Learner Lap >> AWS Details >> Download PEM
7. Copy the labsuser.pem file into the project directory of CloudComputing
8. Navigate with your command line to the location where you stored the project folder
9. The script requires you to pip install boto3, paramiko via the command line. Ignore
if already done.
10. Run the Python script of the stand-alone implementation with python3 SA_MySQL.py
in your command line

##### Performing the MySQL Cluster set-up
1. Set-up everything for the AWS CLI and SDK as described in the previous steps 1-9
2. Run the Python script of the cluster implementation with python3 Cluster_MySQL.py
in your command line
3. The implementation will print the private IP addresses of all created instances to the
console. Copy and paste the private IP address of the primary node to the following
places:
(a) rows 11 and 31 in primary18.sh
(b) row 6 in secondary18.sh
(c) row 19 in primaryMYSQL.sh
4. Copy and paste the private IP address of the secondary nodes to rows 15, 20, 25 of
primary18.sh (one IP per line)
5. SSH into primary node, password ubuntu, and run the entire primary18.sh script by
copy-pasting it to the shell.
6. SSH into all secondary nodes, password ubuntu, and run the entire secondary18.sh
script by copy-pasting it to the shell.
7. Go back to primary node. copy-paste rows 3-8 of primaryMYSQL.sh to the shell. Wait
for the installation and insert desired root password for MySQL.
8. Run command sudo nano /etc/mysql/my.cnf on the shell, row 11, this opens up a
new shell with text.
9. Copy and Paste rows 13-19 of primaryMYSQL.sh after all existing text.
10. press CTRL + O, press ENTER, and press CTRL + X to save and exit the made
changes.
11. run sudo systemctl restart mysql and sudo systemctl enable mysql, rows 26-27
12. Now we can check if everything is set up correctly by running ndb_mgm in the root
directory and then in the new shell insert show.
13. Run command mysql -u root -p and insert password. This opens up a new shell.
14. Alternatively check the status by running command SHOW ENGINE NDB STATUS \G, row
40 of primaryMYSQL.sh
15. Run the commands on rows 41-47 of primaryMYSQL.sh, then exit the shell by typing
exit
16. Then run the rows 50-53, to perform the benchmarking
17. To read the benchmarking file run cat Cluster.txt, row 54, this will print the results
into the shell
