#!/usr/bin/env bash

set -Eeuo pipefail

python /app/cmd/fetch.py users \
    --out-dir=/app/shared/dumps/fluon_refsrv \
    --out-name=user_ids.tsv
python /app/cmd/fetch.py interactions \
    --out-dir=/app/shared/dumps/fluon_refsrv \
    --out-name=user_interactions.tsv
python /app/cmd/fetch.py statements \
    --repository wisski_2024-08-13 \
    --out-dir=/app/shared/dumps/wisski \
    --out-name=statements.nt
python /app/cmd/fetch.py itemlist \
    --repository wisski_2024-08-13 \
    --out-dir=/app/shared/dumps/wisski \
    --out-name=itemlist.nt
python /app/cmd/fetch.py process \
    --res-dir=/app/datasets/wisski/res \
    --dumps-dir=/app/shared/dumps/wisski \
    --out-dir=/app/shared/datasets/wisski
python /app/cmd/sample.py \
    -vvv \
    --save_dir /app/shared/datasets/wisski \
    --interactions_file /app/shared/dumps/fluon_refsrv/user_interactions.tsv \
    --user_file /app/shared/dumps/fluon_refsrv/user_ids.tsv \
    --entities_file /app/shared/datasets/wisski/entities_id.txt \
    --items_file /app/shared/datasets/wisski/items_id.txt \
    --knowledge_graph_file /app/shared/datasets/wisski/kg_final.txt \
    profiles

cd /app/kgat/Model
python Main.py \
    --alg_type kgat \
    --dataset wisski \
    --regs "[1e-5,1e-5]" \
    --layer_size "[64,32,16]" \
    --embed_size 64 \
    --lr 0.0001 \
    --epoch 1000 \
    --verbose 50 \
    --batch_size 1024 \
    --node_dropout "[0.1]" \
    --mess_dropout "[0.1,0.1,0.1]" \
    --use_att True \
    --use_kge True \
    --model_type bprmf \
    --save_flag 1 \
    --pretrain -1 \
    --report 0

cd /app/kgat/Model
python Main.py \
    --alg_type kgat \
    --dataset wisski \
    --regs "[1e-5,1e-5]" \
    --layer_size "[64,32,16]" \
    --embed_size 64 \
    --lr 0.0001 \
    --epoch 1000 \
    --verbose 50 \
    --batch_size 1024 \
    --node_dropout "[0.1]" \
    --mess_dropout "[0.1,0.1,0.1]" \
    --use_att True \
    --use_kge True \
    --model_type bprmf \
    --save_flag -1 \
    --pretrain 1 \
    --report 0

cd /app/kgat_pytorch
python main_kgat.py \
    --use_pretrain 1 \
    --evaluate_every 10 \
    --Ks '[20, 40, 60]' \
    --data_name wisski \
    --data_dir /app/shared/datasets

LATEST_MODEL=$(
    find /app/shared/model/wisski/embed-dim64_relation-dim64_random-walk_bi-interaction_64-32-16_lr0.0001_pretrain1 \
        -newer /app/kgat_pytorch \
        -name '*.pth' \
        -exec stat -c '%Y %n' {} \; |
        sort -nr |
        head -n 1 |
        cut -f2 -d' '
)
cd /app/shared/clustering/
mkdir -p /app/shared/clustering/wisski
CLUSTERING_OUT_DIR=/app/shared/clustering/wisski python /app/cmd/proc_clustering/cluster_training.py \
    --data_name wisski \
    --data_dir /app/shared/datasets/ \
    --Ks '[20, 40, 60]' \
    --pretrain_model_path "$LATEST_MODEL"

cd /app/shared/clustering/wisski/
python /app/cmd/proc_clustering/cluster_inspection.py \
    --cluster /app/shared/clustering/wisski/clustering.joblib \
    --data /app/shared/clustering/wisski/clustering_data.npy \
    --stats /app/shared/clustering/wisski/cluster_stats.joblib \
    --plotdir /app/shared/clustering/wisski/plots/ \
    --outfile /app/shared/clustering/wisski/cluster.csv
RECO_RAW_DIR=/app/shared/raw/wisski python /app/cmd/proc_clustering/cluster_recommender.py \
    --data_name wisski \
    --data_dir /app/datasets \
    --Ks '[20, 40, 60]' \
    --pretrain_model_path "$LATEST_MODEL"
awk -v \
    OFS=',' \
    -f /app/datasets/wisski/res/convert_ids_to_wisski_model.awk /app/shared/datasets/wisski/items_id.txt /app/datasets/fluon_refsrv/user_ids.tsv /app/shared/raw/wisski/recommendations.csv \
    >/app/output/final/wisski/recommendations.csv
awk -v \
    OFS=',' \
    -f /app/datasets/wisski/res/convert_ids_to_wisski_cluster.awk /app/shared/datasets/wisski/items_id.txt /app/shared/clustering/wisski/cluster.csv \
    >/app/output/final/wisski/cluster.csv
