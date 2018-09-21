DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
cd $DIR
mkdir bin
git clone https://github.com/ANTsX/ANTs
mkdir ANTs_build
cd ANTs_build
cmake ../ANTs
make -j4
cp bin/antsRegistration ../bin/