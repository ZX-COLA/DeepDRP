# DeepDRP

The DeepDRP is a predict tool for intrinsically disordered regions in protein and is built by Python framework.

## Environment

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

We only provide the Linux version psi-blast in the software, if you are a MacOS or Windows user, please replace the whole psi-blast tool in the lib folder.

Download and install BLAST+. Installers and source code are available from https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/LATEST/. 

### Download model weights

You need to download the model weights into the lib folder

Weights available at https://xxx.

### Prepare filelist file

```
/home/usr/DeepDRP/demo/4RBXA.fasta
/home/usr/DeepDRP/demo/DP00588.fasta
```

### PSSM file

if you already have the pssm results of the protein, please put the <id>.pssm file into the tmp folder, the DeepDRP will first check if the pssm file exists. If not exist, the program will run the psiblast automatically.



## Running DeepDRP

Run in command line:

```
cd DeepDRP
conda activate DeepDRP
python predict.py -i <filelist> -o <output_path>

#Demo
cd DeepDRP
conda activate DeepDRP
python predict.py -i ./filelist -o ./results
```

Run in GUI mode:

```
cd DeepDRP
conda activate DeepDRP
python GUI.py
```













