<<EOT
echo 'Hello'
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -u
rm Miniconda3-latest-Linux-x86_64.sh
echo ". /home/ubuntu/miniconda3/etc/profile.d/conda.sh" >> ~/.bashrc
source .bashrc
EOT
