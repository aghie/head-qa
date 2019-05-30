################################################
# For the control, IR and DrQA methods
################################################

#Read additional instructions to install DrQA at https://github.com/facebookresearch/DrQA
#For the most recent version cline instead #https://github.com/facebookresearch/DrQA.git
git clone https://github.com/aghie/DrQA.git 
cd DrQA; pip install -r requirements.txt; python setup.py develop
./install_corenlp.sh
./download.sh

pip install scikit-learn==0.20.2
pip install numpy==1.16.0
pip install torch==1.0.0
pip install torchvision
pip install spacy==2.0.0

python -m spacy download en
python -m spacy download es

wget http://www.grupolys.org/software/head-qa-acl2019/HEAD.zip
wget http://www.grupolys.org/software/head-qa-acl2019/HEAD_EN.zip
wget http://www.grupolys.org/software/head-qa-acl2019/data.zip
wget http://www.grupolys.org/software/head-qa-acl2019/wiki-articles.tfidf.zip
wget http://www.grupolys.org/software/head-qa-acl2019/WikiCorpus.zip

unzip HEAD.zip
unzip HEAD_EN.zip
unzip data.zip
mkdir wikipedia
unzip wiki-articles.tfidf.zip -d wikipedia/
unzip WikiCorpus.zip -d wikipedia/

