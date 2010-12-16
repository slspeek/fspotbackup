set -e
READ_BACK_DIR=~/stage/read_back
wodim -tao $1
eject
eject -t
sleep 40s
if test -d $READ_BACK_DIR; then
  rm -rfv $READ_BACK_DIR
fi
cp -Lrv /media/cdrom $READ_BACK_DIR
chmod u=rwX -Rv $READ_BACK_DIR
cd $READ_BACK_DIR/scripts
./par2verify.sh 
cd
rm -rvf $READ_BACK_DIR
eject


