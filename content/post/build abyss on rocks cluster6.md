---
date = "2016-06-18T03:13:00+08:00"
title = "build abyss on rocks cluster6"
tags = ['OTHERS']
---

比较麻烦的是集群需要用到ABYSS-P, 如果不指定--with-mpi参数的话, 这玩意是不会生成的.
记录下编译过程
```
# http://www.bcgsc.ca/platform/bioinfo/software/abyss
install_folder="/prodata/ngs"
bin_folder="$install_folder/bin"
CWD=$(pwd)
#Download ABySS
wget "http://www.bcgsc.ca/platform/bioinfo/software/abyss/releases/1.3.5/abyss-1.3.5.tar.gz"
tar xvfz abyss-1.3.5.tar.gz

wget https://github.com/sparsehash/sparsehash/archive/sparsehash-2.0.3.tar.gz
tar xvzf sparsehash-sparsehash-2.0.3.tar.gz
cd sparsehash-sparsehash-2.0.3
./configure --prefix=$install_folder
make -j12
make install
cd $CWD

#Set up Boost Dependency
cd abyss-1.3.5
wget "http://downloads.sourceforge.net/project/boost/boost/1.50.0/boost_1_50_0.tar.bz2"
tar jxf boost_1_50_0.tar.bz2
ln -s boost_1_50_0/boost boost


# Configure ABySS
./configure --with-mpi=/opt/openmpi CPPFLAGS=-I/prodata/ngs/include --prefix=$install_folder
make -j12
make install
cd $CWD
```