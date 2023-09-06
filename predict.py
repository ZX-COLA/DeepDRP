import sys, getopt
import re
import torch
import numpy as np
import tensorflow as tf
from transformers import AutoModel, T5Tokenizer, T5Model
from transformers import AutoTokenizer, AutoModelForMaskedLM, FeatureExtractionPipeline
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

print("loading ESM-2...")
model_esm2, alphabet_esm2 = torch.hub.load("facebookresearch/esm:main", "esm2_t33_650M_UR50D")

print("loading T5...")
tokenizer_t5 = T5Tokenizer.from_pretrained('Rostlab/prot_t5_xl_uniref50', do_lower_case=False)
model_t5 = T5Model.from_pretrained("Rostlab/prot_t5_xl_uniref50")

print("loading DR-BERT...")
device = "cuda:0" if torch.cuda.is_available() else "cpu"
model_name_drbert = "lib/DR-BERT"
tokenizer_drbert = AutoTokenizer.from_pretrained(model_name_drbert)
model_drbert = AutoModel.from_pretrained(model_name_drbert).eval().to(device)

print("loading OntoProtein...")
tokenizer_onto = AutoTokenizer.from_pretrained("zjukg/OntoProtein")
model_onto = AutoModelForMaskedLM.from_pretrained("zjukg/OntoProtein")
bert_model_onto = FeatureExtractionPipeline(model=model_onto, tokenizer=tokenizer_onto)


def encode_by_esm2(seq):
    batch_converter = alphabet_esm2.get_batch_converter()
    model_esm2.eval()  # disables dropout for deterministic results
    # Prepare data (first 2 sequences from ESMStructuralSplitDataset superfamily / 4)
    data = [
        ("tmpDeepDRP", seq.upper()),
    ]
    batch_labels, batch_strs, batch_tokens = batch_converter(data)

    with torch.no_grad():
        results = model_esm2(batch_tokens, repr_layers=[33], return_contacts=True)
    token_representations = results["representations"][33]
    token_representations = token_representations.detach().cpu().numpy()[0][1:-1, :]

    maxsize = 500
    embedding = 400

    res = token_representations[:maxsize, :embedding]
    res = np.pad(res, ((0, 500 - len(res)), (0, 0)), constant_values=0)
    return res


def encode_by_t5(seq):
    sequences_Example = [" ".join(list(seq.upper()))]
    sequences_Example = [re.sub(r"[UZOB]", "X", sequence) for sequence in sequences_Example]
    ids = tokenizer_t5.batch_encode_plus(sequences_Example,
                                         add_special_tokens=True,
                                         padding=False)

    input_ids = torch.tensor(ids['input_ids'])
    attention_mask = torch.tensor(ids['attention_mask'])

    with torch.no_grad():
        embedding = model_t5(input_ids=input_ids,
                             attention_mask=attention_mask,
                             decoder_input_ids=input_ids,
                             )

    maxsize = 500
    embedding_size = 400

    encoder_embedding = embedding.last_hidden_state[0, :-1].detach().cpu().numpy()
    res = encoder_embedding[:maxsize, :embedding_size]
    res = np.pad(res, ((0, 500 - len(res)), (0, 0)), constant_values=0)
    return res


def encode_by_drbert(seq):
    def get_hidden_states(encoded, model):
        with torch.no_grad():
            output = model(**encoded)
        # Get last hidden state
        return output.last_hidden_state

    maxsize = 500
    embedding_dim = 400

    seq = seq.upper()
    encoded = tokenizer_drbert.encode_plus(seq, return_tensors="pt").to(device)
    embedding = get_hidden_states(encoded, model_drbert).detach().cpu().numpy()[0, 1:-1, :embedding_dim]
    res = embedding[:maxsize]
    res = np.pad(res, ((0, 500 - len(res)), (0, 0)), constant_values=0)
    return res


def encode_by_onto(seq):
    maxsize = 500
    seq = " ".join(list(seq))
    res = bert_model_onto(seq)[0][1:-1]
    res = np.squeeze(res)[:maxsize]
    res = np.pad(res, ((0, 500 - len(res)), (0, 0)), constant_values=0)
    return res


def encode_by_aaindex(seq):
    aaindex = {
        "A": [0.2040667253326738, 1.5500304562497387, 4.4321052603964555, 0.29653022031643717, 1.0286583099810542,
              0.3297316448913777, -1.024285664418221, -0.23520452122559532, 0.8594117256873972, -0.39272583027437796,
              -0.5145500045895719, -0.158214138460611, 0.6266572093287203, -0.42408722052643294, -0.3065638190551728,
              1.7026530704394927, 0.8549957660293978, -0.5578891944340351, -0.28169795586600843,
              1.8568702001633953e-15],
        "R": [-2.7663561860197285, -3.946586336122419, -0.1993523909828032, -0.5670786865636974, -2.4235521326064737,
              -1.89413081312001, -0.3989009565860616, -1.05427811593195, -0.5362003519657095, -1.8387241741815208,
              -0.5684108080271111, 1.491240175354443, -0.6581055014435215, 0.2567342458949246, -0.3956219675831962,
              0.3040995631363612, 0.08302661685272995, 0.017772404732736516, -0.09743566227679744,
              1.856870200163388e-15],
        "N": [-4.468730412755414, 0.24241141739935373, -1.384048517866511, 1.0596441064978885, -0.6883967655409187,
              1.169724953637383, 0.22291698667055643, 1.162007121767873, -0.41690241662603156, 1.6647840485483725,
              -0.09803394416776867, 0.3845039610165121, -1.0710677092081176, 1.2280981507857758, -0.8313916608745813,
              0.9152438388893332, -0.3489079242450166, -0.541656794550879, 0.39502215037640764, 1.8568702001633965e-15],
        "D": [-5.372155437380167, -0.4862175978816571, -0.08557384430436432, 0.6513696450188442, 1.3769454687244926,
              1.5811667803806149, 2.530927167641717, 0.020112050833599387, -0.35577851678164335, -0.29142942439460395,
              -0.04440237376625617, 0.5489918820946185, -0.977060289182356, -1.3324882935404558, 0.36360217306211723,
              -0.40674000738193106, 1.0726761856992584, -0.05840182350076812, 0.05668915063381023,
              1.85687020016339e-15],
        "C": [2.576495708893488, 1.8760699256026006, -2.285979751359163, 4.44937887475275, 1.3365180405509864,
              -2.1991439187928616, 0.21330839163077622, -1.5849470812769686, -0.8930046839169443, 0.7584271354018302,
              -0.5301891640374742, 0.1673752400700567, 0.3784037153785537, 0.0692035486311704, 0.28898659697156864,
              -0.005392227325344671, -0.008040577493031584, -0.12196578549403159, -0.18960514435140455,
              1.8568702001633898e-15],
        "Q": [-2.6093769553607635, -2.3636972056386814, 0.4438190936640589, 0.21027005754123237, 0.1667809373926616,
              -0.7907286964283262, -0.28755713224340146, 0.1343801809595847, 0.7191820395296067, 0.3847424189681072,
              1.9189365677855168, -0.0820349061877445, 0.756011731210403, 1.428942470278879, 0.36034912350915804,
              -0.5973493146523726, 1.4189347231736547, 0.06095107007164686, 0.005423158889936384,
              1.8568702001633925e-15],
        "E": [-3.809180402455202, -2.9021244199989416, 3.267516402276295, -0.11685206740936376, 2.1439311857519407,
              0.7235713906810027, 1.5997457845204175, -0.5174693897697332, -0.6194798522249444, -0.5803532263315474,
              -0.09226932966505447, -0.4496984302161037, 1.0139179582210591, 0.7911894138372194, -0.08596513197248683,
              -0.0433332762831137, -1.4175989800476947, 0.2708693516741586, -0.08883875593556557,
              1.8568702001633866e-15],
        "G": [-4.0204320572791605, 5.840769582783603, -0.04218622590297184, 0.6501322776993989, -1.6429790407074105,
              2.4475571859355463, -1.5748131282648898, -1.001732343174843, -0.8823655404370778, -1.1729073649601753,
              0.6718961561966256, -0.24021401232194298, 0.15510213601965583, 0.2260345623333998, 0.25890529719706906,
              -0.5592014126792646, -0.2180814629900544, -0.03038356409257885, -0.0002841984274747057,
              1.85687020016339e-15],
        "H": [-0.356458764347396, -2.431908087891294, -1.360882659002814, 1.3952752107210076, 0.0673316704635026,
              -0.01979124639593155, -1.2996598328740774, 2.5175099044431866, -0.9165598423622477, -0.9428237674277492,
              -1.3958542851959752, -1.4146301559840644, 0.39840430484299966, -0.16350227795357386, -0.10420396215003883,
              -0.5203701873969597, 0.3522808103123684, 0.015001705041480592, -0.1564418723008084,
              1.8568702001633925e-15],
        "I": [6.086648959520446, 1.2829040536421596, 0.9319849841076945, -1.1702164414579679, -0.7340379968942574,
              -0.35318123366679627, 1.1101810930385507, 0.19848709363269917, -0.9213404948550483, 0.15188019833507158,
              0.8217160647185663, -0.9506608645138245, -1.1281318664210582, 0.26122468204868116, -0.37195317219582896,
              0.10227291588732586, 0.06276255130444887, 0.23041648722196661, -1.4328774473708217,
              1.8568702001633925e-15],
        "L": [5.210639587305067, 0.7725771406041462, 3.2154133692938918, -1.5507854238232244, 0.13423302489031066,
              0.5890952025757933, -0.4562851518321408, -0.11713852383583653, -0.2595709212031507, 1.1662959503806014,
              -1.474609472579437, 1.3632657643478676, 0.19645688364821975, 0.31830668105122795, -0.36581009295035566,
              -1.4476073936553786, 0.25603502627775787, -0.3625283861704165, 0.07625727847071305,
              1.8568702001633862e-15],
        "K": [-3.8355348197755945, -3.386748578057595, 1.476889805920191, -0.9809861287917157, -1.4077797094092839,
              -0.4245099483989886, -1.4398520012230767, -1.0630222672518468, -0.385412687825407, 1.9527943988252043,
              0.07416682561605063, -1.1780083241928645, -0.3616147351802366, -1.1181402029016232, 0.8424632188022506,
              0.005962979253225592, -0.3368044764001986, 0.03431640396550105, 0.0868499674314427,
              1.8568702001633898e-15],
        "M": [4.487820898180619, -1.6651976386540508, 0.7936282698243264, 1.4592923048128086, 1.7357365043354576,
              0.050336642829925615, -1.6182203118561045, 0.7824548339128335, 0.2402093078158453, -0.3757286883862788,
              1.9372626328787677, 0.9468349245216976, -0.6104673847492909, -0.9995823696080424, -0.6439302909465879,
              -0.23969712764475704, -0.7687129132989424, 0.016985382273948673, 0.2811744929165047,
              1.8568702001633878e-15],
        "F": [5.671646914043189, -0.41037687796925915, -1.0009975136046587, -0.6971052659772531, 0.05976606045436561,
              1.05594447739136, -0.07027112042166156, 0.857236926624087, -0.27738116289984227, -0.1529381414575803,
              -0.17768331277172433, 1.039138098647742, 0.00014563137771623385, 0.43828555978551126, 2.149881208861747,
              0.8521943320934077, -0.19163233376850497, 0.4228905701534976, 0.12306991322238552, 1.85687020016339e-15],
        "P": [-3.972808107266611, 3.119419693925638, -3.292836883200152, -4.091518594184148, 3.098057000178919,
              -1.8240500757186264, -0.819454773374471, 0.06559539264007333, -0.4114272746028685, -0.06315735595111285,
              -0.04457705752735752, 0.0006451329004658372, -0.08224312545059574, -0.039226036190614495,
              -0.12321734290586162, 0.11159163095360201, -0.04117189719983404, -0.03389240592668551,
              0.09227346657446511, 1.8568702001633905e-15],
        "S": [-3.516469887104355, 2.428524851131411, 0.1990750399350012, 0.6848970978862567, -0.9377228450925673,
              -0.47327148723538714, 0.10190462321419982, 0.6600286771420248, 1.6587146018398726, 0.6377021059592538,
              -0.5318004162910911, 0.5648102670822179, 0.30824659646796027, -0.31867396846031276, -0.4398558573353599,
              -0.0034663654962304243, -0.1751602893974423, 1.742506787557953, -0.25500017188124896,
              1.8568702001633878e-15],
        "T": [-1.3632321439581234, 1.7692738792527463, 0.1198024624665761, 0.23815231353233993, -1.0443564842036885,
              -1.434443054812606, 0.9681921471756676, 0.7420250421420116, 2.3225417150036325, -0.5004147328134138,
              -0.09668960984251881, -0.2806259061018435, -0.26380929856472146, -0.07345701421310022, 0.7470468681991911,
              -0.55608852696834, -0.847378562050008, -1.1682273616316325, -0.19901369817093445, 1.8568702001633917e-15],
        "W": [4.757410277659562, -2.5514242099334963, -3.5043889489329803, -0.3324016590360895, 0.8319300323192037,
              2.0597552590583894, -0.2969436274547756, -1.7297751667252232, 1.8602835631619403, -0.3692808056168948,
              -0.6744625569211813, -1.0257702043372168, -0.5989874831774972, 0.40494886930749174, -0.44387571606344334,
              -0.06181907117269835, 0.11747985576125437, 0.1724052673550202, 0.1735187721824445, 1.856870200163392e-15],
        "Y": [2.3204760808308205, -0.9073889863415171, -3.575801040660465, -1.158722122515026, -1.898832523475508,
              0.8093308046812985, 1.1544553217592866, 0.09883991681528456, -0.3057251722398105, 0.43348201052357627,
              0.6200628895824681, 0.4170074636279623, 2.06770295840281, -0.918858296223842, -0.6363782983775362,
              0.2960905284269239, -0.08954244274787591, -0.43252485772164806, -0.12122682890284557,
              1.8568702001633886e-15],
        "V": [4.775530021936668, 2.1696889378975084, 1.8518130879323993, -0.4292757190204824, -1.2022307371127807,
              -1.4029638674931646, 1.3846121848977098, 0.06489026827873237, -0.47919403509757297, -0.46962475514675917,
              0.1994911986045261, -1.1439559673473625, -0.1495617315206971, -0.034952504336291775, -0.26246717419264987,
              0.1509560515767096, 0.22484032422772937, 0.32335474347477006, 1.532143384785802, 1.8568702001633905e-15],
    }
    maxlength = 500
    seq = seq[:maxlength].upper()
    arr = [aaindex[aa] for aa in seq]
    res = np.array(arr)
    res = np.pad(res, ((0, 500 - len(seq)), (0, 0)), constant_values=0)
    return res


def encode_by_energy(seq):
    energy1_dict = {
        "A": [-0.20, -0.44, 0.16, 0.26, -0.46, -0.26, 0.50, -0.57, 0.10, -0.36, -0.22, 0.07, 0.14, 0.01, 0.20, -0.09,
              -0.05, -0.42, 0.05, -0.50, ],
        "C": [-0.44, -2.99, 0.21, 0.19, -0.88, -0.34, -1.11, -0.36, -0.09, -0.53, -0.43, -0.52, -0.14, -0.43, -0.24,
              0.13, -0.22, -0.62, 0.24, -0.79, ],
        "D": [0.16, 0.21, 0.17, 0.55, 0.38, 0.35, -0.23, 0.44, -0.39, 0.28, 0.35, -0.02, 1.03, 0.49, -0.37, 0.19, -0.12,
              0.69, 0.04, 0.43, ],
        "E": [0.26, 0.19, 0.55, 0.60, 0.55, 0.65, 0.18, 0.37, -0.47, 0.33, 0.29, 0.01, 0.69, 0.04, -0.52, 0.18, 0.37,
              0.39, 0.03, 0.17, ],
        "F": [-0.46, -0.88, 0.38, 0.55, -0.94, 0.17, -0.40, -0.88, 0.01, -1.08, -0.78, 0.22, 0.20, 0.26, -0.19, -0.22,
              0.02, -1.15, -0.60, -0.88, ],
        "G": [-0.26, -0.34, 0.35, 0.65, 0.17, -0.12, 0.18, 0.24, 0.19, 0.24, 0.02, -0.04, 0.60, 0.46, 0.50, 0.28, 0.28,
              0.27, 0.51, -0.35, ],
        "H": [0.50, -1.11, -0.23, 0.18, -0.40, 0.18, 0.42, -0.00, 0.79, -0.24, -0.07, 0.20, 0.25, 0.69, 0.24, 0.21,
              0.11, 0.16, -0.85, -0.26, ],
        "I": [-0.57, -0.36, 0.44, 0.37, -0.88, 0.24, -0.00, -1.16, 0.15, -1.25, -0.58, -0.09, 0.36, -0.08, 0.14, 0.32,
              -0.27, -1.06, -0.68, -0.85, ],
        "K": [0.10, -0.09, -0.39, -0.47, 0.01, 0.19, 0.79, 0.15, 0.42, 0.13, 0.48, 0.26, 0.50, 0.15, 0.53, 0.10, -0.19,
              0.10, 0.10, 0.04, ],
        "L": [-0.36, -0.53, 0.28, 0.33, -1.08, 0.24, -0.24, -1.25, 0.13, -1.10, -0.50, 0.21, 0.42, -0.01, -0.07, 0.17,
              0.07, -0.97, -0.95, -0.63, ],
        "M": [-0.22, -0.43, 0.35, 0.29, -0.78, 0.02, -0.07, -0.58, 0.48, -0.50, -0.74, 0.32, 0.01, 0.26, 0.15, 0.48,
              0.16, -0.73, -0.56, -1.02, ],
        "N": [0.07, -0.52, -0.02, 0.01, 0.22, -0.04, 0.20, -0.09, 0.26, 0.21, 0.32, 0.14, 0.27, 0.37, 0.13, 0.15, 0.10,
              0.40, -0.12, 0.32, ],
        "P": [0.14, -0.14, 1.03, 0.69, 0.20, 0.60, 0.25, 0.36, 0.50, 0.42, 0.01, 0.27, 0.27, 1.02, 0.47, 0.54, 0.88,
              -0.02, -0.37, -0.12, ],
        "Q": [0.01, -0.43, 0.49, 0.04, 0.26, 0.46, 0.69, -0.08, 0.15, -0.01, 0.26, 0.37, 1.02, -0.12, 0.24, 0.29, 0.04,
              -0.11, 0.18, 0.11, ],
        "R": [0.20, -0.24, -0.37, -0.52, -0.19, 0.50, 0.24, 0.14, 0.53, -0.07, 0.15, 0.13, 0.47, 0.24, 0.17, 0.27, 0.45,
              0.01, -0.73, 0.01, ],
        "S": [-0.09, 0.13, 0.19, 0.18, -0.22, 0.28, 0.21, 0.32, 0.10, 0.17, 0.48, 0.15, 0.54, 0.29, 0.27, -0.06, 0.08,
              0.12, -0.22, -0.14, ],
        "T": [-0.05, -0.22, -0.12, 0.37, 0.02, 0.28, 0.11, -0.27, -0.19, 0.07, 0.16, 0.10, 0.88, 0.04, 0.45, 0.08,
              -0.03, -0.01, 0.11, -0.32, ],
        "V": [-0.42, -0.62, 0.69, 0.39, -1.15, 0.27, 0.16, -1.06, 0.10, -0.97, -0.73, 0.40, -0.02, -0.11, 0.01, 0.12,
              -0.01, -0.89, -0.56, -0.71, ],
        "W": [0.05, 0.24, 0.04, 0.03, -0.60, 0.51, -0.85, -0.68, 0.10, -0.95, -0.56, -0.12, -0.37, 0.18, -0.73, -0.22,
              0.11, -0.56, -0.05, -1.41, ],
        "Y": [-0.50, -0.79, 0.43, 0.17, -0.88, -0.35, -0.26, -0.85, 0.04, -0.63, -1.02, 0.32, -0.12, 0.11, 0.01, -0.14,
              -0.32, -0.71, -1.41, -0.76, ],
    }

    energy2_dict = {
        "C": [-1.79, -1.23, -0.98, -0.48, -0.69, -0.94, -0.3, -0.96, -0.3, -0.42, -0.38, -0.2, -0.49, -0.32, 0.04, 0.55,
              -0.82, -0.4, 0, 0.07, ],
        "M": [-1.23, 0.36, -1.03, -0.41, -0.31, -0.94, -0.07, -1.1, 0.05, 0, 0.06, -0.47, -0.54, 0.31, 0.02, 1.07,
              -0.35, -0.43, 0.55, -0.25, ],
        "F": [-0.98, -1.03, -0.61, -0.66, -1.02, -0.78, -0.89, -0.82, -0.05, 0.21, -0.19, 0.14, 0.1, -0.02, 0.19, 0.2,
              -0.75, -0.22, -0.17, -0.43, ],
        "I": [-0.48, -0.41, -0.66, -0.71, -1.04, -0.98, -0.89, -0.87, -0.64, 0.4, -0.29, -0.13, -0.39, 0.39, -0.2, 0.04,
              -0.52, -0.08, -0.26, 0.25, ],
        "L": [-0.69, -0.31, -1.02, -1.04, -1.14, -1.03, -0.97, -0.6, -0.57, -0.08, -0.39, -0.07, -0.13, -0.1, -0.05,
              0.5, -0.36, -0.1, 0.1, 0.09, ],
        "V": [-0.94, -0.94, -0.78, -0.98, -1.03, -1.15, -0.6, -0.7, -0.6, -0.2, 0.06, -0.31, -0.09, -0.24, -0.02, 0.25,
              -0.35, -0.48, -0.08, -0.08, ],
        "W": [-0.3, -0.07, -0.89, -0.89, -0.97, -0.6, 0.02, -0.99, -0.08, -0.14, 0.07, -0.2, 0.4, -0.68, 0.32, 0.24,
              -0.41, -0.78, -0.3, -0.44, ],
        "Y": [-0.96, -1.1, -0.82, -0.87, -0.6, -0.7, -0.99, 0.35, -0.37, -0.32, -0.23, 0.25, -0.39, -0.74, 0.22, 0.11,
              -0.67, 0.21, -0.2, -0.45, ],
        "A": [-0.3, 0.05, -0.05, -0.64, -0.57, -0.6, -0.08, -0.37, -0.08, -0.09, -0.22, -0.01, -0.11, -0.14, 0.03, 0.1,
              -0.15, 0.07, 0, 0.41, ],
        "G": [-0.42, 0, 0.21, 0.4, -0.08, -0.2, -0.14, -0.32, -0.09, 0.04, 0.13, -0.04, 0.12, -0.18, 0.4, -0.06, 0,
              -0.15, 0.1, 0.4, ],
        "T": [-0.38, 0.06, -0.19, -0.29, -0.39, 0.06, 0.07, -0.23, -0.22, 0.13, 0.26, 0.05, -0.17, -0.27, 0.15, -0.03,
              -0.27, -0.17, 0.09, 0.36, ],
        "S": [-0.2, -0.47, 0.14, -0.13, -0.07, -0.31, -0.2, 0.25, -0.01, -0.04, 0.05, -0.13, 0.4, 0.37, 0.3, -0.09,
              -0.59, 0.61, 0.18, 0.44, ],
        "Q": [-0.49, -0.54, 0.1, -0.39, -0.13, -0.09, 0.4, -0.39, -0.11, 0.12, -0.17, 0.4, -0.08, -0.05, 0.62, 0.46,
              0.05, 0.62, 0.04, -0.21, ],
        "N": [-0.32, 0.31, -0.02, 0.39, -0.1, -0.24, -0.68, -0.74, -0.14, -0.18, -0.27, 0.37, -0.05, -0.86, -0.25,
              -0.12, 0.06, 0.04, 0.18, 0.11, ],
        "E": [0.04, 0.02, 0.19, -0.2, -0.05, -0.02, 0.32, 0.22, 0.03, 0.4, 0.15, 0.3, 0.62, -0.25, 0.21, 0.68, -0.53,
              -0.26, -0.09, 0.33, ],
        "D": [0.55, 1.07, 0.2, 0.04, 0.5, 0.25, 0.24, 0.11, 0.1, -0.06, -0.03, -0.09, 0.46, -0.12, 0.68, 0.6, -0.06,
              -0.15, -0.09, 0.84, ],
        "H": [-0.82, -0.35, -0.75, -0.52, -0.36, -0.35, -0.41, -0.67, -0.15, 0, -0.27, -0.59, 0.05, 0.06, -0.53, -0.06,
              0.14, -0.01, 0.14, -0.22, ],
        "R": [-0.4, -0.43, -0.22, -0.08, -0.1, -0.48, -0.78, 0.21, 0.07, -0.15, -0.17, 0.61, 0.62, 0.04, -0.26, -0.15,
              -0.01, 0.23, 0.3, -0.02, ],
        "K": [0, 0.55, -0.17, -0.26, 0.1, -0.08, -0.3, -0.2, 0, 0.1, 0.09, 0.18, 0.04, 0.18, -0.09, -0.09, 0.14, 0.3,
              1.45, 0.51, ],
        "P": [0.07, -0.25, -0.43, 0.25, 0.09, -0.08, -0.44, -0.45, 0.41, 0.4, 0.36, 0.44, -0.21, 0.11, 0.33, 0.84,
              -0.22, -0.02, 0.51, 0.28, ],
    }

    maxlength = 500
    seq = seq[:maxlength].upper()
    energy1 = [energy1_dict[aa] for aa in seq]
    energy2 = [energy2_dict[aa] for aa in seq]
    res = np.concatenate([energy1, energy2], axis=-1)
    res = np.pad(res, ((0, 500 - len(seq)), (0, 0)), constant_values=0)
    return res


def encode_by_pssm(fasta_file):
    with open(fasta_file) as f:
        id = f.readline().strip().replace(">", '')

    pssm_file = "./tmp/{}.pssm".format(id)
    db_path = './lib/uniref50.fasta/uniref50.fasta' # if u want to use other database of blast, replace the db_path

    if not os.path.exists(pssm_file):
        balst_path = "./lib/ncbi-blast-2.14.0+/bin/psiblast" # if you use another version psiblast replace here
        run_blast = "{} -query {} -num_threads 8 -db {} -num_iterations 3 -out ./tmp/{}.txt -out_ascii_pssm ./tmp/{}.pssm".format(
            balst_path, fasta_file, db_path, id, id)
        os.system(run_blast)

    res = []
    for line in open(pssm_file, "r").readlines()[3:-6]:
        line = line.strip()[7:].split(" ")
        cc = []
        for x in line:
            if x != "":
                cc.append(float(x))
        cc = cc[0:20]
        res.append(cc)
    res = np.array(res)[:500]
    res = np.pad(res, ((0, 500 - len(res)), (0, 0)), constant_values=0)
    return res


def encode(fasta_file):
    with open(fasta_file) as f:
        lines = f.readlines()
        seq_name = lines[0].strip().replace(">", "")
        seq = lines[-1].strip()

    features = np.concatenate([encode_by_esm2(seq),
                               encode_by_t5(seq),
                               encode_by_drbert(seq),
                               encode_by_onto(seq),
                               encode_by_pssm(fasta_file),
                               encode_by_energy(seq),
                               encode_by_aaindex(seq), ], axis=-1)

    return features[np.newaxis, :, :], seq_name, len(seq)


def main():
    filelist = ''
    save_path = ''
    argv = sys.argv[1:]
    opts, args = getopt.getopt(argv, "i:o:")
    for opt, arg in opts:
        if opt == '-i':
            filelist = arg
        elif opt == '-o':
            save_path = arg  # 保存地址

    if not os.path.exists(filelist):
        print("filelist:{} not found".format(filelist))
        return

    DeepDRP = tf.keras.models.load_model('lib/intergrated_model')  # if you want to use other model replace the path
    with open(filelist) as f:
        for line in f.readlines():
            fasta_file = line.strip()

            if not os.path.exists(fasta_file):
                print("fasta file:{} not found".format(fasta_file))
                continue

            features, id, length = encode(fasta_file)
            pred = DeepDRP.predict(features)
            pred = np.squeeze(pred)[:length]
            np.save(save_path + "/{}_result.npy".format(id), pred)

    print("finish")
    print("finish")
    print("finish")


main()

"""
conda activate DeepDRP
cd /home/ys/work/DeepDRP/
python /home/ys/work/DeepDRP/predict.py -i /home/ys/work/DeepDRP/demo/filelist -o /home/ys/work/DeepDRP/results
"""
