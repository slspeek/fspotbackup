set -e
READ_BACK_DIR=~/stage/read_back
wodim -tao $1
eject
eject -t
sleep 40s
if test -d $READ_BACK_DIR; then
  rm -rfv $READ_BACK_DIR
fi
cp -Lrv /media/cdrom ~/leestest
chmod u=rwX -Rv ~/leestest
cd /home/steven/leestest/scripts/
./par2verify.sh 
cd
rm -rvf ~/leestest
eject


