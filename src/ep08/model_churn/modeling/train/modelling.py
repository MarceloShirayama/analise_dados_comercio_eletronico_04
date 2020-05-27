import pandas as pd
import os
import sqlalchemy
from sklearn import tree
from sklearn import ensemble
from sklearn import model_selection
from sklearn import metrics
from sklearn import preprocessing
import matplotlib.pyplot as plt

TRAIN_DIR = os.path.join( os.path.abspath('.'), 'src', 'ep07', 'model_churn', 'modeling','train' )
TRAIN_DIR = os.path.dirname( os.path.abspath(__file__) )
MODELING_DIR = os.path.dirname( TRAIN_DIR )
BASE_DIR = os.path.dirname( MODELING_DIR )
DATA_DIR = os.path.join( os.path.dirname( os.path.dirname( os.path.dirname( BASE_DIR ) ) ), 'data')
MODEL_DIR = os.path.join( BASE_DIR, 'models')

engine = sqlalchemy.create_engine( "sqlite:///" + os.path.join(DATA_DIR, 'olist.db'))

abt = pd.read_sql_table( 'tb_abt_churn', engine ) # Tem TUDOOOOOO

df_oot = abt[ abt["dt_ref"]==abt["dt_ref"].max() ].copy() # Filtrando base out of time
df_oot.reset_index( drop=True, inplace=True )

df_abt = abt[ abt["dt_ref"]<abt["dt_ref"].max() ].copy() # Filtrando base abt

# Definindo varáveis
target = 'flag_churn' # Variável resposta!
to_remove = ['dt_ref', 'seller_city', 'seller_id', target] # Variáveis para retirar das analises

features = df_abt.columns.tolist() # Todas variáveis do dataset
for f in to_remove:
    features.remove(f) # Remove uma variável por vez, das que devem ser removidas

cat_features = df_abt[features].dtypes[ df_abt[features].dtypes == 'object' ].index.tolist()
num_features = list( set(features) - set(cat_features) )

# Separando entre treino e teste
X = df_abt[features] # matriz de features ou variáveis
y = df_abt[target] # Vetor da resposta ou target

# Separa treino e validação
X_train, X_test, y_train, y_test = model_selection.train_test_split(X,
                                                                    y,
                                                                    test_size=0.2,
                                                                    random_state=1992)

X_train.reset_index(drop=True, inplace=True)
X_test.reset_index(drop=True, inplace=True)

onehot = preprocessing.OneHotEncoder(sparse=False, handle_unknown='ignore')
onehot.fit( X_train[cat_features] ) # Treinou o onehot!

onehot_df = pd.DataFrame( onehot.transform( X_train[cat_features] ),
                          columns=onehot.get_feature_names(cat_features) )

df_train = pd.concat([X_train[num_features], onehot_df], axis=1)
features_fit = df_train.columns.tolist()

# Modelo
clf = tree.DecisionTreeClassifier(min_samples_leaf=100)
clf.fit( df_train[features_fit], y_train )

rf = ensemble.RandomForestClassifier(n_estimators=500, min_samples_leaf=75, n_jobs=-3)
rf.fit(df_train[features_fit], y_train)

# Importancia das vairáveis
pd.Series( clf.feature_importances_, index = df_train.columns).sort_values(ascending=False)[:10]

# Analise na base de treino
y_train_proba = clf.predict_proba( df_train ) # Calcula a probabilidade
y_train_proba_rf = rf.predict_proba(df_train) # Calcula a probabilidade

# Fazendo o gráfico da curva ROC
roc_train = metrics.roc_curve(y_train, y_train_proba[:,1] )
auc_train = metrics.roc_auc_score(y_train, y_train_proba[:,1] )

roc_train_rf = metrics.roc_curve(y_train, y_train_proba_rf[:,1] )
auc_train_rf = metrics.roc_auc_score(y_train, y_train_proba_rf[:,1] )

# Análise na base de teste
onehot_df_test = pd.DataFrame( onehot.transform( X_test[cat_features] ),
                               columns=onehot.get_feature_names(cat_features) )
df_predict = pd.concat( [X_test[num_features], onehot_df_test], axis=1 )
y_test_pred = clf.predict( df_predict )
y_test_proba = clf.predict_proba( df_predict )

y_test_proba_rf = rf.predict_proba( df_predict )

# ROC na teste
roc_test = metrics.roc_curve( y_test, y_test_proba[:,1] )
auc_test = metrics.roc_auc_score(y_test, y_test_proba[:,1] )
roc_test_rf = metrics.roc_curve( y_test, y_test_proba_rf[:,1] )
auc_test_rf = metrics.roc_auc_score(y_test, y_test_proba_rf[:,1] )

# Análise na base de oot
onehot_df_oot = pd.DataFrame( onehot.transform( df_oot[cat_features] ),
                               columns=onehot.get_feature_names(cat_features) )
df_oot_predict = pd.concat( [df_oot[num_features], onehot_df_oot], axis=1 )
oot_proba = clf.predict_proba( df_oot_predict )
oot_proba_rf = rf.predict_proba( df_oot_predict )

# ROC na teste
roc_oot = metrics.roc_curve( df_oot[target], oot_proba[:,1] )
auc_oot = metrics.roc_auc_score( df_oot[target], oot_proba[:,1] )

roc_oot_rf = metrics.roc_curve( df_oot[target], oot_proba_rf[:,1] )
auc_oot_rf = metrics.roc_auc_score( df_oot[target], oot_proba_rf[:,1] )

# Fazendo o predict
df_abt_onehot = pd.DataFrame( onehot.transform( abt[cat_features] ),
                              columns=onehot.get_feature_names(cat_features) )
df_abt_predict = pd.concat( [abt[num_features], df_abt_onehot], axis=1 )

probs = clf.predict_proba( df_abt_predict )
abt['score_churn'] = clf.predict_proba( df_abt_predict )[:,1]
abt_score = abt[[ 'dt_ref','seller_id', 'score_churn']]
# abt_score.to_sql( 'tb_churn_score', engine, index=False, if_exists='replace' )


""" plt.plot( roc_train[0], roc_train[1] )
plt.plot( roc_test[0], roc_test[1] )
 """
plt.plot( roc_oot[0], roc_oot[1] )

""" plt.plot( roc_train_rf[0], roc_train_rf[1] )
plt.plot( roc_test_rf[0], roc_test_rf[1] )
 """
plt.plot( roc_oot_rf[0], roc_oot_rf[1] )

plt.xlabel("1 - Especificidade")
plt.ylabel("Sensibilidade")
plt.title("Curva ROC")
plt.legend([#f"Treino Tree: {auc_train} ",
            #f"Teste Tree: {auc_test}",
            f"OOT Tree: {auc_oot}",
            #f"Treino RF: {auc_train_rf} ",
            #f"Teste RF: {auc_test_rf}",
            f"OOT RF: {auc_oot_rf}"] )
plt.show()

# Salvando o modelo
model_data = pd.Series( {
    'num_features': num_features,
    'cat_features': cat_features,
    'onehot': onehot,
    'features_fit':features_fit,
    'model':rf,
    'acc_oot':auc_oot_rf,
    'acc_train':auc_train_rf,
    'acc_test':auc_test_rf,
    'cutoff':0.7
} )

model_data.to_pickle( os.path.join(MODEL_DIR, 'arvore_decisao.pkl') )