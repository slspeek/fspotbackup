set -e
READ_BACK_DIR=~/stage/read_back
DVD_DEV=/dev/dvdrw
DVD_MNT_POINT=/media/cdrom0
mount $DVD_DEV

if test -d $READ_BACK_DIR; then
  rm -rfv $READ_BACK_DIR
fi
cp -Lrv $DVD_MNT_POINT $READ_BACK_DIR
chmod u=rwX -Rv $READ_BACK_DIR
cd $READ_BACK_DIR/scripts
./par2verify.sh 
cd
rm -rvf $READ_BACK_DIR
eject


