# DeepDRP

The DeepDRP is a predict tool for intrinsically disordered regions in protein and is built by Python framework.
****

**Abstract**
Intrinsic disorder in proteins, a widely distributed phenomenon in nature, is related to many crucial biological processes and various diseases. Traditional determination methods tend to be high-cost and time-consuming, therefore it is desirable to seek an accurate identification method of intrinsically disordered proteins (IDPs). In this paper, we proposed a novel Deep learning model for Intrinsically Disordered Regions in Proteins named DeepDRP. DeepDRP employed an innovative TimeDistributed strategy and Bi-LSTM architecture to predict IDPs and is driven by integrated view features of PSSM, Energy-based encoding, AAindex, and transformer-enhanced embeddings including DR-BERT, OntoProtein, Prot-T5, and ESM-2. The comparison of different feature combinations indicates that the transformer-enhanced features contribute far more than traditional features to predict IDPs and ESM-2 accounts for a larger contribution in the pre-trained fusion vectors. The ablation test verified that the novel TimeDistributed strategy surely increased the model performance and is an efficient approach to the IDP prediction. Compared with state-of-the-art models on the DISORDER723, S1, and DisProt832 datasets, the Matthews correlation coefficient of DeepDRP significantly outperformed competing methods by 4.90% to 36.20%, 11.80% to 26.33%, and 4.82% to 13.55%. In brief, DeepDRP is a reliable model for IDP prediction and is freely available at https://github.com/ZX-COLA/DeepDRP.
****

## 1. Environment

Make sure the following python library is installed before using.

```
conda create -n DeepDRP python=3.10
conda activate DeepDRP

pip install tensorflow
pip3 install torch torchvision torchaudio
pip install scikit-learn
pip install transformers
pip install SentencePiece

#if you want to use a GUI version of DeepDRP
pip install pyqt6 
```
### BLAST+ executables

please download the whole psi-blast tool in the lib folder. Download and install BLAST+. Installers and source code are available from https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/. 

In predict.py file:

line 312, variable db_path is the path of the database(blast), which is default setted as <db_path = './lib/uniref50.fasta/uniref50.fasta'>

line 315, variable balst_path is the path of the psi-blast tools, which is default setted as <balst_path = "./lib/ncbi-blast-2.14.0+/bin/psiblast">


### Prepare filelist file

```
/DeepDRP/demo/DP00588.fasta
/DeepDRP/demo/4RBXA.fasta
```
### PSSM file

if you already have the pssm results of the protein, please put the <id>.pssm file into the tmp folder, the DeepDRP will first check if the pssm file exists. If not exist, the program will run the psiblast automatically.


## 2. Running DeepDRP

Run in command line:

```
cd DeepDRP
conda activate DeepDRP
python predict.py -i <filelist> -o <output_path>

#Demo
cd DeepDRP
conda activate DeepDRP
python predict.py -i ./demo/filelist -o ./results
```

Run in GUI mode:

```
cd DeepDRP
conda activate DeepDRP
python GUI.py
```













