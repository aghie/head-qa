pip install sklearn
#Read additional instructions to install DrQA at https://github.com/facebookresearch/DrQA
#cd DrQA; pip install -r requirements.txt; python setup.py develop
pip install torch==0.3.1
pip install torchvision
#I was habing problems running drqa/pipeline/predict.py
#It seems it is due to a problem with the CoreNLP tokenizer
pip install spacy==2.0.0

#See for a more detailed explanation of the following steps https://github.com/allenai/ARC-Solvers
#Clone git clone https://github.com/allenai/ARC-Solvers
#sh scripts/install_requirements.sh
#sh scripts/download_data.sh
#sh scripts/download_and_prepare_glove.sh
#I had problems to run the dgem baseline. The default torch version that is installed if you follow the instructions in the README.md is the 0.4.1. To make them work I needed to install torch 0.3.1 instead
