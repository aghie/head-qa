

![](https://cdn.pixabay.com/photo/2016/11/09/16/24/virus-1812092_960_720.jpg)


HEAD-QA is a multi-choice ***HEA***lthcare ***D***ataset. The questions come from exams to access a specialized position in the Spanish healthcare system, and are challenging even for highly specialized humans. They are designed by the [Ministerio de Sanidad, Consumo y Bienestar Social](https://www.mscbs.gob.es/), who also provides direct [access](https://fse.mscbs.gob.es/fseweb/view/public/datosanteriores/cuadernosExamen/busquedaConvocatoria.xhtml) to the exams of the last 5 years (in Spanish). 

> Date of the last update of the documents object of the reuse: January, 14th, 2019.

HEAD-QA tries to make these questions accesible for the Natural Language Processing community. We hope it is an useful resource towards achieving better QA systems. The dataset contains questions about the following topics:

- Medicine 
- Nursing
- Psychology
- Chemistry
- Pharmacology
- Biology

# Download

[ES_HEAD dataset](https://drive.google.com/open?id=1dUIqVwvoZAtbX_-z5axCoe97XNcFo1No)

[EN_HEAD dataset](https://drive.google.com/open?id=1phryJg4FjCFkn0mSCqIOP2-FscAeKGV0)

[Data (images, pdfs, etc)](https://drive.google.com/open?id=1a_95N5zQQoUCq8IBNVZgziHbeM-QxG2t)

[HEAD-QA paper](https://www.aclweb.org/anthology/P19-1092/)

# Examples

*Question (medicine)*: A 13-year-old girl is operated on due to Hirschsprung illness at 3 months of age. Which of the following tumors is more likely to be present? 

1. Abdominal neuroblastoma
2. **Wilms tumor**
3. Mesoblastic nephroma
4. Familial thyroid medullary carcinoma.

*Question (pharmacology)* The antibiotic treatment of choice for Meningitis caused by Haemophilus influenzae serogroup b is:
1. Gentamicin 
2. Erythromycin 
3. Ciprofloxacin 
4. **Cefotaxime**

*Question (psychology)*	According to research derived from the Eysenck model, there is evidence that extraverts, in comparison with introverts:
1. Perform better in surveillance tasks.
2. Have greater salivary secretion before the lemon juice test.
3. **Have a greater need for stimulation.**
4. Have less tolerance to pain.


# Leaderboard (general) 

#### Unsupervised setting

| Model | Avg. accuracy | Avg. POINTS |
|-------|:----------:|:--------:|
| [Liu et al. (2020)](https://arxiv.org/abs/2008.02434) | **44.4** | **172.3**|
| [IR Baseline - Vilares and Gómez-Rodríguez (2019)](https://www.aclweb.org/anthology/P19-1092/) | 34.6 | 71.2 |


#### Supervised setting

| Model | Avg. accuracy | Avg. POINTS |
|-------|:-------------:|:-----------:|
| [Liu et al. (2020)](https://arxiv.org/abs/2008.02434) | **46.7** | **199.8** |
| [IR Baseline - Vilares and Gómez-Rodríguez (2019)](https://www.aclweb.org/anthology/P19-1092/) | 37.2 | 111.8 |


# Leaderboard (per healthcare discipline)

#### Performance for each healthcare discipline on the unsupervised setting

##### Accuracy

| Model | Biology | Medicine | Nursing | Pharmacology | Psychology | Chemistry|
|-------|:-------:|:--------:|:-------:|:------------:|:----------:|:-------:|
| [Liu et al. (2020)](https://arxiv.org/abs/2008.02434) | 45.5 | 42.4 | 42.3 | 48.0 | 44.3 | 44.3 | 
|[IR Baseline - Vilares and Gómez-Rodríguez (2019)](https://www.aclweb.org/anthology/P19-1092/) | 37.9 | 30.3 | 32.6 | 38.7 | 34.7 | 33.7 |


##### POINTS 

| Model | Biology | Medicine | Nursing | Pharmacology | Psychology | Chemistry|
|-------|:-------:|:--------:|:-------:|:------------:|:----------:|:-------:|
| [Liu et al. (2020)](https://arxiv.org/abs/2008.02434) | 189.4 | 158.8 | 158.8 | 209.6 | 160.6  | 173.0 | 
|[IR Baseline - Vilares and Gómez-Rodríguez (2019)](https://www.aclweb.org/anthology/P19-1092/) | 116.8 | 48.6 | 67.8 | 125.0 | 87.6 | 79.6 |


#### Performance for each healthcare discipline on the supervised setting

#####  Accuracy


| Model | Biology | Medicine | Nursing | Pharmacology | Psychology | Chemistry|
|-------|:-------:|:--------:|:-------:|:------------:|:----------:|:-------:|
| [Liu et al. (2020)](https://arxiv.org/abs/2008.02434) | 47.1 | 45.6 | 46.7 | 48.8 | 46.7 | 45.5 
| [IR Baseline - Vilares and Gómez-Rodríguez (2019)](https://www.aclweb.org/anthology/P19-1092/) | 39.8 | 33.3 | 36.4 | 42.2 | 35.7 | 36.0 |


#### POINTS 

| Model | Biology | Medicine | Nursing | Pharmacology | Psychology | Chemistry|
|-------|:-------:|:--------:|:-------:|:------------:|:----------:|:-------:|
| [Liu et al. (2020)](https://arxiv.org/abs/2008.02434) | 200.0 | 198.4 | 184.6 | 217.0 | 197.2 | 186.8 | 
|[IR Baseline - Vilares and Gómez-Rodríguez (2019)](https://www.aclweb.org/anthology/P19-1092/) | 135.0 | 76.5 | 104.5 | 157.5 | 96.5 | 101.0 |



# Legal requirements

The Ministerio de Sanidad, Consumo y Biniestar Social allows the redistribution of the exams and their content under [certain conditions](https://www.mscbs.gob.es/avisoLegal/home.htm): 

- The denaturalization of the content of the information is prohibited in any circumstance.
- The user is obliged to cite the source of the documents subject to reuse.
- The user is obliged to indicate the date of the last update of the documents object of the reuse.
